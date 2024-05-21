from django_elasticsearch_dsl import fields

from oscar.core.loading import get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")


class ProductAttributesField(fields.ObjectField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.properties = self.get_attributes_properties()

    def get_attributes_properties(self):
        properties = {}

        for attribute in ProductAttribute.objects.all():
            es_type = self.attribute_type_to_es_type(attribute)
            attribute_code = attribute.code

            # If the attribute code is already in the properties, we need to check if the type is the same.
            # If it's not the same, we need to set the type to keyword, otherwise we can't index the document (conflicting types).
            if attribute_code in properties:
                if properties[attribute_code]["type"] != es_type.name:
                    properties[attribute_code] = {
                        "type": fields.Keyword().name,
                    }

                # We're done here, continue to the next attribute.
                continue

            properties[attribute_code] = {
                "type": es_type.name,
            }

            # If the attribute is of type text, also add a keyword field for aggregation (because that's not possible on text).
            if properties[attribute_code]["type"] == fields.Text().name:
                properties[attribute_code]["fields"] = {
                    "keyword": fields.KeywordField()
                }

        return properties

    def attribute_type_to_es_type(self, attribute):
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
