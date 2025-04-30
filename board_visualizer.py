import time
import csv
import math

import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO

# ==== CONFIG ====
ROWS, COLS = 3, 3
MODEL_PATH = "D:/University/OneDrive - UCB-O365/Mech2/Final_Project/runs/detect/train15/weights/best.pt"
OUTPUT_FILE = "detected_coordinates.csv"
CONFIDENCE_THRESHOLD = 0.5

class BoardDetector:
    def __init__(self):
        # — RealSense setup —
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(config)
        self.detection_interval =15
        self.last_detection_time = 0
        profile = self.pipeline.get_active_profile()
        self.color_intrinsics = (
            profile.get_stream(rs.stream.color)
                   .as_video_stream_profile()
                   .get_intrinsics()
        )

        self.ready = True

        # — YOLOv8 model load —
        self.model = YOLO(MODEL_PATH)

        # — Grid parameters (tweak these to match your taped grid) —
        self.grid_top_left     = (134, 100)   # (x, y)
        self.grid_bottom_right = (420, 350)   # (x, y)
        self.rotation_angle    = 0            # set to nonzero if your board is tilted
        self._compute_grid_metrics()

        # — CSV header —
        with open(OUTPUT_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["Label","Row","Col","X","Y","Z"])

    def _compute_grid_metrics(self):
        # called any time you change grid_top_left / bottom_right / rotation_angle
        tl, br = self.grid_top_left, self.grid_bottom_right
        self.center_x = (tl[0] + br[0]) // 2
        self.center_y = (tl[1] + br[1]) // 2
        self.grid_w = br[0] - tl[0]
        self.grid_h = br[1] - tl[1]
        self.cell_w = self.grid_w // COLS
        self.cell_h = self.grid_h // ROWS

    def rotate_point(self, x, y, angle):
        """Rotate (x,y) about the grid center by angle degrees."""
        cx, cy = self.center_x, self.center_y
        a = math.radians(angle)
        dx, dy = x - cx, y - cy
        xr = dx * math.cos(a) - dy * math.sin(a) + cx
        yr = dx * math.sin(a) + dy * math.cos(a) + cy
        return int(xr), int(yr)

    def depth_to_world(self, x, y, depth):
        fx, fy = self.color_intrinsics.fx, self.color_intrinsics.fy
        cx, cy = self.color_intrinsics.ppx, self.color_intrinsics.ppy
        X = (x - cx) * depth / fx
        Y = (y - cy) * depth / fy
        return X, Y, depth
    
    def get_current_board_state(self):
        """
        Poll the camera, run one YOLO inference, and return
        a 3×3 list-of-lists with ''/’X’/’O’ for each cell.
        """
        # grab a fresh frame
        frames = self.pipeline.wait_for_frames()
        cf = frames.get_color_frame()
        df = frames.get_depth_frame()
        if not cf or not df:
            return None

        img = np.asanyarray(cf.get_data())
        # run detection
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.model(rgb, conf=CONFIDENCE_THRESHOLD,verbose=False)

        # clear board
        board = [['' for _ in range(COLS)] for _ in range(ROWS)]

        # same cell-mapping logic as in show_detection_window
        for det in results:
            for box in det.boxes:
                x1,y1,x2,y2 = map(int, box.xyxy[0])
                label = self.model.names[int(box.cls[0])]

                # skip entirely outside grid
                tlx,tly = self.grid_top_left
                brx,bry = self.grid_bottom_right
                if x2<tlx or x1>brx or y2<tly or y1>bry:
                    continue

                # center & inverse rotate
                cx, cy = (x1+x2)//2, (y1+y2)//2
                unx,uny = self.rotate_point(cx, cy, -self.rotation_angle)

                # map into cell
                relx, rely = unx - tlx, uny - tly
                if not (0<=relx<self.grid_w and 0<=rely<self.grid_h):
                    continue

                c = min(relx//self.cell_w, COLS-1)
                r = min(rely//self.cell_h, ROWS-1)
                board[r][c] = label

        return board


    def stop(self):
        self.pipeline.stop()
        cv2.destroyAllWindows()

    def show_detection_window(self):
        """Live stream + manual ‘d’ key to detect"""
        self._compute_grid_metrics()

        while True:
            # grab frames
            frames = self.pipeline.wait_for_frames()
            cf = frames.get_color_frame()
            df = frames.get_depth_frame()
            if not cf or not df:
                continue

            color = np.asanyarray(cf.get_data())
            depth = np.asanyarray(df.get_data())

            # draw grid (unrotated here; if you use rotation, rotate each line endpoint)
            tlx,tly = self.grid_top_left
            brx,bry = self.grid_bottom_right
            # verticals
            for i in range(1, COLS):
                x = tlx + i*self.cell_w
                p1 = self.rotate_point(x, tly, self.rotation_angle)
                p2 = self.rotate_point(x, bry, self.rotation_angle)
                cv2.line(color, p1, p2, (0,255,0), 3)
            # horizontals
            for j in range(1, ROWS):
                y = tly + j*self.cell_h
                p1 = self.rotate_point(tlx, y, self.rotation_angle)
                p2 = self.rotate_point(brx, y, self.rotation_angle)
                cv2.line(color, p1, p2, (0,255,0), 3)
            # outer box
            corners = [
                self.rotate_point(tlx, tly, self.rotation_angle),
                self.rotate_point(brx, tly, self.rotation_angle),
                self.rotate_point(brx, bry, self.rotation_angle),
                self.rotate_point(tlx, bry, self.rotation_angle),
            ]
            for k in range(4):
                cv2.line(color, corners[k], corners[(k+1)%4], (0,255,0), 4)

            cv2.putText(color, "Press 'd' to detect | 'q' to quit",
                        (10,30), cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,0),2)
            cv2.imshow("Tic Tac Toe Detection", color)
            key = cv2.waitKey(1) & 0xFF
            if key==ord('q'):
                break

            if key==ord('d'):
                # ==== RUN DETECTION ====
                rgb = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
                results = self.model(rgb, conf=CONFIDENCE_THRESHOLD)

                # clear board
                board = [['' for _ in range(COLS)] for _ in range(ROWS)]

                # process each detection
                for det in results:
                    for box in det.boxes:
                        x1,y1,x2,y2 = map(int,box.xyxy[0])
                        label = self.model.names[int(box.cls[0])]
                        # ignore entirely outside grid
                        if x2<tlx or x1>brx or y2<tly or y1>bry:
                            continue

                        # center point
                        cx, cy = (x1+x2)//2, (y1+y2)//2
                        # inverse rotate center to align with unrotated grid
                        unx,uny = self.rotate_point(cx, cy, -self.rotation_angle)

                        # local coords
                        lx, ly = unx - tlx, uny - tly
                        if not (0<=lx<self.grid_w and 0<=ly<self.grid_h):
                            continue

                        col = min(lx//self.cell_w, COLS-1)
                        row = min(ly//self.cell_h, ROWS-1)
                        board[row][col] = label

                        # draw box & center
                        cv2.rectangle(color,(x1,y1),(x2,y2),(255,0,0),2)
                        cv2.circle(color,(cx,cy),4,(0,0,255),-1)
                        # optional: depth→world
                        Z = int(depth[cy, cx])
                        X,Y,Z = self.depth_to_world(cx, cy, Z)
                        # log to CSV
                        with open(OUTPUT_FILE,"a",newline="") as f:
                            csv.writer(f).writerow([label,row,col,f"{X:.3f}",f"{Y:.3f}",Z])

                # print board state
                print("\nBoard State:")
                for r in board:
                    print(r)

                cv2.imshow("Tic Tac Toe Detection", color)
                cv2.waitKey(0)

        self.stop()


if __name__ == "__main__":
    bd = BoardDetector()
    bd.show_detection_window()
