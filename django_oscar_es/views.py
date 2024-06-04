import logging

from elasticsearch_dsl import Q

from django.conf import settings
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from django_es_kit.views import ESFacetedSearchView

from oscar.core.loading import get_class, get_model

ProductFacetedSearchForm = get_class(
    "django_oscar_es.forms", "ProductFacetedSearchForm"
)
CatalogueFacetedSearch = get_class(
    "django_oscar_es.faceted_search", "CatalogueFacetedSearch"
)
Category = get_model("catalogue", "Category")

logger = logging.getLogger(__name__)


class BaseCatalogueView(ListView, ESFacetedSearchView):
    form_class = ProductFacetedSearchForm
    faceted_search_class = CatalogueFacetedSearch
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE
    context_object_name = "products"

    def get_search_query(self):
        return self.request.GET.get("q", None)

    def get_faceted_search(self):
        faceted_search = super().get_faceted_search()
        faceted_search.set_pagination(page=1, page_size=self.paginate_by)
        return faceted_search

    def get_queryset(self):
        es_response = self.get_es_response()
        return es_response._search.to_queryset()


class CatalogueView(BaseCatalogueView):
    template_name = "django_oscar_es/browse.html"


class ProductCategoryView(BaseCatalogueView):
    template_name = "django_oscar_es/category.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = None

    def get_faceted_search(self):
        faceted_search = super().get_faceted_search()
        faceted_search.add_filter_query(
            Q(
                "nested",
                path="categories",
                query=Q("term", **{"categories.id": self.get_category().pk}),
            )
        )
        return faceted_search

    def get_category(self):
        if not self.category:
            self.category = get_object_or_404(Category, pk=self.kwargs["pk"])
        return self.category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.get_category()
        return context
