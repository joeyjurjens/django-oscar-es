import logging

from elasticsearch_dsl import (
    FacetedSearch,
    FacetedResponse,
    Search,
)

from oscar.core.loading import get_class, get_model

from .models import AttributeFacet, ESFieldFacet

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

        print(facets.to_dict())
        return facets


class ProductFacetedSearch(FacetedSearch):
    doc_types = [ProductDocument]
    fields = ["title", "description"]

    def __init__(self, query=None, filters={}, sort=()):
        self.facet_mapping = {}
        self.load_attribute_facets()
        self.load_es_fields_facet()
        super().__init__(query=query, filters=filters, sort=sort)

    def search(self):
        return Search(
            doc_type=self.doc_types, index=self.index, using=self.using
        ).response_class(PopulatedFacetedResponse)

    def load_es_fields_facet(self):
        """
        This method adds the configured ES fields facets to the facets list.
        """
        for es_field_facet in ESFieldFacet.objects.all():
            es_facet_obj = es_field_facet.get_es_facet_obj()
            self.facets[es_field_facet.field_name] = es_facet_obj
            self.facet_mapping[es_field_facet.field_name] = es_field_facet

    def load_attribute_facets(self):
        """
        This method adds the configured attribute facets to the facets list.
        """

        for attribute_facet in AttributeFacet.objects.all():
            es_facet_obj = attribute_facet.get_es_facet_obj()
            self.facets[attribute_facet.attribute_code] = es_facet_obj
            self.facet_mapping[attribute_facet.attribute_code] = attribute_facet
