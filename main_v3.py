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

class ModernProgressBar(tk.Canvas):
    """Custom progress bar with gradient effect"""
    def __init__(self, parent, width=600, height=30, **kwargs):
        super().__init__(parent, width=width, height=height, bg='#2c3e50', 
                         highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.progress = 0
        self.create_rectangle(0, 0, width, height, fill='#34495e', outline='')
        self.bar = self.create_rectangle(0, 0, 0, height, fill='#3498db', outline='')
        self.text = self.create_text(width/2, height/2, text='0%', 
                                     fill='white', font=('Segoe UI', 11, 'bold'))
    
    def set_progress(self, value):
        """Set progress (0-100)"""
        self.progress = max(0, min(100, value))
        bar_width = (self.width * self.progress) / 100
        
        # Color changes based on progress
        if self.progress < 30:
            color = '#e74c3c'
        elif self.progress < 70:
            color = '#f39c12'
        else:
            color = '#27ae60'
        
        self.coords(self.bar, 0, 0, bar_width, self.height)
        self.itemconfig(self.bar, fill=color)
        self.itemconfig(self.text, text=f'{int(self.progress)}%')
        self.update_idletasks()

class AutoDubberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Auto AI Dubbing Tool - Professional Edition")
        self.root.geometry("850x850")
        self.root.resizable(True, True)
        self.root.minsize(850, 700)
        
        # Modern color scheme
        self.colors = {
            'bg': '#1e272e',
            'card': '#2c3e50',
            'accent': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'text': '#ecf0f1',
            'text_dark': '#95a5a6'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # --- Variables ---
        self.video_path = tk.StringVar()
        self.script_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng để bắt đầu...")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.processed_count = tk.IntVar(value=0)
        self.total_count = tk.IntVar(value=0)
        
        self.ffmpeg_path = self._find_tool("ffmpeg")
        self.ffprobe_path = self._find_tool("ffprobe")
        
        # --- UI Layout ---
        self.create_modern_widgets()
        
        if not self.ffmpeg_path:
            messagebox.showerror("Lỗi", "Chưa cài đặt FFmpeg!")
    
    def _find_tool(self, tool_name):
        path = shutil.which(tool_name)
        if path:
            return path
        possible_paths = [
            rf"C:\ffmpeg\bin\{tool_name}.exe",
            rf"D:\ffmpeg\bin\{tool_name}.exe",
            os.path.expandvars(rf"%LOCALAPPDATA%\Microsoft\WinGet\Links\{tool_name}.exe")
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        return None
    
    def create_card_frame(self, parent, title):
        """Create a modern card-style frame"""
        frame = tk.Frame(parent, bg=self.colors['card'], relief=tk.FLAT)
        frame.pack(fill="x", padx=20, pady=8)
        
        # Title bar
        title_frame = tk.Frame(frame, bg=self.colors['accent'], height=35)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text=title, bg=self.colors['accent'], 
                fg='white', font=('Segoe UI', 10, 'bold')).pack(side="left", padx=15, pady=6)
        
        # Content area
        content = tk.Frame(frame, bg=self.colors['card'])
        content.pack(fill="both", expand=True, padx=15, pady=12)
        
        return content
    
    def create_modern_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill="both", expand=True)
        
        # ========== HEADER ==========
        header = tk.Frame(main_container, bg=self.colors['accent'], height=65)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🎬 AUTO AI DUBBING STUDIO", 
                bg=self.colors['accent'], fg='white',
                font=('Segoe UI', 18, 'bold')).pack(pady=20)
        
        # ========== 1. VIDEO INPUT CARD ==========
        video_content = self.create_card_frame(main_container, "📹  Video Gốc")
        
        input_frame = tk.Frame(video_content, bg=self.colors['card'])
        input_frame.pack(fill="x")
        
        self.video_entry = tk.Entry(input_frame, textvariable=self.video_path, 
                                    font=('Segoe UI', 10), bg='#34495e', fg='white',
                                    relief=tk.FLAT, insertbackground='white')
        self.video_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        
        btn_video = tk.Button(input_frame, text="📂 Chọn Video", command=self.browse_video,
                             bg=self.colors['accent'], fg='white', font=('Segoe UI', 10, 'bold'),
                             relief=tk.FLAT, cursor='hand2', padx=20, pady=8)
        btn_video.pack(side="right")
        
        # ========== 2. SCRIPT INPUT CARD ==========
        script_content = self.create_card_frame(main_container, "📄  Kịch Bản")
        
        script_frame = tk.Frame(script_content, bg=self.colors['card'])
        script_frame.pack(fill="x")
        
        self.script_entry = tk.Entry(script_frame, textvariable=self.script_path,
                                     font=('Segoe UI', 10), bg='#34495e', fg='white',
                                     relief=tk.FLAT, insertbackground='white')
        self.script_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        
        btn_script = tk.Button(script_frame, text="📄 Chọn Script", command=self.browse_script,
                              bg=self.colors['accent'], fg='white', font=('Segoe UI', 10, 'bold'),
                              relief=tk.FLAT, cursor='hand2', padx=20, pady=8)
        btn_script.pack(side="right")
        
        # ========== 3. MIXER CONTROL CARD ==========
        mixer_content = self.create_card_frame(main_container, "🎚️  Điều Chỉnh Âm Lượng")
        
        # Video Volume
        vol_video_frame = tk.Frame(mixer_content, bg=self.colors['card'])
        vol_video_frame.pack(fill="x", pady=3)
        
        tk.Label(vol_video_frame, text="🔊 Video Gốc:", bg=self.colors['card'],
                fg=self.colors['text'], font=('Segoe UI', 10)).pack(side="left", padx=(0, 10))
        
        self.vol_video_slider = tk.Scale(vol_video_frame, from_=0, to=200, orient="horizontal",
                                         bg=self.colors['card'], fg=self.colors['text'],
                                         highlightthickness=0, troughcolor='#34495e',
                                         activebackground=self.colors['accent'], length=300)
        self.vol_video_slider.set(20)
        self.vol_video_slider.pack(side="left", padx=5)
        
        self.lbl_vol_video = tk.Label(vol_video_frame, text="20%", bg=self.colors['card'],
                                      fg=self.colors['accent'], font=('Segoe UI', 10, 'bold'),
                                      width=5)
        self.lbl_vol_video.pack(side="left", padx=10)
        self.vol_video_slider.config(command=lambda v: self.lbl_vol_video.config(text=f"{int(float(v))}%"))
        
        # AI Voice Volume
        vol_ai_frame = tk.Frame(mixer_content, bg=self.colors['card'])
        vol_ai_frame.pack(fill="x", pady=3)
        
        tk.Label(vol_ai_frame, text="🎤 AI Voice:  ", bg=self.colors['card'],
                fg=self.colors['text'], font=('Segoe UI', 10)).pack(side="left", padx=(0, 10))
        
        self.vol_ai_slider = tk.Scale(vol_ai_frame, from_=0, to=200, orient="horizontal",
                                      bg=self.colors['card'], fg=self.colors['text'],
                                      highlightthickness=0, troughcolor='#34495e',
                                      activebackground=self.colors['success'], length=300)
        self.vol_ai_slider.set(150)
        self.vol_ai_slider.pack(side="left", padx=5)
        
        self.lbl_vol_ai = tk.Label(vol_ai_frame, text="150%", bg=self.colors['card'],
                                   fg=self.colors['success'], font=('Segoe UI', 10, 'bold'),
                                   width=5)
        self.lbl_vol_ai.pack(side="left", padx=10)
        self.vol_ai_slider.config(command=lambda v: self.lbl_vol_ai.config(text=f"{int(float(v))}%"))
        
        # ========== 4. PROGRESS SECTION ==========
        progress_card = tk.Frame(main_container, bg=self.colors['card'], relief=tk.FLAT)
        progress_card.pack(fill="x", padx=20, pady=8)
        
        prog_inner = tk.Frame(progress_card, bg=self.colors['card'])
        prog_inner.pack(fill="x", padx=15, pady=12)
        
        # Status counter
        counter_frame = tk.Frame(prog_inner, bg=self.colors['card'])
        counter_frame.pack(fill="x", pady=(0, 8))
        
        tk.Label(counter_frame, text="Tiến Độ Xử Lý:", bg=self.colors['card'],
                fg=self.colors['text'], font=('Segoe UI', 11, 'bold')).pack(side="left")
        
        self.lbl_counter = tk.Label(counter_frame, text="0 / 0 câu", bg=self.colors['card'],
                                    fg=self.colors['accent'], font=('Segoe UI', 11, 'bold'))
        self.lbl_counter.pack(side="right")
        
        # Modern progress bar
        self.progress_bar = ModernProgressBar(prog_inner, width=760, height=32)
        self.progress_bar.pack(pady=8)
        
        # ========== 5. LOGS ==========
        log_content = self.create_card_frame(main_container, "📋  Nhật Ký Hoạt Động")
        
        self.log_area = scrolledtext.ScrolledText(log_content, height=6, state='disabled',
                                                  font=('Consolas', 9), bg='#1e272e',
                                                  fg='#2ecc71', insertbackground='white',
                                                  relief=tk.FLAT)
        self.log_area.pack(fill="both", expand=True)
        
        # ========== 6. ACTION BUTTON ==========
        btn_frame = tk.Frame(main_container, bg=self.colors['bg'])
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_run = tk.Button(btn_frame, text="🚀 BẮT ĐẦU XỬ LÝ",
                                command=self.start_processing_flow,
                                bg=self.colors['success'], fg='white',
                                font=('Segoe UI', 13, 'bold'),
                                relief=tk.FLAT, cursor='hand2',
                                height=2)
        self.btn_run.pack(fill="x", ipady=8)
        
        # ========== 7. STATUS BAR ==========
        status_bar = tk.Frame(main_container, bg=self.colors['card'], height=35)
        status_bar.pack(side="bottom", fill="x")
        status_bar.pack_propagate(False)
        
        self.lbl_status = tk.Label(status_bar, textvariable=self.status_var,
                                   bg=self.colors['card'], fg=self.colors['text_dark'],
                                   font=('Segoe UI', 9), anchor="w")
        self.lbl_status.pack(side="left", padx=15, fill="x", expand=True)
        
        # Version label
        tk.Label(status_bar, text="v2.0 Pro", bg=self.colors['card'],
                fg=self.colors['text_dark'], font=('Segoe UI', 8)).pack(side="right", padx=15)
    
    def log(self, message):
        self.log_area.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
    
    def update_progress(self, percent, status_text=None):
        self.progress_bar.set_progress(percent)
        if status_text:
            self.status_var.set(status_text)
        self.root.update_idletasks()
    
    def update_counter(self, current, total):
        self.processed_count.set(current)
        self.total_count.set(total)
        self.lbl_counter.config(text=f"{current} / {total} câu")
        self.root.update_idletasks()
    
    def browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv *.avi")])
        if path:
            self.video_path.set(path)
            self.log(f"✓ Đã chọn video: {os.path.basename(path)}")
    
    def browse_script(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path:
            self.script_path.set(path)
            self.log(f"✓ Đã chọn script: {os.path.basename(path)}")
    
    def start_processing_flow(self):
        if not self.video_path.get() or not self.script_path.get():
            messagebox.showwarning("⚠️ Thiếu thông tin", 
                                 "Vui lòng chọn Video và Script!")
            return
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4")],
            initialfile="Dubbed_Video_Pro.mp4"
        )
        if not output_path:
            return
        
        self.btn_run.config(state="disabled", bg='#95a5a6')
        self.progress_bar.set_progress(0)
        self.update_counter(0, 0)
        
        threading.Thread(target=self.process_pipeline, args=(output_path,), daemon=True).start()
    
    def process_pipeline(self, output_path):
        try:
            self.log("=" * 60)
            self.log("🎬 BẮT ĐẦU PIPELINE XỬ LÝ (STRICT MODE)")
            self.log("=" * 60)
            
            abs_temp = os.path.abspath(TEMP_FOLDER)
            if os.path.exists(abs_temp):
                shutil.rmtree(abs_temp)
            os.makedirs(abs_temp)
            
            # 1. Đọc Script
            self.update_progress(5, "🔄 Đang đọc kịch bản...")
            subtitles = self.read_script_file(self.script_path.get())
            if not subtitles:
                raise Exception("Script rỗng!")
            
            self.log(f"✓ Đã nạp {len(subtitles)} câu thoại")
            self.update_counter(0, len(subtitles))
            
            # 2. Sinh Audio
            full_audio_path = os.path.join(abs_temp, "full_tts.mp3").replace("\\", "/")
            self.create_tts_track(subtitles, full_audio_path, abs_temp)
            
            # 3. Mix Video
            self.update_progress(80, "🎥 Đang render video cuối cùng...")
            self.log("🎬 Bắt đầu ghép video...")
            self.mix_video_audio(self.video_path.get(), full_audio_path, output_path)
            
            # 4. Finish
            self.update_progress(100, "✅ Hoàn thành!")
            self.log("=" * 60)
            self.log(f"✅ OUTPUT SAVED: {output_path}")
            self.log("=" * 60)
            
            messagebox.showinfo("🎉 Thành công", 
                              "Video đã được xử lý hoàn tất!\n\nẤn OK để mở file.")
            
            if os.name == 'nt':
                try:
                    os.startfile(output_path)
                except:
                    pass
                    
        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
            messagebox.showerror("❌ Lỗi", str(e))
        finally:
            if os.path.exists(TEMP_FOLDER):
                shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
            self.root.after(0, lambda: self.btn_run.config(state="normal", 
                                                          bg=self.colors['success']))
    
    def read_script_file(self, file_path):
        data = []
        pattern = re.compile(r"\[([\d\.]+)s\s*->\s*([\d\.]+)s\]\s*(.*)")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    data.append({
                        'start': float(match.group(1)),
                        'end': float(match.group(2)),
                        'text': match.group(3).strip()
                    })
        data.sort(key=lambda x: x['start'])
        return data
    
    async def _generate_clip(self, text, filename, rate_str="+0%"):
        communicate = edge_tts.Communicate(text, GIONG_DOC_DEFAULT, 
                                          rate=rate_str, volume="+0%")
        await communicate.save(filename)
    
    def _get_audio_duration(self, file_path):
        try:
            cmd = [
                self.ffprobe_path, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, startupinfo=startupinfo)
            return float(res.stdout.strip())
        except:
            return 0.0
    
    def _create_specific_silence(self, filename, duration):
            """Tạo file silence chính xác từng miligiây bằng WAV"""
            if duration <= 0: return
            cmd = [
                self.ffmpeg_path, "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=24000:cl=mono:d={duration}",
                "-c:a", "pcm_s16le", # Dùng PCM WAV để chính xác tuyệt đối
                filename
            ]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        startupinfo=startupinfo)
    
    def create_tts_track(self, subtitles, output_file, temp_folder):
            # Đổi đuôi file output trung gian sang wav để ghép cho chuẩn
            concat_list_path = os.path.join(temp_folder, "mylist.txt").replace("\\", "/")
            
            # Biến quan trọng: Theo dõi độ dài thực tế của audio đã tạo
            current_audio_position = 0.0
            total_subs = len(subtitles)
            
            concat_files = [] # Lưu danh sách file để ghi vào mylist.txt sau

            for i, item in enumerate(subtitles):
                percent = 5 + (i / total_subs) * 75
                self.update_progress(percent, f"🎤 Đang xử lý câu thoại {i+1}/{total_subs}...")
                self.update_counter(i + 1, total_subs)
                
                # 1. Tính toán khoảng lặng cần chèn TRƯỚC câu thoại
                # Logic: Lấy thời gian bắt đầu mong muốn - thời gian audio hiện có
                target_start_time = item['start']
                gap_needed = target_start_time - current_audio_position
                
                if gap_needed > 0.05: # Chỉ chèn nếu gap > 50ms
                    silence_filename = os.path.join(temp_folder, f"silence_{i}.wav").replace("\\", "/")
                    self._create_specific_silence(silence_filename, gap_needed)
                    concat_files.append(f"file '{silence_filename}'")
                    current_audio_position += gap_needed
                
                # 2. Xử lý TTS
                if item['text']:
                    # Dùng file WAV tạm thời
                    temp_wav = os.path.join(temp_folder, f"clip_{i}.wav").replace("\\", "/")
                    temp_mp3 = os.path.join(temp_folder, f"clip_{i}_raw.mp3").replace("\\", "/")
                    
                    # Sinh file MP3 từ Edge TTS trước
                    asyncio.run(self._generate_clip(item['text'], temp_mp3))
                    
                    # Convert MP3 sang WAV ngay lập tức để lấy độ dài chuẩn
                    cmd_convert = [
                        self.ffmpeg_path, "-y", "-i", temp_mp3, 
                        "-c:a", "pcm_s16le", "-ar", "24000", temp_wav
                    ]
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.run(cmd_convert, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)

                    actual_duration = self._get_audio_duration(temp_wav)
                    slot_duration = item['end'] - item['start']

                    # 3. Kiểm tra tốc độ: Nếu nói dài hơn khung thời gian cho phép -> Tăng tốc
                    if actual_duration > slot_duration:
                        ratio = actual_duration / slot_duration
                        increase_percent = int((ratio - 1) * 100) + 15 # +15% dư ra cho chắc
                        self.log(f"⚡ Tăng tốc câu {i+1}: +{increase_percent}%")
                        
                        # Sinh lại file với tốc độ mới
                        asyncio.run(self._generate_clip(item['text'], temp_mp3, rate_str=f"+{increase_percent}%"))
                        # Convert lại sang WAV
                        subprocess.run(cmd_convert, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                        actual_duration = self._get_audio_duration(temp_wav)

                    concat_files.append(f"file '{temp_wav}'")
                    current_audio_position += actual_duration
                
                # LƯU Ý QUAN TRỌNG: 
                # Không còn bước "Gap After" để lấp đầy đến item['end'].
                # Chúng ta để thả nổi. Vòng lặp tiếp theo sẽ tự tính gap_needed 
                # dựa trên current_audio_position thực tế. -> Đây là bước sửa lỗi trôi.

            # Ghi file list
            with open(concat_list_path, "w", encoding='utf-8') as f:
                for line in concat_files:
                    f.write(line + "\n")

            # Concat all (xuất ra file wav tạm full track)
            full_wav_path = os.path.join(temp_folder, "full_track.wav").replace("\\", "/")
            self.log("🔗 Đang ghép toàn bộ audio (WAV mode)...")
            cmd = [
                self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list_path, "-c", "copy", full_wav_path
            ]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        startupinfo=startupinfo)
            
            # Convert full wav sang mp3 output cuối cùng (nếu cần) hoặc trả về wav
            # Ở đây ta trả về wav để mix cho chất lượng tốt nhất
            shutil.move(full_wav_path, output_file)
    
    def mix_video_audio(self, video_in, audio_in, video_out):
        vol_v = self.vol_video_slider.get() / 100.0
        vol_a = self.vol_ai_slider.get() / 100.0
        
        filter_complex = (
            f"[0:a]volume={vol_v}[original];"
            f"[1:a]volume={vol_a}[new];"
            f"[original][new]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_in,
            "-i", audio_in,
            "-filter_complex", filter_complex,
            "-map", "0:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            video_out
        ]
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      startupinfo=startupinfo)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AutoDubberApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")