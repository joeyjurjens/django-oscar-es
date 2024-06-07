from django import forms
from django.utils.translation import gettext_lazy as _

from django_es_kit.forms import FacetedSearchForm
from django_es_kit.fields import SortField

from oscar.core.loading import get_class

from .form_fields import (
    PriceInputField,
    DbFacetField,
    DbRangeFacetField,
)
from .models import ProductFacet

get_product_elasticsearch_settings = get_class(
    "django_oscar_es.cache", "get_product_elasticsearch_settings"
)


class BaseProductFacetedSearchForm(FacetedSearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically add facet fields from the database
        product_es_settings = get_product_elasticsearch_settings()
        for db_facet in product_es_settings.facets.all():
            if db_facet.facet_type == ProductFacet.FACET_TYPE_TERM:
                self.fields[db_facet.field] = DbFacetField(
                    es_field=db_facet.field,
                    field_type=str,
                    db_facet=db_facet,
                )
            elif db_facet.facet_type == ProductFacet.FACET_TYPE_RANGE:
                self.fields[db_facet.field] = DbRangeFacetField(
                    es_field=db_facet.field,
                    field_type=str,
                    db_facet=db_facet,
                )
            else:
                raise ValueError(f"Unknown facet type '{db_facet.facet_type}'")


class ProductFacetedSearchForm(BaseProductFacetedSearchForm):
    RELEVANCY = "relevancy"
    TOP_RATED = "rating"
    NEWEST = "newest"
    PRICE_HIGH_TO_LOW = "price-desc"
    PRICE_LOW_TO_HIGH = "price-asc"
    TITLE_A_TO_Z = "title-asc"
    TITLE_Z_TO_A = "title-desc"

    SORT_BY_CHOICES = [
        (RELEVANCY, _("Relevancy"), "_score"),
        (TOP_RATED, _("Customer rating"), "-rating"),
        (NEWEST, _("Newest"), "-date_created"),
        (PRICE_HIGH_TO_LOW, _("Price high to low"), "-price"),
        (PRICE_LOW_TO_HIGH, _("Price low to high"), "price"),
        (TITLE_A_TO_Z, _("Title A to Z"), "title.keyword"),
        (TITLE_Z_TO_A, _("Title Z to A"), "-title.keyword"),
    ]

    q = forms.CharField(required=False, label=_("Search"))
    sort_by = SortField(SORT_BY_CHOICES, required=False)
    price = PriceInputField(required=False)
