from oscar.config import OscarConfig as AppConfig
from oscar.core.loading import get_class


class DjangoOscarEsConfig(AppConfig):
    name = "apps.django_oscar_es"
    verbose_name = "Django Oscar Elasticsearch"

    def ready(self):
        super().ready()

        register_documents = get_class("django_oscar_es.registry", "register_documents")
        register_documents()
