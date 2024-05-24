from elasticsearch_dsl import Q, Facet, TermsFacet, RangeFacet

from django import forms
from django.utils.translation import gettext_lazy as _

from abc import ABC, abstractmethod


class FacetField(forms.MultipleChoiceField):
    def __init__(self, es_field, **kwargs):
        self.es_field = es_field
        if not "required" in kwargs:
            kwargs["required"] = False
        super().__init__(**kwargs)

    def get_es_filter_value(self, raw_value):
        """
        It's very unlikely that you will need to override this method for other FacetFields.
        As the raw_value is the value we got from ES, so if the user selects this value,
        it just is the value that will be used as the filter value.
        """
        return raw_value

    def get_es_facet(self) -> Facet:
        raise NotImplementedError(
            "You need to implement the method get_es_facet in your subclass."
        )


class TermsFacetField(FacetField):
    """
    The TermsFacetField is a form field that will render ES terms facets as checkboxes by default.
    """

    widget = forms.CheckboxSelectMultiple

    def get_es_facet(self):
        return TermsFacet(field=self.es_field)


class RangeOption(dict):
    def __init__(self, lower=None, upper=None, label=None, formatter=None):
        if not lower and not upper:
            raise ValueError("Either lower or upper must be provided")

        super().__init__(
            {"from": lower, "to": upper, "label": label, "formatter": formatter}
        )


class RangeFacetField(FacetField):
    widget = forms.CheckboxSelectMultiple

    def __init__(self, es_field, ranges, **kwargs):
        self.ranges = self._parse_ranges(ranges)
        super().__init__(es_field, **kwargs)

    def _parse_ranges(self, ranges):
        def to_range_option(range_):
            return range_ if isinstance(range_, RangeOption) else RangeOption(**range_)

        return {
            f"{range_['from']}_{range_['to']}": to_range_option(range_)
            for range_ in ranges
        }

    def get_es_facet(self):
        """
        Converts the range options into the format expected by the Elasticsearch DSL RangeFacet.
        The format should be a list of tuples, each containing a key and a range tuple (lower, upper).
        """
        ranges = [
            (key, (range_.get("from"), range_.get("to")))
            for key, range_ in self.ranges.items()
        ]
        return RangeFacet(field=self.es_field, ranges=ranges)


class ESFilterFormField(ABC):
    @abstractmethod
    def get_es_filter_query(self, data) -> Q:
        """
        This method should return a Q(uery) object based on the passed data.
        """
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
