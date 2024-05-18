from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.documents import Document

from oscar.core.loading import get_model, get_class

Product = get_model("catalogue", "Product")

Selector = get_class("partner.strategy", "Selector")


class ProductDocument(Document):
    class Index:
        name = "products"
        settings = {
            "number_of_shards": 1,
            "max_ngram_diff": 15,
        }

    class Django:
        model = Product

    _all_text = fields.TextField()

    title = fields.TextField(attr="title")
    description = fields.TextField(attr="description")
    is_public = fields.BooleanField(attr="is_public")
    upc = fields.KeywordField(attr="upc")
    slug = fields.TextField(attr="slug")
    rating = fields.FloatField(attr="rating")
    date_created = fields.DateField(attr="date_created")
    date_updated = fields.DateField(attr="date_updated")
    is_discountable = fields.BooleanField(attr="is_discountable")

    categories = fields.NestedField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "description": fields.TextField(),
        }
    )

    absolute_url = fields.TextField()

    def prepare_absolute_url(self, instance):
        return instance.get_absolute_url()

    parent_id = fields.IntegerField()

    def prepare_parent_id(self, instance):
        if instance.parent:
            return instance.parent.id
        return None

    price = fields.DoubleField()

    def prepare_price(self, instance):
        purchase_info = self.__purchase_info(instance)
        if purchase_info.price.exists:
            return purchase_info.price.incl_tax
        return None

    num_in_stock = fields.IntegerField()

    def prepare_num_in_stock(self, instance):
        purchase_info = self.__purchase_info(instance)
        return getattr(purchase_info.availability, "num_available", 0)

    is_available = fields.BooleanField()

    def prepare_is_available(self, instance):
        purchase_info = self.__purchase_info(instance)
        return purchase_info.availability.is_available_to_buy

    attributes = fields.NestedField(
        properties={
            "name": fields.KeywordField(),
            "value": fields.KeywordField(),
        }
    )

    def prepare_attributes(self, instance):
        attribute_values = instance.attribute_values.all()
        result = []

        for attribute_value in attribute_values:
            result.append(
                {
                    "name": attribute_value.attribute.name,
                    "value": self.__attribute_value_to_representable_value(
                        attribute_value
                    ),
                }
            )

        return result

    def __purchase_info(self, instance):
        if self._purchase_info is not None:
            return self._purchase_info

        strategy = Selector().strategy()

        if instance.is_parent:
            self._purchase_info = strategy.fetch_for_parent(instance)
        else:
            self._purchase_info = strategy.fetch_for_product(instance)

        return self._purchase_info

    _purchase_info = None

    def __attribute_value_to_representable_value(self, attribute_value):
        attribute = attribute_value.attribute

        if attribute.type == attribute.OPTION:
            return attribute_value.value.option
        elif attribute.type == attribute.MULTI_OPTION:
            return [option for option in attribute_value.value.options]
        elif attribute.type == attribute.FILE:
            return attribute_value.value.url
        elif attribute.type == attribute.IMAGE:
            return attribute_value.value.url

        return attribute_value.value
