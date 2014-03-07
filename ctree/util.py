__author__ = 'Chick Markley'

def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance
