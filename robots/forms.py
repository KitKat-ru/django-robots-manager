from django import forms
from django.contrib.sites.models import Site
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

        robot = self.cleaned_data.get("robot")
        sites = self.cleaned_data.get("sites")
        if robot and sites:
            other_rules = Rule.objects.filter(robot__iexact=robot).exclude(
                pk=self.instance.pk
            )
            duplicate_domains = (
                Site.objects.filter(pk__in=sites, rule__in=other_rules)
                .values_list("domain", flat=True)
                .distinct()
            )
            if duplicate_domains:
                raise forms.ValidationError(
                    _("A rule for robot %(robot)s already exists on sites: %(sites)s."),
                    params={
                        "robot": robot,
                        "sites": ", ".join(sorted(duplicate_domains)),
                    },
                )
        return self.cleaned_data
