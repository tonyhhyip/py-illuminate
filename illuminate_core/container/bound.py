import inspect
from inspect import Signature, Parameter
from typing import Any, Callable, Dict, List, Union, Optional
from illuminate_core.contract.container import Container
from .types import Callback, Parameters


def call(
        container: Container,
        callback: Callback,
        parameters: Optional[Parameters] = None,
        default_method: Optional[Callable] = None
) -> Any:
    """
    Call the given Closure / class@method and inject its dependencies.
    """
    if _is_callable_with_at_sign(callback) or default_method:
        return _call_class(container, callback, parameters, default_method)

    def closure():
        return callback(*_get_method_dependencies(container, callback, parameters))

    return _call_bound_method(container, callback, closure)


def _call_class(container: Container, target: str, parameters: Parameters = None, default_method: Optional[Callable] = None) -> Any:
    segments = '@'.split(target)

    method = segments[1] if len(segments) == 2 else default_method

    if method is None:
        raise RuntimeError('Method not provided')

    return call(container, [container.make(segments[0]), method], parameters)


def _call_bound_method(container: Container, callback: Callback, default_value: Union[Callable, Any]) -> Any:
    if not isinstance(callback, list):
        return default_value() if callable(default_value) else default_value

    method = _normalize_method(callback)

    if container.has_method_binding(method):
        return container.call_method_binding(method, callback[0])

    return default_value() if callable(default_value) else default_value


def _normalize_method(callback: Callback) -> str:
    cls = callback[0] if isinstance(callback, str) else callback[0].__qualname__

    return "{0}@{1}".format(cls, callback[1])


def _get_method_dependencies(container: Container, callback: Union[str, Callable], parameters: List[Any] = None):
    dependencies = []
    if parameters is None:
        parameters = []

    for name, parameter in _get_call_reflector(callback).parameters.items():
        parameters, dependencies = _add_dependency_for_call_parameter(container, parameter, parameters, dependencies)

    return dependencies + parameters


def _get_call_reflector(callback: Callable) -> Signature:
    return inspect.signature(callback)


def _add_dependency_for_call_parameter(container: Container, parameter: Parameter, parameters: Dict[str, Parameter] = None, dependencies: List[Any] = None) -> List:
    if parameters is None:
        parameters = {}

    if dependencies is None:
        dependencies = []

    if parameter.name in parameters:
        dependencies.append(parameters[parameter.name])
        del parameters[parameter.name]
    elif parameter.annotation is not Signature.empty:
        dependencies.append(container.make(parameter.annotation.__qualname__))
    else:
        dependencies.append(parameter.default)

    return [parameters, dependencies]


def _is_callable_with_at_sign(callback: Callback) -> bool:
    return isinstance(callback, str) and '@' in callback
