from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet

from ..models import (
    ProductElasticsearchSettings,
    ProductSearchField,
    ProductFacet,
    ProductFacetRangeOption,
)


class ProductSearchFieldForm(forms.ModelForm):
    class Meta:
        model = ProductSearchField
        fields = ["field", "boost", "disabled"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["field"].choices = [
            ("", "")
        ] + ProductSearchField.get_field_choices()


ProductSearchFieldFormSet = inlineformset_factory(
    ProductElasticsearchSettings,
    ProductSearchField,
    form=ProductSearchFieldForm,
    extra=3,
)


class ProductFacetInlineFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)

        form.nested = ProductFacetRangeOptionFormSet(
            instance=form.instance,
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None,
            prefix="range-option-%s-%s"
            % (form.prefix, ProductFacetRangeOptionForm.prefix),
        )

    def is_valid(self):
        result = super().is_valid()
        for form in self.forms:
            if hasattr(form, "nested"):
                result = result and form.nested.is_valid()
        return result

    def save(self, commit=True):
        result = super().save(commit=commit)
        for form in self.forms:
            if hasattr(form, "nested"):
                form.nested.save(commit=commit)
        return result


class ProductFacetForm(forms.ModelForm):
    class Meta:
        model = ProductFacet
        fields = [
            "field",
            "label",
            "facet_type",
            "formatter",
            "enabled_categories",
            "disabled_categories",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["field"].choices = [("", "")] + ProductFacet.get_field_choices()


ProductFacetFormSet = inlineformset_factory(
    ProductElasticsearchSettings,
    ProductFacet,
    formset=ProductFacetInlineFormset,
    form=ProductFacetForm,
    extra=3,
)


class ProductFacetRangeOptionForm(forms.ModelForm):
    class Meta:
        model = ProductFacetRangeOption
        fields = ["label", "range_type", "from_value", "to_value"]


ProductFacetRangeOptionFormSet = inlineformset_factory(
    ProductFacet, ProductFacetRangeOption, form=ProductFacetRangeOptionForm, extra=3
)
