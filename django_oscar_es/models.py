import logging

from elasticsearch_dsl import TermsFacet, RangeFacet
from django_elasticsearch_dsl import fields

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
        return [("", "")] + cls.get_es_field_choices() + cls.get_attribute_choices()

    @classmethod
    def get_es_field_choices(self):
        """
        Returns all fields that are able to be faceted on from the product document mapping.
        """
        ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

        choices = []

        es_document_properties = ProductDocument._doc_type.mapping.properties.to_dict()
        for es_property in es_document_properties.values():
            for es_field_name, es_field_properties in es_property.items():
                es_field_type = es_field_properties["type"]

                # Fields of type text can't be aggregated
                if es_field_type == "text":

                    # Check if there is a subfield of type keyword, if so, we can use that for aggregation.
                    subfields = es_field_properties.get("fields", {})
                    for subfield_name, subfield_properties in subfields.items():
                        if subfield_properties["type"] == "keyword":
                            aggregate_field_name = f"{es_field_name}.{subfield_name}"
                            choices.append(
                                (
                                    aggregate_field_name,
                                    f"[field] {es_field_name} ({es_field_name}.{subfield_name})",
                                )
                            )
                            break

                    # At this point, we did not find a subfield of type keyword, so we check if fielddata is set to true.
                    # If it is, we can use the actual field for aggregation, but it's not recommened due to high memory usage.
                    if es_field_properties.get("fielddata") is True:
                        if es_field_properties.get("fielddata") is True:
                            choices.append((es_field_name, f"[field] {es_field_name}"))
                else:
                    choices.append((es_field_name, f"[field] {es_field_name}"))

        return choices

    @classmethod
    def get_attribute_choices(cls):
        choices = []
        es_attributes_mapping_properties = cls.get_es_attributes_mapping_properties()
        for attribute_code in es_attributes_mapping_properties.keys():
            choices.append(
                (f"attributes.{attribute_code}", f"[attribute] {attribute_code}")
            )
        return choices

    @classmethod
    def get_es_attributes_mapping_properties(cls):
        """
        Returns the ES mapping properties for the attribute facets.
        """
        properties = {}

        for attribute in ProductAttribute.objects.all():
            es_type = cls.attribute_type_to_es_type(attribute)
            attribute_code = attribute.code

            # If the attribute code is already in the properties, we need to check if the type is the same.
            # If it's not the same, we need to set the type to keyword, otherwise we can't index the document (conflicting types).
            if attribute_code in properties:
                if properties[attribute_code]["type"] != es_type.name:
                    properties[attribute_code] = {
                        "type": fields.Keyword().name,
                    }

                # We're done here, continue to the next attribute.
                continue

            properties[attribute_code] = {
                "type": es_type.name,
            }

            # If the attribute is of type text, also add a keyword field for aggregation (because that's not possible on text).
            if properties[attribute_code]["type"] == fields.Text().name:
                properties[attribute_code]["fields"] = {
                    "keyword": fields.KeywordField()
                }

        return properties

    @classmethod
    def attribute_type_to_es_type(cls, attribute):
        if attribute.type in [attribute.TEXT, attribute.OPTION, attribute.MULTI_OPTION]:
            return fields.Keyword()
        elif attribute.type == attribute.RICHTEXT:
            return fields.Text()
        elif attribute.type in [attribute.DATE, attribute.DATETIME]:
            return fields.Date()
        elif attribute.type == attribute.BOOLEAN:
            return fields.Boolean()
        elif attribute.type == attribute.INTEGER:
            return fields.Integer()
        elif attribute.type == attribute.FLOAT:
            return fields.Float()
        return fields.Keyword()
