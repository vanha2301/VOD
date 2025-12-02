import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import subprocess
import shutil
import os
import threading
import re

# ==============================================================================
# ⚙️ CẤU HÌNH
# ==============================================================================
TEMP_FOLDER = "temp_layers_v3"
FONT_SIZE = 20  # Cỡ chữ trung bình (sẽ tự canh giữa vùng mờ)
PRIMARY_COLOR = "&H00FFFFFF" # Trắng

class LayerRow(tk.Frame):
    """Class quản lý giao diện cho 1 Lớp (1 Layer)"""
    def __init__(self, parent, index, app_ref, delete_callback):
        super().__init__(parent, bd=1, relief=tk.RIDGE)
        self.pack(fill="x", pady=2, padx=5)
        self.app = app_ref
        self.index = index
        self.delete_callback = delete_callback

        # Data placeholders
        self.blur_rect = None # (x, y, w, h)
        self.script_path = tk.StringVar()

        # UI Components
        lbl_id = tk.Label(self, text=f"Layer #{index+1}", font=("bold", 10), width=8)
        lbl_id.pack(side="left", padx=5)

        # 1. Nút chọn vùng
        self.btn_region = tk.Button(self, text="[ ] Vẽ vùng mờ", command=self.pick_region, bg="#ffeaa7")
        self.btn_region.pack(side="left", padx=5)
        
        self.lbl_coords = tk.Label(self, text="Chưa chọn vùng", fg="red", width=25)
        self.lbl_coords.pack(side="left", padx=5)

        # 2. Nút chọn file
        btn_file = tk.Button(self, text="📂 Chọn Script (.txt)", command=self.pick_file)
        btn_file.pack(side="left", padx=5)

        self.lbl_file = tk.Entry(self, textvariable=self.script_path, width=30, state="readonly")
        self.lbl_file.pack(side="left", padx=5)

        # 3. Nút xóa
        btn_del = tk.Button(self, text="❌", command=lambda: delete_callback(self), bg="#ff7675", fg="white")
        btn_del.pack(side="right", padx=5)

    def pick_region(self):
        self.app.open_visual_selector(self)

    def pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path:
            self.script_path.set(path)

    def set_rect(self, x, y, w, h):
        self.blur_rect = (x, y, w, h)
        self.btn_region.config(bg="#55efc4", text="[✓] Đã vẽ")
        self.lbl_coords.config(text=f"X:{x}, Y:{y}, W:{w}, H:{h}", fg="green")

