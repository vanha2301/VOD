import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import shutil
import os
import threading
import asyncio
import nest_asyncio
import re
import edge_tts
import time

# Apply nest_asyncio để chạy asyncio trong môi trường có loop sẵn (như Tkinter)
nest_asyncio.apply()

# ==============================================================================
# ⚙️ CẤU HÌNH MẶC ĐỊNH
# ==============================================================================
GIONG_DOC_DEFAULT = "vi-VN-HoaiMyNeural"
MAX_SPEED_INCREASE = 100 
TEMP_FOLDER = "temp_processing"

class AutoDubberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TDTU Auto Dubber - AI TTS & Video Mixer v3.1 (Fix Path)")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        # --- Variables ---
        self.video_path = tk.StringVar()
        self.script_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng...")
        
        # Tìm FFmpeg ngay khi khởi động
        self.ffmpeg_path = self._find_tool("ffmpeg")
        self.ffprobe_path = self._find_tool("ffprobe")

        # --- UI Layout ---
        self.create_widgets()

        if not self.ffmpeg_path:
            messagebox.showerror("Lỗi Môi Trường", "Không tìm thấy FFmpeg! Vui lòng cài đặt FFmpeg và thêm vào PATH.")

    def _find_tool(self, tool_name):
        path = shutil.which(tool_name)
        if path: return path
        possible_paths = [
            os.path.expandvars(rf"%LOCALAPPDATA%\Microsoft\WinGet\Links\{tool_name}.exe"),
            rf"C:\ffmpeg\bin\{tool_name}.exe",
            rf"D:\ffmpeg\bin\{tool_name}.exe"
        ]
        for p in possible_paths:
            if os.path.exists(p): return p
        return None

    def create_widgets(self):
        # Header
        lbl_title = tk.Label(self.root, text="AUTOMATIC AI DUBBING TOOL", font=("Segoe UI", 16, "bold"), fg="#c0392b")
        lbl_title.pack(pady=10)

        # 1. Chọn Video Gốc
        grp_video = tk.LabelFrame(self.root, text="1. Video Gốc (Background)", padx=10, pady=5)
        grp_video.pack(fill="x", padx=10, pady=5)
        tk.Entry(grp_video, textvariable=self.video_path, width=70).pack(side="left", padx=5)
        tk.Button(grp_video, text="📂 Video", command=self.browse_video).pack(side="left")

        # 2. Chọn Script
        grp_script = tk.LabelFrame(self.root, text="2. File Kịch bản (.txt - Format: [start->end] Text)", padx=10, pady=5)
        grp_script.pack(fill="x", padx=10, pady=5)
        tk.Entry(grp_script, textvariable=self.script_path, width=70).pack(side="left", padx=5)
        tk.Button(grp_script, text="📄 Script", command=self.browse_script).pack(side="left")

        # 3. Mixer (Volume)
        grp_vol = tk.LabelFrame(self.root, text="3. Mixer Control", padx=10, pady=5)
        grp_vol.pack(fill="x", padx=10, pady=5)

        # Grid layout cho mixer
        tk.Label(grp_vol, text="Volume Video Gốc:").grid(row=0, column=0, sticky="w", padx=5)
        self.vol_video_slider = tk.Scale(grp_vol, from_=0, to=200, orient="horizontal", length=200)
        self.vol_video_slider.set(80) # Giảm nhạc nền xuống
        self.vol_video_slider.grid(row=0, column=1)

        tk.Label(grp_vol, text="Volume Giọng AI:").grid(row=0, column=2, sticky="w", padx=5)
        self.vol_ai_slider = tk.Scale(grp_vol, from_=0, to=200, orient="horizontal", length=200)
        self.vol_ai_slider.set(150) # Tăng giọng đọc lên
        self.vol_ai_slider.grid(row=0, column=3)

        # 4. Console Log (Để dân Dev nhìn cho chuyên nghiệp)
        grp_log = tk.LabelFrame(self.root, text="Process Logs", padx=10, pady=5)
        grp_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_area = scrolledtext.ScrolledText(grp_log, height=10, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

        # 5. Action Button
        self.btn_run = tk.Button(self.root, text="🚀 BẮT ĐẦU XỬ LÝ (RENDER)", command=self.start_processing_flow, 
                                 bg="#2ecc71", fg="white", font=("Segoe UI", 12, "bold"), height=2)
        self.btn_run.pack(fill="x", padx=20, pady=10)

        # Status Bar
        self.lbl_status = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    # --- File Dialogs ---
    def browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.avi")])
        if path: self.video_path.set(path)

    def browse_script(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path: self.script_path.set(path)

    # --- Core Logic ---
    def start_processing_flow(self):
        # 1. Validate
        if not self.video_path.get() or not self.script_path.get():
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn Video và Script!")
            return
        
        # 2. Save location
        output_path = filedialog.asksaveasfilename(
            title="Lưu video kết quả", defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")], initialfile="Video_Final_AI_Dubbed.mp4"
        )
        if not output_path: return

        # 3. Start Thread
        self.btn_run.config(state="disabled", text="⏳ Đang xử lý... Vui lòng đợi")
        threading.Thread(target=self.process_pipeline, args=(output_path,), daemon=True).start()

    def process_pipeline(self, output_path):
        try:
            self.log("=== BẮT ĐẦU PIPELINE ===")
            
            # B1: Chuẩn bị thư mục temp (Tạo đường dẫn tuyệt đối ngay từ đầu)
            abs_temp_folder = os.path.abspath(TEMP_FOLDER)
            if os.path.exists(abs_temp_folder): shutil.rmtree(abs_temp_folder, ignore_errors=True)
            os.makedirs(abs_temp_folder)
            self.log(f"Temp folder: {abs_temp_folder}")

            # B2: Đọc script
            self.status_var.set("Đang đọc kịch bản...")
            subtitles = self.read_script_file(self.script_path.get())
            if not subtitles:
                raise Exception("Không đọc được script hoặc script rỗng!")
            self.log(f"Đã tìm thấy {len(subtitles)} câu thoại.")

            # B3: Tạo Audio TTS hoàn chỉnh
            self.status_var.set("Đang sinh giọng đọc AI...")
            full_audio_path = os.path.join(abs_temp_folder, "full_tts_track.mp3").replace("\\", "/")
            self.create_tts_track(subtitles, full_audio_path, abs_temp_folder)

            # B4: Trộn Video + Audio TTS
            self.status_var.set("Đang render video cuối cùng...")
            # Kiểm tra xem file audio đã được tạo chưa trước khi mix
            if not os.path.exists(full_audio_path):
                 raise Exception(f"Lỗi nghiêm trọng: Không tìm thấy file audio đã sinh ra tại {full_audio_path}")

            self.mix_video_audio(self.video_path.get(), full_audio_path, output_path)

            self.status_var.set("Hoàn tất!")
            self.log(f"=== XONG! File lưu tại: {output_path} ===")
            messagebox.showinfo("Thành công", "Đã xử lý xong video!")
            # Mở file hoặc thư mục chứa file
            if os.name == 'nt':
                 try:
                    os.startfile(output_path)
                 except: pass

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            # Cleanup (Có thể comment dòng này nếu muốn debug file trong temp)
            if os.path.exists(TEMP_FOLDER): shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
            self.root.after(0, lambda: self.btn_run.config(state="normal", text="🚀 BẮT ĐẦU XỬ LÝ (RENDER)"))

    # --- TTS GENERATOR LOGIC ---
    def read_script_file(self, file_path):
        data = []
        pattern = re.compile(r"\[([\d\.]+)s\s*->\s*([\d\.]+)s\]\s*(.*)")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue 
                match = pattern.match(line)
                if match:
                    try:
                        data.append({
                            'start': float(match.group(1)), 
                            'end': float(match.group(2)), 
                            'text': match.group(3).strip()
                        })
                    except ValueError: pass
        data.sort(key=lambda x: x['start'])
        return data

    def _get_audio_duration(self, file_path):
        try:
            cmd = [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
            # Thêm startupinfo để ẩn cửa sổ console đen xì khi chạy
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            return float(result.stdout.strip())
        except: return 0.0

    def _create_silent_file(self, filename, duration=600):
        # Tạo file im lặng, dùng đường dẫn tuyệt đối
        cmd = [self.ffmpeg_path, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(duration), "-c:a", "libmp3lame", filename]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)

    async def _generate_clip(self, text, filename, rate_str="+0%"):
        communicate = edge_tts.Communicate(text, GIONG_DOC_DEFAULT, rate=rate_str, volume="+0%")
        await communicate.save(filename)

    def create_tts_track(self, subtitles, output_file, temp_folder):
        # Sử dụng đường dẫn tuyệt đối cho file silence
        silent_file = os.path.join(temp_folder, "silence.mp3").replace("\\", "/")
        self._create_silent_file(silent_file)

        concat_list_path = os.path.join(temp_folder, "mylist.txt").replace("\\", "/")
        current_cursor = 0.0
        
        with open(concat_list_path, "w", encoding='utf-8') as f:
            for i, item in enumerate(subtitles):
                slot_duration = item['end'] - item['start']
                # Sử dụng đường dẫn tuyệt đối cho từng clip nhỏ
                temp_filename = os.path.join(temp_folder, f"clip_{i}.mp3").replace("\\", "/")
                
                # Gap Before
                gap_before = item['start'] - current_cursor
                if gap_before > 0.01:
                    f.write(f"file '{silent_file}'\n")
                    f.write(f"inpoint 0\n")
                    f.write(f"outpoint {gap_before}\n")
                    current_cursor = item['start']

                # Generate Audio
                if item['text']:
                    self.log(f"Processing: {item['text'][:30]}...")
                    asyncio.run(self._generate_clip(item['text'], temp_filename))
                    actual_duration = self._get_audio_duration(temp_filename)

                    # Time Stretching logic
                    if actual_duration > slot_duration:
                        ratio = actual_duration / slot_duration
                        increase_percent = int((ratio - 1) * 100) + 10
                        increase_percent = min(increase_percent, MAX_SPEED_INCREASE)
                        self.log(f"  -> Tăng tốc +{increase_percent}% để khớp")
                        asyncio.run(self._generate_clip(item['text'], temp_filename, rate_str=f"+{increase_percent}%"))
                        actual_duration = self._get_audio_duration(temp_filename)
                    
                    # Quan trọng: Ghi đường dẫn tuyệt đối vào file list
                    f.write(f"file '{temp_filename}'\n")
                
                # Padding After (nếu nói xong sớm)
                remaining = slot_duration - actual_duration
                if remaining > 0.01:
                    f.write(f"file '{silent_file}'\n")
                    f.write(f"inpoint 0\n")
                    f.write(f"outpoint {remaining}\n")
                
                current_cursor = item['end']

        # Concat Audio segments
        self.log("Đang ghép nối các đoạn audio...")
        cmd = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", output_file]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Thêm check=True để bắt lỗi ngay nếu ffmpeg concat thất bại
        # Bỏ stderr=subprocess.DEVNULL để nếu lỗi thì in ra log
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
        
        if result.returncode != 0:
            self.log(f"FFmpeg Concat Error:\n{result.stderr}")
            raise Exception("Lỗi khi ghép nối audio (FFmpeg concat failed)")

    # --- MIXER LOGIC ---
    def mix_video_audio(self, video_in, audio_in, video_out):
        vol_v = self.vol_video_slider.get() / 100.0
        vol_a = self.vol_ai_slider.get() / 100.0

        filter_complex = (
            f"[0:a]volume={vol_v}[original];"
            f"[1:a]volume={vol_a}[new];"
            f"[original][new]amix=inputs=2:duration=first:dropout_transition=0[aout]" 
            # duration=first: lấy độ dài theo video gốc
        )

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_in,
            "-i", audio_in,
            "-filter_complex", filter_complex,
            "-map", "0:v:0",    
            "-map", "[aout]",   
            "-c:v", "copy",     # Copy video stream cho nhanh
            "-c:a", "aac",
            "-shortest",       
            video_out
        ]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Bắt lỗi khi mix
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
        if result.returncode != 0:
             self.log(f"FFmpeg Mix Error:\n{result.stderr}")
             raise Exception("Lỗi khi trộn Video (FFmpeg mix failed)")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AutoDubberApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Critical Error: {e}")