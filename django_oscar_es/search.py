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

from .models import AttributeFacet, ESFieldFacet

ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")
AttributeFacets = get_class("django_oscar_es.facets", "AttributeFacets")

loggger = logging.getLogger(__name__)


class ProductFacetedSearch(FacetedSearch):
    doc_types = [ProductDocument]
    fields = ["title", "description"]

    def __init__(self, query=None, filters={}, sort=()):
        self.load_attribute_facets()
        self.load_es_fields_facet()
        super().__init__(query=query, filters=filters, sort=sort)

    def load_es_fields_facet(self):
        """
        This method adds the configured ES fields facets to the facets list.
        """
        for es_field in ESFieldFacet.objects.all():
            if es_field.facet_type == ESFieldFacet.FACET_TYPE_TERM:
                self.facets[es_field.field_name] = TermsFacet(field=es_field.field_name)
            elif es_field.facet_type == ESFieldFacet.FACET_TYPE_RANGE:
                self.facets[es_field.field_name] = RangeFacet(
                    ranges=es_field.get_ranges(),
                    field=es_field.field_name,
                )
            else:
                raise NotImplementedError(
                    f"Unknown facet type '{es_field.facet_type}' for field '{es_field.field_name}'."
                )

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
                self.facets[attribute_code] = RangeFacet(
                    ranges=attribute_facet.get_ranges(),
                    field=es_field_name,
                )
            else:
                raise NotImplementedError(
                    f"Unknown facet type '{facet_type}' for attribute '{attribute_code}'."
                )
