from elasticsearch_dsl import Q

from django import forms
from django.utils.translation import gettext_lazy as _

from django_es_kit.fields import (
    FilterField,
    TermsFacetField,
    RangeFacetField,
    RangeOption,
)


class DbFacetField(TermsFacetField):
    def __init__(self, es_field, db_facet, **kwargs):
        super().__init__(es_field, **kwargs)
        self.db_facet = db_facet
        self.label = db_facet.label or db_facet.field
        self.size = db_facet.size
        self.formatter = db_facet.get_formatter()


class DbRangeFacetField(RangeFacetField):
    def __init__(self, es_field, db_facet, **kwargs):
        ranges = []
        for db_range in db_facet.range_options.all():
            ranges.append(
                RangeOption(
                    db_range.get_from_value(),
                    db_range.get_to_value(),
                    db_range.label,
                )
            )
        super().__init__(es_field, ranges, **kwargs)

        self.db_facet = db_facet
        self.label = db_facet.label or db_facet.field
        self.size = db_facet.size
        self.formatter = db_facet.get_formatter()


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


class PriceInputField(forms.MultiValueField, FilterField):
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
