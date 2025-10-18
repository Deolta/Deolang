from __future__ import annotations

from typing import Any

from deolang.gridmap import GridMap
from deolang.constants import (TURN_LEFT, TURN_RIGHT, DIRECTIONS)


class Interpreter:
    def __init__(self, program_input: str | None = None) -> None:
        """Initialize interpreter state.

        Args:
            program_input: Optional external input string to use instead of standard input
        """
        self.program = None
        self.stack, self.addition_stack, self.output = [], [], []
        self.x, self.y = 0, 0
        self.direction = (0, 0)
        self.ignore_mode = False

        if program_input:
            self.built_in_input = False
            self.input = program_input
            self.input_pointer = 0
        else:
            self.built_in_input = True

    def load_program(self, file: str) -> None:
        """Load program from file into GridMap.

        Args:
            file: Path to the program file
        """
        self.program = GridMap(file)

    def run(self, steps: int = 0) -> bool:
        """Execute the program for specified steps or until termination.

        Args:
            steps: Number of execution steps to perform.
                   If 0 execute until program terminates.
                   If positive, execute exactly that many steps.
                   If negative, raises ValueError.

        Returns:
            False if program terminates during execution,
            True if all requested steps completed successfully.

        Raises:
            ValueError: If steps argument is negative
        """
        if steps < 0:
            raise ValueError("Program execution steps must be a non-negative integer")

        max_iterations = steps if steps > 0 else float('inf')

        for _ in range(max_iterations):
            char = self.program.get_item(self.x, self.y)
            if not char:
                continue

            result = self.process_char(char)
            if result is False:
                return False

        return 0 < steps


    def get_current_char(self) -> str:
        """Retrieve the current character from the program grid at the interpreter's position.

        Returns:
            str: The character at the current (x, y) coordinates if the program is loaded,
                 otherwise an empty string. Returns an empty string for out-of-bounds positions.
        """
        if self.program:
            return self.program.get_item(self.x, self.y)
        else:
            return ""

    def get_output(self) -> str:
        """Get accumulated output as string.

        Returns:
            Concatenated output string
        """
        return "".join(self.output)

    def get_program(self) -> GridMap | None:
        """Get the program grid map.

        Returns:
            Program grid map if loaded, otherwise None
        """
        if self.program:
            return self.program.get_map()
        else:
            return None

    def get_stack(self) -> str:
        """Format stack contents for display.

        Returns:
            Formatted string showing stack elements in LIFO order
        """
        return "Stack:\n\n" + "\n".join(f"[{item}]" for item in reversed(self.stack))

    def get_addition_stack(self) -> str:
        """Format addition stack contents for display.

        Returns:
            Formatted string showing addition stack elements in LIFO order
        """
        addition_stack_dump = "Addition Stack:\n\n"
        for item in reversed(self.addition_stack):
            addition_stack_dump += f"[{item}]\n"
        return addition_stack_dump

    def get_information(self) -> dict[str, Any]:
        """Get current interpreter state information.

        Returns:
            Dictionary containing output, stacks, position, and direction
        """
        return {
            "output": self.get_output(),
            "stack": self.stack,
            "addition_stack": self.addition_stack,
            "position": (self.x, self.y),
            "direction": self.direction,
            "character": self.get_current_char(),
            "ignore_mode": self.ignore_mode
        }

    def reset(self) -> None:
        """Reset interpreter state to initial values."""
        self.stack, self.addition_stack, self.output = [], [], []
        self.x, self.y = 0, 0
        self.direction = (0, 0)

    def process_char(self, char: str) -> bool | IndexError:
        """Process a single character instruction from the DeoLang program.

        Args:
            char: Instruction character to execute (PNADUCI+-*%/\_|1234567890)

        Returns:
            -
            - True: Execution should continue normally
            - False: Program execution should terminate
            - IndexError: Raised when stack operations encounter insufficient elements



        ^, >, <, V: Change direction

        0-9: Push to stack

        P: Pop from stack

        N: Append top stack element to output as integer

        A: Append top stack element to output as character

        D: Push top stack element to addition stack

        U: Push top addition stack element to stack

        C: Copy top stack element to top of stack

        I: Push input character to stack

        |, _: Do nothing (ignored)

        +, -, *, %: Pop top two stack elements, perform operation bottom over top, push result

        /: Pop top stack element, turn left if 0, right if non-zero

        \: Pop top stack element, turn right if 0, left if non-zero

        Updates interpreter state (position, direction, stacks) accordingly.
        """
        try:
            if char == "" or char is None:
                return False
            if self.ignore_mode:
                if char in "|_":
                    self.ignore_mode = False
                self.x += self.direction[0]
                self.y += self.direction[1]
                return True
            if char in DIRECTIONS:
                self.direction = DIRECTIONS[char]
            elif char.isdigit():
                self.stack.append(int(char))
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
                raise NotImplementedError("Instruction I not tested")
                # if self.built_in_input:
                #     _input = input("Input: ")
                #     if not _input:
                #         raise ValueError("No input provided")
                #     for input_char in _input:
                #         self.stack.append(ord(input_char))
                #     self.stack.append(0)
                # else:
                #     self.stack.append(ord(self.input[self.input_pointer]))
                #     self.input_pointer += 1
            elif char in "|_":
                if char == "|" and self.direction in ((-1, 0), (1, 0)):
                    self.ignore_mode = True
                elif char == "_" and self.direction in ((0, -1), (0, 1)):
                    self.ignore_mode = True
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
