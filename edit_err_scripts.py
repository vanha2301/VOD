import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import re
import os

class Segment:
    def __init__(self, start, end, text, original_line):
        self.start = start
        self.end = end
        self.text = text
        self.original_line = original_line
        self.modified = False
        self.log_msg = ""

    def to_string(self):
        # Format lại thành chuỗi [start -> end] text
        # Sử dụng .2f để giữ 2 số thập phân giống format gốc
        return f"[{self.start:.2f}s -> {self.end:.2f}s] {self.text}"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ Sửa Timestamp - Trần Văn Hà TDTU")
        self.root.geometry("800x600")
        
        self.segments = []
        self.filename = "output.txt"

        # --- UI SETUP ---
        
        # Frame Control
        control_frame = tk.Frame(root, pady=10)
        control_frame.pack(fill=tk.X)

        self.btn_load = tk.Button(control_frame, text="1. Chọn File (output.txt)", command=self.load_file, bg="#e1f5fe")
        self.btn_load.pack(side=tk.LEFT, padx=10)

        self.btn_process = tk.Button(control_frame, text="2. Tự Động Sửa Lỗi", command=self.process_data, state=tk.DISABLED, bg="#fff9c4")
        self.btn_process.pack(side=tk.LEFT, padx=10)

        self.btn_save = tk.Button(control_frame, text="3. Lưu File (output_final.txt)", command=self.save_file, state=tk.DISABLED, bg="#c8e6c9")
        self.btn_save.pack(side=tk.LEFT, padx=10)

        # Label status
        self.lbl_status = tk.Label(root, text="Chưa tải file nào.", fg="gray")
        self.lbl_status.pack()

        # Frame hiển thị nội dung
        content_frame = tk.Frame(root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Cột trái: Log báo cáo
        tk.Label(content_frame, text="Báo cáo sửa lỗi:").grid(row=0, column=0, sticky="w")
        self.txt_log = scrolledtext.ScrolledText(content_frame, width=40, height=25)
        self.txt_log.grid(row=1, column=0, sticky="ns")

        # Cột phải: Preview dữ liệu
        tk.Label(content_frame, text="Xem trước dữ liệu (Sau khi sửa):").grid(row=0, column=1, sticky="w")
        self.txt_preview = scrolledtext.ScrolledText(content_frame, width=50, height=25)
        self.txt_preview.grid(row=1, column=1, sticky="nsew")

        content_frame.grid_columnconfigure(1, weight=1)

    def parse_line(self, line):
        # Regex bắt format [241.92s -> 243.66s] Text
        pattern = r"\[([\d\.]+)s\s*->\s*([\d\.]+)s\]\s*(.*)"
        match = re.match(pattern, line.strip())
        if match:
            return float(match.group(1)), float(match.group(2)), match.group(3)
        return None

    def load_file(self):
        # Mở dialog chọn file, mặc định tìm output.txt ở thư mục hiện tại
        initial_dir = os.getcwd()
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Chọn file dữ liệu",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )

        if not file_path:
            return

        self.filename = file_path
        self.segments = []
        self.txt_log.delete(1.0, tk.END)
        self.txt_preview.delete(1.0, tk.END)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                parsed = self.parse_line(line)
                if parsed:
                    self.segments.append(Segment(parsed[0], parsed[1], parsed[2], line.strip()))
                else:
                    # Giữ nguyên các dòng không đúng format (như dòng trống)
                    if line.strip():
                        self.txt_log.insert(tk.END, f"Bỏ qua dòng lỗi format: {line.strip()}\n")

            self.lbl_status.config(text=f"Đã tải: {os.path.basename(file_path)} ({len(self.segments)} dòng)", fg="blue")
            self.btn_process.config(state=tk.NORMAL)
            
            # Hiển thị dữ liệu gốc lên preview
            self.update_preview()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được file: {e}")

    def process_data(self):
        if not self.segments:
            return

        count_fixed = 0
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.insert(tk.END, "--- BẮT ĐẦU QUÉT VÀ SỬA LỖI ---\n\n")

        # Duyệt qua danh sách (trừ phần tử cuối cùng)
        for i in range(len(self.segments) - 1):
            current_seg = self.segments[i]
            next_seg = self.segments[i+1]

            # Logic: Nếu kết thúc hiện tại < bắt đầu tiếp theo (GAP)
            # Thay đổi kết thúc hiện tại = bắt đầu tiếp theo
            # Sử dụng sai số nhỏ 0.001 để tránh so sánh float bằng nhau
            if current_seg.end < next_seg.start - 0.001: 
                old_end = current_seg.end
                
                # THỰC HIỆN SỬA
                current_seg.end = next_seg.start
                current_seg.modified = True
                
                # Ghi log
                msg = (f"[Dòng {i+1}] Đã sửa Gap:\n"
                       f"   Cũ: {old_end:.2f}s\n"
                       f"   Mới: {current_seg.end:.2f}s (Khớp với dòng {i+2})\n"
                       f"-----------------------------\n")
                self.txt_log.insert(tk.END, msg)
                count_fixed += 1

        self.lbl_status.config(text=f"Hoàn tất! Đã sửa {count_fixed} lỗi khoảng trống.", fg="green")
        if count_fixed == 0:
            self.txt_log.insert(tk.END, "Không tìm thấy khoảng trống (gap) nào cần sửa.")
        
        self.update_preview()
        self.btn_save.config(state=tk.NORMAL)

    def update_preview(self):
        self.txt_preview.delete(1.0, tk.END)
        for seg in self.segments:
            line = seg.to_string()
            # Nếu dòng này đã sửa thì highlight hoặc đánh dấu (ở đây mình chỉ in ra)
            self.txt_preview.insert(tk.END, line + "\n")

    def save_file(self):
        # Mặc định lưu thành output_final.txt
        default_name = "output_final.txt"
        file_path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for seg in self.segments:
                    f.write(seg.to_string() + "\n")
            
            messagebox.showinfo("Thành công", f"Đã lưu file tại:\n{file_path}")
            self.lbl_status.config(text=f"Đã lưu file: {os.path.basename(file_path)}", fg="black")
            
        except Exception as e:
            messagebox.showerror("Lỗi lưu file", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()