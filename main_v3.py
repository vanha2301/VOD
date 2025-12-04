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
import yt_dlp
import whisper

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
        self.progress = max(0, min(100, value))
        bar_width = (self.width * self.progress) / 100
        
        if self.progress < 30: color = '#e74c3c'
        elif self.progress < 70: color = '#f39c12'
        else: color = '#27ae60'
        
        self.coords(self.bar, 0, 0, bar_width, self.height)
        self.itemconfig(self.bar, fill=color)
        self.itemconfig(self.text, text=f'{int(self.progress)}%')
        self.update_idletasks()

class AutoDubberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Auto AI Dubbing Tool - Professional Edition (Fixed Error Handling)")
        self.root.geometry("850x950") 
        self.root.resizable(True, True)
        self.root.minsize(850, 700)
        
        self.colors = {
            'bg': '#1e272e', 'card': '#2c3e50', 'accent': '#3498db',
            'success': '#27ae60', 'danger': '#e74c3c', 'text': '#ecf0f1', 'text_dark': '#95a5a6',
            'warning': '#f39c12'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # --- Variables ---
        self.video_path = tk.StringVar()
        self.script_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng...")
        self.url_var = tk.StringVar()
        
        self.ffmpeg_path = self._find_tool("ffmpeg")
        self.ffprobe_path = self._find_tool("ffprobe")
        
        # --- UI Layout ---
        self.create_modern_widgets()
        
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
    
    def create_card_frame(self, parent, title, color_theme=None):
        if color_theme is None: color_theme = self.colors['accent']
        
        frame = tk.Frame(parent, bg=self.colors['card'], relief=tk.FLAT)
        frame.pack(fill="x", padx=20, pady=8)
        
        title_frame = tk.Frame(frame, bg=color_theme, height=35)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text=title, bg=color_theme, 
                fg='white', font=('Segoe UI', 10, 'bold')).pack(side="left", padx=15, pady=6)
        
        content = tk.Frame(frame, bg=self.colors['card'])
        content.pack(fill="both", expand=True, padx=15, pady=12)
        return content
    
    def create_modern_widgets(self):
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill="both", expand=True)
        
        # HEADER
        header = tk.Frame(main_container, bg=self.colors['accent'], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🎬 AUTO AI DUBBING STUDIO", bg=self.colors['accent'], fg='white', font=('Segoe UI', 16, 'bold')).pack(pady=15)
          
        # ==================== 1. VIDEO INPUT ====================
        video_content = self.create_card_frame(main_container, "1️⃣  Video Gốc (Input)")
        
        input_frame = tk.Frame(video_content, bg=self.colors['card'])
        input_frame.pack(fill="x", pady=(0, 5))
        
        file_box = tk.Frame(input_frame, bg=self.colors['card'])
        file_box.pack(fill="x")

        self.video_entry = tk.Entry(file_box, textvariable=self.video_path, font=('Segoe UI', 10), bg='#34495e', fg='white', relief=tk.FLAT, insertbackground='white')
        self.video_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        
        tk.Button(file_box, text="📂 Chọn File", command=self.browse_video, bg='#7f8c8d', fg='white', font=('Segoe UI', 9, 'bold'), relief=tk.FLAT, padx=15, pady=4).pack(side="right")

        # Youtube Download
        separator = tk.Frame(video_content, bg='#95a5a6', height=1)
        separator.pack(fill="x", pady=10)
        yt_box = tk.Frame(video_content, bg=self.colors['card'])
        yt_box.pack(fill="x")
        self.url_entry = tk.Entry(yt_box, textvariable=self.url_var, font=('Segoe UI', 10), bg='#34495e', fg='white', relief=tk.FLAT, insertbackground='white')
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        
        self.btn_download = tk.Button(yt_box, text="⬇️ Tải Video", command=self.start_download_thread, bg='#c0392b', fg='white', font=('Segoe UI', 9, 'bold'), relief=tk.FLAT, padx=15, pady=4)
        self.btn_download.pack(side="right")
        
        # ==================== 2. WHISPER EXTRACT (RIÊNG BIỆT) ====================
        whisper_content = self.create_card_frame(main_container, "2️⃣  Tách Lời Thoại (Whisper - Tạo Raw Text)", color_theme='#8e44ad')
        
        w_frame = tk.Frame(whisper_content, bg=self.colors['card'])
        w_frame.pack(fill="x")
        
        # Hướng dẫn
        lbl_guide = tk.Label(w_frame, text="💡 Dùng tính năng này để lấy text gốc, sau đó bạn tự dịch file text và nạp vào bước 3.", 
                             bg=self.colors['card'], fg='#bdc3c7', font=('Segoe UI', 9, 'italic'), justify="left")
        lbl_guide.pack(anchor="w", pady=(0, 10))
        
        self.btn_whisper = tk.Button(w_frame, text="🎙️ Trích Xuất Văn Bản Gốc", command=self.start_whisper_thread, 
                                     bg='#8e44ad', fg='white', font=('Segoe UI', 10, 'bold'), relief=tk.FLAT, width=30)
        self.btn_whisper.pack(anchor="center", ipady=5)

        # ==================== 3. SCRIPT INPUT ====================
        script_content = self.create_card_frame(main_container, "3️⃣  Kịch Bản Đã Dịch (Vietnamese)", color_theme=self.colors['accent'])
        
        script_frame = tk.Frame(script_content, bg=self.colors['card'])
        script_frame.pack(fill="x")
        
        self.script_entry = tk.Entry(script_frame, textvariable=self.script_path, font=('Segoe UI', 10), bg='#34495e', fg='white', relief=tk.FLAT, insertbackground='white')
        self.script_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        
        # Chỉ còn nút Browse
        tk.Button(script_frame, text="📄 Chọn Script (Đã dịch)", command=self.browse_script, bg=self.colors['accent'], fg='white', font=('Segoe UI', 10, 'bold'), relief=tk.FLAT, padx=20, pady=8).pack(side="right")
        
        # ==================== 4. MIXER & PROGRESS ====================
        mixer_content = self.create_card_frame(main_container, "4️⃣  Cấu Hình & Xử Lý")
        
        # Sliders
        sliders_frame = tk.Frame(mixer_content, bg=self.colors['card'])
        sliders_frame.pack(fill="x")
        
        # Video Volume
        v_frame = tk.Frame(sliders_frame, bg=self.colors['card'])
        v_frame.pack(fill="x", pady=2)
        tk.Label(v_frame, text="Video Gốc:", bg=self.colors['card'], fg='white', width=10, anchor='w').pack(side="left")
        self.vol_video_slider = tk.Scale(v_frame, from_=0, to=200, orient="horizontal", bg=self.colors['card'], fg='white', highlightthickness=0, troughcolor='#34495e', activebackground=self.colors['accent'], length=250)
        self.vol_video_slider.set(20)
        self.vol_video_slider.pack(side="left")

        # AI Volume
        a_frame = tk.Frame(sliders_frame, bg=self.colors['card'])
        a_frame.pack(fill="x", pady=2)
        tk.Label(a_frame, text="AI Voice:", bg=self.colors['card'], fg='white', width=10, anchor='w').pack(side="left")
        self.vol_ai_slider = tk.Scale(a_frame, from_=0, to=200, orient="horizontal", bg=self.colors['card'], fg='white', highlightthickness=0, troughcolor='#34495e', activebackground=self.colors['success'], length=250)
        self.vol_ai_slider.set(150)
        self.vol_ai_slider.pack(side="left")

        # Progress
        tk.Frame(mixer_content, height=1, bg='#7f8c8d').pack(fill="x", pady=15) # Line
        self.progress_bar = ModernProgressBar(mixer_content, width=760, height=25)
        self.progress_bar.pack(pady=5)
        self.lbl_counter = tk.Label(mixer_content, text="0/0", bg=self.colors['card'], fg='white')
        self.lbl_counter.pack()

        # Logs
        log_content = self.create_card_frame(main_container, "📋  Logs")
        self.log_area = scrolledtext.ScrolledText(log_content, height=5, state='disabled', font=('Consolas', 9), bg='#1e272e', fg='#2ecc71', relief=tk.FLAT)
        self.log_area.pack(fill="both", expand=True)
        
        # Run Button
        btn_frame = tk.Frame(main_container, bg=self.colors['bg'])
        btn_frame.pack(fill="x", padx=20, pady=10)
        self.btn_run = tk.Button(btn_frame, text="🚀 BẮT ĐẦU LỒNG TIẾNG (BƯỚC 4)", command=self.start_processing_flow, bg=self.colors['success'], fg='white', font=('Segoe UI', 12, 'bold'), relief=tk.FLAT, cursor='hand2', height=2)
        self.btn_run.pack(fill="x")
        
        # Status Bar
        status_bar = tk.Frame(main_container, bg=self.colors['card'], height=30)
        status_bar.pack(side="bottom", fill="x")
        self.lbl_status = tk.Label(status_bar, textvariable=self.status_var, bg=self.colors['card'], fg=self.colors['text_dark'], font=('Segoe UI', 9), anchor="w")
        self.lbl_status.pack(side="left", padx=15)
    
    # --- HELPER FUNCTIONS ---
    def log(self, message):
        self.log_area.config(state='normal')
        timestamp = time.strftime('%H:%M:%S')
        
        # Đổi màu nếu là lỗi
        tag = None
        if "❌" in message or "ERROR" in message:
            self.log_area.tag_config('error', foreground='#e74c3c')
            tag = 'error'
        elif "⚠️" in message:
            self.log_area.tag_config('warning', foreground='#f39c12')
            tag = 'warning'
            
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
    
    def update_progress(self, percent, status_text=None):
        self.progress_bar.set_progress(percent)
        if status_text: self.status_var.set(status_text)
        self.root.update_idletasks()
        
    def update_counter(self, current, total):
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
            self.log(f"✓ Đã chọn script lồng tiếng: {os.path.basename(path)}")

    # ==========================================================================
    # 🎙️ WHISPER LOGIC (ĐÃ TÁCH RIÊNG)
    # ==========================================================================
    def start_whisper_thread(self):
        video_file = self.video_path.get()
        if not video_file or not os.path.exists(video_file):
            messagebox.showwarning("Thiếu Video", "Vui lòng chọn Video ở Bước 1 trước!")
            return
        
        # Hỏi nơi lưu file RAW (chưa dịch)
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt")],
            initialfile=f"raw_script_original.txt",
            title="Lưu file text gốc ở đâu?"
        )
        if not save_path:
            return

        self.btn_whisper.config(state="disabled", text="⏳ Đang phân tích...", bg='#7f8c8d')
        threading.Thread(target=self.process_whisper_generation, args=(video_file, save_path), daemon=True).start()

    def process_whisper_generation(self, video_path, save_path):
        try:
            self.log("=" * 40)
            self.log("🎙️ BẮT ĐẦU TÁCH LỜI THOẠI (WHISPER)")
            self.status_var.set("⏳ Đang tải model & xử lý audio...")
            
            # Load Model
            model = whisper.load_model("base") # Dùng base cho nhanh
            self.log("✓ Model loaded. Transcribing...")
            
            # Transcribe
            result = model.transcribe(video_path, fp16=False) 
            segments = result['segments']
            self.log(f"✓ Tìm thấy {len(segments)} đoạn hội thoại.")

            # Lưu file: Vẫn giữ format [time] text để sau này dùng lại được
            with open(save_path, "w", encoding="utf-8") as f:
                for seg in segments:
                    start_time = seg['start']
                    end_time = seg['end']
                    text = seg['text'].strip()
                    # Format chuẩn để app đọc được sau khi dịch
                    line = f"[{start_time:.2f}s -> {end_time:.2f}s] {text}\n"
                    f.write(line)
            
            self.root.after(0, lambda: self.log(f"✅ Đã xuất file thô: {save_path}"))
            
            msg = (f"Đã tách lời thoại thành công!\n\n"
                   f"File lưu tại: {save_path}\n\n"
                   f"👉 BƯỚC TIẾP THEO: Hãy mở file này lên, dịch nội dung sang tiếng Việt (giữ nguyên timecode [...]), "
                   f"sau đó chọn file đã dịch ở mục '3. Kịch Bản'.")
            
            self.root.after(0, lambda: messagebox.showinfo("Hoàn thành trích xuất", msg))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ WHISPER ERROR: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Lỗi", str(e)))
        finally:
            self.root.after(0, lambda: self.btn_whisper.config(state="normal", text="🎙️ Trích Xuất Văn Bản Gốc", bg='#8e44ad'))
            self.root.after(0, lambda: self.status_var.set("Sẵn sàng..."))

    # ==========================================================================
    # CORE PIPELINE (DUBBING)
    # ==========================================================================
    def start_processing_flow(self):
        if not self.video_path.get() or not self.script_path.get():
            messagebox.showwarning("⚠️ Thiếu thông tin", "Vui lòng làm xong Bước 1 và Bước 3!")
            return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")], initialfile="Dubbed_Video_Final.mp4")
        if not output_path: return
        
        self.btn_run.config(state="disabled", bg='#95a5a6')
        self.progress_bar.set_progress(0)
        self.update_counter(0, 0)
        
        threading.Thread(target=self.process_pipeline, args=(output_path,), daemon=True).start()
    
    def process_pipeline(self, output_path):
        try:
            self.log("=" * 60)
            self.log("🎬 BẮT ĐẦU LỒNG TIẾNG")
            
            abs_temp = os.path.abspath(TEMP_FOLDER)
            if os.path.exists(abs_temp): shutil.rmtree(abs_temp)
            os.makedirs(abs_temp)
            
            # 1. Đọc Script (File đã dịch)
            self.update_progress(5, "🔄 Đang đọc script tiếng Việt...")
            subtitles = self.read_script_file(self.script_path.get())
            if not subtitles: raise Exception("Script rỗng hoặc sai định dạng!")
            
            self.log(f"✓ Đã nạp {len(subtitles)} câu thoại")
            self.update_counter(0, len(subtitles))
            
            # 2. Sinh Audio
            full_audio_path = os.path.join(abs_temp, "full_tts.mp3").replace("\\", "/")
            self.create_tts_track(subtitles, full_audio_path, abs_temp)
            
            # 3. Mix Video
            self.update_progress(80, "🎥 Đang ghép video...")
            self.mix_video_audio(self.video_path.get(), full_audio_path, output_path)
            
            # 4. Finish
            self.update_progress(100, "✅ Xong!")
            self.log(f"✅ FILE: {output_path}")
            
            messagebox.showinfo("Thành công", "Video đã lồng tiếng xong!")
            if os.name == 'nt':
                try: os.startfile(output_path)
                except: pass
                    
        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            if os.path.exists(TEMP_FOLDER): shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
            self.root.after(0, lambda: self.btn_run.config(state="normal", bg=self.colors['success']))
    
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
    
    def _create_specific_silence(self, filename, duration):
            if duration <= 0: return
            cmd = [self.ffmpeg_path, "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono:d={duration}", "-c:a", "pcm_s16le", filename]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
    
    # ----------------------------------------------------------------------
    # 🔥 HÀM ĐÃ SỬA LỖI (FIXED)
    # ----------------------------------------------------------------------
    def create_tts_track(self, subtitles, output_file, temp_folder):
            concat_list_path = os.path.join(temp_folder, "mylist.txt").replace("\\", "/")
            current_audio_position = 0.0
            total_subs = len(subtitles)
            concat_files = [] 

            for i, item in enumerate(subtitles):
                percent = 5 + (i / total_subs) * 75
                self.update_progress(percent, f"🎤 Đang tạo giọng đọc câu {i+1}/{total_subs}...")
                self.update_counter(i + 1, total_subs)
                
                target_start_time = item['start']
                target_end_time = item['end']
                
                # 1. Tính toán và thêm khoảng lặng trước câu thoại (Pre-gap)
                # Phần này ít lỗi nên để ngoài try, hoặc nếu muốn an toàn tuyệt đối thì đưa vào trong luôn
                gap_needed = target_start_time - current_audio_position
                
                if gap_needed > 0.05:
                    silence_filename = os.path.join(temp_folder, f"silence_gap_{i}.wav").replace("\\", "/")
                    self._create_specific_silence(silence_filename, gap_needed)
                    concat_files.append(f"file '{silence_filename}'")
                    current_audio_position += gap_needed
                
                # 2. Xử lý tạo âm thanh (CÓ BẮT LỖI)
                duration_slot = target_end_time - target_start_time
                
                try:
                    if not item['text']: 
                        raise Exception("Text rỗng")

                    temp_wav = os.path.join(temp_folder, f"clip_{i}.wav").replace("\\", "/")
                    temp_mp3 = os.path.join(temp_folder, f"clip_{i}_raw.mp3").replace("\\", "/")
                    
                    # Sinh file MP3 gốc
                    asyncio.run(self._generate_clip(item['text'], temp_mp3))
                    
                    # Convert sang WAV
                    cmd_convert = [self.ffmpeg_path, "-y", "-i", temp_mp3, "-c:a", "pcm_s16le", "-ar", "24000", temp_wav]
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.run(cmd_convert, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)

                    # Kiểm tra độ dài và tua nhanh nếu cần
                    actual_duration = self._get_audio_duration(temp_wav)
                    
                    if actual_duration > duration_slot:
                        ratio = actual_duration / duration_slot
                        # Tính % tăng tốc. Cộng thêm 15% buffer để chắc chắn nó ngắn hơn slot
                        increase_percent = int((ratio - 1) * 100) + 15
                        
                        # Fix lỗi rate âm hoặc quá lớn gây lỗi chuỗi
                        if increase_percent < 0: increase_percent = 0
                        
                        # Sinh lại với tốc độ mới
                        asyncio.run(self._generate_clip(item['text'], temp_mp3, rate_str=f"+{increase_percent}%"))
                        subprocess.run(cmd_convert, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                        actual_duration = self._get_audio_duration(temp_wav)

                    concat_files.append(f"file '{temp_wav}'")
                    current_audio_position += actual_duration

                except Exception as e:
                    # 🔥 KHI CÓ LỖI XẢY RA Ở ĐÂY 🔥
                    # 1. In log lỗi ra màn hình
                    error_msg = f"⚠️ LỖI SKIP CÂU {i+1}: {str(e)}"
                    self.log(error_msg)
                    self.log(f"   ➥ Nội dung lỗi: \"{item['text'][:50]}...\"")
                    self.log(f"   ➥ Thay thế bằng khoảng lặng {duration_slot:.2f}s")
                    
                    # 2. Tạo khoảng lặng thay thế (Fallback Silence)
                    fallback_silence = os.path.join(temp_folder, f"silence_error_{i}.wav").replace("\\", "/")
                    self._create_specific_silence(fallback_silence, duration_slot)
                    
                    # 3. Thêm file lặng vào danh sách ghép
                    concat_files.append(f"file '{fallback_silence}'")
                    current_audio_position += duration_slot
                    # Chương trình sẽ tiếp tục vòng lặp sang câu tiếp theo...

            with open(concat_list_path, "w", encoding='utf-8') as f:
                for line in concat_files: f.write(line + "\n")

            full_wav_path = os.path.join(temp_folder, "full_track.wav").replace("\\", "/")
            cmd = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", full_wav_path]
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
            shutil.move(full_wav_path, output_file)
    
    def mix_video_audio(self, video_in, audio_in, video_out):
        vol_v = self.vol_video_slider.get() / 100.0
        vol_a = self.vol_ai_slider.get() / 100.0
        filter_complex = (f"[0:a]volume={vol_v}[original];[1:a]volume={vol_a}[new];[original][new]amix=inputs=2:duration=first:dropout_transition=0[aout]")
        cmd = [self.ffmpeg_path, "-y", "-i", video_in, "-i", audio_in, "-filter_complex", filter_complex, "-map", "0:v:0", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-shortest", video_out]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    
    # --- YOUTUBE DOWNLOAD (UPDATED) ---
    def start_download_thread(self):
            url = self.url_var.get().strip()
            if not url:
                messagebox.showwarning("Thiếu Link", "Vui lòng nhập Link YouTube!")
                return
            
            # === THAY ĐỔI: Yêu cầu người dùng chọn nơi lưu file ngay lập tức ===
            save_path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 Video", "*.mp4")],
                title="Chọn nơi lưu video tải về"
            )
            
            if not save_path: # Nếu người dùng ấn Cancel
                return

            self.btn_download.config(state="disabled", text="⏳ Đang tải...", bg='#7f8c8d')
            # Truyền save_path vào thread
            threading.Thread(target=self.download_youtube_video, args=(url, save_path), daemon=True).start()

    def download_youtube_video(self, url, save_path):
            try:
                self.root.after(0, lambda: self.log(f"⬇️ ĐANG TẢI: {url} -> {save_path}"))
                
                # Cấu hình yt-dlp để lưu đúng vào save_path người dùng chọn
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4', # Ép định dạng MP4
                    'outtmpl': save_path,         # Ép đường dẫn đầu ra chính xác
                    'quiet': True,
                    'no_warnings': True,
                    'overwrites': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_title = info.get('title', 'Video')
                
                # Kiểm tra nếu file đã tồn tại (yt-dlp đôi khi thêm đuôi, nhưng với cấu hình trên thì khá chắc chắn)
                if os.path.exists(save_path):
                    # === THAY ĐỔI: Tự động cập nhật đường dẫn vào ô Input Video ===
                    self.root.after(0, lambda: self.video_path.set(save_path))
                    self.root.after(0, lambda: self.log(f"✅ TẢI XONG: {video_title}"))
                    self.root.after(0, lambda: messagebox.showinfo("Thành công", f"Đã tải xong:\n{video_title}\n\nĐường dẫn đã được cập nhật vào mục Video Gốc."))
                else: 
                    raise Exception("Không tìm thấy file sau khi tải xong.")

            except Exception as e:
                self.root.after(0, lambda: self.log(f"❌ LỖI: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Lỗi Tải", str(e)))
            finally:
                self.root.after(0, lambda: self.btn_download.config(state="normal", text="⬇️ Tải Video", bg='#c0392b'))

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AutoDubberApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")