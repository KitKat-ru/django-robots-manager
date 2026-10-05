from django.contrib.sites.models import Site
from django.test import TestCase

from robots.forms import RuleAdminForm
from robots.models import Rule, Url


class RuleAdminFormTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get(domain="example.com")
        self.url_test = Url.objects.create(pattern="/test")
        self.url_admin = Url.objects.create(pattern="/admin")

    def get_form(self, allowed, disallowed, robot="*", sites=None, instance=None):
        return RuleAdminForm(
            data={
                "robot": robot,
                "sites": [site.pk for site in sites or [self.site]],
                "allowed": [url.pk for url in allowed],
                "disallowed": [url.pk for url in disallowed],
            },
            instance=instance,
        )

    def create_rule(self, robot, sites):
        rule = Rule.objects.create(robot=robot)
        rule.sites.set(sites)
        rule.allowed.add(self.url_test)
        return rule

    def test_different_patterns_are_valid(self):
        form = self.get_form(allowed=[self.url_test], disallowed=[self.url_admin])
        self.assertTrue(form.is_valid(), form.errors)

    def test_same_robot_on_other_site_is_valid(self):
        other_site = Site.objects.create(domain="other.example.com")
        self.create_rule(robot="Googlebot", sites=[other_site])
        form = self.get_form(allowed=[self.url_test], disallowed=[], robot="Googlebot")
        self.assertTrue(form.is_valid(), form.errors)

    def test_editing_existing_rule_is_valid(self):
        rule = self.create_rule(robot="Googlebot", sites=[self.site])
        form = self.get_form(
            allowed=[self.url_test],
            disallowed=[self.url_admin],
            robot="Googlebot",
            instance=rule,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_same_url_in_allowed_and_disallowed(self):
        form = self.get_form(
            allowed=[self.url_test], disallowed=[self.url_test, self.url_admin]
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            ["URL patterns cannot be both allowed and disallowed: /test."],
        )

    def test_duplicate_url_rows_with_same_pattern(self):
        url_test_copy = Url.objects.create(pattern="test")
        form = self.get_form(allowed=[self.url_test], disallowed=[url_test_copy])
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            ["URL patterns cannot be both allowed and disallowed: /test."],
        )

    def test_empty_allowed_and_disallowed(self):
        form = self.get_form(allowed=[], disallowed=[])
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            ["Please specify at least one allowed or disallowed URL."],
        )

    def test_same_robot_on_same_site(self):
        other_site = Site.objects.create(domain="other.example.com")
        self.create_rule(robot="Googlebot", sites=[self.site, other_site])
        form = self.get_form(
            allowed=[self.url_test],
            disallowed=[],
            robot="Googlebot",
            sites=[self.site, other_site],
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [
                (
                    "A rule for robot Googlebot already exists on sites: "
                    "example.com, other.example.com."
                )
            ],
        )

    def test_same_robot_is_case_insensitive(self):
        self.create_rule(robot="Googlebot", sites=[self.site])
        form = self.get_form(allowed=[self.url_test], disallowed=[], robot="googlebot")
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            ["A rule for robot googlebot already exists on sites: example.com."],
        )
