from illuminate_core.contract.container import Container, ContextualBindingBuilder as ContextualBindingBuilderInterface


class ContextualBindingBuilder(ContextualBindingBuilderInterface):
    def __init__(self, container: Container, concrete: str):
        self.container = container
        self.concrete = concrete
        self._needs = ''

    def needs(self, abstract: str):
        self._needs = abstract
        return self

    def give(self, implementation):
        self.container.add_contextual_binding(self.concrete, self._needs, implementation)
