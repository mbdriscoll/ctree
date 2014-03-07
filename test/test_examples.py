"""
Make sure the examples work.

The 'examples' directory needs to be in PYTHONPATH for these to pass.
"""

import unittest

try:
  import examples.ArrayDoubler
except ImportError:
  CANNOT_IMPORT_EXAMPLES = True
else:
  CANNOT_IMPORT_EXAMPLES = False

class TestVerifyParentPointers(unittest.TestCase):
    @unittest.skipIf(CANNOT_IMPORT_EXAMPLES, "$CTREE/examples not in PYTHONPATH")
    def test_AstToDot(self):
        from examples import AstToDot
        AstToDot.main()

    @unittest.skipIf(CANNOT_IMPORT_EXAMPLES, "$CTREE/examples not in PYTHONPATH")
    def test_Fibonacci(self):
        from examples import Fibonacci
        Fibonacci.main()

    @unittest.skipIf(CANNOT_IMPORT_EXAMPLES, "$CTREE/examples not in PYTHONPATH")
    def test_ArrayDoubler(self):
        from examples import ArrayDoubler
        ArrayDoubler.main()

    @unittest.skipIf(CANNOT_IMPORT_EXAMPLES, "$CTREE/examples not in PYTHONPATH")
    def test_TemplateDoubler(self):
        from examples import TemplateDoubler
        TemplateDoubler.main()

    @unittest.skipIf(CANNOT_IMPORT_EXAMPLES, "$CTREE/examples not in PYTHONPATH")
    def test_SimpleTranslator(self):
        from examples import SimpleTranslator
        SimpleTranslator.main()

    @unittest.skip("under development")
    def test_OclDoubler(self):
        from examples import OclDoubler
        OclDoubler.main()

    @unittest.skip("under development")
    def test_StencilGrid(self):
        from examples import StencilGrid
        StencilGrid.main()
