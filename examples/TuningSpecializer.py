import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.templates.nodes import StringTemplate
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import get_ctree_type
from ctree.tune import BruteForceTuningDriver
from ctree.tune import IntegerParameter
from ctree.tune import MinimizeTime

# ---------------------------------------------------------------------------
# Specializer code


class GetHeight(LazySpecializedFunction):
    def __init__(self, min_x, min_y):
        self.min_x = min_x
        self.min_y = min_y
        ast = None
        entry_point = "get_height"
        super(GetHeight, self).__init__(ast, entry_point)

    def get_tuning_driver(self):
        params = [
            IntegerParameter("x", 0, 10),
            IntegerParameter("y", 0, 10),
        ]
        return BruteForceTuningDriver(params, MinimizeTime())

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        tune_cfg = program_config[1]
        x, y = tune_cfg['x'], tune_cfg['y']

        template_args = {
            'min_x': Constant(self.min_x),
            'min_y': Constant(self.min_y),
            'x': Constant(x),
            'y': Constant(y),
        }

        cfile = CFile("generated", [
            StringTemplate("""\
                // paraboloid with global min of 1 at ($min_x, $min_y)
                int get_height() {
                    return ($x-$min_x)*($x-$min_x) +
                           ($y-$min_y)*($y-$min_y) + 1;
                }""",
                template_args)
        ])

        entry_typesig = FuncType(Int(), [])
        return Project([cfile]), entry_typesig.as_ctype()


class ParaboloidHeight(object):
    def __init__(self, min_x, min_y):
        self.c_get_height_func = GetHeight(min_x, min_y)

    def __call__(self):
        retval = self.c_get_height_func()
        # report 'time' back to function
        self.c_get_height_func.report(time=retval)
        return retval


# ---------------------------------------------------------------------------
# User code

def main():
    get_height = ParaboloidHeight(3, 4)

    for i in range(10):
        z = get_height()
        print( "$d-th call: get_height() -> %d" % (i, z))

    print("Success.")


if __name__ == '__main__':
    main()
