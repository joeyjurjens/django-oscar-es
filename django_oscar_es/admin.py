from django.contrib import admin

from oscar.core.loading import get_model

from .models import ProductElasicSearchConfiguration, ProductFacet

ProductAttribute = get_model("catalogue", "ProductAttribute")


class ProductFacetInline(admin.TabularInline):
    model = ProductFacet
    fields = [
        "field_name",
        "label",
        "facet_type",
        "ranges",
        "searchable",
        "enabled_categories",
        "disabled_categories",
    ]
    extra = 1

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (
            db_field.name == "enabled_categories"
            or db_field.name == "disabled_categories"
        ):
            kwargs["queryset"] = db_field.related_model.objects.filter(depth=1)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "field_name":
            kwargs["choices"] = ProductFacet.get_field_name_choices()
        return super().formfield_for_choice_field(db_field, request, **kwargs)


class ProductElasicSearchConfigurationAdmin(admin.ModelAdmin):
    inlines = [ProductFacetInline]

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context.update(
            {
                "show_save": True,
                "show_save_and_continue": True,
                "show_save_and_add_another": False,
                "show_delete": False,
            }
        )
        return super().render_change_form(request, context, add, change, form_url, obj)


admin.site.register(
    ProductElasicSearchConfiguration, ProductElasicSearchConfigurationAdmin
)
