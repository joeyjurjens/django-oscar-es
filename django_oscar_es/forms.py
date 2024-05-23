from django import forms

from .form_fields import PriceInputField, TermsFacetField


class FacetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_es_facets(self, facets):
        """
        Because available facets are returned from ES. We need to update the available choices
        for our facet fields. That's what this method does, it takes the facets from the ES response
        and updates the choices for the form fields.
        """
        for field_name, field in self.fields.items():
            if isinstance(field, TermsFacetField) and field.es_field in facets:
                self.fields[field_name].choices = [
                    (bucket[0], f"{bucket[0]} ({bucket[1]})")
                    for bucket in facets[field.es_field]
                ]

    def get_es_facets(self):
        """
        This returns all Facet objects from the form fields. Those facets are then passed
        to the FacetedSearch class from within the view.
        """
        form_facets = {}
        for field in self.fields.values():
            if isinstance(field, TermsFacetField):
                form_facets[field.es_field] = field.get_es_facet()
        return form_facets


class CatalogueForm(FacetForm):
    price = PriceInputField(required=False)
    num_stock = TermsFacetField("num_in_stock")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
