from typing import Any, Callable, Dict, List, Union, Optional

from illuminate_core.contract.container import Container as ContainerContract
from illuminate_core.container import Container
from illuminate_core.container.types import ClassAnnotation
from illuminate_core.support.utils import call_user_func


Events = Union[List[str], str]


class Dispatcher:
    container: ContainerContract
    listeners: Dict[str, List[Any]]
    wildcards: Dict[str, List[Any]]

    def __init__(self, container: ContainerContract = None):
        self.container = container if container is not None else Container()
        self.listeners: Dict[str, List[Any]] = {}
        self.wildcards: Dict[str, List[Any]] = {}

    def listen(self, events: Events, listener: Any) -> None:
        if not isinstance(events, list):
            events = [events]
        for event in events:
            if '*' in event:
                self.setup_wildcard_listener(event, listener)
            else:
                if event not in self.listeners:
                    self.listeners[event] = []
                self.listeners[event].append(self.make_listener(listener))

    def setup_wildcard_listener(self, event, listener):
        self.wildcards[event].append(self.make_listener(listener))

    def has_listeners(self, event: str) -> bool:
        return event in self.listeners or event in self.wildcards

    def push(self, event: str, payload: List[Any] = None) -> None:
        if payload is None:
            payload = []

        def closure():
            self.dispatch(event, payload)
        self.listen(event + '__pushed', closure)

    def flush(self, event: str) -> None:
        self.dispatch(event + '__pushed')

    def subscribe(self, subscriber: Any):
        subscriber = self.resolve_subscriber(subscriber)
        subscriber.subscribe(self)

    def resolve_subscriber(self, subscriber) -> Any:
        if type(subscriber) is type and isinstance(subscriber, str):
            return self.container.make(subscriber)

        return subscriber

    def until(self, event: str, payload: List[Any] = None):
        if payload is None:
            payload = []

        self.dispatch(event, payload, True)

    def fire(self, event: str, payload: List[Any] = None, halt: bool = False):
        if payload is None:
            payload = []

        self.dispatch(event, payload, halt)

    def dispatch(self, event: str, *payload, halt: bool = False) -> Optional[List[Any]]:
        if payload is None:
            payload = []

        event, payload = self.parse_event_and_payload(event, payload)

        responses = []

        for listener in self.get_listeners(event):
            response = call_user_func(listener, event, *payload)

            if halt and response is not None:
                return [response]

            if response is False:
                break

            responses.append(response)

        return None if halt else responses

    def parse_event_and_payload(self, event, payload):
        if hasattr(event, '__class__') and not isinstance(event, str):
            payload, event = [event], event.__class__

        return [event, payload]

    def get_listeners(self, event: ClassAnnotation) -> List:
        listeners = self.listeners[event] if event in self.listeners else []

        listeners = listeners + self.get_wildcard_listeners(event)

        return self.add_interface_listeners(event, listeners) if type(event) is type else listeners

    def get_wildcard_listeners(self, event: ClassAnnotation) -> List:
        wildcards = []

        for key, listeners in self.wildcards:
            if key in event:
                wildcards += listeners

        return wildcards

    def add_interface_listeners(self, event: ClassAnnotation, listeners: List = None) -> List:
        for interface in event.__bases__:
            if interface in self.listeners:
                for names in self.listeners[interface]:
                    listeners = listeners + names

        return listeners

    def make_listener(self, listener: Union[Callable, ClassAnnotation], wildcard: bool = False) -> Callable:
        if not callable(listener) or type(listener) is type:
            return self.create_class_listener(listener, wildcard)

        def closure(event, *payload):
            if payload is None:
                payload = []
            if wildcard:
                return call_user_func(listener, event, payload)
            else:
                return call_user_func(listener, *payload)

        return closure

    def create_class_listener(self, listener: ClassAnnotation, wildcard: bool = False) -> Callable:
        def closure(event, payload):
            if wildcard:
                return call_user_func(self.create_class_callable(listener), event, payload)
            else:
                return call_user_func(self.create_class_callable(listener), *payload)

        return closure

    def create_class_callable(self, listener: ClassAnnotation) -> Callable:
        cls, method = self.parse_class_callable(listener)
        instance = self.container.make(cls)
        return getattr(instance, method)

    def parse_class_callable(self, listener: ClassAnnotation) -> List:
        if isinstance(listener, str):
            return '@'.split(listener, 2)
        else:
            return [listener, 'handle']

    def forget(self, event: ClassAnnotation):
        if '*' in event:
            self.wildcards.pop(event, None)
        else:
            self.listeners.pop(event, None)

    def forget_pushed(self):
        for key in self.listeners.keys():
            if key.endswith('__pushed'):
                self.forget(key)