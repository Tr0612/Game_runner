import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox,QLabel,QVBoxLayout
from PyQt5.QtCore import Qt,QTimer
import time
from board_visualizer import BoardDetector
import random
# from Arduino_Files.IK import IkSolver
# from Arduino_Files.communicator import SerialDevice
from Arduino_Files.RFBot import RFBot
# from runner import prev_board


ROWS, COLS = 3, 3  # 3x4 board

class TicTacToeGame(QWidget):
    def __init__(self):
        super().__init__()
        self.cell_xyz = {
    "C1": (230,85,90),
    "C2": (230,-10,90),
    "C3": (230,-110,90),
    "X" : (230,-210,150),
    # "D1": (0.79,  0.86, 1.94),
    "B1": (330,75,95),
    "B2": (325,-15,95),
    "B3": (320,-110,95),
    # "D2": (0.62, -0.98, 0.42),
    "A1": (415,70,105),
    "A2": (405,-20,105),
    "A3": (405,-115,105),
    # "D3": (-0.04, -0.88, 0.21)
}
        
        # self.robot = RFBot(port='COM3', baud='9600')
        self.robot = RFBot(port="COM5")
        self.detector = BoardDetector()
        self.reset = 0
        self.X_count = 0
        self.current_player = 'X'  # X starts the game
        self.prev_board = [['' for _ in range(COLS)] for _ in range(ROWS)] 
        self.board = [['' for _ in range(COLS)] for _ in range(ROWS)]
        self.time_seconds = 5
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
            var = self.check_winner()
            if self.check_winner() == None:
                print("[Game] Robot's turn...")
                self.X_count += 1
                self.make_robot_move()
            else:
                self.timer.stop()
                self.show_message(f"Player {var} wins")
                self.reset_game()
                return
                
    
    def make_robot_move(self):
        i = 0
        empty_cells = [(r,c) for r in range(ROWS) for c in range(COLS) if self.board[r][c] == '']
        
        if not empty_cells:
            print("Robot no available moves")
            
        row,col = random.choice(empty_cells)
        
        cell_label = chr(ord('A') + col) + str(row+1)
        pos = self.cell_xyz[cell_label]
        px,py,pz = pos
        xx,xy,xz = self.cell_xyz['X']
        # bx,by,bz = pos
        lift_amount = self.X_count*40
        place_amount = self.X_count*20
        x_pos = (xx,xy,xz+place_amount)
        x_pos_up = (xx,xy,xz+lift_amount)
        # x_pos[2] += self.X_count*20
        # x_pos_up[2] += self.X_count*40
        print(x_pos_up)
        print(x_pos)
        print(pos)
        # self.robot.release()
        self.robot.move(x_pos_up)
        while i ==0:
            data = self.robot.get_state()
            if data != None:
                break
        # time.sleep(100)
        self.robot.move(x_pos)
        while i ==0:
            data = self.robot.get_state()
            if data != None:
                break
        
        
        # # self.robot.grip()
        # self.robot.move(x_pos_up)
        # while i == 0:
        #     data = self.robot.get_state()
        #     print(type(data))
        #     if len(data) != 0:
        #         data = None
        #         self.robot.move(x_pos)
        #         time.sleep(100)
        #         self.robot.grip()
        #         data = self.robot.get_state()
        #         if len(data) != 0:
        #             i = 1
        #             data = None
        #             self.robot.move(x_pos_up)
                    
        self.robot.move(pos)
        while i ==0:
            data = self.robot.get_state()
            if data != None:
                break
        self.robot.zero()
        while i ==0:
            data = self.robot.get_state()
            if data != None:
                break
        
        # # self.robot.release()
        # pos_up = (px,py,pz+40)
        # self.robot.move(pos_up)
        # self.robot.zero()
        # self.robot.grip()
        # i = 0 
        # while i == 0:
        #     data = self.robot.get_state()
        #     if len(data) != 0:
        #         data = None
        #         pos_up = pos
        #         pos_up[2] += 40
        #         time.sleep(100)
        #         self.robot.release()
        #         time.sleep(100)
        #         self.robot.move(pos_up)
        #         data = self.robot.get_state()
        #         if len(data) != 0:
        #             data = None
        #             self.robot.move(zero)
        #             self.robot.grip()
        #             data = self.robot.get_state()
        #             if len(data) != 0:
        #                 i = 1
        #                 data = None
        # time.sleep(100) 
        # self.robot.move(zero)
        # data = self.robot.get_state()
        # if len(data) != 0:
        #     print("Robot Movement Done")
        #     data = None
        #     i = 0
        # RFBot.move(pos=pos)
        
        # x,y,z = self.cell_xyz[cell_label]
        # angle = IkSolver.ik_function(x,y,z)
        
        # robot_status = SerialDevice.send_data_f(angle)
            
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
        
        for row in range(ROWS - 2):
            for col in range(COLS - 2):
                a = self.board[row][col]
                b = self.board[row+1][col+1]
                c = self.board[row+2][col+2]
                if a and a == b == c:
                    return a

    # Check “/” diagonals (top-right → bottom-left)
        for row in range(ROWS - 2):
            for col in range(2, COLS):
                a = self.board[row][col]
                b = self.board[row+1][col-1]
                c = self.board[row+2][col-2]
                if a and a == b == c:
                    return a
                
        return None

    def is_board_full(self):
        return all(cell != '' for row in self.board for cell in row)
    
    def reset_pass(self):
        return self.reset

    def reset_game(self):
        self.board = [['' for _ in range(COLS)] for _ in range(ROWS)]
        self.prev_board = [['' for _ in range(COLS)] for _ in range(ROWS)]
        self.reset = 1
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
        self.robot.zero()
        # self.robot.grip()
        # if hasattr(self.detector,"reset"):
        #     print("Restarting the camera")
        #     self.detector.reset()
        
        QTimer.singleShot(2000, lambda: self.start_turn('X'))
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = TicTacToeGame()
    sys.exit(app.exec_())
