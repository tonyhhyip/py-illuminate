from illuminate_core.contract.container import Container, ContextualBindingBuilder as ContextualBindingBuilderInterface
from .types import Concrete, ClassAnnotation


class ContextualBindingBuilder(ContextualBindingBuilderInterface):
    container: Container
    concrete: Concrete
    _needs: ClassAnnotation

    def __init__(self, container: Container, concrete: Concrete):
        """
        Create a new contextual binding builder.
        """
        self.container = container
        self.concrete = concrete
        self._needs = ''

    def needs(self, abstract: ClassAnnotation) -> ContextualBindingBuilderInterface:
        """
        Define the abstract target that depends on the context.
        """
        self._needs = abstract
        return self

    def give(self, implementation: ClassAnnotation) -> None:
        """
        Define the implementation for the contextual binding.
        """
        self.container.add_contextual_binding(self.concrete, self._needs, implementation)
