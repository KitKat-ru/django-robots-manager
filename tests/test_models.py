from django.test import SimpleTestCase

from robots.models import encode_pattern

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
