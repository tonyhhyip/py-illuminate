from .kernel import Kernel


def test_construct():
    kernel = Kernel()
    assert isinstance(kernel, Kernel)
