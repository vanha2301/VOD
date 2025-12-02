import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.ttk as ttk
import subprocess
import shutil
import os
import threading
import asyncio
import nest_asyncio
import re
import edge_tts
import time

nest_asyncio.apply()

# ==============================================================================
# ⚙️ CẤU HÌNH
# ==============================================================================
GIONG_DOC_DEFAULT = "vi-VN-HoaiMyNeural"
TEMP_FOLDER = "temp_processing"
# Đã bỏ giới hạn MAX_SAFE_SPEED theo yêu cầu của bạn

class AutoDubberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto AI Dubbing Tool v2.0")
        self.root.geometry("750x700")
        self.root.resizable(False, False)

        # --- Variables ---
        self.video_path = tk.StringVar()
        self.script_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng...")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        self.ffmpeg_path = self._find_tool("ffmpeg")
        self.ffprobe_path = self._find_tool("ffprobe")

        # --- UI Layout ---
        self.create_widgets()

        if not self.ffmpeg_path:
            messagebox.showerror("Lỗi", "Chưa cài đặt FFmpeg!")

    def _find_tool(self, tool_name):
        path = shutil.which(tool_name)
        if path: return path
        possible_paths = [
            rf"C:\ffmpeg\bin\{tool_name}.exe",
            rf"D:\ffmpeg\bin\{tool_name}.exe",
            os.path.expandvars(rf"%LOCALAPPDATA%\Microsoft\WinGet\Links\{tool_name}.exe")
        ]
        for p in possible_paths:
            if os.path.exists(p): return p
        return None

    def create_widgets(self):
        # Header
        lbl_title = tk.Label(self.root, text="AUTOMATIC AI DUBBING TOOL v2.0", font=("Segoe UI", 16, "bold"), fg="#c0392b")
        lbl_title.pack(pady=10)

        # 1. Video Input
        grp_video = tk.LabelFrame(self.root, text="1. Video Gốc", padx=10, pady=5)
        grp_video.pack(fill="x", padx=10, pady=5)
        tk.Entry(grp_video, textvariable=self.video_path, width=75).pack(side="left", padx=5)
        tk.Button(grp_video, text="📂 Video", command=self.browse_video).pack(side="left")

        # 2. Script Input
        grp_script = tk.LabelFrame(self.root, text="2. File Kịch bản (.txt)", padx=10, pady=5)
        grp_script.pack(fill="x", padx=10, pady=5)
        tk.Entry(grp_script, textvariable=self.script_path, width=75).pack(side="left", padx=5)
        tk.Button(grp_script, text="📄 Script", command=self.browse_script).pack(side="left")

        # 3. Mixer
        grp_vol = tk.LabelFrame(self.root, text="3. Mixer Control", padx=10, pady=5)
        grp_vol.pack(fill="x", padx=10, pady=5)
        tk.Label(grp_vol, text="Vol Video:").grid(row=0, column=0, padx=5)
        self.vol_video_slider = tk.Scale(grp_vol, from_=0, to=200, orient="horizontal", length=200)
        self.vol_video_slider.set(20)
        self.vol_video_slider.grid(row=0, column=1)
        
        tk.Label(grp_vol, text="Vol AI:").grid(row=0, column=2, padx=5)
        self.vol_ai_slider = tk.Scale(grp_vol, from_=0, to=200, orient="horizontal", length=200)
        self.vol_ai_slider.set(150)
        self.vol_ai_slider.grid(row=0, column=3)

        # 4. Progress Bar
        grp_progress = tk.Frame(self.root)
        grp_progress.pack(fill="x", padx=20, pady=5)
        tk.Label(grp_progress, text="Tiến độ xử lý:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.progress_bar = ttk.Progressbar(grp_progress, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill="x", pady=2)
        
        self.lbl_percent = tk.Label(grp_progress, text="0%", fg="blue")
        self.lbl_percent.pack(anchor="e")

        # 5. Logs
        grp_log = tk.LabelFrame(self.root, text="Logs", padx=10, pady=5)
        grp_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_area = scrolledtext.ScrolledText(grp_log, height=8, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

        # 6. Button Run
        self.btn_run = tk.Button(self.root, text="🚀 BẮT ĐẦU XỬ LÝ", command=self.start_processing_flow, 
                                 bg="#2ecc71", fg="white", font=("Segoe UI", 12, "bold"), height=2)
        self.btn_run.pack(fill="x", padx=20, pady=10)

        # Status Bar
        self.lbl_status = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", bg="#ecf0f1")
        self.lbl_status.pack(side="bottom", fill="x")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def update_progress(self, percent, status_text=None):
        self.progress_var.set(percent)
        self.lbl_percent.config(text=f"{int(percent)}%")
        if status_text:
            self.status_var.set(status_text)
        self.root.update_idletasks()

    def browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv *.avi")])
        if path: self.video_path.set(path)

    def browse_script(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path: self.script_path.set(path)

    def start_processing_flow(self):
        if not self.video_path.get() or not self.script_path.get():
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Video và Script!")
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")], initialfile="Dubbed_Video_Strict.mp4")
        if not output_path: return

        self.btn_run.config(state="disabled")
        self.progress_var.set(0)
        threading.Thread(target=self.process_pipeline, args=(output_path,), daemon=True).start()

    def process_pipeline(self, output_path):
        try:
            self.log("=== BẮT ĐẦU PIPELINE (Strict Mode) ===")
            abs_temp = os.path.abspath(TEMP_FOLDER)
            if os.path.exists(abs_temp): shutil.rmtree(abs_temp)
            os.makedirs(abs_temp)

            # 1. Đọc Script
            self.update_progress(5, "Đang đọc kịch bản...")
            subtitles = self.read_script_file(self.script_path.get())
            if not subtitles: raise Exception("Script rỗng!")
            self.log(f"Đã nạp {len(subtitles)} câu thoại.")

            # 2. Sinh Audio
            full_audio_path = os.path.join(abs_temp, "full_tts.mp3").replace("\\", "/")
            self.create_tts_track(subtitles, full_audio_path, abs_temp)

            # 3. Mix Video
            self.update_progress(80, "Đang render video...")
            self.mix_video_audio(self.video_path.get(), full_audio_path, output_path)

            # 4. Finish
            self.update_progress(100, "Xong!")
            self.log(f"Output saved: {output_path}")
            messagebox.showinfo("Thành công", "Xử lý video hoàn tất!")
            if os.name == 'nt': 
                try: os.startfile(output_path)
                except: pass

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            if os.path.exists(TEMP_FOLDER): shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
            self.root.after(0, lambda: self.btn_run.config(state="normal"))

    def read_script_file(self, file_path):
        data = []
        pattern = re.compile(r"\[([\d\.]+)s\s*->\s*([\d\.]+)s\]\s*(.*)")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    data.append({'start': float(match.group(1)), 'end': float(match.group(2)), 'text': match.group(3).strip()})
        data.sort(key=lambda x: x['start'])
        return data

    async def _generate_clip(self, text, filename, rate_str="+0%"):
        communicate = edge_tts.Communicate(text, GIONG_DOC_DEFAULT, rate=rate_str, volume="+0%")
        await communicate.save(filename)

    def _get_audio_duration(self, file_path):
        try:
            cmd = [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            return float(res.stdout.strip())
        except: return 0.0

    def _create_silent_file(self, filename, duration):
        cmd = [self.ffmpeg_path, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(duration), "-c:a", "libmp3lame", filename]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)

    def create_tts_track(self, subtitles, output_file, temp_folder):
        silent_file = os.path.join(temp_folder, "silence.mp3").replace("\\", "/")
        self._create_silent_file(silent_file, 600)

        concat_list_path = os.path.join(temp_folder, "mylist.txt").replace("\\", "/")
        current_cursor = 0.0
        total_subs = len(subtitles)
        
        with open(concat_list_path, "w", encoding='utf-8') as f:
            for i, item in enumerate(subtitles):
                percent = 5 + (i / total_subs) * 75
                self.update_progress(percent, f"Đang xử lý câu {i+1}/{total_subs}...")

                slot_duration = item['end'] - item['start']
                temp_filename = os.path.join(temp_folder, f"clip_{i}.mp3").replace("\\", "/")
                
                # Tính khoảng lặng trước câu nói (nếu có)
                gap_before = item['start'] - current_cursor
                if gap_before > 0.01:
                    f.write(f"file '{silent_file}'\n")
                    f.write(f"inpoint 0\n")
                    f.write(f"outpoint {gap_before}\n")
                    current_cursor = item['start'] # Cập nhật cursor về đúng điểm bắt đầu

                if item['text']:
                    # 1. Sinh lần đầu để lấy độ dài thực tế
                    asyncio.run(self._generate_clip(item['text'], temp_filename))
                    actual_duration = self._get_audio_duration(temp_filename)

                    # 2. ÉP TỐC ĐỘ (STRICT TIMING)
                    if actual_duration > slot_duration:
                        ratio = actual_duration / slot_duration
                        # Tính % cần tăng. Cộng thêm 10% buffer để chắc chắn nó nhỏ hơn slot
                        increase_percent = int((ratio - 1) * 100) + 10 
                        
                        self.log(f"⚡ Ép tốc: '{item['text'][:15]}...' (+{increase_percent}%)")
                        
                        # Sinh lại với tốc độ cao
                        asyncio.run(self._generate_clip(item['text'], temp_filename, rate_str=f"+{increase_percent}%"))
                        actual_duration = self._get_audio_duration(temp_filename)
                    
                    f.write(f"file '{temp_filename}'\n")
                
                # Tính khoảng lặng sau câu nói (nếu nói xong sớm)
                remaining = slot_duration - actual_duration
                if remaining > 0.01:
                    f.write(f"file '{silent_file}'\n")
                    f.write(f"inpoint 0\n")
                    f.write(f"outpoint {remaining}\n")
                
                # Trong chế độ Strict Timing, Cursor luôn nhảy đến đúng điểm kết thúc của slot
                current_cursor = item['end']

        # Concat
        self.log("Đang ghép file audio tổng...")
        cmd = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", output_file]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)

    def mix_video_audio(self, video_in, audio_in, video_out):
        vol_v = self.vol_video_slider.get() / 100.0
        vol_a = self.vol_ai_slider.get() / 100.0

        filter_complex = f"[0:a]volume={vol_v}[original];[1:a]volume={vol_a}[new];[original][new]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        
        cmd = [
            self.ffmpeg_path, "-y", "-i", video_in, "-i", audio_in,
            "-filter_complex", filter_complex,
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", video_out
        ]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AutoDubberApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")