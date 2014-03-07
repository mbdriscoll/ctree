import unittest

from ctree.nodes import *
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.jit import LazySpecializedFunction

class TestVerifyParentPointers(unittest.TestCase):
    def test_self_ref(self):
        cfile = CFile("generated", [])
        tree = Project([cfile])
        stmt = Assign(SymbolRef("path", Ptr(Char())), \
                      cfile.get_generated_path_ref())
        cfile.body.append(stmt)

        proj = Project([cfile])
        llvm_module = proj.codegen() # triggers path resolution

        self.assertIsNone( proj.find(GeneratedPathRef) )
        self.assertIsNotNone( proj.find(String) )

    def test_other_ref(self):
        from ctree.ocl.nodes import OclFile
        cfile = CFile("generated", [])
        oclfile = OclFile("kernel", [])
        tree = Project([cfile])
        stmt = Assign(SymbolRef("path", Ptr(Char())), \
                      oclfile.get_generated_path_ref())
        cfile.body.append(stmt)

        proj = Project([cfile])
        llvm_module = proj.codegen() # triggers path resolution

        self.assertIsNone( proj.find(GeneratedPathRef) )
        self.assertIsNotNone( proj.find(String) )
