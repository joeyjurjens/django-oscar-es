from .formatters.registry import register_formatter


@register_formatter("uppercase_formatter")
def uppercase_formatter(request, key, doc_count):
    return f"{key.upper()} ({doc_count})"


@register_formatter("lowercase_formatter")
def lowercase_formatter(request, key, doc_count):
    return f"{key.lower()} ({doc_count})"
