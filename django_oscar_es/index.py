from elasticsearch_dsl import Index, analyzer, tokenizer, token_filter

product_index = Index("products").settings(
    number_of_shards=1,
    max_ngram_diff=15,
    number_of_replicas=0,
    analysis={
        "analyzer": {
            "title_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "asciifolding",
                    "ngram_filter",
                ],
            },
            "description_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "asciifolding",
                ],
            },
        },
        "filter": {
            "ngram_filter": {
                "type": "ngram",
                "min_gram": 3,
                "max_gram": 15,
            }
        },
        "normalizer": {
            "lowercase": {
                "type": "custom",
                "filter": ["lowercase"],
            }
        },
    },
)
