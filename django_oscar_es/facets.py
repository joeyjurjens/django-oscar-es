from django.core.cache import cache

from django_elasticsearch_dsl import fields

from oscar.core.loading import get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")

CACHE_TIMEOUT = 60 * 60
CACHE_KEY = "product_attribute_es_facets"


class AttributeFacets:
    """
    This class is responsible for managing the product attributes that are used for faceting in Elasticsearch.
    It is loaded with get_class, so it's possible to override it in your own project.
    """

    CACHE_TIMEOUT = 60 * 60
    CACHE_KEY = "product_attribute_es_facets"

    @staticmethod
    def get_attribute_facets():
        attributes = cache.get(AttributeFacets.CACHE_KEY)
        if not attributes:
            attributes = list(ProductAttribute.objects.all())
            cache.set(
                AttributeFacets.CACHE_KEY, attributes, AttributeFacets.CACHE_TIMEOUT
            )
        return attributes

    @staticmethod
    def attribute_type_to_es_type(attribute):
        if attribute.type in [attribute.TEXT, attribute.OPTION, attribute.MULTI_OPTION]:
            return fields.Keyword()
        elif attribute.type == attribute.RICHTEXT:
            return fields.Text()
        elif attribute.type in [attribute.DATE, attribute.DATETIME]:
            return fields.Date()
        elif attribute.type == attribute.BOOLEAN:
            return fields.Boolean()
        elif attribute.type == attribute.INTEGER:
            return fields.Integer()
        elif attribute.type == attribute.FLOAT:
            return fields.Float()
        return fields.Text()

    @staticmethod
    def get_attributes_mapping_properties():
        properties = {}
        for attribute in ProductAttribute.objects.all():
            es_type = AttributeFacets.attribute_type_to_es_type(attribute).name

            # If the same attribute code already exists in the properties, we must ensure that the
            # type is the same. Otherwise it fails to index. If it's not the same, we'll make it a keyword type.
            if attribute.code in properties:
                if properties[attribute.code]["type"] != es_type:
                    properties[attribute.code] = {
                        "type": fields.Keyword().name,
                    }
            else:
                properties[attribute.code] = {
                    "type": es_type,
                }

            # If the attribute is a text type, we must add a keyword field to it, otherwise we can't aggregate it.
            if properties[attribute.code]["type"] == fields.Text().name:
                properties[attribute.code]["fields"] = {
                    "keyword": fields.KeywordField()
                }

        return properties
