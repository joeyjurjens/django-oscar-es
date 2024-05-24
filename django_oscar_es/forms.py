from django import forms

from .form_fields import (
    FacetField,
    RangeFacetField,
    TermsFacetField,
    RangeOption,
)


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
    # price = PriceInputField(required=False)
    price = RangeFacetField(
        "price",
        ranges=[
            RangeOption(lower=0, upper=10, label="0 tot 10"),
            RangeOption(lower=10, upper=20, label="10 tot 20"),
            RangeOption(lower=20, upper=30, label="20 tot 30"),
            RangeOption(lower=30, upper=40, label="30 tot 40"),
            RangeOption(lower=40, label="40 of meer"),
        ],
    )
    num_stock = TermsFacetField("num_in_stock")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
