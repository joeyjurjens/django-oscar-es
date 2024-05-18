from django_elasticsearch_dsl.registries import registry

from oscar.core.loading import get_class


def register_documents():
    ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

    registry.register_document(ProductDocument)
