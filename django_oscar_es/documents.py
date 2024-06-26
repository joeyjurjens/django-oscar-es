from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.documents import Document

from oscar.core.loading import get_model, get_class

from .es_fields import ProductAttributesField
from .settings import get_product_index

Product = get_model("catalogue", "Product")
Selector = get_class("partner.strategy", "Selector")
product_index = get_product_index()


class BaseProductDocument(Document):
    attributes = ProductAttributesField()

    def prepare_attributes(self, instance):
        result = {}
        attribute_values = instance.attribute_values.all()
        for attribute_value in attribute_values:
            result[attribute_value.attribute.code] = (
                self.__attribute_value_to_representable_value(attribute_value)
            )
        return result

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


@product_index.document
class ProductDocument(BaseProductDocument):
    class Django:
        model = Product

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("parent", "product_class")
            .prefetch_related("attribute_values", "attribute_values__attribute")
        )

    title = fields.TextField(
        attr="title",
        analyzer="title_analyzer",
        fields={"keyword": fields.KeywordField(normalizer="lowercase")},
    )
    description = fields.TextField(attr="description", analyzer="description_analyzer")
    upc = fields.KeywordField(attr="upc")
    rating = fields.FloatField(attr="rating")
    is_public = fields.BooleanField(attr="is_public")
    categories = fields.NestedField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.KeywordField(),
            "description": fields.TextField(),
        }
    )
    product_class = fields.NestedField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.KeywordField(),
            "requires_shipping": fields.BooleanField(),
        }
    )

    date_created = fields.DateField(attr="date_created")
    date_updated = fields.DateField(attr="date_updated")

    structure = fields.KeywordField(attr="structure")
    is_discountable = fields.BooleanField(attr="is_discountable")
    slug = fields.TextField(attr="slug")

    absolute_url = fields.TextField()

    def prepare_absolute_url(self, instance):
        return instance.get_absolute_url()

    parent_id = fields.IntegerField()

    def prepare_parent_id(self, instance):
        if instance.parent:
            return instance.parent.id
        return None

    parent_upc = fields.KeywordField()

    def prepare_parent_upc(self, instance):
        if instance.parent:
            return instance.parent.upc
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

    def __purchase_info(self, instance):
        strategy = Selector().strategy()
        if instance.is_parent:
            return strategy.fetch_for_parent(instance)
        else:
            return strategy.fetch_for_product(instance)
