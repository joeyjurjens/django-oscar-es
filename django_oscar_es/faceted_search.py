import logging

from elasticsearch_dsl import FacetedSearch, FacetedResponse, Search

from oscar.core.loading import get_class, get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductDocument = get_class("django_oscar_es.documents", "ProductDocument")

loggger = logging.getLogger(__name__)


class MetadataFacetedResponse(FacetedResponse):
    """
    This class changes the facets property to include the facet object from the database.
    """

    @property
    def facets(self):
        facets = super().facets
        # ToDo: Add extra metadata to the facets, which then in return can be used when rendering
        # the facet form fields in the template.
        return facets


class DynamicFacetedSearch(FacetedSearch):
    """
    This class is a subclass of the FacetedSearch class from elasticsearch_dsl.
    It allows passing a list of facets to the constructor, rather than defining them in the class.
    """

    def __init__(self, facets, query=None, filters={}, sort=()):
        self.facets = facets
        super().__init__(query=query, filters=filters, sort=sort)

    def search(self):
        search = Search(doc_type=self.doc_types, index=self.index, using=self.using)
        return search.response_class(MetadataFacetedResponse)

    def execute(self):
        """
        The original FacetedSearch builds the search object in the __init__ method.
        This is because they assume every filtering decision is made from the __init__ arguments.
        But we allow all sort of dynamic filtering, so we re-build the search object right before executing it.
        Eg in ESFacetedSearchView we call the add_filter method to apply form filters.
        """
        self._s = self.build_search()
        return super().execute()


class CatalogueRootFacetedSearch(DynamicFacetedSearch):
    def query(self, search, query):
        search = super().query(search, query)
        search = search.filter("term", is_public=True)
        return search
