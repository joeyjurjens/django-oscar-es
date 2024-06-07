from .formatter_registry import register_formatter


@register_formatter("uppercase_formatter")
def uppercase_formatter(request, key, doc_count):
    try:
        key = key.upper()
    except Exception:
        key = key
    return f"{key.upper()} ({doc_count})"


@register_formatter("lowercase_formatter")
def lowercase_formatter(request, key, doc_count):
    try:
        key = key.lower()
    except Exception:
        key = key
    return f"{key.lower()} ({doc_count})"
