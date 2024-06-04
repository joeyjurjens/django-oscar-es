from django_es_kit.forms import FacetedSearchForm

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


class ProductFacetedSearchForm(FacetedSearchForm):
    price = PriceInputField(required=False)
