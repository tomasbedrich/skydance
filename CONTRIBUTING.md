# Setup

Install [uv](https://docs.astral.sh/uv/), then install the project with its dev dependencies:

```text
$ uv sync
```

# Development Tasks

```text
$ uv run pytest
$ uv run mypy skydance tests
$ uv run ruff format .
$ uv run ruff check .
```

`tests/test_manual.py` needs a physical Wi-Fi relay on the local network (set `IP`). It is skipped when the `CI` environment variable is set.

# Release Tasks

Bump `version` in `pyproject.toml`, update `CHANGELOG.md`, then:

```text
$ uv build
$ uv publish
```
