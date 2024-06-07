import logging
import datetime

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from .settings import get_product_document
from .formatters.registry import formatter_registry

ProductDocument = get_product_document()

logger = logging.getLogger(__name__)


class ProductElasticsearchSettings(models.Model):
    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create()
        return (
            cls.objects.select_related()
            .prefetch_related("facets", "facets__range_options")
            .get(pk=settings.pk)
        )


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
        properties = ProductDocument._doc_type.mapping.to_dict()["properties"].items()
        return [
            (field, field)
            for field, field_info in properties
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
    size = models.IntegerField(
        default=10,
        help_text=_("The number of facet values to return."),
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

    def get_formatter(self):
        if self.formatter:
            formatter_func = formatter_registry.get_formatter(self.formatter)
            if formatter_func:
                return formatter_func
            else:
                logger.warning(
                    "Formatter %s is not registered in the formatter registry. This could happen if this formatter was chosen for a facet but removed later.",
                    self.formatter,
                )

        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field("field").choices = self.get_field_choices()
        self._meta.get_field("formatter").choices = self.get_formatter_choices()

    @classmethod
    def get_field_choices(cls):
        field_choices = []
        mapping = ProductDocument._doc_type.mapping.to_dict()["properties"]
        for field_name, field_info in mapping.items():
            field_type = field_info.get("type")
            # Text fields can't be used for faceting, search for a keyword field instead.
            if field_type == "text":
                if "fields" in field_info:
                    for sub_field_name, sub_field_info in field_info.get(
                        "fields", []
                    ).items():
                        if sub_field_info["type"] == "keyword":
                            field_choices.append(
                                (
                                    f"{field_name}.{sub_field_name}",
                                    f"{field_name}.{sub_field_name}",
                                )
                            )
                            break
            elif field_type not in ["object", "nested"]:
                field_choices.append((field_name, field_name))
            else:
                logger.warning(
                    "Skipping field '%s' as for now we don't support object or nested fields (with attributes as exception)",
                    field_name,
                )

            # We know the structure of attributes, so we can add those to the field choices.
            if field_name == "attributes":
                for attribute_code, attribute_info in field_info["properties"].items():
                    if attribute_info["type"] == "text":
                        facet_field = f"attributes.{attribute_code}.keyword"
                    else:
                        facet_field = f"attributes.{attribute_code}"

                    field_choices.append((facet_field, facet_field))

        return field_choices

    @classmethod
    def get_formatter_choices(cls):
        return [("", "")] + [
            (name, name) for name, _ in formatter_registry.get_formatters()
        ]


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
