import numpy as np
import pyrealsense2 as rs
import cv2
import csv
from ultralytics import YOLO
import time

# ==== CONFIG ====
ROWS, COLS = 3, 4
MODEL_PATH = "D:/University/OneDrive - UCB-O365/Mech2/Final_Project/runs/detect/train5/weights/best.pt"
# MODEL_PATH = "/media/thanush/Elements/University/OneDrive - UCB-O365/Mech2/Final_Project/runs/detect/train5/weights/best.pt"
OUTPUT_FILE = "detected_coordinates.csv"
CONFIDENCE_THRESHOLD = 0.8


class BoardDetector:
    def __init__(self):
        # Initialize RealSense pipeline
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(config)
        self.detection_interval =15
        self.last_detection_time = 0
        profile = self.pipeline.get_active_profile()
        self.color_intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

        self.ready = True
        
        # Load YOLOv8 model
        self.model = YOLO(MODEL_PATH)
        self.cell_width = 640 // COLS
        self.cell_height = 480 // ROWS

        # CSV header setup
        with open(OUTPUT_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Label", "Row", "Col", "X", "Y", "Z"])

    def depth_to_world(self, x, y, depth):
        fx, fy = self.color_intrinsics.fx, self.color_intrinsics.fy
        cx, cy = self.color_intrinsics.ppx, self.color_intrinsics.ppy
        X = (x - cx) * depth / fx
        Y = (y - cy) * depth / fy
        Z = depth
        return X, Y, Z

    def get_current_board_state(self):
        """Get the current board state as a 2D array of detected symbols."""
        
        current_time = time.time()
        
        if (current_time - self.last_detection_time) < self.detection_interval:
            return None
        
        
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            return None

        color_image = np.asanyarray(color_frame.get_data())
        rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        results = self.model(rgb_image, conf=CONFIDENCE_THRESHOLD)

        board_state = [['' for _ in range(COLS)] for _ in range(ROWS)]
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = self.model.names[int(box.cls[0])]
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                col = min(center_x // self.cell_width, COLS - 1)
                row = min(center_y // self.cell_height, ROWS - 1)
                board_state[row][col] = label
                
        self.last_detection_time = current_time
        
        return board_state

    def stop(self):
        self.pipeline.stop()
        cv2.destroyAllWindows()
    
    def reset(self):
        print("Camera Reset")
        self.ready = False
        self.pipeline.stop()
        time.sleep(0.5)
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(config)
        
        for _ in range(5):
            try:
                self.pipeline.wait_for_frames()
            except Exception as e:
                print("[Detector] Frame wait failed (warming up):", e)
            time.sleep(0.1)
        
        self.ready = True
        print("Camera Ready")

    def show_detection_window(self):
        """Optional: run manual OpenCV loop where pressing 'd' triggers detection display."""
        
        if not self.ready:
            print("Detector not ready")
            return
        
        for attempt in range(10):
            try:
                frames = self.pipeline.wait_for_frames()
                break  # ✅ success
            except RuntimeError:
                print(f"[Detector] Frame wait failed, retry {attempt + 1}/5")
                time.sleep(0.2)
        
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()

                if not color_frame or not depth_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())
                display_image = color_image.copy()

                # Draw grid overlay
                for i in range(1, COLS):
                    cv2.line(display_image, (i * self.cell_width, 0),
                             (i * self.cell_width, display_image.shape[0]), (255, 0, 0), 2)
                for j in range(1, ROWS):
                    cv2.line(display_image, (0, j * self.cell_height),
                             (display_image.shape[1], j * self.cell_height), (255, 0, 0), 2)

                cv2.putText(display_image, "Press 'd' to detect | Press 'q' to quit",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                cv2.imshow('Tic Tac Toe Detection', display_image)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    break

                elif key == ord('d'):
                    # Detection mode
                    board_state = [['' for _ in range(COLS)] for _ in range(ROWS)]
                    color_image_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
                    results = self.model(color_image_rgb, conf=CONFIDENCE_THRESHOLD)

                    for r in results:
                        for box in r.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = box.conf[0].item()
                            label = self.model.names[int(box.cls[0])]
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2

                            col = min(center_x // self.cell_width, COLS - 1)
                            row = min(center_y // self.cell_height, ROWS - 1)
                            board_state[row][col] = label

                            depth = depth_image[center_y, center_x]
                            X, Y, Z = self.depth_to_world(center_x, center_y, depth)

                            with open(OUTPUT_FILE, mode='a', newline='') as file:
                                writer = csv.writer(file)
                                writer.writerow([label, row, col, X, Y, Z])

                            cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(color_image, f"{label} {conf:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Show detected board
                    for r in range(ROWS):
                        for c in range(COLS):
                            if board_state[r][c] != '':
                                cx = c * self.cell_width + 10
                                cy = r * self.cell_height + 30
                                cv2.putText(color_image, board_state[r][c], (cx, cy),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                    print("\nBoard State:")
                    for row in board_state:
                        print(row)

                    cv2.imshow('Tic Tac Toe Detection', color_image)
                    cv2.waitKey(0)

        finally:
            self.stop()
