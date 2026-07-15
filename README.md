# usage
Plugin-based Python CLI/TUI to fetch usage, quota, and billing from cloud and AI providers

## Usage

Install:

```sh
uv tool install .
```

Run (default opens an interactive TUI):

```sh
usage
```

Output modes:

- (default) interactive TUI with gauges
- `--cli` formatted tables, one-shot report
- `--text` plain text
- `--json` machine-readable JSON

Sources: `github`, `hetzner`, `claude_code` (plus the built-in `demo`). Credentials go in `.env` (see `.env.template`); preferences in `config.yml` (see `config.example.yml`).

- [Design doc](docs/specs/2026-07-15-usage-design.md)
- [Authoring a source](docs/authoring-a-source.md)
