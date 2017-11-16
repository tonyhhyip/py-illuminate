from typing import Any, Callable, Dict, List, Union, Optional
from illuminate_core.container import Container
from illuminate_core.service import ServiceProvider
from illuminate_core.container.types import ClassAnnotation, Parameters
from illuminate_core.support.utils import call_user_func
from illuminate_core.events import EventServiceProvider

Provider = Union[ServiceProvider, ClassAnnotation]
DeferredServices = Dict[ClassAnnotation, Union[ServiceProvider, ClassAnnotation]]


class Kernel(Container):
    booted: bool = False
    serviceProviders: List[ServiceProvider]
    loadedProviders: Dict[str, bool]
    deferredServices: DeferredServices
    bootingCallbacks: List[Callable]
    bootedCallbacks: List[Callable]
    hasBeenBootstrapped: bool = False

    def __init__(self):
        super().__init__()

        self.serviceProviders: List[ServiceProvider] = []
        self.loadedProviders: Dict[str, bool] = {}
        self.deferredServices: DeferredServices = {}
        self.bootingCallbacks: List[Callable] = []
        self.bootedCallbacks: List[Callable] = []

        self.register_base_bindings()
        self.register_base_service_providers()

    def register_base_bindings(self):
        self.instance('app', self)
        self.instance(Container, self)

    def register_base_service_providers(self) -> None:
        self.register(EventServiceProvider(self))

    def bootstrap_with(self, bootstrappers: List) -> None:
        self.hasBeenBootstrapped = True

        events = self.make('events')

        for bootstrapper in bootstrappers:
            events.fire('bootstrapping: {0}'.format(bootstrapper), self)
            self.make(bootstrapper).bootstrap(self)
            events.fire('bootstrapped: {0}'.format(bootstrapper), self)

    def before_bootstrapping(self, bootstrapper: str, callback: Callable) -> None:
        self['events'].listen('bootstrapping: {0}'.format(bootstrapper), callback)

    def after_bootstrapping(self, bootstrapper: str, callback: Callable) -> None:
        self['events'].listen('bootstrapped: {0}'.format(bootstrapper), callback)

    def has_been_bootstrapped(self) -> bool:
        return self.hasBeenBootstrapped

    def register(self, provider: ServiceProvider, options: Dict = None, force: bool = False) -> ServiceProvider:
        if options is None:
            options = {}

        registered = self.get_provider(provider)
        if registered and not force:
            return registered

        if not isinstance(provider, ServiceProvider):
            provider = self.resolve_provider(provider)

        if hasattr(provider, 'register'):
            method = getattr(provider, 'register')
            call_user_func(method)

        self.mark_as_registered(provider)

        if self.booted:
            self.boot_provider(provider)

        return provider

    def get_provider(self, provider: ClassAnnotation) -> Optional[ServiceProvider]:
        values = self.get_providers(provider)
        return values[0] if len(values) > 0 else None

    def get_providers(self, provider: ClassAnnotation) -> List:
        name = provider if isinstance(provider, str) else provider

        return [provider for provider in self.serviceProviders if isinstance(provider, name)]

    def resolve_provider(self, provider):
        return call_user_func(provider, self)

    def mark_as_registered(self, provider: ServiceProvider):
        self.serviceProviders.append(provider)
        self.loadedProviders[provider.__class__.__qualname__] = True

    def load_deferred_providers(self):
        for service in self.deferredServices.keys():
            self.load_deferred_provider(service)

        self.deferredServices = {}

    def load_deferred_provider(self, service: str) -> None:
        if service not in self.deferredServices:
            return

        provider = self.deferredServices[service]

        if provider not in self.loadedProviders:
            self.register_deferred_provider(provider, service)

    def register_deferred_provider(self, provider: ClassAnnotation, service: Optional[ClassAnnotation] = None):
        if service:
            self.deferredServices.pop(service, None)

        instance = provider(self)
        self.register(instance)

        if not self.booted:
            def closure():
                self.boot_provider(instance)
            self.booting(closure)

    def make(self, abstract: str, parameters: Parameters = None) -> Any:
        abstract = self.get_alias(abstract)

        if abstract in self.deferredServices and abstract not in self.instances:
            self.load_deferred_provider(abstract)

        return super().make(abstract, parameters)

    def bound(self, abstract: ClassAnnotation) -> bool:
        return abstract in self.deferredServices or super().bound(abstract)

    def is_booted(self) -> bool:
        return self.booted

    def boot(self) -> None:
        if self.booted:
            return

        self.fire_app_callbacks(self.bootingCallbacks)

        for provider in self.serviceProviders:
            self.boot_provider(provider)

        self.booted = True
        self.fire_app_callbacks(self.bootedCallbacks)

    def boot_provider(self, provider: ServiceProvider) -> Any:
        if hasattr(provider, 'boot'):
            return self.call(getattr(provider, 'boot'))

    def booting(self, callback: Callable):
        self.bootingCallbacks.append(callback)

    def booted(self, callback: Callable):
        self.bootedCallbacks.append(callback)

        if self.is_booted():
            self.fire_app_callbacks([callback])

    def fire_app_callbacks(self, callbacks: List[Callable]):
        for callback in callbacks:
            call_user_func(callback, self)

    def get_loaded_providers(self) -> Dict[str, bool]:
        return self.loadedProviders

    def get_deferred_services(self) -> DeferredServices:
        return self.deferredServices

    def set_deferred_services(self, services: DeferredServices):
        self.deferredServices = services

    def add_deferred_services(self, services: DeferredServices):
        self.deferredServices = self.deferredServices + services

    def is_deferred_service(self, service: ClassAnnotation):
        return service in self.deferredServices

    def flush(self):
        super().flush()

        self.buildStack = []
        self.loadedProviders = {}
        self.bootedCallbacks = []
        self.bootingCallbacks = []
        self.deferredServices = {}
        self.reboundCallbacks = {}
        self.serviceProviders = []
        self.resolvingCallbacks = {}
        self.afterResolvingCallbacks = {}
        self.globalResolvingCallbacks = {}
