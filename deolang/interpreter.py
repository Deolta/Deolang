from __future__ import annotations

from typing import Any

from deolang.gridmap import GridMap
from deolang.constants import (TURN_LEFT, TURN_RIGHT, DIRECTIONS)

class Interpreter:
    def __init__(self, program_input: str | None = None) -> None:
        self.program = None
        self.stack, self.addition_stack, self.output = [], [], []
        self.x, self.y = 0, 0
        self.direction = (0, 0)

        if program_input:
            self.built_in_input = False
            self.input = program_input
            self.input_pointer = 0
        else:
            self.built_in_input = True

    def load_program(self, file: str) -> None:
        self.program = GridMap(file)

    def run(self) -> bool:
        process_result = None
        while True:
            char = self.program.get_item(self.x, self.y)
            if char:
                process_result = self.process_char(char)
            if process_result is False:
                return True


    def get_output(self) -> str:
        return "".join(self.output)

    def get_program(self) -> GridMap| None:
        if self.program:
            return self.program.get_map()
        else:
            return None

    def get_stack(self) -> str:
        stack_dump = "Stack:\n\n"
        for item in reversed(self.stack):
            stack_dump += f"[{item}]\n"
        return stack_dump

    def get_addition_stack(self) -> str:
        addition_stack_dump = "Addition Stack:\n\n"
        for item in reversed(self.addition_stack):
            addition_stack_dump += f"[{item}]\n"
        return addition_stack_dump

    def get_information(self) -> dict[str, Any]:
        return {
            "output": self.get_output(),
            "stack": self.stack,
            "addition_stack": self.addition_stack,
            "position": (self.x, self.y),
            "direction": self.direction
        }

    def reset(self) -> None:
        self.stack, self.addition_stack, self.output = [], [], []
        self.x, self.y = 0, 0
        self.direction = (0, 0)

    def process_char(self, char: str) -> bool | IndexError:
        try:
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
        except IndexError as index_error:
            return index_error

        self.x += self.direction[0]
        self.y += self.direction[1]

        return True