import os
from typing import Union, Any

import numpy as np


class GridMap:
    def __init__(self, file=None):
        if not file or not os.path.exists(file):
            raise FileNotFoundError("file not found or not specified")

        grid = []
        temp = []

        with open(file, 'r') as map_file:
            while True:
                char = map_file.read(1)
                if not char:
                    break
                elif char == '\n':
                    grid.append(temp)
                    temp = []
                elif char == ' ':
                    temp.append('')
                else:
                    temp.append(char)

        if temp:
            grid.append(temp)

        row_length = len(grid[0])
        if not all(len(row) == row_length for row in grid):
            raise ValueError(f"All rows must be of the same length{row_length}")

        self._map = np.array(grid, dtype=str)
        if self._map.size == 0:
            raise ValueError("Map is cannot be empty")

    def get_map(self):
        return self._map.copy()

    def get_item(self, x: int, y: int) :
        if x < 0 or y < 0 or x >= self._map.shape[1] or y >= self._map.shape[0]:
            return False
        return self._map[y, x]

    def __len__(self):
        return self._map.size