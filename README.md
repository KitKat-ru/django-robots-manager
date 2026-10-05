# django-robots-manager

A continuation of [django-robots](https://github.com/jazzband/django-robots/),
picking up from the 6.x series (based on release 6.1), after a long pause in releases
of the original library.

The import path and app label stay `robots`, so it is a drop-in replacement for
django-robots 5.0 and 6.x: existing tables and migration history are reused.

## Changes from upstream 6.1

- `__version__` is read via `importlib.metadata` only; the `pkg_resources` fallback
  and `default_app_config` (Django < 3.2) are removed.
- The South guard in `robots.migrations` is removed.
- `RuleAdminForm` rejects a rule whose allowed and disallowed URLs share a pattern.
- `RuleAdminForm` rejects a second rule for the same robot (case-insensitive) on the
  same site.
- Only the `ru` locale is shipped.

## Installation

```python
INSTALLED_APPS = [
    "django.contrib.sites",
    ...
    "robots",
]
```

```python
urlpatterns = [
    re_path(r"^robots\.txt", include("robots.urls")),
]
```

Settings (`ROBOTS_SITEMAP_URLS`, `ROBOTS_USE_SITEMAP`, `ROBOTS_USE_HOST`,
`ROBOTS_CACHE_TIMEOUT`, `ROBOTS_SITE_BY_REQUEST`, `ROBOTS_USE_SCHEME_IN_HOST`,
`ROBOTS_SITEMAP_VIEW_NAME`) are unchanged from upstream.

## Development

`tests/` holds a minimal Django project (SQLite) used both for the test suite and for
trying the app locally. It is not part of the distributed package. Run the commands
from the repository root.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
export DJANGO_SETTINGS_MODULE=tests.settings

python -m django test tests          # run the test suite

python -m django migrate
python -m django createsuperuser
python -m django runserver           # http://localhost:8000/admin/, http://localhost:8000/robots.txt

python -m django makemigrations robots --check --dry-run   # after model changes
```

The demo project uses `SITE_ID = 1` (`example.com`), so rules must be attached to that
site to appear in `/robots.txt`.

Linting and formatting use [ruff](https://docs.astral.sh/ruff/) via
[pre-commit](https://pre-commit.com/); neither is a dependency of the package.

```bash
pip install pre-commit
pre-commit install                   # run the hooks on every commit
pre-commit run --all-files           # run them on the whole repository
```
