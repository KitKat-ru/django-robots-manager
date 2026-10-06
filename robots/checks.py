from urllib.parse import SplitResult, urlsplit

from django.core import checks

from robots import settings


def check_sitemap_urls(app_configs, **kwargs):
    """Validate that ROBOTS_SITEMAP_URLS is a list of absolute ASCII URLs."""
    sitemap_urls = settings.SITEMAP_URLS
    if isinstance(sitemap_urls, str):
        return [
            checks.Error(
                "ROBOTS_SITEMAP_URLS must be a list or tuple of URLs, not a string.",
                hint="Wrap the URL in a list: ['https://example.com/sitemap.xml'].",
                id="robots.E001",
            )
        ]

    messages = []
    for url in sitemap_urls:
        parts: SplitResult = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            messages.append(
                checks.Warning(
                    f"ROBOTS_SITEMAP_URLS has a URL that is not absolute: {url!r}.",
                    hint="Use an absolute URL, e.g. 'https://example.com/sitemap.xml'.",
                    id="robots.W001",
                )
            )
        elif not parts.netloc.isascii():
            messages.append(
                checks.Warning(
                    f"ROBOTS_SITEMAP_URLS contains a non-ASCII domain: {url!r}.",
                    hint="Write the domain in Punycode, e.g. 'xn--d1aqf.xn--p1ai'.",
                    id="robots.W002",
                )
            )
    return messages
