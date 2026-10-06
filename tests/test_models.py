from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from robots.models import CleanParam, encode_pattern

CATALOG_ENCODED = "/%D0%BA%D0%B0%D1%82%D0%B0%D0%BB%D0%BE%D0%B3/"


class EncodePatternTest(SimpleTestCase):
    def test_ascii_is_unchanged(self):
        for pattern in ["/admin/", "/*.jpg$", "/search?q=1&page=2", "/a-b_c~d"]:
            with self.subTest(pattern=pattern):
                self.assertEqual(encode_pattern(pattern), pattern)

    def test_already_encoded_is_unchanged(self):
        self.assertEqual(encode_pattern(CATALOG_ENCODED), CATALOG_ENCODED)

    def test_cyrillic_is_encoded(self):
        self.assertEqual(encode_pattern("/каталог/"), CATALOG_ENCODED)

    def test_space_and_hash_are_encoded(self):
        self.assertEqual(encode_pattern("/a b#c"), "/a%20b%23c")


class CleanParamTest(SimpleTestCase):
    def test_directive_with_path(self):
        clean_param = CleanParam(parameters="ref&sid", path="/catalog/")
        self.assertEqual(clean_param.directive, "Clean-param: ref&sid /catalog/")

    def test_directive_without_path(self):
        clean_param = CleanParam(parameters="ref")
        self.assertEqual(clean_param.directive, "Clean-param: ref")

    def test_leading_slash_is_added(self):
        clean_param = CleanParam(parameters="ref", path="catalog")
        clean_param.clean_fields()
        self.assertEqual(clean_param.path, "/catalog")

    def test_path_with_slash_or_star_is_unchanged(self):
        for path in ["/catalog", "*/catalog", ""]:
            with self.subTest(path=path):
                clean_param = CleanParam(parameters="ref", path=path)
                clean_param.clean_fields()
                self.assertEqual(clean_param.path, path)

    def build_clean_param(self, directive_length):
        """Build a CleanParam whose directive is exactly directive_length long."""
        # Each field fits 255 characters, so neither can reach the directive limit
        # alone: the parameters take 250 and the path gets the rest.
        parameters = "a" * 250
        prefix = f"Clean-param: {parameters} /"
        path = "/" + "b" * (directive_length - len(prefix))
        clean_param = CleanParam(parameters=parameters, path=path)
        self.assertEqual(len(clean_param.directive), directive_length)
        return clean_param

    def test_directive_at_max_length_is_valid(self):
        clean_param = self.build_clean_param(CleanParam.MAX_DIRECTIVE_LENGTH)
        clean_param.clean()

    def test_leading_slash_counts_towards_max_length(self):
        path_max_length = CleanParam._meta.get_field("path").max_length
        clean_param = CleanParam(parameters="ref", path="b" * path_max_length)
        with self.assertRaises(ValidationError) as context:
            clean_param.clean_fields()
        self.assertIn("path", context.exception.message_dict)

    def test_directive_over_max_length(self):
        clean_param = self.build_clean_param(CleanParam.MAX_DIRECTIVE_LENGTH + 1)
        with self.assertRaises(ValidationError) as context:
            clean_param.clean()
        self.assertEqual(
            context.exception.messages,
            [
                (
                    "The Clean-param directive must not exceed "
                    f"{CleanParam.MAX_DIRECTIVE_LENGTH} characters."
                )
            ],
        )


class CleanParamSaveTest(TestCase):
    def test_leading_slash_is_added_on_save(self):
        clean_param = CleanParam.objects.create(parameters="ref", path="catalog")
        clean_param.refresh_from_db()
        self.assertEqual(clean_param.path, "/catalog")
