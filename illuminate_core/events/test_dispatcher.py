from .dispatcher import Dispatcher


def test_dispatcher_construct():
    dispatcher = Dispatcher()
    assert isinstance(dispatcher, Dispatcher)
    assert hasattr(dispatcher, 'listen')


def test_function_listener():
    a = [1]

    def listener():
        a[0] = 2

    dispatcher = Dispatcher()
    dispatcher.listen('foo', listener)
    dispatcher.dispatch('foo')
    assert a[0] == 2


def test_function_listener_with_payload():
    a = [1]

    def listener(b: int):
        a[0] = a[0] + b

    dispatcher = Dispatcher()
    dispatcher.listen('foo', listener)
    dispatcher.dispatch('foo', 2)
    assert a[0] == 3
