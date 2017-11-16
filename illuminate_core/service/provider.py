from typing import List
from illuminate_core.contract.container import Container
from illuminate_core.container.types import ClassAnnotation


class ServiceProvider:
    app: Container
    defer: bool = False

    def __init__(self, app: Container):
        self.app = app

    def provides(self) -> List[ClassAnnotation]:
        return []

    def is_defered(self) -> bool:
        return self.defer

    def register(self):
        pass
