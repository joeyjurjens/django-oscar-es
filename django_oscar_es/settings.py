from importlib import import_module

from django.conf import settings

PRODUCT_DOCUMENT_MODULE = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_PRODUCT_DOCUMENT",
    "django_oscar_es.documents.ProductDocument",
)

PRODUCT_INDEX_MODULE = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_PRODUCT_INDEX",
    "django_oscar_es.index.product_index",
)


def get_product_document():
    module_path, class_name = PRODUCT_DOCUMENT_MODULE.rsplit(".", 1)
    module = import_module(module_path)
    document_class = getattr(module, class_name)

    # Prevent circular imports (as documents imports get_product_index)
    from .documents import BaseProductDocument

    if not issubclass(document_class, BaseProductDocument):
        raise ValueError(
            "OSCAR_ELASTICSEARCH_PRODUCT_DOCUMENT must be a subclass of BaseProductDocument"
        )

    return document_class


def get_product_index():
    module_path, class_name = PRODUCT_INDEX_MODULE.rsplit(".", 1)
    module = import_module(module_path)
    index_class = getattr(module, class_name)
    return index_class
