import unicodedata

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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
