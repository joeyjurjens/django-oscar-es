import logging

from elasticsearch_dsl import TermsFacet, RangeFacet

from django.db import models
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model, get_class

from .validator import RangeFormatValidator

ProductAttribute = get_model("catalogue", "ProductAttribute")

logger = logging.getLogger(__name__)


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


class ProductFacet(models.Model):
    FACET_TYPE_TERM = "term"
    FACET_TYPE_RANGE = "range"
    FACET_TYPE_CHOICES = (
        (FACET_TYPE_TERM, _("Term")),
        (FACET_TYPE_RANGE, _("Range")),
    )

    configuration = models.ForeignKey(
        ProductElasicSearchConfiguration,
        on_delete=models.CASCADE,
        related_name="facets",
    )

    field_name = models.CharField(max_length=255, choices=[("", "")], unique=True)
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
        validators=[RangeFormatValidator()],
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("field_name").choices = self.get_field_name_choices()

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

    def get_es_facet_obj(self):
        """
        Returns the correct ES facet object based on the facet type.
        """

        if self.facet_type == self.FACET_TYPE_TERM:
            return TermsFacet(field=self.field_name)
        elif self.facet_type == self.FACET_TYPE_RANGE:
            return RangeFacet(ranges=self.get_ranges(), field=self.field_name)
        else:
            raise NotImplementedError(
                f"Unknown facet type '{self.facet_type}' for attribute '{self.field_name}'."
            )

    @classmethod
    def get_field_name_choices(cls):
        return cls.get_es_field_choices()

    @classmethod
    def get_es_field_choices(self):
        """
        Returns all fields that are able to be faceted on from the product document mapping.
        """
        ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

        choices = [("", "")]

        es_document_properties = ProductDocument._doc_type.mapping.properties.to_dict()
        for es_property in es_document_properties.values():
            for es_field_name, es_field_properties in es_property.items():
                es_field_type = es_field_properties["type"]

                # Fields of type text can't be aggregated by default.
                if es_field_type == "text":
                    choice = self.get_es_text_field_choice(
                        es_field_name, es_field_properties
                    )
                    if choice is not None:
                        choices.append(choice)
                # fields of type object and nested are not implemented for faceting.
                elif es_field_type not in ["object", "nested"]:
                    choices.append((es_field_name, f"[field] {es_field_name}"))

                # Attributes is of type object, but we know the format so for this we can add them to our choices.
                if es_field_name == "attributes":
                    for attribute_code in es_field_properties["properties"].keys():
                        choices.append(
                            (
                                f"attributes.{attribute_code}",
                                f"[attribute] {attribute_code}",
                            )
                        )

        return choices

    @classmethod
    def get_es_text_field_choice(cls, es_field_name, es_field_properties):
        subfields = es_field_properties.get("fields", {})
        for subfield_name, subfield_properties in subfields.items():
            if subfield_properties["type"] == "keyword":
                aggregate_field_name = f"{es_field_name}.{subfield_name}"
                return (
                    aggregate_field_name,
                    f"[field] {es_field_name} ({es_field_name}.{subfield_name})",
                )

        # At this point, we did not find a subfield of type keyword, so we check if fielddata is set to true.
        # If it is, we can use the actual field for aggregation, but it's not recommened due to high memory usage.
        if es_field_properties.get("fielddata") is True:
            if es_field_properties.get("fielddata") is True:
                return (es_field_name, f"[field] {es_field_name}")

        return None
