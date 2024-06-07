import inspect


class FormatterRegistry:
    _instance = None
    _registry = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, name, formatter):
        if name in self._registry:
            raise ValueError(
                f"A formatter with the name '{name}' is already registered."
            )
        # Check function signature
        self._validate_formatter_signature(formatter)
        self._registry[name] = formatter

    def _validate_formatter_signature(self, formatter):
        sig = inspect.signature(formatter)
        params = sig.parameters
        if len(params) != 3:
            raise ValueError(
                f"Formatter {formatter.__name__} must have exactly three parameters: request, key, doc_count."
            )

    def get_formatters(self):
        return self._registry.items()

    def get_formatter(self, name):
        return self._registry.get(name)


# Decorator to register a formatter
def register_formatter(name):
    def decorator(func):
        formatter_registry.register(name, func)
        return func

    return decorator


formatter_registry = FormatterRegistry()
