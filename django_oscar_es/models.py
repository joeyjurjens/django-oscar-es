from typing import Any

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from oscar.core.loading import get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")


class ProductElasicSearchConfiguration(models.Model):
    search_fields = models.TextField(
        help_text=_(
            "Enter the fields which should be used for search. You can enter multiple fields separated by comma."
        ),
        default="title,description,upc",
    )
    auto_complete_fields = models.TextField(
        help_text=_(
            "Enter the fields which should be used for auto-complete. You can enter multiple fields separated by comma."
        ),
        default="title,upc",
    )

    def save(self, *args, **kwargs):
        if ProductElasicSearchConfiguration.objects.exists() and not self.pk:
            raise ValueError(
                "There can be only one ProductElasicSearchConfiguration instance."
            )
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Product ElasticSearch Configuration")
        verbose_name_plural = _("Product ElasticSearch Configuration")


class AttributeFacet(models.Model):
    FACET_TYPE_TERM = "term"
    FACET_TYPE_RANGE = "range"
    FACET_TYPE_CHOICES = (
        (FACET_TYPE_TERM, _("Term")),
        (FACET_TYPE_RANGE, _("Range")),
    )

    configuration = models.ForeignKey(
        ProductElasicSearchConfiguration,
        on_delete=models.CASCADE,
        related_name="attribute_facets",
    )

    # The actual choices are loaded in ProductAttributeFacetInline formfield_for_choice_field override
    # and in the __init__ method from this model.
    attribute_code = models.CharField(max_length=255, choices=[("", "")], unique=True)
    facet_type = models.CharField(
        max_length=20,
        choices=FACET_TYPE_CHOICES,
        default=FACET_TYPE_TERM,
    )
    ranges = models.TextField(
        help_text=_(
            "Enter the ranges for this facet. You can enter multiple ranges separated by comma. Each range should be in the format 'from|to'."
        ),
        blank=True,
    )
    label = models.CharField(
        max_length=255,
        help_text=_("Enter the label for this facet."),
    )
    searchable = models.BooleanField(
        default=False,
        help_text=_(
            "If you enable this, a search bar will be shown under this facet so you can filter the facet values. This is useful for large facets with a lot of values."
        ),
    )
    enabled_categories = models.ManyToManyField(
        "catalogue.Category",
        blank=True,
        related_name="enabled_facets",
        help_text=_(
            "If this facet is for a specific set of categories, you can choose them here. If you leave this (and disabled categories) empty, the facet will be enabled for all categories."
        ),
    )
    disabled_categories = models.ManyToManyField(
        "catalogue.Category",
        blank=True,
        related_name="disabled_facets",
        help_text=_(
            "If this facet should be hidden for a specific set of categories, you can choose them here. If you leave this (and disabled categories) empty, the facet will be enabled for all categories."
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("attribute_code").choices = (
            self.get_attribute_code_choices()
        )

    def clean(self):
        if self.facet_type == self.FACET_TYPE_RANGE:
            self.validate_ranges_format()
        super().clean()

    def validate_ranges_format(self):
        invalid_ranges = []
        for range_line in self.ranges.split("\n"):
            range_line = range_line.strip()
            if not range_line:
                continue

            try:
                label, min_value, max_value = range_line.split("|")
            except ValueError:
                invalid_ranges.append(range_line)
                continue

            if not label.strip():
                invalid_ranges.append(range_line)
                continue

            min_value = min_value.strip()
            max_value = max_value.strip()

            if not min_value and not max_value:
                invalid_ranges.append(range_line)
                continue

            if min_value and not min_value.isdigit():
                invalid_ranges.append(range_line)
                continue

            if max_value and not max_value.isdigit():
                invalid_ranges.append(range_line)
                continue

        if invalid_ranges:
            valid_examples = (
                "up to 25 |  | 24 <br>"
                "25 tot 150 | 25 | 149 <br>"
                "150 tot 300 | 150 | 299 <br>"
                "300 of meer | 300 |"
            )
            error_message = _(
                "Invalid range format in the following lines: <br><br>"
            ) + "<br>".join(invalid_ranges)
            error_message += _(
                "<br><br>The correct format is: <br> label | from | to.<br>"
            )
            error_message += (
                _("<br>For example, this would be a valid list of ranges:<br>")
                + valid_examples
            )
            raise ValidationError({"ranges": format_html(error_message)})

    def get_ranges(self):
        """
        The ranges should be stored like this:

        tot 25 |  | 24
        25 tot 150 | 25 | 149
        150 tot 300 | 150 | 299
        300 of meer | 300 |

        This method returns a range item like this:
        [
            ("tot 25", (None, 24)),
            ("25 tot 150", (25, 149)),
            ("150 tot 300", (150, 299)),
            ("300 of meer", (300, None)),
        ]

        """
        ranges = []
        for range_line in self.ranges.split("\n"):
            range_line = range_line.strip()
            if not range_line:
                continue

            label, min_value, max_value = range_line.split("|")

            try:
                min_value = int(min_value.strip()) if min_value else None
            except:
                min_value = None

            try:
                max_value = int(max_value.strip()) if max_value else None
            except:
                max_value = None
            ranges.append((label, (min_value, max_value)))
        return ranges

    @classmethod
    def get_attribute_code_choices(cls):
        attr_codes = set(attr.code for attr in ProductAttribute.objects.all())
        return [("", "")] + [(code, code) for code in attr_codes]
