from elasticsearch_dsl import Q, Facet, TermsFacet

from django import forms
from django.utils.translation import gettext_lazy as _

from abc import ABC, abstractmethod


class ESFacetFormField(ABC):
    @abstractmethod
    def get_es_facet(self) -> Facet:
        pass

    @abstractmethod
    def get_es_filter_query(self) -> dict:
        """
        This method should return a dictionary that can be passed to the filters field of the
        FacetedSearch class from elasticsearch_dsl.
        """
        # ToDo: Maybe rename this method, facet filters are not actually ES queries you'd expect because they are passed into the FacetedSearch.
        # This class has a helper method to add filters more easily.
        pass


class ESFilterFormField(ABC):
    @abstractmethod
    def get_es_filter_query(self) -> Q:
        """
        This method should return a Q(uery) object.
        """
        pass


class TermsFacetField(forms.MultipleChoiceField, ESFacetFormField):
    """
    The TermsFacetField is a form field that will render ES terms facets as checkboxes by default.
    """

    widget = forms.CheckboxSelectMultiple

    def __init__(self, es_field, **kwargs):
        # In most cases, it makes no sense to have it required
        if not "required" in kwargs:
            kwargs["required"] = False

        self.es_field = es_field
        super().__init__(choices=[], **kwargs)

    def get_es_facet(self):
        return TermsFacet(field=self.es_field)

    def get_es_filter_query(self, data):
        return data


class RangeFacetField(forms.MultiValueField, ESFacetFormField):
    pass


class PriceInputField(forms.MultiValueField, ESFilterFormField):
    widget = forms.MultiWidget(
        widgets=[
            forms.NumberInput(attrs={"placeholder": _("Min price")}),
            forms.NumberInput(attrs={"placeholder": _("Max price")}),
        ]
    )

    def __init__(self, *args, **kwargs):
        fields = [
            forms.DecimalField(required=False),
            forms.DecimalField(required=False),
        ]
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        range_filter = {}
        if data_list:
            if data_list[0] is not None:
                range_filter["gte"] = data_list[0]
            if data_list[1] is not None:
                range_filter["lte"] = data_list[1]
        return range_filter

    def get_es_filter_query(self):
        data = self.cleaned_data
        if data:
            price_range = self.compress(data)
            if price_range:
                return Q("range", price=price_range)
        return None
