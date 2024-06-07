from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from .models import ProductFacet, ProductSearchField
from .cache import (
    PRODUCT_ELASTICSEARCH_SETTINGS_CACHE_KEY,
    get_product_elasticsearch_settings,
)


# pylint: disable=unused-argument
@receiver(post_save, sender=ProductFacet)
@receiver(post_delete, sender=ProductFacet)
@receiver(post_save, sender=ProductSearchField)
@receiver(post_delete, sender=ProductSearchField)
def refresh_product_elasticsearch_settings_cache(sender, instance, **kwargs):
    from django.core.cache import cache

    cache.delete(PRODUCT_ELASTICSEARCH_SETTINGS_CACHE_KEY)
    get_product_elasticsearch_settings()
