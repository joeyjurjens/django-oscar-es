class FormatterRegistry:
    _instance = None
    _registry = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FormatterRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, name, formatter):
        self._registry[name] = formatter

    def get_registry(self):
        return self._registry


formatter_registry = FormatterRegistry()
