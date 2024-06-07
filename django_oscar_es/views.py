import logging

from elasticsearch_dsl import Q

from django.conf import settings
from django.shortcuts import get_object_or_404

from django_es_kit.views import ESFacetedSearchListView

from oscar.core.loading import get_class, get_model
from oscar.apps.search.signals import user_search

ProductFacetedSearchForm = get_class(
    "django_oscar_es.forms", "ProductFacetedSearchForm"
)
CatalogueFacetedSearch = get_class(
    "django_oscar_es.faceted_search", "CatalogueFacetedSearch"
)
Category = get_model("catalogue", "Category")

logger = logging.getLogger(__name__)


class BaseCatalogueView(ESFacetedSearchListView):
    form_class = ProductFacetedSearchForm
    faceted_search_class = CatalogueFacetedSearch
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE
    context_object_name = "products"

    def get_search_query(self):
        return self.request.GET.get("q", "")


class CatalogueView(BaseCatalogueView):
    """
    This view is a replacement for the default oscar.apps.search.views.CatalogueView.
    """

    template_name = "django_oscar_es/browse.html"


class ProductCategoryView(BaseCatalogueView):
    """
    This view is a replacement for the default oscar.apps.search.views.ProductCategoryView.
    """

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


class SearchView(BaseCatalogueView):
    """
    This view is a replacement for the default oscar.apps.search.views.FacetedSearchView.
    """

    template_name = "django_oscar_es/results.html"

    def dispatch(self, request, *args, **kwargs):
        user_search.send(
            sender=self,
            session=self.request.session,
            user=self.request.user,
            query=self.get_search_query(),
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # for some reason oscar named the page obj different in the search view lol
        context["page"] = context["page_obj"]
        return context
