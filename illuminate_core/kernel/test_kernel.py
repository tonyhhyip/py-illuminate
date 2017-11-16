from .kernel import Kernel
from illuminate_core.service import ServiceProvider


def test_construct():
    kernel = Kernel()
    assert isinstance(kernel, Kernel)


def test_name_bind():
    c = Kernel()

    t = [123]

    def closure():
        t[0] += 1
        return t[0]

    c.bind('a', closure)
    assert c.make('a') == 124
    assert c.make('a') == 125


def test_name_singleton():
    c = Kernel()

    n = [123]

    def closure():
        n[0] += 1
        return n[0]

    c.singleton('a', closure)
    assert c.make('a') == 124
    assert c.make('a') == 124


def test_multiple_bind():
    c = Kernel()

    c.instance('a', 123)

    def closure(app: Kernel):
        a = app.make('a')
        return a + 1

    c.bind('b', closure)
    assert c.make('b') == 124


def test_name_alias():
    c = Kernel()

    def closure():
        return 124

    c.bind('a', closure)
    c.alias('a', 'b')
    assert c.make('b') == 124


def test_class_inject():
    c = Kernel()

    class A:
        def __init__(self):
            pass

    class B:
        def __init__(self, a: A):
            pass

    assert isinstance(c.make(B), B)
    assert isinstance(c[B], B)


def test_service_provider():
    c = Kernel()

    class AServiceProvider(ServiceProvider):
        def register(self):
            def closure():
                return 123
            self.app.singleton('a', closure)

    c.register(AServiceProvider)
    assert 123 == c.make('a')
