# Authoring a source

A source is one file in `src/usage/sources/` that returns a `SourceReport` of flat
`Metric` rows. Discovery is automatic - no registration anywhere.

## Steps

1. Copy `src/usage/sources/_template.py` to `<name>.py`.
2. Set `name` and, if you read credentials from `.env`, `env_prefix` (the part before `_`).
   Use `None` if the source authenticates another way (e.g. a local CLI).
3. In `fetch(ctx)`:
   - read tokens from `ctx.creds` (already sliced to your `env_prefix`);
   - read preferences from `ctx.config` (your `config.yml` slice under `sources.<name>`);
   - make HTTP calls with `ctx.http` (a shared `httpx.AsyncClient`), or spawn a subprocess;
   - return `SourceReport(source=self.name, metrics=[...], warnings=[...])`.
4. Export `source = YourSource()` at module bottom.

Run it alone: `uv run usage --sources <name> --text`.

## Metric shape

- `dimension` is `"cost"` (money; put the currency in `unit`, e.g. `"EUR"`) or
  `"quota"` (units with a ceiling; set `limit`, e.g. minutes or `%`).
- `scope` labels the account/org/project the row belongs to.

## Worked examples

- `demo.py` - no credentials, canned metrics.
- `github.py` - HTTP API, `env_prefix="GITHUB"`.
- `hetzner.py` - HTTP API, `env_prefix="HETZNER"`.
- `claude_code.py` - subprocess, `env_prefix=None`.

## Tests

Add `tests/sources/test_<name>.py`. Put a recorded, anonymized response in
`tests/fixtures/` and drive `fetch` with `httpx.MockTransport` (HTTP) or test the
parser against a text fixture (subprocess). No live API calls in tests.
