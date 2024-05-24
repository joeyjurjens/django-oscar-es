import logging

from django.views.generic import View
from django.shortcuts import render

from .faceted_search import CatalogueRootFacetedSearch, DynamicFacetedSearch
from .forms import FacetForm, CatalogueForm
from .form_fields import FacetField, ESFilterFormField

logger = logging.getLogger(__name__)


class ESFacetedSearchView(View):
    faceted_search_class = None
    form_class = None

    def __init__(self, *args, **kwargs):
        if not self.get_faceted_search_class():
            raise NotImplementedError("The class must have a faceted_search_class")

        if not issubclass(self.get_faceted_search_class(), DynamicFacetedSearch):
            raise ValueError(
                "The faceted_search_class must be a subclass of DynamicFacetedSearch"
            )

        if not self.get_form_class():
            raise NotImplementedError("The class must have a form_class")

        if not issubclass(self.get_form_class(), FacetForm):
            raise ValueError("The form_class must be a subclass of FacetForm")

        self._faceted_search = None
        self._form = None
        super().__init__(*args, **kwargs)

    def get_faceted_search_class(self):
        return self.faceted_search_class

    def get_faceted_search(self):
        if self._faceted_search:
            return self._faceted_search

        faceted_search_class = self.get_faceted_search_class()
        self._faceted_search = faceted_search_class(
            facets=self.get_form().get_es_facets()
        )
        return self._faceted_search

    def get_form_class(self):
        return self.form_class

    def get_form(self):
        if self._form:
            return self._form

        form_class = self.get_form_class()
        if self.request.GET:
            return form_class(self.request.GET)

        self._form = form_class()
        return self._form

    def clean_form_data(self, form_data):
        """
        This method removes empty values from the raw form data (GET params). It also makes sure
        that the value is retrieved by the request.GET.getlist(key) method. As we have no way of
        getting cleaned_form data without doing two ES queries (which we don't want), this is the way to go.
        """
        cleaned_data = {}
        for key in form_data:
            values = form_data.getlist(key)
            if values:
                cleaned_data[key] = values
        return cleaned_data

    def get_es_response(self, form):
        faceted_search = self.get_faceted_search()
        form = self.get_form()

        # No filters to apply
        if not form.data:
            return faceted_search.execute()

        # Apply filters before executing the search based on the form data
        cleaned_form_data = self.clean_form_data(form.data)
        for key, value in cleaned_form_data.items():
            # Fuck off
            if key not in form.fields:
                continue

            form_field = form.fields[key]
            if isinstance(form_field, FacetField):
                try:
                    faceted_search.add_filter(
                        form_field.es_field, form_field.get_es_filter_value(value)
                    )
                except KeyError:
                    logger.warning(
                        "Could not apply filter for field %s. This is likely because of an invalid query parameter for this facet.",
                        form_field.es_field,
                    )
            elif isinstance(form_field, ESFilterFormField):
                pass

        response = faceted_search.execute()
        return response

    def get_context_data(self, **kwargs):
        form = self.get_form()
        es_reponse = self.get_es_response(form)
        form.process_es_facets(es_reponse.facets)
        return {"es_form": form, "es_response": es_reponse}


class CatalogueRootView(ESFacetedSearchView):
    form_class = CatalogueForm
    faceted_search_class = CatalogueRootFacetedSearch
    template_name = "django_oscar_es/products.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())
