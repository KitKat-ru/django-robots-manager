# django-robots-manager

A continuation of [django-robots](https://github.com/jazzband/django-robots/),
picking up from the 6.x series (based on release 6.1), after a long pause in releases
of the original library.

The import path and app label stay `robots`, so it is a drop-in replacement for
django-robots 5.0 and 6.x: existing tables and migration history are reused.

## Changes from upstream 6.1

- `__version__` is read via `importlib.metadata` only; the `pkg_resources` fallback
  and `default_app_config` (Django < 3.2) are removed.
- The South guard in `robots.migrations` and the bundled unittest suite are removed.
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
