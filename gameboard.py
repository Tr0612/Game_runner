import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox,QLabel,QVBoxLayout
from PyQt5.QtCore import Qt,QTimer
from board_visualizer import BoardDetector
import random
from Arduino_Files.IK import IkSolver
from Arduino_Files.communicator import SerialDevice


ROWS, COLS = 3, 3  # 3x4 board

class TicTacToeGame(QWidget):
    def __init__(self):
        super().__init__()
        self.cell_xyz = {
    "A1": (0.46, -0.36, 0.65),
    "B1": (0.52, -0.45, 1.15),
    "C1": (0.55,  0.39, 1.75),
    "D1": (0.79,  0.86, 1.94),
    "A2": (-0.43, 0.73, 1.93),
    "B2": (-0.05, 0.16, 1.37),
    "C2": (0.86,  0.06, 1.72),
    "D2": (0.62, -0.98, 0.42),
    "A3": (-0.28, -0.06, 1.91),
    "B3": (0.57,  0.00, 1.30),
    "C3": (0.64,  0.32, 0.50),
    "D3": (-0.04, -0.88, 0.21)
}
        
        self.detector = BoardDetector()
        self.current_player = 'X'  # X starts the game
        self.board = [['' for _ in range(COLS)] for _ in range(ROWS)]
        self.time_seconds = 15
        self.initUI()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        self.start_turn('X')

    def update_board_state(self, new_board):
        print("Received new board state")
        for row in new_board:
            print(row)
        
        changed = False
            
        # self.board = new_board
        for row in range(ROWS):
            for col in range(COLS):
                symbol = new_board[row][col]
                if symbol and self.board[row][col] == '':
                    self.board[row][col] = symbol
                    self.buttons[row][col].setText(symbol)
                    changed = True
                    cell_label = chr(ord('A') + col) + str(row + 1)
                    print(f"[Camera] Detected move: {symbol} at {cell_label}")
                        # self.update_empty_cell_count()
                    
                    if symbol and self.board[row][col] == '':
                        self.timer_seconds = 15
                        self.timer.start()
        if changed:   
            self.update_empty_cell_count()
            next_player = 'O' if self.current_player == 'X' else 'X'
            self.start_turn(next_player)
                # label = chr(ord('A') + col) + str(row + 1)
                # text = f"<center>{label}<br>{symbol}</center>" if symbol else f"<center>{label}</center>"
                # self.buttons[row][col].setText(text)
                # self.buttons[row][col].setText(new_board[row][col])

    def initUI(self):
        self.setWindowTitle('Tic-Tac-Toe')
        self.setGeometry(100, 100, 500, 400)
        self.timer_label = QLabel("Timer: 15s")
        self.timer_label.setStyleSheet("font-size: 16px; color: blue;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        grid = QGridLayout()
        self.buttons = [[None for _ in range(COLS)] for _ in range(ROWS)]
        
        for row in range(ROWS):
            for col in range(COLS):
                label_text = chr(ord('A') + col) + str(row + 1)
                
                button = QPushButton('')
                button.setFixedSize(80, 80)
                button.setStyleSheet("font-size: 24px;")
                button.clicked.connect(lambda _, r=row, c=col: self.make_move(r, c))
                self.buttons[row][col] = button
                
                # Create label
                label = QLabel(label_text)
                label.setStyleSheet("font-size: 12px; color: gray;")
                label.setAlignment(Qt.AlignCenter)

                # Create a vertical layout with button on top, label below
                cell_layout = QVBoxLayout()
                cell_layout.addWidget(button)
                cell_layout.addWidget(label)

                # Wrap in a QWidget to add to QGridLayout
                container = QWidget()
                container.setLayout(cell_layout)

                grid.addWidget(container, row, col)
                
        reset_button = QPushButton("Reset Game")
        reset_button.setStyleSheet("font-size: 16px; padding: 8px;")
        reset_button.clicked.connect(self.reset_game_and_camera)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addWidget(reset_button, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.timer_label)
        
        self.setLayout(main_layout)
        self.show()
    
    def update_timer(self):
        self.timer_seconds -= 1
        self.timer_label.setText(f"Timer: {self.timer_seconds}s")
        
        if self.timer_seconds <=0:
            self.timer.stop()
            # self.auto_pass_turn()
    
    def auto_pass_turn():
        print(f"[Timer] Player {self.current_player} ran out of time. Passing turn.")
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.start_turn(self.current_player)
    
    def start_turn(self, player):
        
        if self.is_board_full():
            self.timer.stop()
            self.show_message("It's a tie!")
            self.reset_game()
            return
        
        self.current_player = player
        self.timer_seconds = 15
        self.timer_label.setText(f"Timer: {self.timer_seconds}s")
        self.timer.start()
        self.update_empty_cell_count()

        if player == 'X':
            print("[Game] Robot's turn...")
            self.make_robot_move()
    
    def make_robot_move(self):
        empty_cells = [(r,c) for r in range(ROWS) for c in range(COLS) if self.board[r][c] == '']
        
        if not empty_cells:
            print("Robot no available moves")
            
        row,col = random.choice(empty_cells)
        
        cell_label = chr(ord('A') + col) + str(row+1)
        
        x,y,z = self.cell_xyz[cell_label]
        angle = IkSolver.ik_function(x,y,z)
        
        robot_status = SerialDevice.send_data_f(angle)
            
        print(f"Robot Played {cell_label}")
        self.make_move(row,col)
        

    def update_empty_cell_count(self):
        count = sum(1 for row in self.board for cell in row if cell == '')
    
    def make_move(self, row, col):
        if self.board[row][col] == '':
            self.board[row][col] = self.current_player
            self.buttons[row][col].setText(self.current_player)

            winner = self.check_winner()
            if winner:
                self.timer.stop()
                self.show_message(f"Player {winner} wins")
                self.reset_game()
                return
                
            elif self.is_board_full():
                self.show_message("It's a tie!")
                self.reset_game()
                return    
            
            # else:
            #     self.current_player = 'O' if self.current_player == 'X' else 'X'
            
            self.update_empty_cell_count()
            next_player = 'O' if self.current_player == 'X' else 'X'
            self.start_turn(next_player)

    def check_winner(self):
        # Check rows
        # Check horizontal
        for row in range(ROWS):
            for col in range(COLS - 2):
                a, b, c = self.board[row][col:col+3]
                if a and a == b == c:
                    return a  # return 'X' or 'O'

        # Check vertical
        for col in range(COLS):
            for row in range(ROWS - 2):
                a = self.board[row][col]
                b = self.board[row+1][col]
                c = self.board[row+2][col]
                if a and a == b == c:
                    return a

        return None

    def is_board_full(self):
        return all(cell != '' for row in self.board for cell in row)

    def reset_game(self):
        self.board = [['' for _ in range(COLS)] for _ in range(ROWS)]
        for row in range(ROWS):
            for col in range(COLS):
                self.buttons[row][col].setText('')
                self.buttons[row][col].setEnabled(True)
        self.update_empty_cell_count()
        # self.current_player = 'X'
        

    def show_message(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Game Over")
        msg.setText(message)
        msg.exec_()
    
    def reset_game_and_camera(self):
        print("Game reset")
        self.timer.stop()
        self.reset_game()
        # if hasattr(self.detector,"reset"):
        #     print("Restarting the camera")
        #     self.detector.reset()
        
        QTimer.singleShot(2000, lambda: self.start_turn('X'))
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = TicTacToeGame()
    sys.exit(app.exec_())
