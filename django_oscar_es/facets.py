from django.core.cache import cache
from django.db.utils import OperationalError

from django_elasticsearch_dsl import fields

from oscar.core.loading import get_model

from .models import AttributeFacet

ProductAttribute = get_model("catalogue", "ProductAttribute")


class AttributeFacets:
    """
    This class is responsible for managing the product attributes that are used for faceting in Elasticsearch.
    It is loaded with get_class, so it's possible to override it in your own project.
    """

    # To prevent database queries every time a user lands on the product list page, we cache the attribute facets.
    # The cache is invalidated every 24 hours or whenever a new attribute facet was created.
    ATTRIBUTE_FACETS_MAP_CACHE_KEY = "attribute_facets_map"
    FACET_ATTRIBUTES_CACHE_KEY = "facet_attributes"
    CACHE_TIMEOUT = 60 * 60 * 24

    @classmethod
    def attribute_facets_map(cls):
        """
        Returns the AttributeFacet instances mapped by attribute code.
        """
        attribute_facets = cache.get(cls.ATTRIBUTE_FACETS_MAP_CACHE_KEY)
        if not attribute_facets:
            try:
                attribute_facets = {
                    facet.attribute_code: facet
                    for facet in AttributeFacet.objects.all()
                }
            # A bit ugly, but when this app is just added migrations haven't been ran yet.
            # And the django_elasticsearch_dsl has a autodiscover module on documents.py which uses this class.
            except OperationalError:
                return {}

            cache.set(
                key=cls.ATTRIBUTE_FACETS_MAP_CACHE_KEY,
                value=attribute_facets,
                timeout=cls.CACHE_TIMEOUT,
            )
        return attribute_facets

    @classmethod
    def facet_attributes(cls):
        """
        Returns the ProductAttribute instances that are used for faceting.
        """
        facet_attributes = cache.get(cls.FACET_ATTRIBUTES_CACHE_KEY)
        if not facet_attributes:
            facet_attributes = list(
                ProductAttribute.objects.filter(
                    code__in=cls.attribute_facets_map().keys()
                )
            )
            cache.set(
                key=cls.FACET_ATTRIBUTES_CACHE_KEY,
                value=facet_attributes,
                timeout=cls.CACHE_TIMEOUT,
            )
        return facet_attributes

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
        return fields.Keyword()

    @classmethod
    def get_attributes_mapping_properties(cls):
        properties = {}

        for attribute in cls.facet_attributes():
            es_type = cls.attribute_type_to_es_type(attribute).name
            attribute_code = attribute.code

            if attribute_code in properties:
                if properties[attribute_code]["type"] != es_type:
                    properties[attribute_code] = {
                        "type": fields.Keyword().name,
                    }
            else:
                properties[attribute_code] = {
                    "type": es_type,
                }

            if properties[attribute_code]["type"] == fields.Text().name:
                properties[attribute_code]["fields"] = {
                    "keyword": fields.KeywordField()
                }

        return properties
