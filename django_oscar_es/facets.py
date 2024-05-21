from django.core.cache import cache

from django_elasticsearch_dsl import fields

from oscar.core.loading import get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")


class AttributeFacets:
    """
    This class is responsible for managing the product attributes that are used for faceting in Elasticsearch.
    It is loaded with get_class, so it's possible to override it in your own project.
    """

    CACHE_TIMEOUT = 60 * 60
    CACHE_KEY = "product_attribute_es_facets"

    @classmethod
    def get_attribute_facets(cls):
        attributes = cache.get(cls.CACHE_KEY)
        if not attributes:
            attributes = list(ProductAttribute.objects.all())
            cache.set(
                AttributeFacets.CACHE_KEY, attributes, AttributeFacets.CACHE_TIMEOUT
            )
        return attributes

    @classmethod
    def attribute_type_to_es_type(cls, attribute):
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

    @classmethod
    def get_attributes_mapping_properties(cls):
        properties = {}
        for attribute in cls.get_attribute_facets():
            es_type = cls.attribute_type_to_es_type(attribute).name

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
