import logging

from elasticsearch_dsl import (
    FacetedSearch,
    NestedFacet,
    TermsFacet,
    RangeFacet,
    DateHistogramFacet,
)
from django_elasticsearch_dsl import fields

from oscar.core.loading import get_class, get_model

from .models import AttributeFacet

ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")
AttributeFacets = get_class("django_oscar_es.facets", "AttributeFacets")

loggger = logging.getLogger(__name__)


class ProductFacetedSearch(FacetedSearch):
    doc_types = [ProductDocument]
    fields = ["title", "description"]
    facets = {
        "categories": NestedFacet("categories", TermsFacet(field="categories.name")),
        "num_in_stock": TermsFacet(field="num_in_stock"),
    }

    def __init__(self, query=None, filters={}, sort=()):
        self.load_attribute_facets()
        super().__init__(query=query, filters=filters, sort=sort)

    def load_attribute_facets(self):
        """
        This method adds the configured attribute facets to the facets list.
        """
        attribute_mapping = AttributeFacets.get_attributes_mapping_properties()
        attribute_facets_map = AttributeFacets.attribute_facets_map()

        for attribute_code, es_attribute_properties in attribute_mapping.items():
            es_field_name = f"attribute_facets.{attribute_code}"
            es_attribute_type = es_attribute_properties["type"]

            # If the attribute is of type text, aggregate on the keyword field
            if es_attribute_type == fields.Text().name:
                es_field_name += ".keyword"

            attribute_facet = attribute_facets_map[attribute_code]
            facet_type = attribute_facet.facet_type

            if facet_type == AttributeFacet.FACET_TYPE_TERM:
                self.facets[attribute_code] = TermsFacet(field=es_field_name)
            elif facet_type == AttributeFacet.FACET_TYPE_RANGE:
                # ToDo: If the field is not numeric, ES is being very weird regarding results.
                self.facets[attribute_code] = RangeFacet(
                    ranges=attribute_facet.get_ranges(),
                    field=es_field_name,
                )
            else:
                loggger.warning(
                    f"Unknown facet type '{facet_type}' for attribute '{attribute_code}'."
                )
                continue
