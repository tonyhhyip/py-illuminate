from illuminate_core.container import Container


class A:
    def __init__(self):
        pass


class B:
    def __init__(self, a: A):
        self.a = a


class D:
    def __init__(self, a, b):
        self.a = a
        self.b = b


n = [123]


def create_a_val():
    n[0] += 1
    return n[0]


def create_class_d_instance(app):
    a = app.make('a')
    b = app.make(B)
    return D(a, b)


c = Container()

c.singleton('a', create_a_val)
c.bind(D, create_class_d_instance)

b1 = c.make(B)
assert isinstance(b1.a, A)

d1 = c.make(D)
assert isinstance(d1.b, B)

d2 = c.make(D)
assert d1.a == d2.a
