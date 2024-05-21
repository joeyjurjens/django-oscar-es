from django.views.generic import TemplateView

from oscar.core.loading import get_class

ProductFacetedSearch = get_class("django_oscar_es.search", "ProductFacetedSearch")


class ProductsOverview(TemplateView):
    template_name = "django_oscar_es/products.html"

    def get_es_results(self):
        response = ProductFacetedSearch().execute()
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        results = self.get_es_results()
        ctx["results"] = results
        return ctx
