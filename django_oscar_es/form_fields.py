from elasticsearch_dsl import Q

from django import forms
from django.utils.translation import gettext_lazy as _

from django_es_facets.fields import (
    FilterFormField,
    TermsFacetField,
    RangeFacetField,
    RangeOption,
)


class DbFacetField(TermsFacetField):
    def __init__(self, es_field, db_facet, **kwargs):
        self.db_facet = db_facet
        super().__init__(es_field, **kwargs)


class DbRangeFacetField(RangeFacetField):
    def __init__(self, es_field, db_facet, **kwargs):
        self.db_facet = db_facet

        ranges = []
        for db_range in db_facet.range_options.all():
            ranges.append(
                RangeOption(
                    db_range.from_value or None,
                    db_range.to_value or None,
                    db_range.label,
                )
            )

        super().__init__(es_field, ranges, **kwargs)


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
            return Q("range", price={"gt": cleaned_data[0], "lt": cleaned_data[1]})
        return None
