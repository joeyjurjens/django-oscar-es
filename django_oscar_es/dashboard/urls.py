from django.urls import path

from .views import ProductElasticsearchSettingsView

# ToDo: This should instead be done in the AppConfig as Oscar has a custom AppConfig that allows for this.
urlpatterns = [
    path(
        "",
        ProductElasticsearchSettingsView.as_view(),
        name="product-elasticsearch-settings",
    ),
]
