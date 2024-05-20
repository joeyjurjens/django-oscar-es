from elasticsearch_dsl import FacetedSearch, NestedFacet, TermsFacet, Facet, A, Q

from oscar.core.loading import get_class

ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")


class ProductAttributseFacet(Facet):
    """
    This facet is used to aggregate on the attributes of a product. The aggregation is a multi level nested aggregation.
    The first level is the attribute code and the second level is the attribute value. This way it's grouped and we know
    which values are available for which attribute.

    The aggregation looks like this:
    {
        "aggs": {
            "attributes": {
                "nested": {
                    "path": "attributes"
                },
                "aggs": {
                    "names": {
                        "terms": {
                            "field": "attributes.code"
                        },
                        "aggs": {
                            "values": {
                                "terms": {
                                    "field": "attributes.value"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    def get_aggregation(self):
        nested_agg = A("nested", path="attributes")
        code_agg = A("terms", field="attributes.code")
        value_agg = A("terms", field="attributes.value")
        nested_agg.bucket("codes", code_agg).bucket("values", value_agg)
        return nested_agg

    def add_filter(self, filter_values):
        """
        This method is overridden to allow filtering on attributes using the FacetedSearch API. Eg you can now do this:
        response = ProductFacetedSearch(
            filters={
                "attributes": {
                    "size": ["Medium"],
                    "color": ["Red"]
                }
            }
        ).execute()
        """
        if filter_values:
            nested_filter = []

            for filter_item in filter_values:
                should_conditions = []

                for code, values in filter_item.items():
                    terms_query = Q(
                        "nested",
                        path="attributes",
                        query=Q(
                            "bool",
                            must=[
                                Q("match", **{"attributes.code": code}),
                                Q("terms", **{"attributes.value": values}),
                            ],
                        ),
                    )
                    should_conditions.append(terms_query)

                nested_filter.append(Q("bool", should=should_conditions))

            return Q("bool", should=nested_filter)

    def is_filtered(self, attribute_code, attribute_value, filter_values):
        """
        This method is overridden to check if the attribute value is selected in the filter.
        """
        for filter_item in filter_values:
            if (
                attribute_code in filter_item
                and attribute_value in filter_item[attribute_code]
            ):
                return True
        return False

    def get_value(self, bucket):
        return super().get_value(bucket)

    def get_metric(self, bucket):
        return super().get_metric(bucket)

    def get_values(self, data, filter_values):
        """
        This method is overridden to return the values of the nested aggregation in a more structured way.
        """
        out = []
        for bucket in data["codes"].buckets:
            values = [
                {
                    "key": value["key"],
                    "doc_count": value["doc_count"],
                    "selected": self.is_filtered(
                        bucket["key"], value["key"], filter_values
                    ),
                }
                for value in bucket["values"].buckets
            ]
            out.append((bucket["key"], bucket["doc_count"], values))

        return out


class ProductFacetedSearch(FacetedSearch):
    doc_types = [ProductDocument]
    fields = ["title", "description"]
    facets = {
        "categories": NestedFacet("categories", TermsFacet(field="categories.name")),
        "num_in_stock": TermsFacet(field="num_in_stock"),
        "attributes": ProductAttributseFacet(),
    }
