# usage

A plugin-based Python CLI/TUI that fetches **usage, quota, and billing** information from cloud and AI providers and presents it in one place.

Each system is an isolated module (a "provider") behind a shared core that handles config, auth, CLI flags, and output rendering. Add a new system by writing one provider module - no core changes.

## Tech stack

- Python 3.12+
- `pyproject.toml` (hatchling), dependencies via `uv`
- `pydantic` v2 / `pydantic-settings` for config
- `rich` / `textual` for the TUI and formatted output
- `httpx` for provider HTTP calls
- `pytest` for tests

## Output modes

The default is a **fancy interactive TUI** with graphs. Alternative outputs via flags:

- (default) interactive TUI with charts
- `--cli` non-interactive formatted tables, one-shot report
- `--text` plain text
- `--json` machine-readable JSON

## Configuration

- `.env` (gitignored) - credentials: provider tokens, API keys, service-account JSON paths. Prefixed per provider, e.g. `HETZNER_API_TOKEN=...`, `GITHUB_TOKEN=...`.
- `.env.template` (tracked) - documents the env vars without secrets.
- `config.yml` (tracked) - per-provider include/exclude lists and preferences, e.g. which GitHub orgs/accounts to report, which Hetzner projects, etc.

## v1 scope

Core framework plus three reference providers:

1. **GitHub** - Actions minutes per account and org (configurable include/exclude).
2. **Hetzner** - cloud billing / cost.
3. **Claude Code** - subscription usage + API credits.

Additional providers (GCP, AWS, Scaleway, z.ai, Kimi, Cursor) are added incrementally once the contract is locked.

## Repo layout

Bare git + worktree. The canonical worktree is `main/`. See `~/.claude/rules/worktree-operations.md`.

```
usage/
├── .bare/          # bare repo (GIT_DIR)
├── main/           # default-branch worktree - work here
└── .workspace/     # shared local-only files, symlinked into worktrees
```

## AI state files

| File | Tracked? | Purpose |
|---|---|---|
| `.ai-settings.md` | yes | Project metadata, canonical commands |
| `.ai-local.md` | no (in `.workspace/`) | Cross-agent in-flight state |
| `.ai-secrets.md` | no (in `.workspace/`) | Credentials - never commit |
| `.env` | no (in `.workspace/`) | Real env; `.env.template` stays tracked |

## Design and planning

Architecture and design decisions live in `docs/superpowers/specs/`. Implementation plans in `docs/superpowers/plans/`.

## How to add a provider

Documented after the v1 contract is locked. See the design doc and `docs/authoring-a-provider.md`.
