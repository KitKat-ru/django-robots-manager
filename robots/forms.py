from django import forms
from django.utils.translation import gettext_lazy as _

from robots.models import Rule


class RuleAdminForm(forms.ModelForm):
    class Meta:
        model = Rule
        fields = "__all__"

    def clean(self):
        if not self.cleaned_data.get("disallowed", False) and not self.cleaned_data.get(
            "allowed", False
        ):
            raise forms.ValidationError(
                _("Please specify at least one allowed or disallowed URL.")
            )
        allowed = self.cleaned_data.get("allowed")
        disallowed = self.cleaned_data.get("disallowed")
        if allowed and disallowed:
            conflicts = set(allowed.values_list("pattern", flat=True)) & set(
                disallowed.values_list("pattern", flat=True)
            )
            if conflicts:
                raise forms.ValidationError(
                    _(
                        "URL patterns cannot be both allowed and disallowed: "
                        "%(patterns)s."
                    ),
                    params={"patterns": ", ".join(sorted(conflicts))},
                )
        return self.cleaned_data
