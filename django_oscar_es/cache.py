from django.core.cache import cache

from .models import ProductElasticsearchSettings

PRODUCT_ELASTICSEARCH_SETTINGS_CACHE_KEY = "product_elasticsearch_settings"


def get_product_elasticsearch_settings():
    settings = cache.get(PRODUCT_ELASTICSEARCH_SETTINGS_CACHE_KEY)
    if settings is None:
        settings = ProductElasticsearchSettings.load()
        cache.set(PRODUCT_ELASTICSEARCH_SETTINGS_CACHE_KEY, settings)
    return settings
