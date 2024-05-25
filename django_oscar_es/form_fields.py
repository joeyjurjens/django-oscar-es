from elasticsearch_dsl import Q, Facet, TermsFacet, RangeFacet

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class FacetField(forms.MultipleChoiceField):
    def __init__(self, es_field, **kwargs):
        self.es_field = es_field
        if not "required" in kwargs:
            kwargs["required"] = False
        super().__init__(**kwargs)

    def validate(self, value):
        """
        Removed the check for valid choices, as this is too complex for FacetFields.
        Those choices are populated from the ES response and in order to do the ES query,
        we need to access cleaned_data from already potential faceted fields. We can't access
        cleaned_data if the form complains about invalid choices. If we don't remove this
        check, we have to do TWO queries to ES, one to get the available choices and one to
        get the actual results. This is not efficient and it doesn't really matter if there
        are invalid choices anyways.
        """
        if self.required and not value:
            raise ValidationError(self.error_messages["required"], code="required")

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

    def process_facet_buckets(self, buckets):
        """
        This method processes the ES facet bucket from the response and updates the available choices.
        A bucket look likes this: [(0, 11, False), (23, 8, False), (7, 6, False)]
        """
        choices = []
        for bucket in buckets:
            key, doc_count, _ = bucket
            choices.append((key, self.format_choice_label(key, doc_count)))
        self.choices = choices

    def format_choice_label(self, key, doc_count):
        # ToDo: Allow label formatters for displayable facet keys
        return f"{key} ({doc_count})"


class TermsFacetField(FacetField):
    """
    The TermsFacetField is a form field that will render ES terms facets as checkboxes by default.
    """

    widget = forms.CheckboxSelectMultiple

    def get_es_facet(self):
        return TermsFacet(field=self.es_field)


class RangeOption(dict):
    def __init__(self, lower=None, upper=None, label=None):
        if not lower and not upper:
            raise ValueError("Either lower or upper must be provided")

        super().__init__({"from": lower, "to": upper, "label": label})


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

    def process_facet_buckets(self, buckets):
        """
        This method is overriden from the FacetField class to make use of
        the potential RangeOption label. Also if the doc_count is 0,
        we don't want to show the range option.
        """
        choices = []
        for bucket in buckets:
            key, doc_count, _ = bucket
            if doc_count > 0:
                range_option = self.ranges.get(key)
                label = range_option.get("label", key) if range_option else key
                choices.append((key, self.format_choice_label(label, doc_count)))
        self.choices = choices


class FilterFormField:
    def get_es_filter_query(self, cleaned_data) -> Q:
        raise NotImplementedError(
            "You need to implement the method get_es_filter_query in your subclass."
        )


class PriceInputWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [
            forms.NumberInput(attrs={"placeholder": _("Min price")}),
            forms.NumberInput(attrs={"placeholder": _("Max price")}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value[0], value[1]]
        return [None, None]


class PriceInputField(forms.MultiValueField, FilterFormField):
    widget = PriceInputWidget

    def __init__(self, *args, **kwargs):
        fields = [
            forms.DecimalField(required=False),
            forms.DecimalField(required=False),
        ]
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return data_list

    def get_es_filter_query(self, cleaned_data):
        if cleaned_data:
            return Q("range", price={"gte": cleaned_data[0], "lte": cleaned_data[1]})
        return None
