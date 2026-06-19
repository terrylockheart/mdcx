# Copilot instructions for MDCx

MDCx is a PyQt6 desktop app that scrapes adult-video metadata, downloads images, and
writes NFO/media files for media servers (Emby/Jellyfin). Python 3.13.4+ only (it relies
on `os.path.ALLOW_MISSING` and PEP 696 type-parameter defaults). Dependencies and tooling
are managed with [uv](https://docs.astral.sh/uv/).

## Commands

```bash
uv sync --all-extras --dev      # install deps
uv run pre-commit install       # install hooks
uv pip install -e .             # editable install (needed for entry-point scripts)

uv run main.py                  # launch the Qt GUI
uv run pytest                   # full test suite
uv run pytest tests/crawlers    # one directory
uv run pytest tests/test_utils.py::test_name   # one test

uv run ruff format              # format (line-length 120, double quotes)
uv run ruff check --fix         # lint
```

CI (`.github/workflows/ci.yaml`) only enforces `ruff format --check` and `ruff check`;
it does **not** run pytest, so run tests locally before pushing. Async tests are marked
explicitly with `@pytest.mark.asyncio` (there is no global asyncio auto mode).

## Architecture

- `main.py` boots `QApplication` and `mdcx.controllers.main_window.main_window.MyMAinWindow`.
- `mdcx/consts.py` defines runtime constants; `MAIN_PATH` is the one hardcoded path and the
  anchor for locating the active config file and user data directory.
- `mdcx/config/` — settings. The `Config` dataclass lives in `mdcx/config/models.py`; a
  process-wide singleton is exposed as `from mdcx.config.manager import manager`, accessed
  via `manager.config.<key>`. (CONTRIBUTING.md's `mdcx.models.config.manager` path is stale.)
- `mdcx/crawlers/` — 40+ per-site scrapers. New-style scrapers subclass
  `BaseCrawler` / `GenericBaseCrawler` from `mdcx/crawlers/base/` and are registered with
  `register_crawler()` in `mdcx/crawlers/__init__.py`; legacy function scrapers register via
  `CRAWLER_FUNCS`. A migration is in progress — see `docs/crawler-migration.md` before
  touching crawlers. New crawlers must use `self.async_client` for requests, return
  `CrawlerData`, log via `ctx.debug()`, and raise `CralwerException` for site-level failures.
- `mdcx/core/` — orchestration: `scraper.py`, `file_crawler.py`, `nfo.py`, `image.py`,
  `naming/`, `translate.py`, face cropping, etc.
- `mdcx/controllers/main_window/` — Qt controllers and config↔UI binding.
- `mdcx/tools/` — Emby/Jellyfin actor-image and metadata helpers.

## Conventions

- Adding a config field: add it to the `Config` class in `mdcx/config/models.py` with a
  default, then wire the UI in `mdcx/controllers/main_window/load_config.py` and
  `save_config.py`.
- GUI is defined in Qt Designer files (`mdcx/views/*.ui`). After editing a `.ui`, run
  `./scripts/pyuic.sh` to regenerate Python. Generated code (`mdcx/views/*.py`,
  `*_generated.py`) is excluded from ruff — never hand-edit it. Wire widget events in
  `mdcx.controllers.main_window.init.Init_Singal` and handle them in `main_window.py` /
  `handlers.py`.
- `StrEnum`s are generated from dataclasses via the `gen_enums` script — regenerate rather
  than editing generated enums by hand.
- Network/scraping code is async (httpx / curl-cffi); don't block the event loop
  (ruff enforces `ASYNC230`/`ASYNC251`).
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`), often
  with Chinese descriptions.
