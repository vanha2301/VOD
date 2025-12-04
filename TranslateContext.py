import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# 1. Nạp biến môi trường & Cấu hình
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Lỗi: Không tìm thấy biến 'GEMINI_API_KEY' trong file .env")
    exit()

genai.configure(api_key=api_key)

# ================= CẤU HÌNH =================

MODEL_NAME = "gemini-2.5-flash"
INPUT_FILE = "input.txt"
OUTPUT_FILE = "output.txt"
BATCH_SIZE = 500  # Mỗi lần gửi 500 câu thoại (1500 dòng)

genai.configure(api_key=api_key)

# ================= HÀM XỬ LÝ =================
def read_file_content(filepath):
    if not os.path.exists(filepath):
        print(f"Lỗi: Không tìm thấy file {filepath}")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def translate_batch(batch_lines, model):
    prompt = """
    Bạn là biên dịch viên phim Hàn Quốc "The Player 2".
    Input: Các nhóm 3 dòng (Start, End, Korean Text).
    Output: Dịch sang tiếng Việt, giữ đúng format [Start -> End] Nội dung.
    Văn phong: Tự nhiên, đời thường, xã hội đen.
    KHÔNG thêm lời dẫn.
    
    Dữ liệu:
    """
    full_prompt = prompt + "\n" + "\n".join(batch_lines)
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi API: {e}")
        return None

# ================= MAIN =================
if __name__ == "__main__":
    lines = read_file_content(INPUT_FILE)
    
    if lines:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # BƯỚC 1: Xóa trắng file output cũ (nếu có) để chuẩn bị ghi mới
        print("Đang khởi tạo file đầu ra...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("") # Ghi rỗng để reset file
        
        lines_per_batch = BATCH_SIZE * 3
        total_batches = (len(lines) + lines_per_batch - 1) // lines_per_batch
        
        print(f"Tổng: {len(lines)} dòng. Chia làm {total_batches} đợt.")

        for i in range(0, len(lines), lines_per_batch):
            batch = lines[i : i + lines_per_batch]
            current_batch_num = (i // lines_per_batch) + 1
            
            print(f"--- Đang xử lý đợt {current_batch_num}/{total_batches} ---")
            
            # Gọi hàm dịch
            result = translate_batch(batch, model)
            
            if result:
                # BƯỚC 2: Ghi ngay vào file (Mode 'a' = append/nối tiếp)
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(result + "\n")
                print(f"✅ Đã lưu đợt {current_batch_num} vào {OUTPUT_FILE}")
            else:
                print(f"❌ Đợt {current_batch_num} bị lỗi, bỏ qua.")
            
            # Nghỉ 2s tránh bị ban
            time.sleep(1)

        print(f"\nHOÀN TẤT! Kiểm tra file {OUTPUT_FILE}")