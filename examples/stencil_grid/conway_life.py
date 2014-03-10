"""
use a stencil kernel to compute successive generation of a conway life game
"""

from __future__ import print_function

import numpy as np
import copy
from examples.stencil_grid.stencil_kernel import StencilKernel
from examples.stencil_grid.stencil_grid import StencilGrid


def render(sk, msg="---"):
    """
    Simplistic render of a life board
    """
    print(msg)
    for h in range(sk.shape[0]):
        for w in range(sk.shape[1]):
            if sk[h][w] > 0:
                print('*', end='')
            else:
                print(' ', end='')
        print('')


class ConwayKernel(StencilKernel):
    """
    in_img is the life board at time t
    out_img is the life board at time t+1
    new_state_map defines the output state for a cell
        first 9 indices are for dead cell, next 9 are for live cell
        value at index is the new cell state
    """

    def kernel(self, in_img, new_state_map, out_img):
        for x in out_img.interior_points():
            out_img[x] = in_img[x] * 9
            for y in in_img.neighbors(x, 2):
                out_img[x] += in_img[y]
            out_img[x] = new_state_map[int(out_img[x])]


class IteratedConwayKernel(StencilKernel):
    """
    in_img is the life board at time t
    out_img is the life board at time t+1
    new_state_map defines the output state for a cell
        first 9 indices are for dead cell, next 9 are for live cell
        value at index is the new cell state
    """

    def __init__(self, generations):
        self.generations = generations

    def kernel(self, in_img, new_state_map, out_img):
        for generation in range(self.generations):
            for x in out_img.interior_points():
                out_img[x] = in_img[x] * 9
                for y in in_img.neighbors(x, 2):
                    out_img[x] += in_img[y]
                out_img[x] = new_state_map[int(out_img[x])]


class GameRunner(object):
    def __init__(self, width, height, pure_python=False, should_unroll=False):
        self.width = width
        self.height = height

        self.kernel = ConwayKernel()
        self.kernel.pure_python = pure_python
        self.kernel.should_unroll = should_unroll
        # kernel.pure_python = True

        # create a stencil grid for t+1
        self.current_grid = StencilGrid([height, width])
        all_neighbors = [(x, y) for x in range(-1, 2) for y in range(-1, 2)]
        all_neighbors.remove((0, 0))
        self.current_grid.neighbor_definition.append(all_neighbors)
        self.future_grid = copy.deepcopy(self.current_grid)  # this will be swapped to current after each iteration

        # Randomly initialize a quarter of the cells to 1
        for x in self.current_grid.interior_points():
            if np.random.random() > 0.75:
                self.current_grid[x] = 1

        self.new_state_map = StencilGrid([18])
        for index, new_state in enumerate([0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0]):
            self.new_state_map[index] = new_state

    def set_pure_python(self, new_mode):
        self.kernel.pure_python = new_mode

    def run_game(self, generations=1):
        for generation in range(generations):
            self.kernel.kernel(self.current_grid, self.new_state_map, self.future_grid)
            self.current_grid, self.future_grid = self.future_grid, self.current_grid
            print("gen %s" % generation)

    def __call__(self, *args, **kwargs):
        self.run_game()

    def run(self):
        self.run_game()


if __name__ == '__main__':
    import sys
    import timeit
    parameters = len(sys.argv)

    width = 25 if parameters < 2 else int(sys.argv[1])
    height = 25 if parameters < 3 else int(sys.argv[2])
    generations = 1 if parameters < 4 else int(sys.argv[3])

    game_runner = GameRunner(width, height)

    #game_runner()
    game_runner.set_pure_python(True)
    print("average time for specialized %s" % timeit.timeit(stmt=game_runner, number=10))
    game_runner.set_pure_python(False)
    print("average time for specialized %s" % timeit.timeit(stmt=game_runner, number=10))

