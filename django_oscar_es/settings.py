from importlib import import_module

from django.conf import settings

from .documents import BaseProductDocument

PRODUCT_DOCUMENT_MODULE = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_PRODUCT_DOCUMENT",
    "django_oscar_es.documents.ProductDocument",
)


def get_product_document():
    module_path, class_name = PRODUCT_DOCUMENT_MODULE.rsplit(".", 1)
    module = import_module(module_path)
    document_class = getattr(module, class_name)

    if not issubclass(document_class, BaseProductDocument):
        raise ValueError(
            "OSCAR_ELASTICSEARCH_PRODUCT_DOCUMENT must be a subclass of BaseProductDocument"
        )

    return document_class()
