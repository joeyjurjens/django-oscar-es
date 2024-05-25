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

    def process_es_facets(self, facets):
        """
        Because available facets are returned from ES. We need to update the available choices
        for our facet fields. That's what this method does, it takes the facets from the ES response
        and updates the choices for the form fields.
        """
        for field_name, field in self.fields.items():
            if not field.es_field in facets:
                continue

            if isinstance(field, FacetField):
                choices = []
                for bucket in facets[field.es_field]:
                    key, doc_count, _ = bucket
                    # ToDo: Allow label formatters for displayable facet keys
                    label = f"{key} ({doc_count})"
                    choices.append((key, label))

                self.fields[field_name].choices = choices

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
