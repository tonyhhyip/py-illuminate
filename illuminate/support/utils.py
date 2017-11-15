import inspect
from typing import Any, Callable


def call_user_func(func: Callable, *args) -> Any:
    signature = inspect.signature(func)
    args = args[0:len(signature.parameters)]
    return func(*args)