# runner_test_gui.py
import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gameboard import TicTacToeGame  # Adjust if it's named differently

app = QApplication(sys.argv)
game = TicTacToeGame()

# Dummy states to simulate updates
dummy_boards = [
    [['X', '', 'O'], ['', '', ''], ['', '', '']],
    [['X', 'O', 'O'], ['', 'X', ''], ['', '', '']],
    [['X', 'O', 'O'], ['', 'X', ''], ['O', '', 'X']],
]

step = 0

def update_fake_board():
    global step
    game.update_board_state(dummy_boards[step])
    step = (step + 1) % len(dummy_boards)

timer = QTimer()
timer.timeout.connect(update_fake_board)
timer.start(1000)  # Update every 1 second

sys.exit(app.exec_())
