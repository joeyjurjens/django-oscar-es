# django-oscar-es

**django-oscar-es** provides an integration between **Django-Oscar** and **Elasticsearch**. It's built on top of [django-es-kit](https://github.com/joeyjurjens/django-es-kit), [python-elasticsearch-dsl](https://github.com/elastic/elasticsearch-dsl-py) and [django-elasticsearch-dsl](https://github.com/django-es/django-elasticsearch-dsl).

### Installation:

```bash
pip install django-oscar-es
```

Add `"django_oscar_es.apps.DjangoOscarEsConfig"` to your `INSTALLED_APPS`.

As it leverages `django-elasticsearch-dsl` under the hood, you must also [configure this](https://django-elasticsearch-dsl.readthedocs.io/en/latest/quickstart.html#install-and-configure) for it to be able to connect to your elasticsearch instance. As of writing this, that means adding the `ELASTICSEARCH_DSL` setting, eg:
```python
ELASTICSEARCH_DSL = {
    "default": {
        "hosts": "http://localhost:9200",
    }
}
```
