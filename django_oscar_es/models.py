import logging
import datetime

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class

ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

logger = logging.getLogger(__name__)


class ProductElasticsearchSettings(models.Model):
    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create()
        return settings


class ProductSearchField(models.Model):
    settings = models.ForeignKey(
        ProductElasticsearchSettings,
        on_delete=models.CASCADE,
        related_name="search_fields",
    )

    field = models.CharField(max_length=255, choices=[("", "")])
    boost = models.FloatField(
        default=1.0, help_text=_("The boost factor for this field.")
    )
    disabled = models.BooleanField(
        default=False,
        help_text=_("If checked, this field will not be used for searching."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("field").choices = self.get_field_choices()

    @classmethod
    def get_field_choices(cls):
        """
        Returns all text and keyword fields from the ProductDocument mapping.
        """
        return [
            (field, field)
            for field, field_info in ProductDocument._doc_type.mapping.to_dict()[
                "properties"
            ].items()
            if field_info["type"] in ["text", "keyword"]
        ]


class ProductFacet(models.Model):
    FACET_TYPE_TERM = "term"
    FACET_TYPE_RANGE = "range"
    FACET_TYPE_CHOICES = (
        (FACET_TYPE_TERM, _("Term")),
        (FACET_TYPE_RANGE, _("Range")),
    )

    settings = models.ForeignKey(
        ProductElasticsearchSettings,
        on_delete=models.CASCADE,
        related_name="facets",
    )

    field = models.CharField(max_length=255, choices=[("", "")])
    label = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            "The label is typically shown above all available choices for this facet. By default is uses the field name."
        ),
    )
    facet_type = models.CharField(
        max_length=20,
        choices=FACET_TYPE_CHOICES,
        default=FACET_TYPE_TERM,
    )
    formatter = models.CharField(
        max_length=255,
        choices=[("", "")],
        help_text=_(
            "If you select a formatter, the values returned from Elasticsearch will be formatted using this function."
        ),
        blank=True,
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
            "If this facet should be hidden for a specific set of categories, you can choose them here. If you leave this (and enabled categories) empty, the facet will be enabled for all categories."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("field").choices = self.get_field_choices()

    @classmethod
    def get_field_choices(cls):
        field_choices = []
        mapping = ProductDocument._doc_type.mapping.to_dict()["properties"]
        for field_name, field_info in mapping.items():
            field_type = field_info.get("type")
            if field_type == "text":
                field_choices.append((f"{field_name}.keyword", f"{field_name}.keyword"))
            elif field_type not in ["object", "nested"]:
                field_choices.append((field_name, field_name))
            else:
                logger.warning(
                    "Skipping field '%s' as for now we don't support object or nested fields (with attributes as exception)",
                    field_name,
                )

            # We know the structure of attributes, so we can add those to the field choices.
            if field_name == "attributes":
                for attribute_code in field_info["properties"].keys():
                    field_choices.append(
                        (
                            f"attributes.{attribute_code}",
                            f"attributes.{attribute_code}",
                        )
                    )

        return field_choices


class ProductFacetRangeOption(models.Model):
    RANGE_TYPE_INTEGER = "integer"
    RANGE_TYPE_FLOAT = "float"
    RANGE_TYPE_DOUBLE = "double"
    RANGE_TYPE_DECIMAL = "decimal"
    RANGE_TYPE_DATE = "date"
    RANGE_TYPE_CHOICES = (
        (RANGE_TYPE_INTEGER, _("Integer")),
        (RANGE_TYPE_FLOAT, _("Float")),
        (RANGE_TYPE_DOUBLE, _("Double")),
        (RANGE_TYPE_DECIMAL, _("Decimal")),
        (RANGE_TYPE_DATE, _("Date")),
    )

    facet = models.ForeignKey(
        ProductFacet,
        on_delete=models.CASCADE,
        related_name="range_options",
    )

    label = models.CharField(
        max_length=255,
        help_text=_("The label for this range option. Eg; '10 to 50'"),
    )
    range_type = models.CharField(
        max_length=20,
        choices=RANGE_TYPE_CHOICES,
        default=RANGE_TYPE_INTEGER,
        help_text=_("The type of range this option represents."),
    )

    from_value = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("The 'from' value for this range option."),
    )
    to_value = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("The 'to' value for this range option."),
    )

    def get_from_value(self):
        """
        Returns the correct value based on the range_type
        """
        return self.value_to_python(self.from_value)

    def get_to_value(self):
        """
        Returns the correct value based on the range_type
        """
        return self.value_to_python(self.to_value)

    def value_to_python(self, value):
        """
        Converts the value to the correct type based on the range_type
        """
        if not value:
            return None

        if self.range_type == self.RANGE_TYPE_INTEGER:
            return int(value)
        elif self.range_type == self.RANGE_TYPE_FLOAT:
            return float(value)
        elif self.range_type == self.RANGE_TYPE_DOUBLE:
            return float(value)
        elif self.range_type == self.RANGE_TYPE_DECIMAL:
            return Decimal(value)
        elif self.range_type == self.RANGE_TYPE_DATE:
            return datetime.strptime(value, "%Y-%m-%d")
        else:
            raise ValueError(f"Unknown range type: {self.range_type}")
