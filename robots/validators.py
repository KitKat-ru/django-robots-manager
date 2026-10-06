import re
import unicodedata

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Characters Yandex allows in the Clean-param path prefix.
CLEAN_PARAM_PATH_RE = re.compile(r"[A-Za-z0-9.\-/*_]+")

# Control characters and Unicode line/paragraph separators. Tab is allowed: RFC 9309
# permits whitespace inside comments.
FORBIDDEN_CATEGORIES = {"Cc", "Zl", "Zp"}


def validate_single_line(value):
    """Reject line breaks and other control characters except tab."""
    if any(
        char != "\t" and unicodedata.category(char) in FORBIDDEN_CATEGORIES
        for char in value
    ):
        raise ValidationError(
            _("Use a single line without line breaks or control characters."),
            code="invalid",
        )


def validate_clean_param_parameters(value):
    """Require "&"-separated parameter names of printable ASCII without "=" and "#"."""
    for name in value.split("&"):
        if not name or any(not "!" <= char <= "~" or char in "=#" for char in name):
            raise ValidationError(
                _(
                    'Enter parameter names separated by "&", without spaces, '
                    '"=", "#" or non-ASCII characters.'
                ),
                code="invalid",
            )


def validate_clean_param_path(value):
    """Allow only the characters Yandex accepts in a Clean-param path prefix."""
    if not CLEAN_PARAM_PATH_RE.fullmatch(value):
        raise ValidationError(
            _(
                "The path may contain only Latin letters, digits and the characters "
                '".", "-", "/", "*" and "_".'
            ),
            code="invalid",
        )
