from __future__ import annotations

import os
import sys
import warnings

import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QLineEdit, QSpinBox, QHBoxLayout, QVBoxLayout,
                             QLabel, QGroupBox, QPushButton, QListWidget, QSizePolicy, QAction, QFileDialog)
from PyQt5.QtWinExtras import QWinTaskbarButton

warnings.filterwarnings("ignore", category=DeprecationWarning)

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
            raise FileNotFoundError("File not found or not specified")

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
            raise ValueError(f"All rows must be the same length: {row_length}")

        self._map = np.array(grid, dtype=str)
        if self._map.size == 0:
            raise ValueError("Map is can't be empty")

    def get_map(self):
        return self._map.copy()

    def get_item(self, x: int, y: int) -> str:
        if x < 0 or y < 0 or x >= self._map.shape[1] or y >= self._map.shape[0]:
            raise IndexError(f"index out of range: ({x}, {y})")
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
        raise NotImplementedError("Method not implemented")

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
        elif char == "" or char is None:
            return False
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
            raise NotImplementedError(f"Instruction not implemented: {char}")
        elif char == "/":
            val = self.stack.pop()
            self.direction = TURN_LEFT[self.direction] if val == 0 else TURN_RIGHT[self.direction]
        elif char == "\\":
            val = self.stack.pop()
            self.direction = TURN_RIGHT[self.direction] if val == 0 else TURN_LEFT[self.direction]

        self.x += self.direction[0]
        self.y += self.direction[1]

        return self.get_information()


