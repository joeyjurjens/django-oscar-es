from django.urls import path, include

from oscar.config import OscarConfig as AppConfig
from oscar.core.loading import get_class

from django_elasticsearch_dsl.registries import registry


class DjangoOscarEsConfig(AppConfig):
    name = "django_oscar_es"
    verbose_name = "Django Oscar Elasticsearch"

    def ready(self):
        super().ready()

        ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")
        registry.register_document(ProductDocument)
