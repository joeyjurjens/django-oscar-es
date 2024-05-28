import logging

from django.shortcuts import render

from django_es_facets.views import ESFacetedSearchView

from .faceted_search import CatalogueRootFacetedSearch
from .forms import ProductFacetForm

logger = logging.getLogger(__name__)


class CatalogueRootView(ESFacetedSearchView):
    form_class = ProductFacetForm
    faceted_search_class = CatalogueRootFacetedSearch
    template_name = "django_oscar_es/products.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())
