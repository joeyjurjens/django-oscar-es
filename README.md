# django-oscar-es

**django-oscar-es** provides an integration between **Django-Oscar** and **Elasticsearch**. It's built on top of [django-es-kit](https://github.com/joeyjurjens/django-es-kit), [python-elasticsearch-dsl](https://github.com/elastic/elasticsearch-dsl-py) and [django-elasticsearch-dsl](https://github.com/django-es/django-elasticsearch-dsl)

### Features:

- **Enhanced Dashboard Configuration**: A dashboard view where end users can configure search fields, autocomplete options, and facets for the product model.

- **Prebuilt Views**: Views for searching, autocomplete and faceted search which can be used right away by adding them to your urls.

- **Default Document Class**: A default `Document` class which defines the Elasticsearch mapping for the `Product` model. This document class is easily replaceable with a Django setting.

- **Customization Options**: As expected, like django-oscar, this package also allows you customize most of the code if needed.

### Installation:

```bash
pip install django-oscar-es
```

As it leverages django-elasticsearch-dsl under the hood, you must also [configure this](https://django-elasticsearch-dsl.readthedocs.io/en/latest/quickstart.html#install-and-configure) for it to be able to connect to your elasticsearch instance.
