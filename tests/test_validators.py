from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from robots.validators import validate_single_line


class ValidateSingleLineTest(SimpleTestCase):
    def test_plain_text_is_valid(self):
        validate_single_line("Close search: duplicates & params")

    def test_tab_and_unicode_are_valid(self):
        validate_single_line("Закрываем\tпоиск")

    def test_line_breaks_are_invalid(self):
        for value in ["a\nb", "a\rb", "a\u2028b", "a\u0085b"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_single_line(value)

    def test_control_characters_are_invalid(self):
        for value in ["a\x00b", "a\x1bb"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_single_line(value)
