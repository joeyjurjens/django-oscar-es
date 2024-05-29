import logging

from django.shortcuts import render

from django_es_kit.views import ESFacetedSearchView

from oscar.core.loading import get_class

ProductFacetForm = get_class("django_oscar_es.forms", "ProductFacetForm")
CatalogueFacetedSearch = get_class(
    "django_oscar_es.faceted_search", "CatalogueFacetedSearch"
)

logger = logging.getLogger(__name__)


class CatalogueView(ESFacetedSearchView):
    form_class = ProductFacetForm
    faceted_search_class = CatalogueFacetedSearch
    template_name = "django_oscar_es/products.html"

    def get_search_query(self):
        return self.request.GET.get("q", None)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())
