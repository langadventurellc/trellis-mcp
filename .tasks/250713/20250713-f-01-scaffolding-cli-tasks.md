# F-01 · Scaffolding & CLI — Task Checklist  (bootstrap scope)

Each task is ≤ 2 h (“XS” < 1 h, “S” 1–2 h, “M” 2–4 h).

| Size key | XS < 1 h | S 1-2 h | M 2-4 h |
|----------|----------|---------|---------|

## Checklist

- [ ] **S-01** (XS) Create `src/trellis_mcp/` package and `__init__.py`
- [ ] **S-02** (S) Add `pyproject.toml` with deps (click ≥ 8.1, fastmcp ≥ 0.7) & build-system
- [ ] **S-03** (XS) Add `.gitignore` and bootstrap `README.md`
- [ ] **S-04** (XS) Configure **uv** lock file; verify `uv pip install -e .` works
- [ ] **S-05** (S) Add **pre-commit** config (black, flake8, pyright, pytest)
- [ ] **S-06** (XS) Set up pytest skeleton (`tests/conftest.py`)
- [ ] **S-07** (XS) Implement `settings.py` with default config values
- [ ] **S-08** (S) Implement `loader.py` — load YAML/TOML, apply env overrides
- [ ] **S-09** (XS) Create `trellis_mcp.cli:cli` Click command group
- [ ] **S-10** (S) Implement `serve` sub-command — start FastMCP server (STDIO)
- [ ] **S-11** (S) Add `--http HOST:PORT` flag — attach HTTP transport
- [ ] **S-12** (S) Implement `init` sub-command — create minimal `planning/` tree
- [ ] **S-13** (XS) Unit tests for settings loader & precedence chain
- [ ] **S-14** (M) Integration test: start `trellis-mcp serve` and hit with FastMCP test client

### Quality Gates
* **Black, flake8, pyright** all pass.
* **pytest** coverage ≥ 90 % on new code.
* `trellis-mcp serve` prints active transport(s) at startup.
* CLI commands work on macOS, Linux, Windows (CI matrix).
