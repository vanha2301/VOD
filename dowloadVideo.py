import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import os
import re
import sys

# Kiểm tra thư viện yt-dlp
try:
    import yt_dlp
except ImportError:
    print("Lỗi: Bạn chưa cài đặt thư viện 'yt-dlp'.")
    print("Vui lòng chạy lệnh: pip install yt-dlp")
    sys.exit(1)

class BilibiliDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ Tải Video Bilibili - Cho Hà TDTU")
        self.root.geometry("750x600")
        
        # --- Biến lưu trữ đường dẫn ---
        self.file_path_var = tk.StringVar(value="data_phim.txt")  # Mặc định tìm file này
        self.save_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "Downloads_Bilibili"))

        # --- Giao diện: Chọn File Dữ liệu ---
        frame_input = tk.LabelFrame(root, text="Cấu hình đầu vào", padx=10, pady=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_input, text="File danh sách (.txt):").grid(row=0, column=0, sticky="w")
        entry_file = tk.Entry(frame_input, textvariable=self.file_path_var, width=55)
        entry_file.grid(row=0, column=1, padx=5)
        tk.Button(frame_input, text="Chọn File...", command=self.browse_file).grid(row=0, column=2)

        # --- Giao diện: Chọn Thư mục Lưu ---
        tk.Label(frame_input, text="Lưu video tại:").grid(row=1, column=0, sticky="w", pady=5)
        entry_save = tk.Entry(frame_input, textvariable=self.save_dir_var, width=55)
        entry_save.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(frame_input, text="Chọn Thư mục...", command=self.browse_folder).grid(row=1, column=2, pady=5)

        # --- Nút Bắt đầu ---
        self.btn_start = tk.Button(root, text="BẮT ĐẦU TẢI (START)", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.start_download_thread)
        self.btn_start.pack(pady=10)

        # --- Khu vực hiển thị Log ---
        frame_log = tk.LabelFrame(root, text="Nhật ký tải (Log)", padx=10, pady=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(frame_log, height=15, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

        # --- Tag màu cho log ---
        self.log_area.tag_config("info", foreground="blue")
        self.log_area.tag_config("success", foreground="green")
        self.log_area.tag_config("error", foreground="red")
        self.log_area.tag_config("warning", foreground="#FF8C00") # Dark Orange

    def log(self, message, tag=None):
        """Hàm ghi log vào giao diện"""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n", tag)
        self.log_area.see(tk.END) # Tự động cuộn xuống cuối
        self.log_area.config(state='disabled')

    def browse_file(self):
        filename = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Chọn file danh sách link",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filename:
            self.file_path_var.set(filename)

    def browse_folder(self):
        folder = filedialog.askdirectory(
            initialdir=os.getcwd(),
            title="Chọn thư mục lưu video"
        )
        if folder:
            self.save_dir_var.set(folder)

    def sanitize_filename(self, name):
        """Làm sạch tên file để tránh lỗi hệ điều hành"""
        # Thay thế ký tự cấm
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        name = name.replace("\n", "").replace("\r", "")
        # Xóa khoảng trắng thừa và thay bằng gạch dưới hoặc khoảng trắng
        return " ".join(name.split())

    def parse_data_file(self, file_path):
        """
        Đọc file format mới: 
        1. Ten_Video - https://link...
        """
        if not os.path.exists(file_path):
            self.log(f"LỖI: Không tìm thấy file tại {file_path}", "error")
            return []

        videos = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line: continue 

                # Regex giải thích:
                # ^(\d+\.)?   : Bắt đầu bằng số và dấu chấm (ví dụ "1."), có thể có hoặc không
                # \s* : Khoảng trắng tùy ý
                # (.*?)       : Group 1 - Tên tiêu đề (lấy ít nhất có thể)
                # \s*-\s* : Dấu gạch ngang ngăn cách (có thể có khoảng trắng quanh nó)
                # (https?://\S+) : Group 2 - Link (bắt đầu bằng http/https và không chứa khoảng trắng)
                
                match = re.search(r'^(\d+\.)?\s*(.*?)\s*-\s*(https?://\S+)', line)
                
                if match:
                    title = match.group(2).strip() # Lấy tên video
                    url = match.group(3).strip()   # Lấy link
                    
                    # Nếu tên bị rỗng (trường hợp dòng chỉ có "- Link"), đặt tên mặc định
                    if not title:
                        title = "Video_No_Name"
                        
                    videos.append({"title": title, "url": url})
                else:
                    # Log nhẹ để biết dòng nào bị bỏ qua (ví dụ dòng header DANH SÁCH)
                    if "http" in line:
                        self.log(f"Bỏ qua dòng không đúng định dạng: {line}", "warning")
            
            return videos
            
        except Exception as e:
            self.log(f"LỖI khi đọc file: {e}", "error")
            return []

    def start_download_thread(self):
        """Chạy process tải trong luồng riêng"""
        file_path = self.file_path_var.get()
        save_dir = self.save_dir_var.get()

        if not file_path or not save_dir:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file dữ liệu và thư mục lưu!")
            return

        # Khóa nút bấm
        self.btn_start.config(state='disabled', text="Đang tải...")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END) # Xóa log cũ
        self.log_area.config(state='disabled')

        # Tạo thread
        thread = threading.Thread(target=self.run_download_process, args=(file_path, save_dir))
        thread.daemon = True
        thread.start()

    def run_download_process(self, file_path, save_dir):
        self.log(f"--- Bắt đầu quét file: {os.path.basename(file_path)} ---", "info")
        videos = self.parse_data_file(file_path)
        
        if not videos:
            self.log("Không tìm thấy video nào hợp lệ trong file.", "warning")
            self.root.after(0, lambda: self.btn_start.config(state='normal', text="BẮT ĐẦU TẢI (START)"))
            return

        self.log(f"Tìm thấy {len(videos)} video hợp lệ.", "info")
        self.log(f"Thư mục lưu: {save_dir}\n", "info")

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Cấu hình yt-dlp logger
        class MyLogger:
            def __init__(self, app_instance):
                self.app = app_instance
            def debug(self, msg):
                if "[download]" in msg:
                    self.app.log(msg)
            def warning(self, msg):
                self.app.log(f"Cảnh báo: {msg}", "warning")
            def error(self, msg):
                self.app.log(f"Lỗi: {msg}", "error")

        for index, video in enumerate(videos):
            raw_title = video['title']
            url = video['url']
            safe_title = self.sanitize_filename(raw_title)
            
            # Đặt tên file đầu ra
            save_path = os.path.join(save_dir, f"{safe_title}.%(ext)s")
            
            self.log(f"[{index + 1}/{len(videos)}] Đang tải: {safe_title} ...", "info")

            ydl_opts = {
                'outtmpl': save_path,
                'format': 'bestvideo+bestaudio/best', 
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': True,
                'logger': MyLogger(self),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.bilibili.com/'
                }
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.log(f"-> XONG: {safe_title}", "success")
            except Exception as e:
                self.log(f"-> THẤT BẠI: {safe_title}. Lỗi: {str(e)}", "error")
            
            self.log("-" * 20)

        self.log("\n=== HOÀN TẤT TOÀN BỘ DANH SÁCH ===", "success")
        messagebox.showinfo("Thông báo", "Đã tải xong toàn bộ danh sách!")
        
        # Mở lại nút bấm
        self.root.after(0, lambda: self.btn_start.config(state='normal', text="BẮT ĐẦU TẢI (START)"))

if __name__ == "__main__":
    root = tk.Tk()
    app = BilibiliDownloaderApp(root)
    root.mainloop()