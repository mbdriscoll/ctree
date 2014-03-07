"""
use a stencil kernel to compute successive generation of a conway life game
"""

from __future__ import print_function

import numpy as np

np.random.seed(0)

def render(sk,msg="---"):
    """
    Simplistic render of a life board
    """
    print(msg)
    for h in range(height):
        for w in range(width):
            if sk[h][w] > 0:
                print('*',end='')
            else:
                print(' ',end='')
        print('')


class Kernel(StencilKernel):
    """
    in_img is the life board at time t
    out_img is the life board at time t+1
    new_state_map defines the output state for a cell
        first 8 indices are for dead cell, next 8 are for live cell
        value at index is the new cell state
    """

    def kernel(self, in_img,new_state_map,out_img):
        for x in out_img.interior_points():
            out_img[x] = in_img[x] * 8
            for y in in_img.neighbors(x, 2):
                out_img[x] += in_img[y]
            out_img[x] = new_state_map[int(out_img[x])]


def run_game(width=25, height=25, generations=1):
    """play the game on board of specified size"""

    kernel = Kernel()
    kernel.should_unroll = False

    # create a stencil grid for t+1
    current_grid = StencilGrid([height,width])
    all_neighbors = [(x,y) for x in range(-1,2) for y in range(-1,2)]
    all_neighbors.remove( (0,0) )
    current_grid.neighbor_definition.append( all_neighbors )

    # Randomly initialize a quarter of the cells to 1
    for x in current_grid.interior_points():
        if np.random.random() > 0.75:
            current_grid[x] = 1

    # create a stencil grid for t+1
    future_grid = StencilGrid([height,width])

    new_state_map = StencilGrid([16])
    for index, new_state in enumerate([0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]):
        new_state_map[index] = new_state

    render(current_grid,"Original input")

    for generation in xrange(generations):
        kernel.kernel(current_grid,new_state_map,future_grid)
        current_grid, future_grid = future_grid, current_grid


    render(current_grid,"\nStencil version of kernel gives")

if __name__ == '__main__':
    run_game()