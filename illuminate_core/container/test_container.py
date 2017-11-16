from .container import Container


def test_create():
    c = Container()
    assert isinstance(c, Container)


def test_named_instance():
    c = Container()
    c.instance('a', 123)
    a = c.make('a')
    assert a == 123


def test_name_bind_with_setter():
    c = Container()

    n = [123]

    def closure():
        n[0] += 1
        return n[0]

    c['a'] = closure
    assert c.make('a') == 124
    assert n[0] == 124


def test_name_bind():
    c = Container()

    t = [123]

    def closure():
        t[0] += 1
        return t[0]

    c.bind('a', closure)
    assert c.make('a') == 124
    assert c.make('a') == 125


def test_name_singleton():
    c = Container()

    n = [123]

    def closure(container):
        n[0] += 1
        return n[0]

    c.singleton('a', closure)
    assert c.make('a') == 124
    assert c.make('a') == 124


def test_multiple_bind():
    c = Container()

    c.instance('a', 123)

    def closure(app: Container):
        a = app.make('a')
        return a + 1

    c.bind('b', closure)
    assert c.make('b') == 124


def test_name_alias():
    c = Container()

    def closure():
        return 124

    c.bind('a', closure)
    c.alias('a', 'b')
    assert c.make('b') == 124


def test_class_binding():
    c = Container()

    class A:
        def __init__(self):
            pass

    assert isinstance(c.make(A), A)
    assert isinstance(c[A], A)


def test_class_inject():
    c = Container()

    class A:
        def __init__(self):
            pass

    class B:
        def __init__(self, a: A):
            self.a = a

    b = c.make(B)
    assert isinstance(c.make(B), B)
    assert isinstance(c[B], B)
    assert isinstance(c.make(B).a, A)
