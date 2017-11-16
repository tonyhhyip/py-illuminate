# Container

Container is the basic element of the packages.

## Import
```python
from illuminate_core.container import Container
```

## Bind With Name Using builder function
```python
def create_a_val():
    return 123

container = Container()    
container.singleton('a', create_a_val)
```

### Build class with auto injection
```python
class A:
    def __init__(self):
        pass


class B:
    def __init__(self, a: A):
        self.a = a
        

container = Container()
b = container.make(B)
assert isinstance(b.a, A)
```

## Build with binding class builder
```python

class B:
    pass
        

class D:
    def __init__(self, a, b):
        self.a = a
        self.b = b
        
def create_class_d_instance(app):
    a = app.make('a')
    b = app.make(B)
    return D(a, b)
        

container = Container()
container.bind(D, create_class_d_instance)
d = container.make(D)
assert isinstance(d.b, B)
```

## Singleton
Container would always return the same instance with singleton

```python
n = [123]


def create_a_val():
    n[0] += 1
    return n[0]
    
container = Container()
container.bind('a', create_a_val)
    
a1 = container.make('a')

a2 = container.make('a')
assert a1 == a2 == n[0] == 124
```
