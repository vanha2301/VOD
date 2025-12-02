import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import shutil
import os
import threading

class VideoMixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tool Trộn Video & Audio - TDTU Student Edition v2.0")
        self.root.geometry("550x500")
        self.root.resizable(False, False)

        # --- Variables ---
        self.video_path = tk.StringVar()
        self.audio_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng...")

        # --- UI Layout ---
        self.create_widgets()

    def create_widgets(self):
        # 1. Chọn Video Gốc
        grp_video = tk.LabelFrame(self.root, text="1. Video Gốc (Hình ảnh + Âm thanh nền)", padx=10, pady=10)
        grp_video.pack(fill="x", padx=10, pady=5)
        
        tk.Entry(grp_video, textvariable=self.video_path, width=55).pack(side="left", padx=5)
        tk.Button(grp_video, text="📂 Chọn File", command=self.browse_video).pack(side="left")

        # 2. Chọn Audio Thuyết Minh
        grp_audio = tk.LabelFrame(self.root, text="2. Audio Thuyết Minh (MP3/WAV)", padx=10, pady=10)
        grp_audio.pack(fill="x", padx=10, pady=5)
        
        tk.Entry(grp_audio, textvariable=self.audio_path, width=55).pack(side="left", padx=5)
        tk.Button(grp_audio, text="🎵 Chọn File", command=self.browse_audio).pack(side="left")

        # 3. Chỉnh Âm Lượng (Sliders)
        grp_vol = tk.LabelFrame(self.root, text="3. Mixer (Cân bằng âm lượng)", padx=10, pady=10)
        grp_vol.pack(fill="x", padx=10, pady=5)

        # Slider Video Gốc
        tk.Label(grp_vol, text="Âm lượng Video gốc:").grid(row=0, column=0, sticky="w", padx=5)
        self.vol_video_slider = tk.Scale(grp_vol, from_=0, to=200, orient="horizontal", length=300)
        self.vol_video_slider.set(100) # Mặc định 100%
        self.vol_video_slider.grid(row=0, column=1)
        tk.Label(grp_vol, text="%").grid(row=0, column=2)

        # Slider Audio Mới
        tk.Label(grp_vol, text="Âm lượng Audio mới:").grid(row=1, column=0, sticky="w", padx=5)
        self.vol_audio_slider = tk.Scale(grp_vol, from_=0, to=200, orient="horizontal", length=300)
        self.vol_audio_slider.set(100) # Mặc định 100%
        self.vol_audio_slider.grid(row=1, column=1)
        tk.Label(grp_vol, text="%").grid(row=1, column=2)

        # 4. Nút Xử lý
        # Lưu ý: Nút này sẽ gọi hàm ask_save_path trước, sau đó mới chạy thread
        self.btn_run = tk.Button(self.root, text="💾 LƯU FILE & XUẤT VIDEO", command=self.start_processing_flow, 
                                 bg="#007bff", fg="white", font=("Segoe UI", 11, "bold"), height=2)
        self.btn_run.pack(fill="x", padx=20, pady=20)

        # Status Bar
        self.lbl_status = tk.Label(self.root, textvariable=self.status_var, fg="#666", relief=tk.SUNKEN, anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

    # --- Functions ---
    def browse_video(self):
        path = filedialog.askopenfilename(title="Chọn Video Gốc", filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")])
        if path: self.video_path.set(path)

    def browse_audio(self):
        path = filedialog.askopenfilename(title="Chọn Audio Thuyết Minh", filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.aac")])
        if path: self.audio_path.set(path)

    def start_processing_flow(self):
        # 1. Validate Input
        if not self.video_path.get() or not self.audio_path.get():
            messagebox.showwarning("Thiếu file", "Vui lòng chọn đủ Video và Audio trước!")
            return

        # 2. Hỏi nơi lưu file (Save As Dialog)
        output_path = filedialog.asksaveasfilename(
            title="Đặt tên file video kết quả",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")],
            initialfile="Video_Mixed_Output.mp4"
        )

        # Nếu người dùng bấm Cancel (không chọn nơi lưu) -> Dừng lại
        if not output_path:
            return

        # 3. Bắt đầu Thread xử lý
        self.btn_run.config(state="disabled", text="⏳ Đang render... (Đừng tắt tool)")
        self.status_var.set("Đang khởi động FFmpeg...")
        
        # Truyền output_path vào thread
        thread = threading.Thread(target=self.process_video, args=(output_path,), daemon=True)
        thread.start()

    def process_video(self, output_file):
        video_in = self.video_path.get()
        audio_in = self.audio_path.get()

        # Lấy giá trị Volume từ Slider
        vol_v = self.vol_video_slider.get() / 100.0
        vol_a = self.vol_audio_slider.get() / 100.0

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
             # Fallback cho Windows nếu cài thủ công
            possible_paths = [r"C:\ffmpeg\bin\ffmpeg.exe", r"D:\ffmpeg\bin\ffmpeg.exe"]
            for p in possible_paths:
                if os.path.exists(p):
                    ffmpeg_path = p
                    break
        
        if not ffmpeg_path:
            self.root.after(0, lambda: self.update_status("❌ Lỗi: Không tìm thấy FFmpeg trong máy!", True))
            return

        # Filter Complex: Chỉnh volume -> Mix -> Cắt ngắn nhất
        filter_complex = (
            f"[0:a]volume={vol_v}[original];"
            f"[1:a]volume={vol_a}[new];"
            f"[original][new]amix=inputs=2:duration=shortest:dropout_transition=0[aout]"
        )

        cmd = [
            ffmpeg_path, "-y",
            "-i", video_in,
            "-i", audio_in,
            "-filter_complex", filter_complex,
            "-map", "0:v:0",    
            "-map", "[aout]",   
            "-c:v", "copy",    # Copy stream video để render siêu nhanh
            "-c:a", "aac",
            "-shortest",       
            output_file
        ]

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Chạy lệnh
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            
            # Update UI từ main thread (thông qua lambda hoặc after)
            self.root.after(0, lambda: self.on_success(output_file))

        except subprocess.CalledProcessError as e:
            self.root.after(0, lambda: self.update_status(f"❌ Lỗi render: {e}", True))
        except Exception as ex:
            self.root.after(0, lambda: self.update_status(f"❌ Lỗi không xác định: {ex}", True))
        finally:
            self.root.after(0, self.reset_button)

    def on_success(self, filepath):
        self.update_status(f"✅ Xong! File lưu tại: {filepath}")
        if messagebox.askyesno("Thành công", "Đã trộn xong video!\nBạn có muốn mở file ngay không?"):
            if os.name == 'nt':
                os.startfile(filepath)

    def update_status(self, text, is_error=False):
        self.status_var.set(text)
        if is_error:
            messagebox.showerror("Lỗi", text)

    def reset_button(self):
        self.btn_run.config(state="normal", text="💾 LƯU FILE & XUẤT VIDEO")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        # Set icon nếu có (bỏ qua nếu không có file .ico)
        # root.iconbitmap("icon.ico") 
        app = VideoMixerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Lỗi khởi động: {e}")