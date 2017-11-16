import inspect
from inspect import Signature, Parameter
from typing import Dict, List, Callable, Any, Optional, Union

from illuminate_core.support.utils import call_user_func
from illuminate_core.contract.container import Container as ContainerInterface, ContextualBindingBuilder as ContextualBindingBuilderInterface
from illuminate_core.container import bound
from .builder import ContextualBindingBuilder
from .exception import BindingResolutionException, EntryNotFoundException
from .types import ClassAnnotation, Abstract, Concrete, Parameters


class Container(ContainerInterface):
    _resolved: Dict[ClassAnnotation, bool]
    bindings: Dict[ClassAnnotation, Dict[str, Any]]
    methodBindings: Dict[str, Callable]
    instances: Dict[ClassAnnotation, Any]
    aliases: Dict[ClassAnnotation, ClassAnnotation]
    abstractAliases: Dict[ClassAnnotation, List[ClassAnnotation]]
    extenders: Dict[ClassAnnotation, List[Callable[[Any, ContainerInterface], Any]]]
    tags: Dict[Any, List[ClassAnnotation]]
    buildStack: List[str]
    withParameters: List[Parameters]
    reboundCallbacks: Dict[ClassAnnotation, List[Callable[[ContainerInterface, Any], Any]]]
    globalResolvingCallbacks: List[Callable[[Any, ContainerInterface], Any]]
    globalAfterResolvingCallbacks: List[Callable[[Any, ContainerInterface], Any]]
    resolvingCallbacks: Dict[str, List[Callable]]
    afterResolvingCallbacks: Dict[str, List[Callable]]
    contextual: Dict[Concrete, Dict[ClassAnnotation, Union[ClassAnnotation, Callable]]]

    def __init__(self):
        self._resolved: Dict[ClassAnnotation, bool] = {}
        self.bindings: Dict[ClassAnnotation, Dict[str, Any]] = {}
        self.methodBindings = {}
        self.instances: Dict[ClassAnnotation, Any] = {}
        self.aliases: Dict[ClassAnnotation, ClassAnnotation] = {}
        self.abstractAliases: Dict[ClassAnnotation, List[ClassAnnotation]] = {}
        self.extenders: Dict[ClassAnnotation, List[Callable[[Any, ContainerInterface], Any]]] = {}
        self.tags: Dict[Any, List[ClassAnnotation]] = {}
        self.buildStack: List[str] = []
        self.withParameters: List[Parameters] = []
        self.reboundCallbacks: Dict[ClassAnnotation, List[Callable[[ContainerInterface, Any], Any]]] = {}
        self.globalResolvingCallbacks: List[Callable[[Any, ContainerInterface], Any]] = {}
        self.globalAfterResolvingCallbacks: List[Callable[[Any, ContainerInterface], Any]] = {}
        self.resolvingCallbacks: Dict[str, List[Callable]] = {}
        self.afterResolvingCallbacks: Dict[str, List[Callable]] = {}
        self.contextual: Dict[Concrete, Dict[ClassAnnotation, Union[ClassAnnotation, Callable]]] = {}

    def when(self, concrete: ClassAnnotation) -> ContextualBindingBuilderInterface:
        return ContextualBindingBuilder(self, self.get_alias(concrete))

    def bound(self, abstract: ClassAnnotation) -> bool:
        return abstract in self.bindings or abstract in self.instances or self.is_alias(abstract)

    def has(self, name: ClassAnnotation) -> bool:
        return self.bound(name)

    def resolved(self, abstract: ClassAnnotation) -> bool:
        if self.is_alias(abstract):
            abstract = self.get_alias(abstract)

        return abstract in self._resolved or abstract in self.instances

    def is_shared(self, abstract: ClassAnnotation) -> bool:
        return abstract in self.instances or \
               (
                abstract in self.bindings and
                'shared' in self.bindings[abstract] and
                self.bindings[abstract]['shared'] is True
                )

    def is_alias(self, name: ClassAnnotation) -> bool:
        return name in self.aliases

    def bind(self, abstract: ClassAnnotation, concrete: Optional[Union[ClassAnnotation, Callable]] = None, shared: bool = False):
        self.drop_stale_instances(abstract)

        if concrete is None:
            concrete = abstract

        if not callable(concrete):
            concrete = self.get_closure(abstract, concrete)

        self.bindings[abstract] = {
            'concrete': concrete,
            'shared': shared
        }

        if abstract in self._resolved:
            self.rebound(abstract)

    def get_closure(self, abstract: ClassAnnotation, concrete: ClassAnnotation) -> Callable:
        def closure(container: Container, parameters: Parameters = None):
            if parameters is None:
                parameters = []

            if abstract == concrete:
                return container.build(concrete)

            return container.make(concrete, parameters)

        return closure

    def has_method_binding(self, method: str) -> bool:
        return method in self.methodBindings

    def bind_method(self, method: Union[str, List], callback: Callable) -> None:
        self.methodBindings[self.parse_bind_method(method)] = callback

    def parse_bind_method(self, method: Union[str, List]) -> str:
        if isinstance(method, list):
            return '{0}@{1}'.format(*method)

        return method

    def call_method_binding(self, method: str, instance: Any) -> Any:
        return self.methodBindings[method](instance, self)

    def add_contextual_binding(self, concrete: Concrete, abstract: ClassAnnotation, implementation: Union[ClassAnnotation, Callable]) -> None:
        if concrete not in self.contextual:
            self.contextual[concrete] = {}
        self.contextual[concrete][self.get_alias(abstract)] = implementation

    def bind_if(self, abstract: ClassAnnotation, concrete: Optional[Concrete] = None, shared: bool = False) -> None:
        if not self.bound(abstract):
            self.bind(abstract, concrete, shared)

    def singleton(self, abstract: Abstract, concrete: Concrete = None) -> None:
        self.bind(abstract, concrete, True)

    def extend(self, abstract: ClassAnnotation, closure: Callable) -> None:
        abstract = self.get_alias(abstract)

        if abstract in self.instances:
            self.instances[abstract] = closure(self.instances[abstract], self)
            self.rebound(abstract)
        else:
            self.extenders[abstract].append(closure)

            if self.resolved(abstract):
                self.rebound(abstract)

    def instance(self, abstract: ClassAnnotation, instance: Any) -> Any:
        self.remove_abstract_alias(abstract)
        is_bound = self.bound(abstract)

        self.aliases.pop(abstract, None)

        self.instances[abstract] = instance

        if is_bound:
            self.rebound(abstract)

        return instance

    def remove_abstract_alias(self, searched: ClassAnnotation) -> None:
        if searched not in self.aliases:
            return

        for abstract, aliases in self.abstractAliases.items():
            for index, alias in enumerate(aliases):
                if alias == searched:
                    del self.abstractAliases[abstract][index]

    def tag(self, abstracts: Abstract, *tags):
        for tag in tags:
            if tag not in self.tags:
                self.tags[tag] = []

            if not isinstance(abstracts, list):
                abstracts = [abstracts]
            for abstract in abstracts:
                self.tags[tag].append(abstract)

    def tagged(self, tag: str) -> List:
        results = []

        if tag in self.tags:
            for abstract in self.tags[tag]:
                results.append(self.make(abstract))

        return results

    def alias(self, abstract: ClassAnnotation, alias: ClassAnnotation):
        self.aliases[alias] = abstract
        if abstract not in self.abstractAliases:
            self.abstractAliases[abstract] = []
        self.abstractAliases[abstract].append(alias)

    def rebinding(self, abstract: ClassAnnotation, callback: Callable):
        abstract = self.get_alias(abstract)
        self.reboundCallbacks[abstract].append(callback)

        if self.bound(abstract):
            self.make(abstract)

    def refresh(self, abstract: ClassAnnotation, target: Any, method: str) -> Any:
        def closure(app, instance):
            func = getattr(target, method)
            func(instance)

        return self.rebinding(abstract, closure)

    def rebound(self, abstract: ClassAnnotation) -> None:
        instance = self.make(abstract)

        for callback in self.get_rebound_callbacks(abstract):
            callback(self, instance)

    def get_rebound_callbacks(self, abstract: ClassAnnotation) -> List[Callable[[ContainerInterface, Any], Any]]:
        if abstract in self.reboundCallbacks:
            return self.reboundCallbacks[abstract]

        return []

    def wrap(self, callback: Callable, parameters: Parameters) -> Callable:
        def closure():
            self.call(callback, parameters)

        return closure

    def call(self, callback: Callable, parameters: Parameters = None, default_method: Callable = None):
        return bound.call(self, callback, parameters, default_method)

    def factory(self, abstract: ClassAnnotation) -> Callable:
        def closure():
            return self.make(abstract)
        return closure

    def make_with(self, abstract: ClassAnnotation, parameters: Parameters = None) -> Any:
        return self.make(abstract, parameters)

    def make(self, abstract: str, parameters: Parameters = None) -> Any:
        if parameters is None:
            parameters = []
        return self.resolve(abstract, parameters)

    def get(self, name):
        if self.has(name):
            return self.resolve(name)

        raise EntryNotFoundException()

    def resolve(self, abstract: ClassAnnotation, parameters: Parameters = None) -> Any:
        if parameters is None:
            parameters = []

        abstract = self.get_alias(abstract)

        needs_contextual_build = len(parameters) > 0 or self.get_contextual_concrete(abstract) is not None

        if abstract in self.instances and not needs_contextual_build:
            return self.instances[abstract]

        self.withParameters.append(parameters)

        concrete = self.get_concrete(abstract)

        if self.is_buildable(concrete, abstract):
            obj = self.build(concrete)
        else:
            obj = self.make(concrete)

        for extender in self.get_extenders(abstract):
            obj = extender(obj, self)

        if self.is_shared(abstract) and not needs_contextual_build:
            self.instances[abstract] = obj

        self.fire_resolving_callbacks(abstract, obj)
        self._resolved[abstract] = True

        self.withParameters.pop()

        return obj

    def get_concrete(self, abstract: ClassAnnotation) -> Any:
        concrete = self.get_contextual_concrete(abstract)
        if concrete is not None:
            return concrete

        if abstract in self.bindings:
            return self.bindings[abstract]['concrete']

        return abstract

    def get_contextual_concrete(self, abstract: ClassAnnotation) -> Any:
        binding = self.find_in_contextual_bindings(abstract)
        if binding is not None:
            return binding

        if abstract not in self.abstractAliases or len(self.abstractAliases[abstract]) == 0:
            return None

        for alias in self.abstractAliases[abstract]:
            binding = self.find_in_contextual_bindings(alias)
            if binding is not None:
                return binding

        return None

    def find_in_contextual_bindings(self, abstract: str) -> Any:
        if len(self.buildStack) > 0 and abstract in self.contextual[self.buildStack[-1]]:
            return self.contextual[self.buildStack[-1]][abstract]

        return None

    def is_buildable(self, concrete: Any, abstract: ClassAnnotation) -> bool:
        return concrete == abstract or callable(concrete)

    def build(self, concrete: Union[Callable, ClassAnnotation]) -> Any:
        if callable(concrete):
            return call_user_func(concrete, self, *self.get_last_parameter_override())

        self.buildStack.append(concrete)

        constructor = getattr(concrete, '__init__')
        dependencies = inspect.signature(constructor)

        instances = self.resolve_dependencies(dependencies)

        self.buildStack.pop()

        return concrete(*instances)

    def resolve_dependencies(self, dependencies: Signature):
        results = []
        for key, dependency in dependencies.parameters.items():
            if self.has_parameter_override(dependency):
                results.append(self.get_parameter_override(dependency))
                continue

            results.append(self.resolve_primitive(dependency) if dependency.annotation is Signature.empty else self.resolve_class(dependency))

        return results

    def has_parameter_override(self, dependency: Parameter) -> bool:
        return dependency.name in self.get_last_parameter_override()

    def get_parameter_override(self, dependency: inspect.Parameter) -> Any:
        return self.get_last_parameter_override()[dependency.name]

    def add_contextual_binding(self, concrete: str, abstract: str, implementation) -> None:
        if concrete not in self.contextual:
            self.contextual[concrete] = {}
        self.contextual[concrete][self.get_alias(abstract)] = implementation

    def get_last_parameter_override(self) -> Parameters:
        return self.withParameters[-1] if len(self.withParameters) > 0 else []

    def resolve_primitive(self, parameter: Parameter) -> Any:
        concrete = self.get_contextual_concrete(parameter.name)
        if concrete is not None:
            return concrete(self) if callable(concrete) else concrete

        if parameter.default is not Signature.empty:
            return parameter.default

        self.unresolvable_primitive(parameter.name)

    def resolve_class(self, parameter: Parameter) -> Any:
        try:
            return self.make(parameter.annotation)
        except BindingResolutionException as e:
            if parameter.default is not Signature.empty:
                return parameter.default

            raise e

    def unresolvable_primitive(self, name: str):
        message = f"Unresolvable dependency resolve [{name}]"
        raise BindingResolutionException(message)

    def resolving(self, *, abstract: ClassAnnotation = None, callback: Callable):
        if abstract is not None:
            abstract = self.get_alias(abstract)

        if abstract is not None:
            self.globalResolvingCallbacks.append(callback)
        else:
            if abstract not in self.resolvingCallbacks:
                self.resolvingCallbacks[abstract] = []
            self.resolvingCallbacks[abstract].append(callback)

    def after_resolving(self, *, abstract: str = '', callback: Callable):
        if abstract != '':
            abstract = self.get_alias(abstract)

        if abstract == '':
            self.globalAfterResolvingCallbacks.append(callback)
        else:
            if abstract not in self.afterResolvingCallbacks:
                self.afterResolvingCallbacks[abstract] = []
            self.afterResolvingCallbacks[abstract].append(callback)

    def fire_resolving_callbacks(self, abstract: str, obj: Any) -> None:
        self.fire_callback_array(obj, self.globalResolvingCallbacks)
        self.fire_callback_array(obj, self.get_callbacks_for_types(abstract, obj, self.resolvingCallbacks))
        self.fire_after_resolving_callbacks(abstract, obj)

    def fire_after_resolving_callbacks(self, abstract: str, obj: Any) -> None:
        self.fire_callback_array(obj, self.globalAfterResolvingCallbacks)
        self.fire_callback_array(obj, self.get_callbacks_for_types(abstract, obj, self.afterResolvingCallbacks))

    def get_callbacks_for_types(self, abstract: str, obj: Any, callbacks_per_type: Dict[Any, List[Callable]]) -> List[Callable]:
        results = []

        for t, callbacks in callbacks_per_type.items():
            if t == abstract or isinstance(obj, t):
                results.extend(callbacks)

        return results

    def fire_callback_array(self, obj: Any, callbacks: List[Callable[[Any, ContainerInterface], Any]]) -> None:
        for callback in callbacks:
            callback(obj, self)

    def get_bindings(self) -> Dict[str, Dict[str, Any]]:
        return self.bindings

    def get_alias(self, abstract: ClassAnnotation) -> ClassAnnotation:
        if abstract not in self.aliases:
            return abstract

        if self.aliases[abstract] == abstract:
            raise RuntimeError("{0} is aliased to itself".format(abstract))

        name = self.aliases[abstract]

        return self.get_alias(name)

    def get_extenders(self, abstract: ClassAnnotation) -> List[Callable[[Any, ContainerInterface], Any]]:
        abstract = self.get_alias(abstract)

        if abstract in self.extenders:
            return self.extenders[abstract]

        return []

    def forget_extenders(self, abstract: ClassAnnotation) -> None:
        self.extenders.pop(abstract, None)

    def drop_stale_instances(self, abstract: ClassAnnotation) -> None:
        self.instances.pop(abstract, None)
        self.aliases.pop(abstract, None)

    def forget_instance(self, abstract: ClassAnnotation) -> None:
        self.instances.pop(abstract, None)

    def forget_instances(self) -> None:
        self.instances = {}

    def flush(self) -> None:
        self.aliases = {}
        self._resolved = {}
        self.bindings = {}
        self.instances = {}
        self.abstractAliases = {}

    def __getitem__(self, key):
        return self.make(key)

    def __setitem__(self, key, value):
        def closure():
            return value
        self.bind(key, value if callable(value) else closure)

    def __contains__(self, key):
        return self.bound(key)

    def __delitem__(self, key):
        self.bindings.pop(key, None)
        self.instances.pop(key, None)
        self._resolved.pop(key, None)
