__author__ = 'Chick Markley'

"""
Example taking from Shoaib Kamil stencil_specializer
"""

import inspect
import ast
from ctree.dotgen import to_dot


def func(x: int, y: int) -> int:
    return x + y


def distance(x: tuple, y: tuple) -> int:
    return abs(x[0]-y[0]) + abs(x[1]-y[1])


def kernel(in_img, filter_d, filter_s, out_img):
        for x in out_img.interior_points():
            for y in in_img.neighbors(x, 1):
                out_img[x] += in_img[y] * filter_d[int(distance(x, y))] * filter_s[abs(int(in_img[x] - in_img[y]))]


if __name__ == '__main__':
    tree = ast.parse(inspect.getsource(kernel))

    with open("graph.dot", 'w') as ofile:
      ofile.write( to_dot(tree) )
