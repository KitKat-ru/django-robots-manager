from io import StringIO

from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.db import connection
from django.http import SimpleCookie
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils.encoding import force_str

from robots.models import Rule, Url
from robots.views import RuleList


class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_factory = RequestFactory()

    def get_request(self, path, user, lang, secure=False):
        from django.contrib.auth.models import AnonymousUser

        request = self.request_factory.get(path, secure=secure)

        if not user:
            user = AnonymousUser()
        request.user = user
        request._cached_user = user
        request.session = {}
        if secure:
            request.environ["SERVER_PORT"] = "443"
            request.environ["wsgi.url_scheme"] = "https"
        if user.is_authenticated:
            request.session[SESSION_KEY] = user._meta.pk.value_to_string(user)
        request.cookies = SimpleCookie()
        request.errors = StringIO()
        request.LANGUAGE_CODE = lang
        if request.method == "POST":
            request._dont_enforce_csrf_checks = True
        return request

    def setUp(self):
        super().setUp()
        site_1 = Site.objects.get(domain="example.com")
        site_2 = Site.objects.create(domain="https://sub.example.com")

        url_admin = Url.objects.create(pattern="/admin")
        url_root = Url.objects.create(pattern="/")
        url_media = Url.objects.create(pattern="/media")

        rule_all = Rule.objects.create(robot="*", crawl_delay=10)
        rule_1 = Rule.objects.create(robot="Bing", crawl_delay=20)
        rule_2 = Rule.objects.create(robot="Googlebot")

        rule_all.allowed.add(url_root)
        for url in [url_admin, url_media]:
            rule_all.disallowed.add(url)
        for site in [site_1, site_2]:
            rule_all.sites.add(site)

        rule_1.allowed.add(url_root)
        rule_1.disallowed.add(url_admin)
        rule_1.sites.add(site_1)

        rule_2.disallowed.add(url_media)
        rule_2.sites.add(site_2)

    def _test_stanzas(self, stanzas):
        for stanza in stanzas:
            if stanza.startswith("User-agent: *"):
                self.assertTrue("Allow: /" in stanza)
                self.assertTrue("Disallow: /admin" in stanza)
                self.assertTrue("Disallow: /media" in stanza)
                self.assertTrue("Crawl-delay: 10" in stanza)
            elif stanza.startswith("User-agent: Bing"):
                self.assertTrue("Allow: /" in stanza)
                self.assertTrue("Disallow: /admin" in stanza)
                self.assertFalse("Disallow: /media" in stanza)
                self.assertFalse("Crawl-delay: 10" in stanza)
                self.assertTrue("Crawl-delay: 20" in stanza)
            elif stanza.startswith("User-agent: Googlebot"):
                self.assertFalse("Allow: /" in stanza)
                self.assertFalse("Disallow: /admin" in stanza)
                self.assertTrue("Disallow: /media" in stanza)
                self.assertFalse("Crawl-delay: 10" in stanza)
                self.assertFalse("Crawl-delay: 20" in stanza)
                self.assertFalse("Crawl-delay" in stanza)

    def test_view_site_1(self):
        request = self.get_request(path="/", user=AnonymousUser(), lang="en")

        view_obj = RuleList()
        view_obj.request = request
        view_obj.current_site = view_obj.get_current_site(request)
        view_obj.object_list = view_obj.get_queryset()
        context = view_obj.get_context_data(object_list=view_obj.object_list)
        self.assertEqual(context["object_list"].count(), 2)
        self.assertTrue(context["object_list"].filter(robot="*").exists())
        self.assertTrue(context["object_list"].filter(robot="Bing").exists())

        response = view_obj.render_to_response(context)
        response.render()
        content = force_str(response.content)
        self.assertTrue("Sitemap: http://example.com/sitemap.xml" in content)
        stanzas = content.split("\n\n")
        self._test_stanzas(stanzas)

    def test_view_site_2(self):
        request = self.get_request(path="/", user=AnonymousUser(), lang="en")

        view_obj = RuleList()
        view_obj.request = request
        view_obj.current_site = Site.objects.get(pk=2)
        view_obj.object_list = view_obj.get_queryset()
        context = view_obj.get_context_data(object_list=view_obj.object_list)
        self.assertEqual(context["object_list"].count(), 2)
        self.assertTrue(context["object_list"].filter(robot="*").exists())
        self.assertTrue(context["object_list"].filter(robot="Googlebot").exists())

        response = view_obj.render_to_response(context)
        response.render()
        content = force_str(response.content)
        self.assertTrue("Sitemap: https://sub.example.com/sitemap.xml" in content)
        self.assertFalse("Host:" in content)
        stanzas = content.split("\n\n")
        self._test_stanzas(stanzas)

    def test_use_scheme_in_host_setting(self):
        request = self.get_request(path="/", user=AnonymousUser(), lang="en")

        view_obj = RuleList()
        view_obj.request = request
        view_obj.current_site = Site.objects.get(pk=1)
        view_obj.object_list = view_obj.get_queryset()

        with self.settings(ROBOTS_USE_HOST=True):
            with self.settings(ROBOTS_USE_SCHEME_IN_HOST=True):
                context = view_obj.get_context_data(object_list=view_obj.object_list)
                response = view_obj.render_to_response(context)
                response.render()
                content = force_str(response.content)
                self.assertTrue("Host: http://example.com" in content)
            with self.settings(ROBOTS_USE_SCHEME_IN_HOST=False):
                context = view_obj.get_context_data(object_list=view_obj.object_list)
                response = view_obj.render_to_response(context)
                response.render()
                content = force_str(response.content)
                self.assertTrue("Host: example.com" in content)

        with self.settings(ROBOTS_USE_HOST=False):
            context = view_obj.get_context_data(object_list=view_obj.object_list)
            response = view_obj.render_to_response(context)
            response.render()
            content = force_str(response.content)
            self.assertFalse("Host: example.com" in content)

    def test_cached_sitemap(self):
        request = self.get_request(path="/", user=AnonymousUser(), lang="en")

        view_obj = RuleList()
        view_obj.request = request
        view_obj.current_site = Site.objects.get(pk=1)
        view_obj.object_list = view_obj.get_queryset()
        context = view_obj.get_context_data(object_list=view_obj.object_list)
        response = view_obj.render_to_response(context)
        response.render()
        content = force_str(response.content)
        self.assertTrue("Sitemap: http://example.com/sitemap.xml" in content)

        with self.settings(ROBOTS_SITEMAP_VIEW_NAME="cached-sitemap"):
            context = view_obj.get_context_data(object_list=view_obj.object_list)
            response = view_obj.render_to_response(context)
            response.render()
            content = force_str(response.content)
            self.assertTrue("Sitemap: http://example.com/other/sitemap.xml" in content)


