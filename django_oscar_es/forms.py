from django_es_kit.forms import FacetForm

from .form_fields import (
    PriceInputField,
    DbFacetField,
    DbRangeFacetField,
)
from .models import ProductFacet


class ProductFacetForm(FacetForm):
    price = PriceInputField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically add facet fields from the database
        for db_facet in ProductFacet.objects.all():
            if db_facet.facet_type == ProductFacet.FACET_TYPE_TERM:
                self.fields[db_facet.field] = DbFacetField(
                    es_field=db_facet.field,
                    db_facet=db_facet,
                )
            elif db_facet.facet_type == ProductFacet.FACET_TYPE_RANGE:
                self.fields[db_facet.field] = DbRangeFacetField(
                    es_field=db_facet.field,
                    db_facet=db_facet,
                )
            else:
                raise ValueError(f"Unknown facet type '{db_facet.facet_type}'")
