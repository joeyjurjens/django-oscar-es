import logging

from elasticsearch_dsl import (
    FacetedSearch,
    FacetedResponse,
    Search,
)

from oscar.core.loading import get_class, get_model

from .models import ProductFacet

ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

loggger = logging.getLogger(__name__)


class PopulatedFacetedResponse(FacetedResponse):
    """
    This class changes the facets propert to include the facet object from the database.
    """

    @property
    def facets(self):
        facets = super().facets
        for facet_name, facet in facets.items():
            facets[facet_name] = {
                "db_facet": self._faceted_search.facet_mapping[facet_name],
                "values": facet,
            }
        return facets


class ProductFacetedSearch(FacetedSearch):
    doc_types = [ProductDocument]
    fields = ["title", "description"]

    def __init__(self, query=None, filters={}, sort=()):
        self.facet_mapping = {}
        self.load_product_facets()
        super().__init__(query=query, filters=filters, sort=sort)

    def search(self):
        return Search(
            doc_type=self.doc_types, index=self.index, using=self.using
        ).response_class(PopulatedFacetedResponse)

    def load_product_facets(self):
        """
        This method adds the configured product facets to the facets list.
        """

        for product_facet in ProductFacet.objects.all():
            es_facet_obj = product_facet.get_es_facet_obj()
            self.facets[product_facet.field_name] = es_facet_obj
            self.facet_mapping[product_facet.field_name] = product_facet