class AutoSubBlurV3:
    def __init__(self, root):
        self.root = root
        self.root.title("TDTU Multi-Layer Subtitler v3.0 (Map Region <-> Text)")
        self.root.geometry("950x700")
        
        self.layers = [] # List các object LayerRow
        self.video_path = tk.StringVar()
        self.ffmpeg_path = self._find_tool("ffmpeg")
        
        self.create_widgets()
        
        if not self.ffmpeg_path:
            messagebox.showerror("Lỗi", "Không tìm thấy FFmpeg!")

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
        tk.Label(self.root, text="MULTI-LAYER SUB & BLUR TOOL", font=("Segoe UI", 16, "bold"), fg="#2980b9").pack(pady=10)

        # 1. Video Input
        grp_in = tk.LabelFrame(self.root, text="Bước 1: Chọn Video Gốc", padx=10, pady=5)
        grp_in.pack(fill="x", padx=10)
        tk.Entry(grp_in, textvariable=self.video_path, width=80).pack(side="left")
        tk.Button(grp_in, text="📂 Chọn Video", command=self.browse_video).pack(side="left", padx=5)

        # 2. Layers Container
        grp_layers = tk.LabelFrame(self.root, text="Bước 2: Quản lý các Lớp (Mỗi vùng mờ đi kèm 1 file text)", padx=10, pady=5)
        grp_layers.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollable Frame for layers
        self.canvas = tk.Canvas(grp_layers)
        self.scrollbar = ttk.Scrollbar(grp_layers, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Buttons Control
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10)
        tk.Button(btn_frame, text="➕ Thêm Lớp Mới (Add Layer)", command=self.add_layer, bg="#3498db", fg="white", font=("bold", 10)).pack(side="left", pady=5)

        # 3. Action
        self.btn_run = tk.Button(self.root, text="🚀 XUẤT VIDEO (RENDER ALL LAYERS)", command=self.start_render,
                                 bg="#e74c3c", fg="white", font=("Segoe UI", 12, "bold"), height=2)
        self.btn_run.pack(fill="x", padx=20, pady=10)

        # Logs
        self.log_area = scrolledtext.ScrolledText(self.root, height=6)
        self.log_area.pack(fill="x", padx=10, pady=5)

    def log(self, msg):
        self.log_area.insert(tk.END, f"> {msg}\n")
        self.log_area.see(tk.END)

    def browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv")])
        if path: self.video_path.set(path)

    def add_layer(self):
        idx = len(self.layers)
        layer = LayerRow(self.scrollable_frame, idx, self, self.delete_layer)
        self.layers.append(layer)

    def delete_layer(self, layer_obj):
        layer_obj.destroy()
        self.layers.remove(layer_obj)
        # Update indexes (optional cosmetic)

    # --- VISUAL SELECTOR ---
    def open_visual_selector(self, layer_instance):
        if not self.video_path.get():
            messagebox.showwarning("!", "Chọn Video trước!")
            return

        # Extract temp frame
        temp_img = "temp_frame_v3.jpg"
        cmd = [self.ffmpeg_path, "-y", "-ss", "00:00:05", "-i", self.video_path.get(), "-frames:v", "1", "-q:v", "2", temp_img]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        
        if not os.path.exists(temp_img): return

        top = tk.Toplevel(self.root)
        top.title(f"Chọn vùng cho Layer #{layer_instance.index+1}")
        top.state('zoomed')

        pil_img = Image.open(temp_img)
        screen_h = top.winfo_screenheight() - 100
        ratio = 1.0
        if pil_img.size[1] > screen_h:
            ratio = screen_h / pil_img.size[1]
            new_w = int(pil_img.size[0] * ratio)
            pil_img = pil_img.resize((new_w, screen_h), Image.Resampling.LANCZOS)
        
        real_ratio = 1 / ratio
        tk_img = ImageTk.PhotoImage(pil_img)

        canvas = tk.Canvas(top, width=tk_img.width(), height=tk_img.height(), cursor="cross")
        canvas.pack()
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        
        # Keep ref
        canvas.image = tk_img 

        self.start_x = 0
        self.start_y = 0
        self.cur_rect = None

        def on_press(event):
            self.start_x = event.x
            self.start_y = event.y
            if self.cur_rect: canvas.delete(self.cur_rect)
            self.cur_rect = canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", width=2)

        def on_drag(event):
            canvas.coords(self.cur_rect, self.start_x, self.start_y, event.x, event.y)

        def on_release(event):
            end_x, end_y = event.x, event.y
            x = int(min(self.start_x, end_x) * real_ratio)
            y = int(min(self.start_y, end_y) * real_ratio)
            w = int(abs(end_x - self.start_x) * real_ratio)
            h = int(abs(end_y - self.start_y) * real_ratio)
            
            if w > 5 and h > 5:
                res = messagebox.askyesno("Confirm", f"Chọn vùng này?\nX={x}, Y={y}, W={w}, H={h}")
                if res:
                    layer_instance.set_rect(x, y, w, h)
                    top.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

    # --- PROCESSING LOGIC ---
    def start_render(self):
        if not self.video_path.get(): return
        
        # Validate data
        valid_layers = []
        for l in self.layers:
            if l.blur_rect and l.script_path.get():
                valid_layers.append(l)
        
        if not valid_layers:
            messagebox.showwarning("!", "Chưa có Layer nào đủ dữ liệu (Cần chọn Vùng + File)!")
            return

        out_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")], initialfile="Video_MultiLayered.mp4")
        if not out_path: return

        self.btn_run.config(state="disabled")
        threading.Thread(target=self.run_pipeline, args=(valid_layers, out_path), daemon=True).start()

    def run_pipeline(self, layers, output_path):
        try:
            self.log("Bắt đầu xử lý...")
            abs_temp = os.path.abspath(TEMP_FOLDER)
            if os.path.exists(abs_temp): shutil.rmtree(abs_temp)
            os.makedirs(abs_temp)

            # Chuỗi Filter FFmpeg sẽ rất dài
            # Logic: [in] -> [Layer1_Blur] -> [Layer1_Sub] -> [temp1] -> [Layer2_Blur] -> [Layer2_Sub] -> ...
            
            filter_chains = []
            last_stream = "0:v"

            for i, layer in enumerate(layers):
                x, y, w, h = layer.blur_rect
                txt_file = layer.script_path.get()
                
                # 1. Prepare SRT with Position Tags
                # Tính tâm của vùng mờ để đặt text vào giữa
                center_x = x + (w // 2)
                center_y = y + (h // 2)
                
                srt_name = f"sub_layer_{i}.srt"
                srt_path = os.path.join(abs_temp, srt_name).replace("\\", "/")
                
                self.log(f"Layer {i+1}: Convert text -> SRT (Pos: {center_x},{center_y})")
                self.convert_to_positioned_srt(txt_file, srt_path, center_x, center_y)

                # 2. Build Filter
                # a) Blur Step
                blur_stream = f"blur_{i}"
                chain_blur = (
                    f"[{last_stream}]split=2[bg{i}][fg{i}];"
                    f"[fg{i}]crop={w}:{h}:{x}:{y},gblur=sigma=20:steps=2[fg_blur{i}];"
                    f"[bg{i}][fg_blur{i}]overlay={x}:{y}[{blur_stream}]"
                )
                filter_chains.append(chain_blur)

                # b) Subtitle Step
                # Lưu ý: \: để escape dấu : trong đường dẫn
                srt_path_esc = srt_path.replace(":", "\\:")
                sub_stream = f"sub_{i}"
                
                # Dùng force_style Alignment=5 (Center) kết hợp với tag \pos trong file SRT
                chain_sub = (
                    f"[{blur_stream}]subtitles='{srt_path_esc}':"
                    f"force_style='FontSize={FONT_SIZE},PrimaryColour={PRIMARY_COLOR},Outline=1,Shadow=1'[out_{i}]"
                )
                filter_chains.append(chain_sub)
                
                last_stream = f"out_{i}"

            # Final render
            full_filter = ";".join(filter_chains)
            
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", self.video_path.get(),
                "-filter_complex", full_filter,
                "-map", f"[{last_stream}]", # Map stream cuối cùng
                "-map", "0:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "copy",
                output_path
            ]

            self.log("Đang Render FFmpeg (Có thể lâu)...")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
            out, err = proc.communicate()

            if proc.returncode != 0:
                self.log(f"Error: {err}")
                raise Exception("Render thất bại!")

            self.log("Hoàn tất!")
            messagebox.showinfo("Xong", "Video đã render xong!")
            if os.name == 'nt': os.startfile(output_path)

        except Exception as e:
            self.log(f"Lỗi: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            if os.path.exists(TEMP_FOLDER): shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
            self.btn_run.config(state="normal")

    def convert_to_positioned_srt(self, txt_file, srt_file, cx, cy):
        # Hàm này tạo file SRT nhưng chèn thêm tag ASS {\pos(x,y)} vào nội dung
        # để ép FFmpeg hiển thị text đúng vị trí ta muốn
        pattern = re.compile(r"\[([\d\.]+)s\s*->\s*([\d\.]+)s\]\s*(.*)")
        entries = []
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    entries.append((float(match.group(1)), float(match.group(2)), match.group(3).strip()))
        
        def fmt(s):
            h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60); ms = int((s - int(s)) * 1000)
            return f"{h:02}:{m:02}:{sec:02},{ms:03}"

        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, (start, end, text) in enumerate(entries):
                f.write(f"{i+1}\n")
                f.write(f"{fmt(start)} --> {fmt(end)}\n")
                # Tag quan trọng: {\pos(cx, cy)\an5} 
                # \an5: Alignment Center. \pos: Tọa độ tuyệt đối
                f.write(f"{{\\pos({cx},{cy})\\an5}}{text}\n\n")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AutoSubBlurV3(root)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")