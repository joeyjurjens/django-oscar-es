from django.urls import path, re_path

from oscar.core.loading import get_class

CatalogueView = get_class("django_oscar_es.views", "CatalogueView")
ProductCategoryView = get_class("django_oscar_es.views", "ProductCategoryView")
SearchView = get_class("django_oscar_es.views", "SearchView")


app_name = "django_oscar_es"

# Replaces the Django Oscar catalogue URLs (optional).
urlpatterns = [
    path("catalogue/", CatalogueView.as_view(), name="catalogue-root"),
    re_path(
        r"^catalogue/category/(?P<category_slug>[\w-]+(/[\w-]+)*)_(?P<pk>\d+)/$",
        ProductCategoryView.as_view(),
        name="category",
    ),
    path("search/", SearchView.as_view(), name="search"),
]
