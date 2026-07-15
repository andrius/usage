---
name: usage-v1-design
status: approved
created: 2026-07-15T09:09:27Z
updated: 2026-07-15T09:09:27Z
---

# usage - design spec

- **Repo:** [andrius/usage](https://github.com/andrius/usage) (public), bare git + worktree; canonical worktree `main/`

## Problem

Usage, quota, and billing data is scattered across many unrelated systems - cloud bills (Hetzner, later GCP/AWS/Scaleway), CI meters (GitHub Actions minutes), and AI subscriptions/credits (Claude Code, later z.ai/Kimi/Cursor). Each has its own auth, its own API shape, and its own notion of "usage". There is no single place to see all of it.

## Goal

A plugin-based Python CLI/TUI that fetches usage, quota, and billing from each system behind one command, with a fancy default TUI and machine/text/table alternatives. Adding a system means dropping in one source module - no core changes.

## v1 scope

Core framework plus three reference sources that together stress every part of the contract:

1. **github** - Actions minutes per account and org (quota, HTTP API).
2. **hetzner** - estimated monthly cost (cost, HTTP API, run-rate estimate).
3. **claude_code** - subscription usage (quota, **local subprocess** - proves sources are not always HTTP).

**Out of scope for v1:** GCP, AWS, Scaleway, z.ai, Kimi, Cursor (added incrementally once the contract is locked); historical trend graphs and any persistence (see Future).

## Non-goals

- No persistence, no database, no history. Each run is a fresh snapshot. (The data model carries timestamps so trends can be added later without rework.)
- No daemon, no scheduling. On-demand only.
- No write operations against any provider - read-only everywhere.

## Architecture

A thin core does four jobs; sources are dumb leaves.

```
config (load .env + config.yml)
   |
   v
core (discover sources -> run each in isolation -> aggregate)
   |
   v
render (tui | cli | text | json)
```

Layers and boundaries:

- **Sources are leaves.** A source takes a `FetchContext` (its own creds + config slice + time window + a shared HTTP client) and returns a `SourceReport` of flat `Metric` rows. A source never imports another source, never imports a renderer, never knows the CLI exists.
- **Transport is the source's choice.** `fetch()` is transport-agnostic. HTTP sources use `ctx.http`; `claude_code` spawns a subprocess and ignores `ctx.http`. The contract does not assume HTTP.
- **Side effects at the edges.** Domain logic (the flat `Metric` model) does not import infrastructure (`httpx`, `textual`). Renderers import the model; the model imports nothing downstream.
- **Design for extraction.** `core`, `config`, `models`, `render`, and `sources` are each plausible standalone units with explicit boundaries.

## Repo layout

```
usage/main/
  pyproject.toml              # hatchling; [project.scripts] usage = usage.cli:main
  config.example.yml          # tracked template for config.yml
  src/usage/
    __init__.py
    __main__.py               # python -m usage
    cli.py                    # argparse flags + dispatch
    config.py                 # load .env + config.yml; per-source slicing
    core.py                   # discover, run, aggregate
    models.py                 # Metric, SourceReport, FetchContext, DateRange, Source
    render/
      tui.py                  # textual app (default render)
      table.py                # rich table (--cli)
      text.py                 # plain text (--text)
      json.py                 # JSON (--json)
    sources/
      __init__.py             # auto-discovery scan
      _template.py            # "bake a source" starter
      demo.py                 # no-creds canned source (reference + smoke test)
      github.py
      hetzner.py
      claude_code.py
  tests/
    fixtures/                 # anonymized recorded responses + /usage text
    test_models.py test_config.py test_core.py
    test_render_json.py test_render_text.py ...
    sources/test_github.py test_hetzner.py test_claude_code.py
  docs/
    specs/        # this doc + future specs
    plans/        # implementation plans
    authoring-a-source.md
```

## Data contract (`models.py`)

The flat `Metric` is the keystone: one row per measurement makes aggregation (total cost, quota utilization) and every renderer trivial. Cost metrics carry currency in `unit`; quota metrics carry `used`/`limit`.

```python
@dataclass(frozen=True)
class DateRange:
    since: date
    until: date

@dataclass(frozen=True)
class Metric:
    source: str
    scope: str               # "org:acme", "user:alice", "project:web-prod", "plan:claude-code"
    label: str               # "Actions minutes", "Estimated monthly cost", "Weekly usage"
    dimension: Literal["cost", "quota"]
    used: Decimal
    limit: Decimal | None = None   # quota ceiling / budget; None when N/A
    unit: str = ""                 # "USD", "EUR", "minutes", "%", "credits", "tokens"
    window: DateRange | None = None
    fetched_at: datetime           # UTC

@dataclass(frozen=True)
class FetchContext:
    creds: Mapping[str, str]        # this source's env vars, already resolved+sliced
    config: Mapping[str, Any]       # this source's config.yml slice
    window: DateRange
    http: httpx.AsyncClient         # shared, reused across sources; optional to use

@dataclass(frozen=True)
class SourceReport:
    source: str
    metrics: list[Metric] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

class Source(Protocol):
    name: str
    async def fetch(self, ctx: FetchContext) -> SourceReport: ...
```

Convention: hard failures raise (the runner catches them per-source and records an error); soft caveats go in `warnings`.

## Source discovery

`sources/__init__.py` scans the package at runtime via `pkgutil.iter_modules`. Any module exporting a module-level `source` instance (implementing the `Source` protocol) is registered under `source.name`. Modules whose name starts with `_` (like `_template`) are skipped. **Drop a file in, get a source - no registration anywhere.** Enable/disable and include/exclude are config, not code.

## Configuration

Two files, both gitignored (the repo is public; real org names and tokens never get committed), each with a tracked template:

- **`.env`** - credentials. Per-source, prefixed: `GITHUB_TOKEN`, `HETZNER_API_TOKEN`. (`claude_code` needs none - it uses the ambient `claude` CLI auth.) Template: `.env.template`.
- **`config.yml`** - per-source preferences (include/exclude lists) and the default window. Template: `config.example.yml`.

```yaml
# config.example.yml
window:
  default_days: 30
sources:
  github:
    include: [acme]        # org/user logins to report; empty = all accessible to the token
    exclude: []
  hetzner:
    include_projects: []   # empty = all projects the token can see
  claude_code: {}
```

**Cred slicing:** each source declares `env_prefix: str | None`. The core loads `.env` once and passes into `ctx.creds` only the keys starting with `{prefix}_`. A source with `env_prefix = None` gets an empty `ctx.creds` and fetches its own way (subprocess, ambient auth). This keeps sources testable (inject creds) and decoupled from the global environment.

## CLI and output

```
usage [--sources a,b] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--json | --text | --cli]
```

- **(default)** textual TUI - gauges for quota, bars for cost, total-cost footer, per-source sections/tabs, status area for errors/warnings.
- `--cli` - rich formatted table, one-shot.
- `--text` - plain text, grouped by source.
- `--json` - machine-readable JSON (flat metrics).
- `--sources` - comma-separated subset; default = all discovered. Unknown names are reported as errors, not raised.
- `--since`/`--until` - override the window (default: today minus `config.window.default_days` to today).

## The three v1 sources

### github (HTTP, quota)

GitHub Billing REST API. For the authenticated user and each configured org:

- `GET /users/{user}/settings/billing/actions` and `GET /orgs/{org}/settings/billing/actions`
- Response: `total_minutes_used`, `total_paid_minutes_used`, `included_minutes`, `minutes_used_breakdown` (per OS).

Emits one quota `Metric` per org/user: `used = total_minutes_used`, `limit = included_minutes`, `unit = "minutes"`, `scope = "org:{x}"` / `"user:{x}"`. Include/exclude from `config.yml`. Cred: `GITHUB_TOKEN` (PAT with billing read).

### hetzner (HTTP, cost - estimated)

The Hetzner Cloud API has **no billing/spend endpoint**, so cost is an estimate: sum current resources (servers, volumes, load balancers, IPs, etc.) multiplied by current prices.

- `GET /v1/servers`, `GET /v1/volumes`, `GET /v1/load_balancers`, ... and `/v1/prices`.
- Emits one cost `Metric` per project: `used = estimated_monthly_cost` (resources x prices), `unit = "EUR"`, `scope = "project:{x}"`. Cred: `HETZNER_API_TOKEN`. This is a **run-rate estimate, not an invoice total** - surfaced in the metric label ("Estimated monthly cost") and a warning.

### claude_code (subprocess, quota)

Not HTTP. Runs the local Claude Code CLI headless and parses its text:

- `claude -p '/usage'` via `asyncio.create_subprocess_exec`.
- Output is scrape-parsed (regex) for: current session % used + reset time; weekly usage (all models) %; weekly usage per model (e.g. Fable) %. Request/session counts are captured as informational warnings, not cost/quota metrics.
- Emits quota `Metric`s: `used = <percent>`, `limit = 100`, `unit = "%"`, `scope = "plan:claude-code"`, one per period/model, with the reset time in a warning.
- **Parse fragility:** the `/usage` text format is not a stable contract. On any parse miss, the unparsed raw output is appended to `warnings` and whatever metrics were found are still emitted. Requires `claude` present + authenticated; absence is a per-source error (the core reports it, the run continues).

## Error handling

Per-source isolation, already proven in the spike:

- A hard failure in one source becomes an error string for that source; it never crashes the run or blocks other sources.
- Unknown `--sources` names are errors, not exceptions.
- Errors are surfaced in the chosen renderer (status area in the TUI; trailing lines in text/table; an `errors` array in JSON) and set a non-zero exit code.
- Soft caveats (partial data, deprecation, estimate disclaimers) travel in `SourceReport.warnings`.

## Testing

No live API calls. Record real responses once, anonymize, commit as fixtures under `tests/fixtures/`:

- GitHub billing JSON, Hetzner server+price JSON, and a sanitized `/usage` text fixture (derived from a real capture, scrubbed of anything sensitive).

Coverage:

- Unit: model serialization (`Decimal`/`datetime` handling), config parsing + cred slicing, discovery (finds `demo`, skips `_template`), each source's parser against its fixture.
- Integration: `core` runs `demo` + a fake source, asserts aggregation and per-source error isolation.
- Renderers: assert JSON determinism and text/table output against canned metrics.

## Authoring a source

`docs/authoring-a-source.md` walks through: copy `sources/_template.py` to `<name>.py`, set `name` and `env_prefix`, read `ctx.creds`/`ctx.config`, implement `fetch()` to return a `SourceReport` of `Metric` rows, export `source = YourSource()`. Discovery is automatic. The `demo` source and the three v1 sources serve as worked examples across transports (no-creds, HTTP, subprocess).

## Future (explicitly out of v1)

- **Trend graphs / persistence:** add a local snapshot store and trend views. The `Metric` schema already carries `window` and `fetched_at` so this is an additive change, not a redesign.
- **More sources:** GCP, AWS, Scaleway, z.ai, Kimi, Cursor - each one file, following the v1 contract.
- **Scheduling/cron:** a wrapper or system timer to run periodically (only needed once trends exist).

## Risks

- **Hetzner has no billing API** - cost is an estimate, clearly labeled. If invoice accuracy becomes required, there is no clean path (console-only) and this source would need rethinking.
- **`claude_code` scrapes CLI text** - format changes will break the parser. Mitigated by defensive parsing + raw-output-in-warnings, but it is inherently fragile.
- **Provider auth changes** - tokens, scopes, and endpoints drift over time. Each source is isolated so breakage is contained and visible, not silent.
