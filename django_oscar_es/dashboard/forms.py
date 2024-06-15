from typing import Any
from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet

from oscar.core.loading import get_model

from ..models import (
    ProductElasticsearchSettings,
    ProductSearchField,
    ProductFacet,
    ProductFacetRangeOption,
)

Category = get_model("catalogue", "Category")


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
        is_valid = super().is_valid()

        for form in self.forms:
            if hasattr(form, "nested"):
                is_valid = is_valid and form.nested.is_valid()
        return is_valid

    def save(self, commit=True):
        result = super().save(commit=commit)
        for form in self.forms:
            if hasattr(form, "nested"):
                form.nested.save(commit=commit)
        return result


class ProductFacetedSearchForm(forms.ModelForm):
    class Meta:
        model = ProductFacet
        fields = [
            "field",
            "label",
            "facet_type",
            "size",
            "formatter",
            "enabled_categories",
            "disabled_categories",
            "order",
        ]
        widgets = {
            "order": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["field"].choices = [("", "")] + ProductFacet.get_field_choices()
        self.fields["formatter"].choices = ProductFacet.get_formatter_choices()

        # Only root categories are allowed to be chosen, otherwise the queries to get the allowed facets
        # per category would get too complex and expensive. Also, I think having the option to configure facets
        # for subcategories is not necessary.
        root_categories = Category.objects.filter(depth=1)
        self.fields["enabled_categories"].queryset = root_categories
        self.fields["disabled_categories"].queryset = root_categories

    def has_changed(self):
        # The form is considered unchanged if only the 'order' field has changed and the form has no instance yet.
        if (
            self.instance.pk is None
            and self.empty_permitted
            and self.changed_data == ["order"]
        ):
            return False
        return super().has_changed()


ProductFacetedSearchFormSet = inlineformset_factory(
    ProductElasticsearchSettings,
    ProductFacet,
    formset=ProductFacetInlineFormset,
    form=ProductFacetedSearchForm,
    extra=3,
)


class ProductFacetRangeOptionForm(forms.ModelForm):
    class Meta:
        model = ProductFacetRangeOption
        fields = ["label", "range_type", "from_value", "to_value"]


ProductFacetRangeOptionFormSet = inlineformset_factory(
    ProductFacet, ProductFacetRangeOption, form=ProductFacetRangeOptionForm, extra=3
)