@override_settings(ROBOTS_SITE_BY_REQUEST=True, ALLOWED_HOSTS=["*"])
class SiteByRequestTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get(domain="example.com")

    def get_site(self, host):
        request = RequestFactory().get("/", HTTP_HOST=host)
        return RuleList().get_current_site(request)

    def test_exact_host(self):
        self.assertEqual(self.get_site("example.com"), self.site)

    def test_host_with_port_falls_back_to_domain(self):
        self.assertEqual(self.get_site("example.com:8000"), self.site)

    def test_site_domain_with_port(self):
        site_with_port = Site.objects.create(domain="localhost:8000")
        self.assertEqual(self.get_site("localhost:8000"), site_with_port)

    def test_host_is_case_insensitive(self):
        self.assertEqual(self.get_site("EXAMPLE.com"), self.site)

    def test_unknown_host(self):
        with self.assertRaises(Site.DoesNotExist):
            self.get_site("unknown.example.org")


class RobotsTxtResponseTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get(domain="example.com")

    def create_rule(self, robot, disallowed, comment=""):
        rule = Rule.objects.create(robot=robot, comment=comment)
        rule.sites.add(self.site)
        for pattern in disallowed:
            rule.disallowed.add(Url.objects.create(pattern=pattern))
        return rule

    def get_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        return response

    def test_content_type_is_utf8_plain_text(self):
        response = self.get_robots_txt()
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")

    def test_rules_and_urls_are_sorted(self):
        self.create_rule(robot="Googlebot", disallowed=["/b", "/a"])
        self.create_rule(robot="*", disallowed=["/admin"])
        self.create_rule(robot="Bing", disallowed=["/tmp"])
        lines = force_str(self.get_robots_txt().content).splitlines()
        positions = [
            lines.index(line)
            for line in [
                "User-agent: *",
                "User-agent: Bing",
                "User-agent: Googlebot",
                "Disallow: /a",
                "Disallow: /b",
            ]
        ]
        self.assertEqual(positions, sorted(positions))

    def test_non_ascii_patterns_are_percent_encoded(self):
        self.create_rule(robot="*", disallowed=["/каталог/"])
        lines = force_str(self.get_robots_txt().content).splitlines()
        self.assertIn("Disallow: /%D0%BA%D0%B0%D1%82%D0%B0%D0%BB%D0%BE%D0%B3/", lines)

    def test_single_blank_line_before_sitemap(self):
        self.create_rule(robot="*", disallowed=["/admin"])
        content = force_str(self.get_robots_txt().content)
        self.assertEqual(
            content,
            "User-agent: *\nDisallow: /admin\n\n"
            "Sitemap: http://example.com/sitemap.xml\n\n",
        )

    @override_settings(ROBOTS_USE_SITEMAP=False)
    def test_no_trailing_section_without_host_and_sitemap(self):
        self.create_rule(robot="*", disallowed=["/admin"])
        content = force_str(self.get_robots_txt().content)
        self.assertEqual(content, "User-agent: *\nDisallow: /admin\n\n")

    def test_comment_is_rendered_above_its_group(self):
        self.create_rule(
            robot="Googlebot", disallowed=["/search"], comment="Search & filters"
        )
        lines = force_str(self.get_robots_txt().content).splitlines()
        index = lines.index("User-agent: Googlebot")
        self.assertEqual(lines[index - 1], "# Search & filters")

    def test_rule_without_comment_has_no_comment_line(self):
        self.create_rule(robot="Googlebot", disallowed=["/search"])
        lines = force_str(self.get_robots_txt().content).splitlines()
        self.assertFalse(any(line.startswith("#") for line in lines))

    def test_query_count_does_not_depend_on_rule_count(self):
        self.create_rule(robot="*", disallowed=["/admin"])
        # Warm up SITE_CACHE so the Site query does not land in the first sample only.
        self.get_robots_txt()
        with CaptureQueriesContext(connection) as one_rule:
            self.get_robots_txt()
        self.create_rule(robot="Bing", disallowed=["/tmp", "/media"])
        self.create_rule(robot="Googlebot", disallowed=["/search"])
        with CaptureQueriesContext(connection) as three_rules:
            self.get_robots_txt()
        self.assertEqual(len(three_rules), len(one_rule))
