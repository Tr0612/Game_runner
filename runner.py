import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gameboard import TicTacToeGame
from board_visualizer import BoardDetector

ROWS, COLS = 3, 3

bd = BoardDetector()
# bd.reset
last_detection_time = 0
DETECTION_INTERVAL = 15

def cell_label(row, col):
    col_label = chr(ord('A') + col)  # A, B, C, D
    row_label = str(row + 1)         # 1, 2, 3
    return f"{col_label}{row_label}"

def board_changed(prev, curr):
    return prev != curr

prev_board = [['' for _ in range(COLS)] for _ in range(ROWS)]

def poll_camera_and_update():
    global prev_board,last_detection_time
    
    
    if not detector.ready:
        print("Detector not ready")
        return
    
    try:
        current_time = time.time()
        
        if current_time - last_detection_time < DETECTION_INTERVAL:
            return
        if game.reset_pass() == 0:
            new_board = detector.get_current_board_state()
        if game.reset_pass() == 1:
            prev_board = [['' for _ in range(COLS)] for _ in range(ROWS)]
            new_board = [['' for _ in range(COLS)] for _ in range(ROWS)]
            game.reset=0
        if new_board:
            # Merge new detections into existing board
            updated = False
            for r in range(ROWS):
                for c in range(COLS):
                    if new_board[r][c] and prev_board[r][c] == '':
                        cell = cell_label(r,c)
                        print(f"[Runner] new piece detected at {cell}: {new_board[r][c]}")
                        prev_board[r][c] = new_board[r][c]
                        updated = True

            if updated:
                # game.update_board_state(prev_board)
                game.update_board_state([row[:] for row in prev_board])
                
    except Exception as e:
        print("Polling error:", e)

if __name__ == "__main__":
    print("Starting GUI app...")
    app = QApplication(sys.argv)
    game = TicTacToeGame()

    try:
        detector = BoardDetector()
        # detector.show_detection_window()
        print("Camera + model ready.")
    except Exception as e:
        print("Error initializing camera:", e)
        detector = None  # fallback so GUI can still open

    if detector:
        timer = QTimer()
        timer.timeout.connect(poll_camera_and_update)
        timer.start(1000)  # ms
        # detector.show_detection_window()
    else:
        print("Skipping camera polling...")

    sys.exit(app.exec_())
