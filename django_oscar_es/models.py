from typing import Any

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from oscar.core.loading import get_model, get_class

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

    def __str__(self):
        return "Product ElasticSearch Configuration"

    class Meta:
        verbose_name = _("Product ElasticSearch Configuration")
        verbose_name_plural = _("Product ElasticSearch Configuration")


class AbstractFacet(models.Model):
    class Meta:
        abstract = True

    FACET_TYPE_TERM = "term"
    FACET_TYPE_RANGE = "range"
    FACET_TYPE_CHOICES = (
        (FACET_TYPE_TERM, _("Term")),
        (FACET_TYPE_RANGE, _("Range")),
    )

    configuration = models.ForeignKey(
        ProductElasicSearchConfiguration,
        on_delete=models.CASCADE,
        related_name="%(class)s_attribute_facets",
    )

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
        related_name="%(class)s_enabled_facets",
        help_text=_(
            "If this facet is for a specific set of categories, you can choose them here. If you leave this (and disabled categories) empty, the facet will be enabled for all categories."
        ),
    )
    disabled_categories = models.ManyToManyField(
        "catalogue.Category",
        blank=True,
        related_name="%(class)s_disabled_facets",
        help_text=_(
            "If this facet should be hidden for a specific set of categories, you can choose them here. If you leave this (and disabled categories) empty, the facet will be enabled for all categories."
        ),
    )

    def clean(self):
        if self.facet_type == self.FACET_TYPE_RANGE:
            self.validate_ranges_format()
        super().clean()

    def validate_ranges_format(self):
        invalid_ranges = []
        valid_example = (
            "up to 25 |  | 24 <br>"
            "25 tot 150 | 25 | 149 <br>"
            "150 tot 300 | 150 | 299 <br>"
            "300 of meer | 300 |"
        )

        for range_line in map(str.strip, self.ranges.split("\n")):
            if not range_line:
                continue

            parts = range_line.split("|")
            if len(parts) != 3:
                invalid_ranges.append(range_line)
                continue

            label, min_value, max_value = map(str.strip, parts)

            if (
                not label
                or (min_value and not min_value.isdigit())
                or (max_value and not max_value.isdigit())
            ):
                invalid_ranges.append(range_line)

        if invalid_ranges:
            error_message = _(
                "Invalid range format in the following lines: <br><br>"
            ) + "<br>".join(invalid_ranges)
            error_message += _(
                "<br><br>The correct format is: <br> label | from | to.<br>"
            )
            error_message += (
                _("<br>For example, this would be a valid list of ranges:<br>")
                + valid_example
            )
            raise ValidationError({"ranges": format_html(error_message)})

    def get_ranges(self):
        ranges = []

        for range_line in map(str.strip, self.ranges.split("\n")):
            if not range_line:
                continue

            label, min_value, max_value = map(str.strip, range_line.split("|"))

            min_value = int(min_value) if min_value.isdigit() else None
            max_value = int(max_value) if max_value.isdigit() else None

            ranges.append((label, (min_value, max_value)))

        return ranges


class AttributeFacet(AbstractFacet):
    """
    This model allows you to create facets for products based on product attributes.
    It loads the all attribute codes as choices, which a user can then configure.
    """

    attribute_code = models.CharField(max_length=255, choices=[("", "")], unique=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("attribute_code").choices = (
            self.get_attribute_code_choices()
        )

    def __str__(self):
        return self.attribute_code

    @classmethod
    def get_attribute_code_choices(cls):
        attr_codes = set(attr.code for attr in ProductAttribute.objects.all())
        return [("", "")] + [(code, code) for code in attr_codes]


class ESFieldFacet(AbstractFacet):
    """
    This model allows you to create facets for products based on ElasticSearch fields.
    """

    field_name = models.CharField(max_length=255, choices=[("", "")], unique=True)

    def __str__(self):
        return self.field_name

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._meta.get_field("field_name").choices = self.get_field_name_choices()

    @classmethod
    def get_field_name_choices(cls):
        """
        Returns all field names that are able to be faceted on from the product document mapping.
        """
        ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

        field_choices = [("", "")]
        for (
            es_properties
        ) in ProductDocument._doc_type.mapping.properties.to_dict().values():
            for es_field_name, es_field_properties in es_properties.items():
                es_field_type = es_field_properties["type"]

                # Fields of type text can't be aggregated, however, if it has a sub field of type keyword we can use that in the aggregation.
                # Alternatively, if fielddata is set to true, we can use it for aggregation but it's not recommended due to memory usage.
                if es_field_type == "text":
                    subfields = es_field_properties.get("fields", {})
                    for subfield_name, subfield_properties in subfields.items():
                        if subfield_properties["type"] == "keyword":
                            aggregate_field_name = f"{es_field_name}.{subfield_name}"
                            field_choices.append(
                                (aggregate_field_name, aggregate_field_name)
                            )
                            break
                    else:
                        if es_field_properties.get("fielddata") is True:
                            field_choices.append((es_field_name, es_field_name))
                else:
                    field_choices.append((es_field_name, es_field_name))

        return field_choices
