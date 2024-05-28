from elasticsearch_dsl import Q

from django_es_facets.faceted_search import DynamicFacetedSearch


class CatalogueRootFacetedSearch(DynamicFacetedSearch):
    default_filter_queries = [
        Q("term", is_public=True),
    ]


class CatalogueCategoryFacetedSearch(CatalogueRootFacetedSearch):
    def __init__(self, category, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category

        # Append to the default filter queries
        self.filter_queries.append(Q("term", categories__id=category.id))
