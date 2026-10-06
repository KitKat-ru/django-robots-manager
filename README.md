# django-robots-manager

[![Tests](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml)
[![GitHub tag](https://img.shields.io/github/v/tag/KitKat-ru/django-robots-manager?sort=semver)](https://github.com/KitKat-ru/django-robots-manager/tags)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.2%20%7C%206.0%20%7C%206.1-0C4B33)](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue)](LICENSE.txt)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

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
- `ROBOTS_USE_HOST` now defaults to `False`: Yandex
  [stopped using](https://webmaster.yandex.ru/blog/301-y-redirekt-polnostyu-zamenil-direktivu-host)
  the `Host` directive in 2018, and Google
  [never supported it](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt)
  (it is not part of [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309) either). Set it
  to `True` to keep the old output.
- `ROBOTS_SITE_BY_REQUEST` looks the site up the same way as Django's sites framework:
  case-insensitively, retrying without the port (`example.com:8000` matches
  `example.com`).
- `robots.txt` is served as `text/plain; charset=utf-8`
  ([RFC 9309](https://www.rfc-editor.org/rfc/rfc9309) requires UTF-8), with rules sorted
  by robot and URLs by pattern, in a fixed number of queries.
- Only the `ru` locale is shipped.

## Installation

Requires Python 3.10+ and Django 4.2+ (tested with Django 4.2, 5.2, 6.0 and 6.1).
Projects on older Python or Django versions can stay on django-robots 6.1.

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
`ROBOTS_SITEMAP_VIEW_NAME`) are the same as upstream, except for the changes listed
above.

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

pip install "coverage[toml]"         # test coverage, as in CI
python -m coverage run -m django test tests
python -m coverage report

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
