from typing import Any, Callable, List, Optional, Union
from illuminate_core.container.types import Abstract, ClassAnnotation, Concrete, Parameters


class ContextualBindingBuilder:
    def needs(self, abstract: str):
        raise NotImplementedError("Should have implemented this")

    def give(self, implementation):
        raise NotImplementedError("Should have implemented this")


class Container:
    def add_contextual_binding(self, concrete: Concrete, abstract: ClassAnnotation, implementation: Union[ClassAnnotation, Callable]) -> None:
        raise NotImplementedError("Should have implemented this")

    def bound(self, abstract: str) -> bool:
        raise NotImplementedError("Should have implemented this")

    def alias(self, abstract: ClassAnnotation, alias: ClassAnnotation) -> None:
        raise NotImplementedError("Should have implemented this")

    def tag(self, abstract: Abstract, *tags) -> None:
        raise NotImplementedError("Should have implemented this")

    def tagged(self, tag: str) -> List:
        raise NotImplementedError("Should have implemented this")

    def bind(self, abstract: Abstract, concrete: Optional[Concrete] = None, shared: bool = False) -> None:
        raise NotImplementedError("Should have implemented this")

    def bind_if(self, abstract: Abstract, concrete: Optional[Concrete] = None, shared: bool = False) -> None:
        raise NotImplementedError("Should have implemented this")

    def singleton(self, abstract: Abstract, concrete: Optional[Concrete] = None) -> None:
        raise NotImplementedError("Should have implemented this")

    def extend(self, abstract: Abstract, closure: Callable) -> None:
        raise NotImplementedError("Should have implemented this")

    def instance(self, abstract: ClassAnnotation, instance: Any) -> Any:
        raise NotImplementedError("Should have implemented this")

    def when(self, concrete: ClassAnnotation) -> ContextualBindingBuilder:
        raise NotImplementedError("Should have implemented this")

    def factory(self, abstract: ClassAnnotation) -> Callable:
        raise NotImplementedError("Should have implemented this")

    def make(self, abstract: ClassAnnotation, parameters: Parameters = None) -> Any:
        raise NotImplementedError("Should have implemented this")

    def call(self, callback: Callable, parameters: Parameters = None, default_method: Callable = None):
        raise NotImplementedError("Should have implemented this")

    def resolved(self, abstract: ClassAnnotation) -> bool:
        raise NotImplementedError("Should have implemented this")

    def resolving(self, *, abstract: ClassAnnotation, callback: Callable = None) -> None:
        raise NotImplementedError("Should have implemented this")

    def afterResolving(self, abstract: ClassAnnotation, callback: Callable = None) -> None:
        raise NotImplementedError("Should have implemented this")
