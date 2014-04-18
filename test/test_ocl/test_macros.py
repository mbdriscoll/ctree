import unittest

from ctree.ocl.macros import *


class TestOclMacros(unittest.TestCase):
    def test_CL_SUCCESS(self):
        tree = CL_SUCCESS()
        self.assertEqual(tree.codegen(), "CL_SUCCESS")

    def test_CL_DEVICE_TYPE_GPU(self):
        tree = CL_DEVICE_TYPE_GPU()
        self.assertEqual(tree.codegen(), "CL_DEVICE_TYPE_GPU")

    def test_CL_DEVICE_TYPE_CPU(self):
        tree = CL_DEVICE_TYPE_CPU()
        self.assertEqual(tree.codegen(), "CL_DEVICE_TYPE_CPU")

    def test_CL_DEVICE_TYPE_ACCELERATOR(self):
        tree = CL_DEVICE_TYPE_ACCELERATOR()
        self.assertEqual(tree.codegen(), "CL_DEVICE_TYPE_ACCELERATOR")

    def test_CL_DEVICE_TYPE_DEFAULT(self):
        tree = CL_DEVICE_TYPE_DEFAULT()
        self.assertEqual(tree.codegen(), "CL_DEVICE_TYPE_DEFAULT")

    def test_CL_DEVICE_TYPE_ALL(self):
        tree = CL_DEVICE_TYPE_ALL()
        self.assertEqual(tree.codegen(), "CL_DEVICE_TYPE_ALL")

    def test_CLK_LOCAL_MEM_FENCE(self):
        tree = CLK_LOCAL_MEM_FENCE()
        self.assertEqual(tree.codegen(), "CLK_LOCAL_MEM_FENCE")

    def test_barrier(self):
        tree = barrier(CLK_LOCAL_MEM_FENCE())
        self.assertEqual(tree.codegen(), "barrier(CLK_LOCAL_MEM_FENCE)")

    def test_get_local_id(self):
        tree = get_local_id(0)
        self.assertEqual(tree.codegen(), "get_local_id(0)")

    def test_get_global_id(self):
        tree = get_global_id(0)
        self.assertEqual(tree.codegen(), "get_global_id(0)")

    def test_get_group_id(self):
        tree = get_group_id(0)
        self.assertEqual(tree.codegen(), "get_group_id(0)")

    def test_get_local_size(self):
        tree = get_local_size(0)
        self.assertEqual(tree.codegen(), "get_local_size(0)")

    def test_get_num_groups(self):
        tree = get_num_groups(0)
        self.assertEqual(tree.codegen(), "get_num_groups(0)")

    def test_clReleaseMemObject(self):
        tree = clReleaseMemObject(SymbolRef('device_object'))
        self.assertEqual(tree.codegen(), "clReleaseMemObject(device_object)")

