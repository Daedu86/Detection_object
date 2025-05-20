import tkinter as tk
from PIL import Image, ImageTk
from ultralytics import YOLO
import cv2
import threading
import numpy as np
import ctypes
import sys
import mss

class DetectionWindow:
    def __init__(self, root, model):
        self.root = root
        self.model = model

        self.root.geometry("800x600+100+100")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.config(bg='black')
        self.root.attributes("-alpha", 0.5)

        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style | 0x80000 | 0x20)
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 128, 0x2)

        self.canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.canvas.pack()

        self.root.bind("<Button-1>", self.on_press)
        self.root.bind("<B1-Motion>", self.on_drag)

        self.x_offset = 0
        self.y_offset = 0

        self.running = True
        self.pause = False
        self.video_thread = threading.Thread(target=self.run_detection)
        self.video_thread.start()

    def on_press(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def on_drag(self, event):
        delta_x = event.x - self.x_offset
        delta_y = event.y - self.y_offset
        new_x = self.root.winfo_x() + delta_x
        new_y = self.root.winfo_y() + delta_y
        self.root.geometry(f'+{new_x}+{new_y}')

    def run_detection(self):
        with mss.mss() as sct:
            while self.running:
                if self.pause:
                    continue

                left = self.root.winfo_x()
                top = self.root.winfo_y()
                width = self.root.winfo_width()
                height = self.root.winfo_height()

                monitor = {"top": top, "left": left, "width": width, "height": height}
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                results = self.model(frame)[0]
                annotated = results.plot()
                annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                image_pil = Image.fromarray(annotated)
                img_tk = ImageTk.PhotoImage(image_pil)

                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
                self.canvas.image = img_tk

        print("Detection thread stopped.")

    def toggle_pause(self):
        self.pause = not self.pause

    def stop(self):
        self.running = False


class ControlPanel:
    def __init__(self, root, detection_window):
        self.root = root
        self.detection_window = detection_window

        self.root.geometry("300x150+1000+100")
        self.root.title("YOLOv8 Console")

        self.label = tk.Label(self.root, text="YOLOv8 Control Panel", font=("Arial", 14))
        self.label.pack(pady=10)

        self.pause_button = tk.Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(pady=5)

        self.resume_button = tk.Button(self.root, text="Resume", command=self.toggle_pause)
        self.resume_button.pack(pady=5)

        self.exit_button = tk.Button(self.root, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=5)

    def toggle_pause(self):
        self.detection_window.toggle_pause()

    def exit_app(self):
        self.detection_window.stop()
        self.root.quit()

if __name__ == "__main__":
    model = YOLO("yolov8n.pt")

    detection_root = tk.Tk()
    detection_window = DetectionWindow(detection_root, model)

    control_root = tk.Toplevel()
    control_panel = ControlPanel(control_root, detection_window)

    tk.mainloop()
