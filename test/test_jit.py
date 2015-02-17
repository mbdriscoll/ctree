import unittest

from ctree.jit import *
from ctree import CONFIG
from fixtures.sample_asts import *
import ctypes
from ctree.transformations import PyBasicConversions

class TestTranslator(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'arg_typesig': tuple(type(get_ctype(a)) for a in args)}

    def transform(self, tree, program_config):
        arg_types = program_config[0]['arg_typesig']
        tree = PyBasicConversions().visit(tree.body[0])
        tree.return_type = arg_types[0]()
        for param, ty in zip(tree.params, arg_types):
            param.type = ty()
        return [CFile(tree.name, [tree])]

    def finalize(self, transform_result, program_config):
        proj = Project(transform_result)
        cfile = transform_result[0]
        arg_types = program_config[0]['arg_typesig']

        func_type = ctypes.CFUNCTYPE(arg_types[0], *arg_types)
        return BasicFunction(cfile.name, proj, func_type)

class BasicFunction(ConcreteSpecializedFunction):
    def __init__(self, entry, tree, typesig):
        self._c_function = self._compile(entry, tree, typesig)

    def __call__(self, *args, **kwargs):
        return self._c_function(*args, **kwargs)


class TestJit(unittest.TestCase):
    def test_identity(self):
        mod = JitModule()
        submod = CFile("test_identity", [identity_ast], path=CONFIG.get('jit','COMPILE_PATH')). \
            _compile(identity_ast.codegen())
        mod._link_in(submod)
        c_identity_fn = mod.get_callable(identity_ast.name,
                                         identity_ast.get_type())
        self.assertEqual(identity(1), c_identity_fn(1))
        self.assertEqual(identity(12), c_identity_fn(12))
        self.assertEqual(identity(123), c_identity_fn(123))

    def test_fib(self):
        mod = JitModule()
        submod = CFile("test_fib", [fib_ast], path=CONFIG.get('jit','COMPILE_PATH'))._compile(fib_ast.codegen())
        mod._link_in(submod)
        c_fib_fn = mod.get_callable(fib_ast.name,
                                    fib_ast.get_type())
        self.assertEqual(fib(1), c_fib_fn(1))
        self.assertEqual(fib(6), c_fib_fn(6))

    def test_gcd(self):
        mod = JitModule()
        submod = CFile("test_gcd", [gcd_ast], path=CONFIG.get('jit','COMPILE_PATH'))._compile(gcd_ast.codegen())
        mod._link_in(submod)
        c_gcd_fn = mod.get_callable(gcd_ast.name,
                                    gcd_ast.get_type())
        self.assertEqual(gcd(44, 122), c_gcd_fn(44, 122))
        self.assertEqual(gcd(27, 39), c_gcd_fn(27, 39))

    def test_choose(self):
        mod = JitModule()
        submod = CFile("test_choose", [choose_ast], path=CONFIG.get('jit','COMPILE_PATH')). \
            _compile(choose_ast.codegen())
        mod._link_in(submod)
        c_choose_fn = mod.get_callable(choose_ast.name,
                                       choose_ast.get_type())
        self.assertEqual(choose(0.2, 44, 122), c_choose_fn(0.2, 44, 122))
        self.assertEqual(choose(0.8, 44, 122), c_choose_fn(0.8, 44, 122))
        self.assertEqual(choose(0.3, 27, 39), c_choose_fn(0.3, 27, 39))
        self.assertEqual(choose(0.7, 27, 39), c_choose_fn(0.7, 27, 39))

    def test_l2norm(self):
        mod = JitModule()
        submod = CFile("test_l2norm",
                       [l2norm_ast], path=CONFIG.get('jit','COMPILE_PATH'))._compile(l2norm_ast.codegen())
        mod._link_in(submod)
        entry = l2norm_ast.find(FunctionDecl, name="l2norm")
        c_l2norm_fn = mod.get_callable(entry.name, entry.get_type())
        self.assertEqual(l2norm(np.ones(12, dtype=np.float64)),
                         c_l2norm_fn(np.ones(12, dtype=np.float64), 12))

    def test_getFile(self):
        getFile(os.path.join(CONFIG.get('jit','COMPILE_PATH'),'test_l2norm.c'))

class TestAuxiliary(unittest.TestCase):
    def test_NameExtractor(self):
        def f(x):
            return x + 3

        py_ast = get_ast(f)
        result = LazySpecializedFunction.NameExtractor().visit(py_ast)
        self.assertEqual(result, 'f')

    def test_from_function(self):
        def f(x):
            return x + 3

        c_f = TestTranslator.from_function(f, 'test_from_function')
        self.assertEqual(c_f(3), 6)