class CellGrid(QWidget):
    def __init__(self, rows, cols):
        super().__init__()
        self.cells = []
        self.cols = cols
        self.current_col = 0
        self.current_row = 0
        self.highlight_col = 0
        self.highlight_row = 0
        self.rows = rows
        self.init_ui()

    def init_ui(self):
        grid_layout = QGridLayout()
        grid_layout.setSpacing(1)

        self.cells = []
        for row in range(self.rows):
            row_cells = []
            for col in range(self.cols):
                cell = QLineEdit()
                cell.setMaxLength(1)
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedSize(20, 20)
                grid_layout.addWidget(cell, row, col)
                row_cells.append(cell)
                cell.keyPressEvent = lambda event, r=row, c=col: self.cell_key_press_event(event, r, c)
                cell.mousePressEvent = lambda event, r=row, c=col: self.set_current_cell(r, c)
            self.cells.append(row_cells)

        self.setLayout(grid_layout)
        self.update_highlights()

    def set_grid_size(self, rows, cols):
        old_data = []
        for r in range(min(rows, self.rows)):
            row_data = []
            for c in range(min(cols, self.cols)):
                row_data.append(self.cells[r][c].text())
            old_data.append(row_data)

        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].setParent(None)

        self.rows = rows
        self.cols = cols
        self.cells = []

        self.current_row = min(self.current_row, rows - 1)
        self.current_col = min(self.current_col, cols - 1)
        self.highlight_row = min(self.highlight_row, rows - 1)
        self.highlight_col = min(self.highlight_col, cols - 1)

        grid_layout = self.layout()
        for row in range(rows):
            row_cells = []
            for col in range(cols):
                cell = QLineEdit()
                cell.setMaxLength(1)
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedSize(20, 20)
                grid_layout.addWidget(cell, row, col)
                row_cells.append(cell)

                if row < len(old_data) and col < len(old_data[row]):
                    cell.setText(old_data[row][col])

                cell.mousePressEvent = lambda event, r=row, c=col: self.set_current_cell(r, c)

            self.cells.append(row_cells)

        self.update_highlights()

    def update_highlights(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].setStyleSheet("")

        if self.rows > 0 and self.cols > 0:
            self.cells[self.current_row][self.current_col].setStyleSheet(
                "background-color: #90EE90; border: 1px solid #000")
            self.cells[self.current_row][self.current_col].setFocus()

        if (self.rows > 0 and self.cols > 0 and
                (self.highlight_row != self.current_row or self.highlight_col != self.current_col)):
            self.cells[self.highlight_row][self.highlight_col].setStyleSheet(
                "background-color: #ADD8E6; border: 2px solid #0000FF")

    def set_current_cell(self, row, col):
        self.current_row = row
        self.current_col = col
        self.update_highlights()

    def set_highlight_cell(self, row, col):
        self.highlight_row = row
        self.highlight_col = col
        self.update_highlights()

    def get_cell_data(self):
        return self.cells[self.highlight_row][self.highlight_col].text()

    def cell_key_press_event(self, event, row, col):
        if event.key() == Qt.Key_Up:
            self.current_row = max(0, self.current_row - 1)
            self.update_highlights()
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.current_row = min(self.rows - 1, self.current_row + 1)
            self.update_highlights()
            event.accept()
        elif event.key() == Qt.Key_Left:
            self.current_col = max(0, self.current_col - 1)
            self.update_highlights()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.current_col = min(self.cols - 1, self.current_col + 1)
            self.update_highlights()
            event.accept()
        else:
            QLineEdit.keyPressEvent(self.cells[row][col], event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auto_run = None
        self.col_spin = None
        self.current_step = None
        self.debug_line1 = None
        self.debug_line2 = None
        self.debug_line3 = None
        self.export_action = None
        self.file_menu = None
        self.grid = None
        self.highlight_col = 0
        self.highlight_row = 0
        self.interpreter = Interpreter()
        self.is_running = False
        self.menu_bar = None
        self.open_action = None
        self.reset_button = None
        self.row_spin = None
        self.run_button = None
        self.speed_slider = None
        self.stack1 = None
        self.stack2 = None
        self.step_all_count = None
        self.step_button = None
        self.step_count = None
        self.step_count_total = None
        self.stop_button = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Deolang debbugger')
        self.setWindowIcon(QIcon('images/main_debugger_no_dragon_no_baground.ico'))
        self.setGeometry(100, 100, 669, 560)
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")

        self.open_action = QAction("&Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Open local file")
        self.open_action.triggered.connect(self.on_open)
        self.file_menu.addAction(self.open_action)

        self.export_action = QAction("&Export", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.setStatusTip("Export to file")
        self.export_action.triggered.connect(self.on_export)
        self.file_menu.addAction(self.export_action)

        self.grid = CellGrid(25, 25)
        main_layout.addWidget(self.grid, 3)

        control_panel = QVBoxLayout()

        size_group = QGroupBox("Grid Size")
        size_layout = QVBoxLayout()

        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 100)
        self.row_spin.setValue(25)
        self.row_spin.valueChanged.connect(self.resize_grid)
        size_layout.addWidget(QLabel("Rows:"))
        size_layout.addWidget(self.row_spin)

        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 100)
        self.col_spin.setValue(25)
        self.col_spin.valueChanged.connect(self.resize_grid)
        size_layout.addWidget(QLabel("Columns:"))
        size_layout.addWidget(self.col_spin)

        size_group.setLayout(size_layout)
        control_panel.addWidget(size_group)

        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()

        self.run_button = QPushButton("Run")
        self.step_button = QPushButton("Step")
        self.stop_button = QPushButton("Stop")
        self.reset_button = QPushButton("Reset")

        buttons = [self.run_button, self.step_button, self.stop_button, self.reset_button]
        min_width = min(btn.sizeHint().width() for btn in buttons)

        for btn in buttons:
            btn.setFixedWidth(min_width)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        self.run_button.clicked.connect(self.run)
        self.step_button.clicked.connect(self.step)
        self.stop_button.clicked.connect(self.stop)
        self.reset_button.clicked.connect(self.reset)

        self.step_all_count = QLabel("      ")
        self.step_count = QSpinBox()
        self.step_count.setRange(1, 1000)
        self.speed_slider = QSpinBox()
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setFixedWidth(self.step_count.sizeHint().width())
        self.debug_line1 = QLabel("Output: ")
        self.debug_line2 = QLabel("Cords: ")
        self.debug_line3 = QLabel("Direction: ")

        first_row = QHBoxLayout()
        first_row.addWidget(self.run_button)
        first_row.addSpacing(10)
        first_row.addWidget(QLabel("Steps: "))
        first_row.addWidget(self.step_count)

        second_row = QHBoxLayout()
        second_row.addWidget(self.step_button)
        second_row.addSpacing(10)
        second_row.addWidget(QLabel("Speed:"))
        second_row.addWidget(self.speed_slider)

        third_row = QHBoxLayout()
        third_row.addWidget(self.stop_button)
        third_row.addSpacing(10)
        third_row.addWidget(self.step_all_count)

        fourth_row = QHBoxLayout()
        fourth_row.addWidget(self.reset_button)
        fourth_row.setAlignment(Qt.AlignLeft)

        control_layout.addLayout(first_row)
        control_layout.addLayout(second_row)
        control_layout.addLayout(third_row)
        control_layout.addLayout(fourth_row)

        control_group.setLayout(control_layout)
        control_panel.addWidget(control_group)

        self.stack1 = QListWidget()
        self.stack1.setFixedWidth(80)
        self.stack1.setAlternatingRowColors(True)
        self.stack2 = QListWidget()
        self.stack2.setFixedWidth(80)
        self.stack2.setAlternatingRowColors(True)

        stack1_label = QLabel("Stack")
        stack2_label = QLabel("Additional Stack")

        label_layout = QHBoxLayout()
        label_layout.addWidget(stack1_label)
        label_layout.addWidget(stack2_label)

        stack2_layout = QHBoxLayout()
        stack2_layout.addWidget(self.stack1)
        stack2_layout.addWidget(self.stack2)

        debug_layout = QVBoxLayout()
        debug_layout.addWidget(self.debug_line1)
        debug_layout.addWidget(self.debug_line2)
        debug_layout.addWidget(self.debug_line3)

        stack_layout = QVBoxLayout()
        stack_layout.addLayout(label_layout)
        stack_layout.addLayout(stack2_layout)

        side_panel_a = QGroupBox("Debug:")
        side_panel = QVBoxLayout()
        side_panel.addLayout(stack_layout)
        side_panel.addLayout(debug_layout)
        side_panel_a.setLayout(side_panel)

        control_panel.addLayout(debug_layout)
        control_panel.addWidget(side_panel_a)
        main_layout.addLayout(control_panel, 1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def run(self):
        self.auto_run = True
        self.step_count_total = self.step_count.value()
        self.current_step = 0
        self.is_running = True
        self.timer.start(1000 // self.speed_slider.value())

    def step(self):

        char = self.grid.get_cell_data()

        if not char:
            print("No more steps")
            self.stop()
            return
        temp_data = self.interpreter.process_char(char)
        self.edit_info(
            temp_data["stack"],
            temp_data["addition_stack"],
            temp_data["output"],
            temp_data["position"],
            temp_data["direction"]
        )
        self.grid.set_highlight_cell(temp_data["position"][1], temp_data["position"][0])
        if self.auto_run:
            self.current_step += 1
            if self.current_step >= self.step_count_total:
                self.stop()
            self.step_all_count.setText(f'Steps left: {self.current_step} / {self.step_count_total}')

    def stop(self):
        self.step_all_count.setText("Done!")
        self.timer.stop()
        self.auto_run = False

    def reset(self):
        self.interpreter.reset()
        self.grid.set_highlight_cell(0, 0)
        self.edit_info([], [], "", (0, 0), "")

    def edit_info(self, stack1_data, stack2_data, output, cords, direction):
        if stack1_data:
            self.stack1.clear()
            for item in reversed(stack1_data):
                self.stack1.addItem(str(item))
        if stack2_data:
            self.stack2.clear()
            for item in reversed(stack2_data):
                self.stack2.addItem(str(item))

        if output:
            self.debug_line1.setText(f"Output: {output}")
        if cords:
            self.debug_line2.setText(f"Cords: {cords}")
        if direction:
            self.debug_line3.setText(f"Direction: {direction}")

    def on_open(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_name:
            try:
                grid_map = GridMap(file_name)
                grid_data = grid_map.get_map()

                self.grid.set_grid_size(self.row_spin.value(), self.col_spin.value())

                for row in range(grid_data.shape[0]):
                    for col in range(grid_data.shape[1]):
                        self.grid.cells[row][col].setText(grid_data[row][col])
            except Exception as e:
                print(f"Error loading file: {e}")

    def on_export(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_name:
            try:
                rows, cols = self.grid.rows, self.grid.cols
                with open(file_name, 'w') as file:
                    for row in range(rows):
                        line = ''.join([self.grid.cells[row][col].text() or ' ' for col in range(cols)])
                        file.write(line + '\n')
            except Exception as e:
                print(f"Error exporting file: {e}")

    def resize_grid(self):
        rows = self.row_spin.value()
        cols = self.col_spin.value()
        self.grid.set_grid_size(rows, cols)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
