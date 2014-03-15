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

import ctypes
import numpy as np

from ctree.frontend import get_ast
from ctree.nodes import Project
from ctree.c.nodes import CFile
from ctree.c.types import Float, FuncType, Ptr
from ctree.dotgen import to_dot
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

        import ctree.c.nodes as c
        template_args = {
            'min_x': c.Constant(self.min_x),
            'min_y': c.Constant(self.min_y),
            'x': c.Constant(x),
            'y': c.Constant(y),
        }

        cfile = CFile("generated", [
            StringTemplate("""\
                // paraboloid with global min of 1 at ($min_x, $min_y)
                float get_height(float *x, float *y) {
                    *x = $x;
                    *y = $y;
                    return 1.0e-2*($x-$min_x)*($x-$min_x) +
                           1.0e-2*($y-$min_y)*($y-$min_y) + 1.0;
                }""",
                template_args)
        ])

        entry_typesig = FuncType(Float(), [Ptr(Float()), Ptr(Float())])
        return Project([cfile]), entry_typesig.as_ctype()


class ParaboloidHeight(object):
    def __init__(self, min_x, min_y):
        self.c_func = GetHeight(min_x, min_y)

    def __call__(self):
        x, y = ctypes.c_float(0.0), ctypes.c_float(0.0)
        z = self.c_func(ctypes.byref(x), ctypes.byref(y))
        self.c_func.report(time=z)
        return z, x.value, y.value


# ---------------------------------------------------------------------------
# Visualization code

import math

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

pan = [0, 0]
dolly = 2.0
rotate = [0, 0]
center = [0.0, 0.0, 0.0]
mbutton = [0,0,0,0,0,0,0]
prev_x, prev_y = 0, 0
width, height = 1260, 1024

points = [
]

frame = 0
best_z = float('inf')
get_min_height = ParaboloidHeight(3, 4)

def timestep():
    # create paraboloid with global min of 1 at (3, 4)
    global frame, best_z, get_min_height, points
    z, x, y = get_min_height()
    points.append((frame, (x, y, z)))
    if z < best_z:
        print("New best on call #%3d: %f" % (frame, z))
        best_z = z
    frame += 1

def clamp(val, mn, mx):
  return min(max(val, mn), mx)

class xform:
  ''' context manager that handles push and pop during transformations '''
  def __init__(self, translate=(0,0,0), rot=(0,0,0,1), scale=(1,1,1), light=True):
    self.trans = translate
    self.rot = rot
    self.scale = scale
    self.light = light

  def __enter__(self):
    glPushMatrix()
    glTranslate(*self.trans)
    glRotate(*self.rot)
    glScale(*self.scale)
    if self.light:
      glEnable(GL_LIGHTING)
    else:
      glDisable(GL_LIGHTING)

  def __exit__(self, type, value, traceback):
    glPopMatrix()

def reshape(w, h):
  global width, height
  width = w
  heigh = h

def motion(x, y):
  global prev_x, prev_y, mbutton, pan, dolly, rotate, width, height
  if mbutton[0]: # orbit
    rotate[0] += x - prev_x
    rotate[1] += y - prev_y
  elif mbutton[1]: # pan
    pan[0] -= dolly*(x-prev_x)/float(width)
    pan[1] += dolly*(y-prev_y)/float(height)
  elif mbutton[2]: # dolly
    dolly -= dolly*0.01*(x - prev_x)
    if dolly <= 0.01: dolly = 0.01
  prev_x, prev_y = x, y

def keyboard(key, x, y):
    if key == 'q':
      exit()

def mouse(button, state, x, y):
    global prev_x, prev_y, mbutton
    prev_x, prev_y = x, y
    mbutton[button] = not state

def display():

  glClearColor(0.,0.,0.,1.)
  glShadeModel(GL_SMOOTH)
  glEnable(GL_CULL_FACE)
  glEnable(GL_DEPTH_TEST)
  lightZeroPosition = [0.,0.,-100.,1.]
  lightZeroColor = [1.,1.0,1.0,1.0]
  glLightfv(GL_LIGHT0, GL_POSITION, lightZeroPosition)
  glLightfv(GL_LIGHT0, GL_DIFFUSE, lightZeroColor)
  glEnable(GL_LIGHT0)

  lightOnePosition = [0.,0.,100.,1.]
  lightOneColor = [1.,1.0,1.0,1.0]
  glLightfv(GL_LIGHT1, GL_POSITION, lightOnePosition)
  glLightfv(GL_LIGHT1, GL_DIFFUSE, lightOneColor)
  glEnable(GL_LIGHT1)

  glEnable(GL_COLOR_MATERIAL)

  global width, height
  glViewport(0, 0, width, height);
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(45.,float(width)/height,.01,800.)
  glMatrixMode(GL_MODELVIEW)
  glLoadIdentity()
  glTranslatef(-pan[0], -pan[1], -dolly);
  glRotatef(rotate[1], 1, 0, 0);
  glRotatef(rotate[0], 0, 1, 0);
  glTranslatef(-center[0], -center[1], -center[2]);
  glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

  timestep()

  with xform():
    color = [1.0,.05,.2,1.]
    glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,color)
    for frame, p in points:
      with xform(translate=p, light=True):
        green = frame / 500.0
        glColor(1-green,green,0)
        glutSolidSphere(1.5, 10, 10)
  glutSwapBuffers()
  glutPostRedisplay()

def main():
  import sys

  glutInit(sys.argv)
  glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
  glutInitWindowSize(width,height)
  glutCreateWindow("Search path")
  glutDisplayFunc(display)
  glutMotionFunc(motion)
  glutReshapeFunc(reshape)
  glutMouseFunc(mouse)
  glutKeyboardFunc(keyboard)
  glutMainLoop()
  return

if __name__ == '__main__':
    main()
