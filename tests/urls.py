from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.urls import include, re_path
from django.views.decorators.cache import cache_page

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^robots\.txt", include("robots.urls")),
    re_path(r"^sitemap.xml$", sitemap_view, {"sitemaps": []}),
    re_path(
        r"^other/sitemap.xml$",
        cache_page(60)(sitemap_view),
        {"sitemaps": []},
        name="cached-sitemap",
    ),
]
