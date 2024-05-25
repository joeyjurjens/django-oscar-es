from django import forms
from django.forms.utils import ErrorDict

from .form_fields import (
    FacetField,
    TermsFacetField,
    PriceInputField,
)


class FacetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always have it accessible, even if it's empty (easier to do stuff with ES).
        self.cleaned_data = {}

    def get_es_facets(self):
        """
        This returns all Facet objects from the form fields. Those facets are then passed
        to the FacetedSearch class from within the view.
        """
        form_facets = {}
        for field in self.fields.values():
            if isinstance(field, FacetField):
                form_facets[field.es_field] = field.get_es_facet()
        return form_facets


class CatalogueForm(FacetForm):
    price = PriceInputField(required=False)
    num_stock = TermsFacetField("num_in_stock")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
