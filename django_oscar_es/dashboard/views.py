from django.db import transaction
from django.contrib import messages
from django.views.generic import TemplateView
from django.shortcuts import redirect

from ..models import ProductElasticsearchSettings

from .forms import (
    ProductSearchFieldFormSet,
    ProductFacetedSearchFormSet,
    ProductFacetRangeOptionFormSet,
)


class ProductElasticsearchSettingsView(TemplateView):
    template_name = "django_oscar_es/dashboard/product_elasticsearch_settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        settings = ProductElasticsearchSettings.load()

        if "search_fields_formset" not in ctx:
            ctx["search_fields_formset"] = ProductSearchFieldFormSet(instance=settings)

        if "facets_formset" not in ctx:
            ctx["facets_formset"] = ProductFacetedSearchFormSet(instance=settings)

        return ctx

    def post(self, request, *args, **kwargs):
        settings = ProductElasticsearchSettings.load()

        search_fields_formset = ProductSearchFieldFormSet(
            request.POST, instance=settings
        )
        facets_formset = ProductFacetedSearchFormSet(request.POST, instance=settings)
        for form in facets_formset:
            form.range_option_formset = ProductFacetRangeOptionFormSet(
                request.POST, instance=form.instance
            )

        forms_valid = search_fields_formset.is_valid() and facets_formset.is_valid()

        if forms_valid:
            with transaction.atomic():
                search_fields_formset.save()
                facets_formset.save()

                for form in facets_formset:
                    form.nested.save()

            return redirect("dashboard-product-elasticsearch")

        context = self.get_context_data()
        context["search_fields_formset"] = search_fields_formset
        context["facets_formset"] = facets_formset
        messages.error(request, "There were some errors on the form(s).")
        return self.render_to_response(context)
