"""
This example demonstrates how to use the tuning subsystem.

We create a function 'get_height' that computes the height of the
surface of a paraboloid centered at a pair of given (x',y') coordinates.
Then, we make successive calls to get_height() where each
computes the height at a location (x,y) prescribed by the autotuner.
It returns the height of the surface at that location, and we attempt
to minimize it by reporting it as 'time'.
"""

import logging

logging.basicConfig(level=50)

import numpy as np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.types import get_ctree_type
from ctree.jit import LazySpecializedFunction
from ctree.templates.nodes import StringTemplate

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
        from ctree.opentuner.driver import OpenTunerDriver
        from opentuner.search.manipulator import ConfigurationManipulator
        from opentuner.search.manipulator import FloatParameter
        from opentuner.search.objective import MinimizeTime

        manip = ConfigurationManipulator()
        manip.add_parameter(FloatParameter("x", -100.0, 100.0))
        manip.add_parameter(FloatParameter("y", -100.0, 100.0))

        return OpenTunerDriver(manipulator=manip, objective=MinimizeTime())

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
                float get_height() {
                    return ($x-$min_x)*($x-$min_x) +
                           ($y-$min_y)*($y-$min_y) + 1.0;
                }""",
                template_args)
        ])

        entry_typesig = FuncType(Float(), [])
        return Project([cfile]), entry_typesig.as_ctype()


class ParaboloidHeight(object):
    def __init__(self, min_x, min_y):
        self.c_func = GetHeight(min_x, min_y)

    def __call__(self):
        retval = self.c_func()
        self.c_func.report(time=retval)
        return retval


# ---------------------------------------------------------------------------
# User code

def main():
    # create paraboloid with global min of 1 at (3, 4)
    get_min_height = ParaboloidHeight(3, 4)

    i = 0
    best_z = float('inf')
    while True:
        z = get_min_height()
        if z < best_z:
            print("New best on call #%3d: get_height() -> %e" % (i, z))
            best_z = z
        if abs(z - 1.0) < 1e-6:
            print("Found global minimum in %d calls." % i)
            break
        i += 1
    print("Success.")

if __name__ == '__main__':
    main()
