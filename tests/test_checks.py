from django.test import SimpleTestCase, override_settings

from robots.checks import check_sitemap_urls


class CheckSitemapUrlsTest(SimpleTestCase):
    def get_ids(self, sitemap_urls):
        with override_settings(ROBOTS_SITEMAP_URLS=sitemap_urls):
            return [message.id for message in check_sitemap_urls(None)]

    def test_absolute_ascii_urls_pass(self):
        for sitemap_urls in [
            [],
            ["https://example.com/sitemap.xml"],
            ("http://example.com/a.xml", "https://xn--d1aqf.xn--p1ai/b.xml"),
        ]:
            with self.subTest(sitemap_urls=sitemap_urls):
                self.assertEqual(self.get_ids(sitemap_urls), [])

    def test_string_instead_of_list(self):
        self.assertEqual(
            self.get_ids("https://example.com/sitemap.xml"), ["robots.E001"]
        )

    def test_not_absolute_urls(self):
        for url in ["/s.xml", "example.com/s.xml", "ftp://example.com/s.xml"]:
            with self.subTest(url=url):
                self.assertEqual(self.get_ids([url]), ["robots.W001"])

    def test_non_ascii_domain(self):
        self.assertEqual(self.get_ids(["https://дом.рф/s.xml"]), ["robots.W002"])

    def test_each_bad_url_is_reported(self):
        sitemap_urls = ["/a.xml", "https://example.com/b.xml", "http://дом.рф/c.xml"]
        self.assertEqual(self.get_ids(sitemap_urls), ["robots.W001", "robots.W002"])
