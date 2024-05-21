from elasticsearch_dsl import FacetedSearch, NestedFacet, TermsFacet
from django_elasticsearch_dsl import fields

from oscar.core.loading import get_class, get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")
AttributeFacets = get_class("django_oscar_es.facets", "AttributeFacets")


class ProductFacetedSearch(FacetedSearch):
    doc_types = [ProductDocument]
    fields = ["title", "description"]
    facets = {
        "categories": NestedFacet("categories", TermsFacet(field="categories.name")),
        "num_in_stock": TermsFacet(field="num_in_stock"),
    }

    def __init__(self, query=None, filters={}, sort=()):
        for (
            attribute_code,
            es_attribute_properties,
        ) in AttributeFacets.get_attributes_mapping_properties().items():
            # If the attribute is of type text, we must do the aggregation on keyword as es can't aggregate on text fields.
            if es_attribute_properties["type"] == fields.Text().name:
                self.facets[attribute_code] = TermsFacet(
                    field=f"attribute_facets.{attribute_code}.keyword"
                )
            else:
                self.facets[attribute_code] = TermsFacet(
                    field=f"attribute_facets.{attribute_code}"
                )

        super().__init__(query=query, filters=filters, sort=sort)
