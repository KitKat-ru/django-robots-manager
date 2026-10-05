from django.contrib.sites.models import Site
from django.test import TestCase

from robots.forms import RuleAdminForm
from robots.models import Url


class RuleAdminFormTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get(domain="example.com")
        self.url_test = Url.objects.create(pattern="/test")
        self.url_admin = Url.objects.create(pattern="/admin")

    def get_form(self, allowed, disallowed):
        return RuleAdminForm(
            data={
                "robot": "*",
                "sites": [self.site.pk],
                "allowed": [url.pk for url in allowed],
                "disallowed": [url.pk for url in disallowed],
            }
        )

    def test_different_patterns_are_valid(self):
        form = self.get_form(allowed=[self.url_test], disallowed=[self.url_admin])
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
