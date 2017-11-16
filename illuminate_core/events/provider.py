from illuminate_core.service import ServiceProvider
from .dispatcher import Dispatcher


class EventServiceProvider(ServiceProvider):
    def register(self):
        def builder(app):
            return Dispatcher(app)

        self.app.singleton('events', builder)