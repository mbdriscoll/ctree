import ast
import inspect

def get_ast(obj):
  """
  Return the Python ast for the given object, which may
  be anything that inspect.getsource accepts (incl.
  a module, class, method, function, traceback, frame,
  or code object).
  """
  program_txt = inspect.getsource(obj)
  return ast.parse(program_txt)
