from __future__ import annotations

import sys
import warnings
from typing import Dict, Any

from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QLineEdit, QSpinBox, QHBoxLayout, QVBoxLayout,
                             QLabel, QGroupBox, QPushButton, QListWidget, QSizePolicy, QAction, QFileDialog,
                             QMessageBox, QDialog)

from deolang.gridmap import GridMap
from deolang.interpreter import Interpreter

warnings.filterwarnings("ignore", category=DeprecationWarning)


class ColorDialog(QDialog):
    def __init__(self, parent=None, colors=None):
        super().__init__(parent)
        self.setWindowTitle("Color input")
        self.setModal(True)
        self.resize(200, 200)

        self.layout = QVBoxLayout()

        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()
        layout1.addWidget(QLabel("Pointer outline color:"))
        self.pointer_outline_color_input = QLineEdit()
        self.pointer_outline_color_input.setText(colors[0])
        layout2.addWidget(self.pointer_outline_color_input)

        layout1.addWidget(QLabel("Pointer fill color:"))
        self.pointer_fill_color_input = QLineEdit()
        self.pointer_fill_color_input.setText(colors[1])
        layout2.addWidget(self.pointer_fill_color_input)

        layout1.addWidget(QLabel("Cursor outline color:"))
        self.cursor_outline_color_input = QLineEdit()
        self.cursor_outline_color_input.setText(colors[2])
        layout2.addWidget(self.cursor_outline_color_input)

        layout1.addWidget(QLabel("Cursor fill color:"))
        self.cursor_fill_color_input = QLineEdit()
        self.cursor_fill_color_input.setText(colors[3])
        layout2.addWidget(self.cursor_fill_color_input)

        self.temp_layout = QHBoxLayout()
        self.temp_layout.addLayout(layout1)
        self.temp_layout.addLayout(layout2)
        self.layout.addLayout(self.temp_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

    def get_values(self):
        return (
            self.pointer_outline_color_input.text(),
            self.pointer_fill_color_input.text(),
            self.cursor_outline_color_input.text(),
            self.cursor_fill_color_input.text()
        )


class InputDialog(QDialog):
    def __init__(self, parent=None, title="Input", input_text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(200, 1)
        self.layout = QVBoxLayout()

        self.layout.addWidget(QLabel("Input:"), alignment=Qt.AlignLeft)

        self.input_box = QLineEdit()
        self.input_box.setText(input_text)
        self.layout.addWidget(self.input_box)

        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.setLayout(self.layout)


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
        self.pointer_outline_color = "#0000FF"
        self.pointer_fill_color = "#ADD8E6"
        self.cursor_outline_color = "#000000"
        self.cursor_fill_color = "#90EE90"
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
        self.update_highlights(ignore_mode=False)

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

        self.update_highlights(False)

    def update_highlights(self, ignore_mode):
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].setStyleSheet("")

        if self.rows > 0 and self.cols > 0:
            self.cells[self.current_row][self.current_col].setStyleSheet(
                f"background-color: {self.cursor_fill_color} ; border: 1px solid {self.cursor_outline_color}")
            self.cells[self.current_row][self.current_col].setFocus()

        if (self.rows > 0 and self.cols > 0 and
                (self.highlight_row != self.current_row or self.highlight_col != self.current_col)):
            if ignore_mode:
                self.cells[self.highlight_row][self.highlight_col].setStyleSheet(
                    f"background-color: #ffffff; border: 2px solid {self.pointer_outline_color}")
            else:
                self.cells[self.highlight_row][self.highlight_col].setStyleSheet(
                    f"background-color: {self.pointer_fill_color}; border: 2px solid {self.pointer_outline_color}")

    def set_current_cell(self, row, col):
        self.current_row = row
        self.current_col = col
        self.update_highlights(False)

    def set_highlight_cell(self, row, col, ignore_mode=False):
        self.highlight_row = row
        self.highlight_col = col
        self.update_highlights(ignore_mode)

    def get_cell_data(self):
        return self.cells[self.highlight_row][self.highlight_col].text()

    def cell_key_press_event(self, event, row, col):
        if event.key() == Qt.Key_Up:
            self.current_row = max(0, self.current_row - 1)
            self.update_highlights(False)
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.current_row = min(self.rows - 1, self.current_row + 1)
            self.update_highlights(False)
            event.accept()
        elif event.key() == Qt.Key_Left:
            self.current_col = max(0, self.current_col - 1)
            self.update_highlights(False)
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.current_col = min(self.cols - 1, self.current_col + 1)
            self.update_highlights(False)
            event.accept()
        else:
            QLineEdit.keyPressEvent(self.cells[row][col], event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.color_change_action = None
        self.color_dialog = None
        self.input_dialog = None
        self.auto_run = None
        self.col_spin = None
        self.current_step = None
        self.debug_line1 = None
        self.debug_line2 = None
        self.debug_line3 = None
        self.debug_line4 = None
        self.debug_line5 = None
        self.export_action = None
        self.file_menu = None
        self.grid = None
        self.highlight_col = 0
        self.highlight_row = 0
        self.interpreter = Interpreter(build_in_input=self.open_input_dialog)
        self.is_running = False
        self.menu_bar = None
        self.open_action = None
        self.reset_button = None
        self.row_spin = None
        self.run_button = None
        self.speed_slider = None
        self.stack1 = None
        self.stack2 = None
        self.steps_remaining_label = None
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

        self.color_change_action = QAction("&Change colors", self)
        self.color_change_action.triggered.connect(self.open_input_color_dialog)
        self.menu_bar.addAction(self.color_change_action)

        self.input_change_action = QAction("&Input", self)
        self.input_change_action.triggered.connect(self.open_input_dialog)
        self.menu_bar.addAction(self.input_change_action)

        self.grid = CellGrid(25, 25)
        self.grid_layout = QVBoxLayout()
        self.grid_layout.addWidget(self.grid)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_layout.addStretch(0)
        main_layout.addLayout(self.grid_layout)

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

        self.steps_remaining_label = QLabel("      ")
        self.step_count = QSpinBox()
        self.step_count.setRange(1, 1000)
        self.speed_slider = QSpinBox()
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setFixedWidth(self.step_count.sizeHint().width())
        self.debug_line1 = QLabel("Output: ")
        self.debug_line2 = QLabel("Cords: ")
        self.debug_line3 = QLabel("Direction: ")
        self.debug_line4 = QLabel("Ignore_mode: ")
        self.debug_line5 = QLabel("input: ")

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
        third_row.addWidget(self.steps_remaining_label)

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
        stack2_layout.addStretch(1)
        debug_layout = QVBoxLayout()
        debug_layout.addWidget(self.debug_line1)
        debug_layout.addWidget(self.debug_line2)
        debug_layout.addWidget(self.debug_line3)
        debug_layout.addWidget(self.debug_line4)
        debug_layout.addWidget(self.debug_line5)
        debug_layout.addStretch(0)

        stack_layout = QVBoxLayout()
        stack_layout.addLayout(label_layout)
        stack_layout.addLayout(stack2_layout)

        side_panel_a = QGroupBox("Debug:")
        side_panel = QHBoxLayout()
        side_panel.addLayout(stack_layout)
        side_panel.addLayout(debug_layout)
        side_panel_a.setLayout(side_panel)

        control_panel.addLayout(debug_layout)
        control_panel.addWidget(side_panel_a)

        main_layout.addStretch(1)
        main_layout.addLayout(control_panel)
        control_panel.setAlignment(Qt.AlignRight)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.reset()

    def run(self):
        self.auto_run = True
        self.step_count_total = self.step_count.value()
        self.current_step = 0
        self.is_running = True
        self.timer.start(1000 // self.speed_slider.value())

    def step(self):
        char = self.grid.get_cell_data()
        if not char:
            QMessageBox.warning(self, "Info", "No character to process")
            self.stop()
            self.edit_info()
            return
        process_result = self.interpreter.process_char(char)
        if not process_result:
            QMessageBox.warning(self, "Info", "Invalid character")
            self.stop()
            return
        if self.auto_run:
            self.current_step += 1
            self.steps_remaining_label.setText(f'Steps left: {self.current_step} / {self.step_count_total}')
            if self.current_step >= self.step_count_total:
                self.stop()
        self.edit_info()

    def stop(self):
        self.steps_remaining_label.setText("Done!")
        self.timer.stop()
        self.auto_run = False

    def reset(self):
        self.interpreter.reset()
        self.highlight_row = 0
        self.highlight_col = 0
        self.grid.set_highlight_cell(0, 0)
        self.stack1.clear()
        self.stack2.clear()
        self.edit_info()

    def edit_info(self):
        information: Dict[str, Any] = self.interpreter.get_information()
        self.stack1.clear()
        self.stack2.clear()
        if information['stack']:
            for item in reversed(information['stack']):
                self.stack1.addItem(str(item))
        if information["addition_stack"]:
            for item in reversed(information["addition_stack"]):
                self.stack2.addItem(str(item))

        self.debug_line4.setText(f"Ignore_mode: {information['ignore_mode']}")
        text = f"Input: {information['input']}"
        self.debug_line5.setText(text)
        symbol_index = information["input_pointer"] + 7
        if symbol_index < len(text):
            highlighted_text = (
                    text[:symbol_index] +
                    f"<span style='background-color: {self.grid.cursor_fill_color}; color: black;'>{text[symbol_index]}</span>" +
                    text[symbol_index + 1:]
            )
            self.debug_line5.setText(highlighted_text)
            self.debug_line5.setTextFormat(Qt.RichText)

        if information["output"]:
            self.debug_line1.setText(f"Output: {information['output']}")
        if information["position"]:
            self.debug_line2.setText(f"Cords: {information['position']}")
            self.grid.set_highlight_cell(information["position"][1], information["position"][0],
                                         information["ignore_mode"])
        if information["direction"]:
            self.debug_line3.setText(f"Direction: {information['direction']}")

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
                QMessageBox.critical(self, "load error", f"Error loading file: {e}")

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
                QMessageBox.critical(self, "export error", f"Error exporting file: {e}")

    def open_input_color_dialog(self):
        self.color_dialog = ColorDialog(self, (
            self.grid.pointer_outline_color, self.grid.pointer_fill_color, self.grid.cursor_outline_color,
            self.grid.cursor_fill_color))
        if self.color_dialog.exec_() == QDialog.Accepted:
            new_values = self.color_dialog.get_values()
            self.update_colors(new_values)

    def open_input_dialog(self):
        self.input_dialog = InputDialog(self, "Input", self.interpreter.get_input())
        if self.input_dialog.exec_() == QDialog.Accepted:
            self.interpreter.set_input(self.input_dialog.input_box.text())
        self.edit_info()

    def update_colors(self, new_values):
        self.grid.pointer_outline_color = new_values[0]
        self.grid.pointer_fill_color = new_values[1]
        self.grid.cursor_outline_color = new_values[2]
        self.grid.cursor_fill_color = new_values[3]
        self.edit_info()

    def resize_grid(self):
        rows = self.row_spin.value()
        cols = self.col_spin.value()
        self.grid.set_grid_size(rows, cols)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
