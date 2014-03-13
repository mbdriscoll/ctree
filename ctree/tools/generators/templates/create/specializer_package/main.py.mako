"""
specializer ${specializer_name}
"""

from ctree.jit import LazySpecializedFunction


class ${specializer_name}(LazySpecializedFunction):

    def transform(self):
        pass

if __name__ == '__main__':
    pass
