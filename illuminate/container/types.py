from typing import List, Callable, Any, Union

classClass = type(type(1))
Callback = Union[str, Callable, List[str]]
ClassAnnotation = Union[classClass, str]
Abstract = Union[List[ClassAnnotation], ClassAnnotation]
Concrete = Union[Callable, str]
Parameters = Union[List[Any]]