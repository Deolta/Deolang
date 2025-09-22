from __future__ import annotations
import os

import numpy as np

DIRECTIONS = {
    "^": (0, -1),
    ">": (1, 0),
    "<": (-1, 0),
    "V": (0, 1)
}

TURN_RIGHT = {
    (0, -1): (1, 0),
    (1, 0): (0, 1),
    (-1, 0): (0, -1),
    (0, 1): (-1, 0)
}

TURN_LEFT = {
    (0, -1): (-1, 0),
    (1, 0): (0, -1),
    (-1, 0): (0, 1),
    (0, 1): (1, 0)
}


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

    def get_item(self, x: int, y: int) -> str:
        if x < 0 or y < 0 or x >= self._map.shape[1] or y >= self._map.shape[0]:
            raise IndexError(f"Index out of bounds: ({x}, {y})")
        return self._map[y, x]

    def __len__(self):
        return self._map.size


class Interpreter:
    def __init__(self, file: str | None = None, program_input: str | None = None) -> None:
        if file is not None:
            self.program = GridMap(file)
        self.stack, self.addition_stack, self.output = [], [], []
        self.x, self.y = 0, 0
        self.direction = (0, 0)

        if program_input:
            self.built_in_input = False
            self.input = program_input
            self.input_pointer = 0
        else:
            self.built_in_input = True

    def run(self) -> None:
        while True:
            char = self.program.get_item(self.x, self.y)
            try:
                process_result = self.process_char(char)
                if process_result is False:
                    print(self.get_output())
                    print(self.get_stack())
                    return
            except Exception as e:
                print(f"Error: {e}")
                return

    def get_output(self):
        return "".join(self.output)

    def get_stack(self):
        stack_dump = "Stack:\n\n"
        for item in reversed(self.stack):
            stack_dump += f"[{item}]\n"
        return stack_dump

    def get_information(self):
        return {
            "output": self.get_output(),
            "stack": self.stack,
            "addition_stack": self.addition_stack,
            "position": (self.x, self.y),
            "direction": self.direction
        }

    def reset(self):
        self.stack, self.addition_stack, self.output = [], [], []
        self.x, self.y = 0, 0
        self.direction = (0, 0)

    def process_char(self, char: str):
        if char in DIRECTIONS:
            self.direction = DIRECTIONS[char]
        elif char.isdigit():
            self.stack.append(int(char))
        elif char == "" or char is None:
            return False
        elif char == "+":
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a + b)
        elif char == "-":
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a - b)
        elif char == "*":
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a * b)
        elif char == "%":
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a // b)
        elif char == "P":
            self.stack.pop()
        elif char == "N":
            self.output.append(str(self.stack.pop()))
        elif char == "A":
            self.output.append(chr(self.stack.pop()))
        elif char == "D":
            self.addition_stack.append(self.stack.pop())
        elif char == "U":
            self.stack.append(self.addition_stack.pop())
        elif char == "C":
            self.stack.append(self.stack[-1])
        elif char == "I":
            if self.built_in_input:
                _input = input("Input: ")
                if not _input:
                    raise ValueError("No input provided")
                for input_char in _input:
                    self.stack.append(ord(input_char))
                self.stack.append(0)
            else:
                self.stack.append(ord(self.input[self.input_pointer]))
                self.input_pointer += 1
        elif char in "|_":
            raise NotImplementedError(f"Instruction {char} not implemented")
        elif char == "/":
            val = self.stack.pop()
            self.direction = TURN_LEFT[self.direction] if val == 0 else TURN_RIGHT[self.direction]
        elif char == "\\":
            val = self.stack.pop()
            self.direction = TURN_RIGHT[self.direction] if val == 0 else TURN_LEFT[self.direction]

        self.x += self.direction[0]
        self.y += self.direction[1]

        return self.get_information()


setup = Interpreter("test.txt")
setup.run()
