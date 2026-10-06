# django-robots-manager

[![Tests](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml)
[![GitHub tag](https://img.shields.io/github/v/tag/KitKat-ru/django-robots-manager?sort=semver)](https://github.com/KitKat-ru/django-robots-manager/tags)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.2%20%7C%206.0%20%7C%206.1-0C4B33)](https://github.com/KitKat-ru/django-robots-manager/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue)](https://github.com/KitKat-ru/django-robots-manager/blob/main/LICENSE.txt)
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
- `Rule.comment`: an optional single-line note rendered as a `# ...` line above the
  rule's group in `robots.txt`.
- URL patterns are percent-encoded on output: non-ASCII characters (e.g. Cyrillic),
  whitespace and `#` become `%XX`, as
  [Yandex requires](https://yandex.ru/support/webmaster/ru/controlling-robot/robots-txt).
  Patterns are stored as entered, and raw and encoded forms of the same path count as
  the same pattern when checking allowed/disallowed conflicts.
- [Clean-param](https://yandex.ru/support/webmaster/ru/robot-workings/clean-param)
  directives (Yandex): see below.
- System checks for `ROBOTS_SITEMAP_URLS`: `robots.E001` if it is a string instead of
  a list, `robots.W001` for URLs that are not absolute, `robots.W002` for non-ASCII
  domains.
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

### Internationalized domains

Store non-ASCII domains in `Site.domain` (and in `ROBOTS_SITEMAP_URLS`) in Punycode,
e.g. `xn--d1aqf.xn--p1ai` instead of `дом.рф`:

- the domain is written to `Sitemap:` (and `Host:`) as stored, and
  [Yandex requires](https://yandex.ru/support/webmaster/ru/controlling-robot/robots-txt)
  Punycode there;
- with `ROBOTS_SITE_BY_REQUEST = True` the site is looked up by the request `Host`
  header, which is always Punycode, so a site stored as `дом.рф` is not found and
  `robots.txt` responds with an error.

## Clean-param

`Clean-param` tells Yandex which URL parameters do not change the page content, so
`/catalog/?ref=vk` and `/catalog/?sid=1` are crawled and indexed as `/catalog/`. Other
search engines ignore it.

Add directives in the admin under *Clean-param directives* and attach them to sites:

| Parameters | Path | Output |
|---|---|---|
| `ref&sid` | `/catalog/` | `Clean-param: ref&sid /catalog/` |
| `sort` | *(empty)* | `Clean-param: sort` (whole site) |

The directive is cross-sectional, so it is rendered once per file, next to `Sitemap`,
not inside a `User-agent` group. Following the Yandex rules, parameter names are
case-sensitive, the path may contain only `A-Za-z0-9.-/*_` (a leading `/` is added
if missing, as for URL patterns), and the whole line is limited to 500 characters.
Unlike `Allow`/`Disallow`, the path is not percent-encoded, so pages with Cyrillic
paths (e.g. `/о-компании/`) can only be covered by a directive without a path.

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

### Releasing

1. Bump `version` in `pyproject.toml` and commit.
2. Tag the commit as `v<version>` and push the tag.

The *Release* workflow checks that the tag matches the version, builds the package and
publishes it to TestPyPI and then to PyPI via trusted publishing.
