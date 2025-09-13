import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import time
import os
from datetime import datetime
import numpy as np
try:
    import mediapipe as mp
    use_hand_detection = True
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.9, min_tracking_confidence=0.85)
    mp_drawing = mp.solutions.drawing_utils
except ImportError:
    use_hand_detection = False
    messagebox.showwarning("Peringatan", "Modul MediaPipe tidak ditemukan. Deteksi tangan dinonaktifkan.")
class CameraApp:
    def __init__(self, window):
        self.window = window
        self.window.title("­ЪДа HoloCam Studio - by FadelShafwanMaliki")
        self.window.geometry("1280x720")
        self.window.configure(bg="#0f172a")
        self.window.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=12, background="#3b82f6", foreground="#ffffff", borderwidth=0)
        self.style.map("TButton", background=[('active', '#2563eb')])
        self.style.configure("TLabel", font=("Segoe UI", 12), background="#0f172a", foreground="#e2e8f0")
        self.style.configure("TFrame", background="#0f172a")
        self.style.configure("Toggle.TButton", font=("Segoe UI", 10, "bold"), padding=8, background="#22c55e", foreground="#ffffff", borderwidth=0)
        self.style.map("Toggle.TButton", background=[('active', '#16a34a')])
        self.style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=8, background="#ef4444", foreground="#ffffff", borderwidth=0)
        self.style.map("Danger.TButton", background=[('active', '#dc2626')])
        self.style.configure("TScale", background="#0f172a", troughcolor="#1e293b", sliderlength=20, sliderthickness=15)
        self.container = ttk.Frame(self.window)
        self.container.pack(fill="both", expand=True)
        self.menu_frame = ttk.Frame(self.container)
        self.menu_frame.pack(fill="both", expand=True)
        self.title_label = ttk.Label(self.menu_frame, text="HoloCam Studio", font=("Segoe UI", 34, "bold"), foreground="#60a5fa")
        self.title_label.pack(pady=50)
        self.start_button = ttk.Button(self.menu_frame, text="Mulai Menggambar", command=self.show_camera_page)
        self.start_button.pack(pady=20, ipadx=20, ipady=10)
        self.footer = ttk.Label(self.menu_frame, text="Dibuat oleh FadelShafwanMaliki | Versi 4.4", font=("Segoe UI", 10, "italic"), foreground="#94a3b8")
        self.footer.pack(side="bottom", pady=20)
        self.camera_frame = ttk.Frame(self.container)
        self.video_container = ttk.Frame(self.camera_frame, style="TFrame")
        self.video_container.pack(pady=20, expand=True, fill="both")
        self.video_frame = tk.Label(self.video_container, bg="#1e293b", bd=0, relief="flat")
        self.video_frame.pack(expand=True)
        self.video_footer = ttk.Label(self.video_container, text="HoloCam Studio - by FadelShafwanMaliki", font=("Segoe UI", 10, "italic"), foreground="#94a3b8")
        self.video_footer.pack(side="bottom", pady=5)
        self.control_frame = ttk.Frame(self.camera_frame, style="TFrame")
        self.control_frame.pack(fill="x", pady=10, padx=20)
        self.back_button = ttk.Button(self.control_frame, text="Kembali ke Menu", command=self.show_menu_page)
        self.back_button.pack(side="left", padx=10)
        self.snapshot_button = ttk.Button(self.control_frame, text="Ambil Snapshot", command=self.take_snapshot, state=tk.DISABLED)
        self.snapshot_button.pack(side="left", padx=10)
        self.draw_toggle = ttk.Button(self.control_frame, text="Aktifkan Menggambar", command=self.toggle_drawing, style="Toggle.TButton")
        self.draw_toggle.pack(side="left", padx=10)
        self.clear_button = ttk.Button(self.control_frame, text="Hapus Gambar", command=self.clear_canvas, style="Danger.TButton", state=tk.DISABLED)
        self.clear_button.pack(side="left", padx=10)
        self.thickness_label = ttk.Label(self.control_frame, text="Ketebalan Garis:")
        self.thickness_label.pack(side="left", padx=10)
        self.thickness_scale = ttk.Scale(self.control_frame, from_=1, to_=10, orient=tk.HORIZONTAL, command=self.update_thickness)
        self.thickness_scale.set(3)
        self.thickness_scale.pack(side="left", padx=5)
        self.opacity_label = ttk.Label(self.control_frame, text="Ketebalan Warna:")
        self.opacity_label.pack(side="left", padx=10)
        self.opacity_scale = ttk.Scale(self.control_frame, from_=0.1, to_=1.0, orient=tk.HORIZONTAL, command=self.update_opacity)
        self.opacity_scale.set(1.0)
        self.opacity_scale.pack(side="left", padx=5)
        self.color_label = ttk.Label(self.control_frame, text="Warna:")
        self.color_label.pack(side="left", padx=10)
        self.color_var = tk.StringVar(value="Cyan")
        self.color_menu = ttk.OptionMenu(self.control_frame, self.color_var, "Cyan", "Cyan", "Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Pink", "White", "Black", command=self.update_color)
        self.color_menu.pack(side="left", padx=5)
        self.status_label = ttk.Label(self.control_frame, text="Status: Kamera Mati")
        self.status_label.pack(side="left", padx=10)
        self.hand_info_label = ttk.Label(self.control_frame, text="Koordinat Jari: - | Gestur: -")
        self.hand_info_label.pack(side="right", padx=10)
        self.drawing = False
        self.canvas = None
        self.last_pos = None
        self.line_thickness = 3
        self.line_opacity = 1.0
        self.line_color = (0, 255, 255)  # Default: Cyan
        self.color_map = {
            "Cyan": (0, 255, 255),
            "Red": (0, 0, 255),
            "Green": (0, 255, 0),
            "Blue": (255, 0, 0),
            "Yellow": (0, 255, 255),
            "Purple": (128, 0, 128),
            "Orange": (0, 165, 255),
            "Pink": (203, 192, 255),
            "White": (255, 255, 255),
            "Black": (0, 0, 0)
        }
        self.snapshot_dir = "snapshots"
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        self.camera_running = False
        self.thread = None
        self.frame_size = None
        self.is_thumb_open = False
    def update_thickness(self, value):
        self.line_thickness = int(float(value))
    def update_opacity(self, value):
        self.line_opacity = float(value)
    def update_color(self, color):
        self.line_color = self.color_map[color]
    def show_menu_page(self):
        self.stop_camera()
        self.camera_frame.pack_forget()
        self.menu_frame.pack(fill="both", expand=True)
    def show_camera_page(self):
        self.menu_frame.pack_forget()
        self.camera_frame.pack(fill="both", expand=True)
        self.start_camera()
    def start_camera(self):
        try:
            self.camera_running = True
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Kamera tidak dapat diakses.")
            self.frame_size = (
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            self.snapshot_button.config(state=tk.NORMAL)
            self.draw_toggle.config(state=tk.NORMAL)
            self.clear_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Kamera Menyala")
            self.thread = threading.Thread(target=self.update_frame, daemon=True)
            self.thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuka kamera: {str(e)}")
            self.show_menu_page()
    def stop_camera(self):
        self.camera_running = False
        if hasattr(self, 'cap'):
            self.cap.release()
        self.snapshot_button.config(state=tk.DISABLED)
        self.draw_toggle.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Kamera Mati")
        self.hand_info_label.config(text="Koordinat Jari: - | Gestur: -")
        self.video_frame.config(image='')
        self.drawing = False
        self.canvas = None
        self.last_pos = None
        self.is_thumb_open = False
    def toggle_drawing(self):
        self.drawing = not self.drawing
        self.draw_toggle.config(text="Nonaktifkan Menggambar" if self.drawing else "Aktifkan Menggambar")
        if self.drawing and self.camera_running:
            self.canvas = np.zeros((self.frame_size[1], self.frame_size[0], 3), dtype=np.uint8)
            self.clear_button.config(state=tk.NORMAL)
        else:
            self.clear_button.config(state=tk.DISABLED)
    def clear_canvas(self):
        if self.canvas is not None:
            self.canvas = np.zeros((self.frame_size[1], self.frame_size[0], 3), dtype=np.uint8)
            messagebox.showinfo("Info", "Kanvas telah dihapus.")
    def take_snapshot(self):
        if hasattr(self, 'cap') and self.camera_running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                if self.drawing and self.canvas is not None:
                    frame = cv2.addWeighted(frame, 0.7, self.canvas, self.line_opacity, 0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.snapshot_dir, f"holocam_{timestamp}.png")
                cv2.imwrite(filename, frame)
                messagebox.showinfo("Sukses", f"Snapshot tersimpan sebagai {filename}")
    def is_thumb_extended(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]  # Ujung jempol
        thumb_mcp = hand_landmarks.landmark[2]  # Pangkal jempol
        index_tip = hand_landmarks.landmark[8]  # Ujung jari telunjuk
        wrist = hand_landmarks.landmark[0]       # Pergelangan tangan
        distance_thumb_wrist = np.sqrt(
            (thumb_tip.x - wrist.x) ** 2 +
            (thumb_tip.y - wrist.y) ** 2
        )
        distance_thumb_mcp = np.sqrt(
            (thumb_tip.x - thumb_mcp.x) ** 2 +
            (thumb_tip.y - thumb_mcp.y) ** 2
        )
        distance_index_wrist = np.sqrt(
            (index_tip.x - wrist.x) ** 2 +
            (index_tip.y - wrist.y) ** 2
        )
        return distance_thumb_wrist > distance_index_wrist * 0.5 or distance_thumb_mcp > distance_index_wrist * 0.3
    def update_frame(self):
        while self.camera_running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, self.frame_size)
            if use_hand_detection:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        index_finger = hand_landmarks.landmark[8]  # Landmark jari telunjuk
                        x = int(index_finger.x * frame.shape[1])
                        y = int(index_finger.y * frame.shape[0])
                        self.is_thumb_open = self.is_thumb_extended(hand_landmarks)
                        mp_drawing.draw_landmarks(
                            frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=4),
                            mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2)
                        )
                        status_text = "Menggambar: Aktif" if self.drawing and not self.is_thumb_open else "Menggambar: Nonaktif"
                        status_color = (0, 255, 0) if self.drawing and not self.is_thumb_open else (0, 0, 255)
                        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                        self.hand_info_label.config(text=f"Koordinat Jari: ({x}, {y}) | Gestur: {'Jempol Terbuka' if self.is_thumb_open else 'Jempol Tertutup'}")
                        if self.drawing and self.canvas is not None and not self.is_thumb_open:
                            if self.last_pos is not None:
                                temp_canvas = np.zeros_like(self.canvas)
                                cv2.line(temp_canvas, self.last_pos, (x, y), self.line_color, self.line_thickness)
                                cv2.circle(temp_canvas, (x, y), self.line_thickness // 2, self.line_color, -1)
                                self.canvas = cv2.addWeighted(self.canvas, 1.0, temp_canvas, self.line_opacity, 0)
                            self.last_pos = (x, y)
                        else:
                            self.last_pos = None
                else:
                    self.last_pos = None
                    self.hand_info_label.config(text="Koordinat Jari: - | Gestur: -")
            if self.drawing and self.canvas is not None:
                glow = cv2.GaussianBlur(self.canvas, (21, 21), 0)
                frame = cv2.addWeighted(frame, 0.8, glow, self.line_opacity, 0)
            cv2.putText(frame, "HoloCam Studio - by Rafashacode.id", (10, self.frame_size[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_frame.imgtk = imgtk
            self.video_frame.configure(image=imgtk)
            time.sleep(0.005)  # Kurangi latensi untuk responsivitas lebih tinggi
        if hasattr(self, 'cap'):
            self.cap.release()
if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()
