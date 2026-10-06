from django.apps import AppConfig
from django.core import checks

from robots.checks import check_sitemap_urls


class RobotsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "robots"

    def ready(self):
        checks.register(check_sitemap_urls)
