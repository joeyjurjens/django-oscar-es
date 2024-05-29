from elasticsearch_dsl import Q

from django_es_kit.faceted_search import DynamicFacetedSearch

from oscar.core.loading import get_class

from .settings import get_product_document

ProductDocument = get_product_document()
get_product_elasticsearch_settings = get_class(
    "django_oscar_es.cache", "get_product_elasticsearch_settings"
)


class CatalogueFacetedSearch(DynamicFacetedSearch):
    doc_types = [ProductDocument]
    default_filter_queries = [
        Q("term", is_public=True),
    ]

    def __init__(self, facets, query=None, filters={}, sort=()):
        super().__init__(facets, query, filters, sort)

        # Add configured search fields
        product_es_settings = get_product_elasticsearch_settings()
        search_fields = [
            f"{search_field.field}^{search_field.boost}"
            for search_field in product_es_settings.search_fields.all()
            if not search_field.disabled
        ]
        if self.fields:
            self.fields += search_fields
        else:
            self.fields = search_fields
