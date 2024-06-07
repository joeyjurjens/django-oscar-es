from django.apps import apps
from django.urls import path
from django.utils.module_loading import autodiscover_modules

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class

from django_elasticsearch_dsl.registries import registry


class DjangoOscarEsConfig(OscarDashboardConfig):
    name = "django_oscar_es"
    verbose_name = "Django Oscar Elasticsearch"

    namespace = "dashboard"

    def ready(self):
        super().ready()
        self.oscar_app = apps.get_app_config("oscar")
        self.product_elasticsearch_settings_view = get_class(
            "django_oscar_es.dashboard.views", "ProductElasticsearchSettingsView"
        )

        # pylint: disable=unused-import
        from . import signal_receivers

        autodiscover_modules("es_formatters")
        self.register_documents()
        self.patch_dashboard_config_urls()

    def register_documents(self):
        from .settings import get_product_document

        registry.register_document(get_product_document())

    def get_urls(self):
        url_patterns = [
            path(
                "dashboard/elasticsearch/",
                self.product_elasticsearch_settings_view.as_view(),
                name="dashboard-product-elasticsearch",
            ),
        ]
        return self.post_process_urls(url_patterns)

    def patch_dashboard_config_urls(self):
        """
        A bit of a hack, but I don't feel like forking the app just to add a url.
        """
        original_urls = self.oscar_app.get_urls()

        def new_urls():
            return original_urls + self.get_urls()

        self.oscar_app.get_urls = new_urls
