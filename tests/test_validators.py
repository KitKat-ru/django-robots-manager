from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from robots.validators import (
    validate_clean_param_parameters,
    validate_clean_param_path,
    validate_single_line,
)


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


class ValidateCleanParamParametersTest(SimpleTestCase):
    def test_valid_parameters(self):
        for value in ["ref", "ref&sid", "filter[color]&page-size&utm_x"]:
            with self.subTest(value=value):
                validate_clean_param_parameters(value)

    def test_invalid_parameters(self):
        for value in ["ref&", "&ref", "ref&&sid", "ref sid", "ref=1", "ref#", "реф"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_clean_param_parameters(value)


class ValidateCleanParamPathTest(SimpleTestCase):
    def test_valid_paths(self):
        for value in ["/catalog/", "/forum*/showthread.php", "/a-b_c.d"]:
            with self.subTest(value=value):
                validate_clean_param_path(value)

    def test_invalid_paths(self):
        for value in ["/каталог/", "/a%20b", "/a b", "/a?b", "/a$"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_clean_param_path(value)
