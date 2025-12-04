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
INPUT_FILE = "A:\\dataYTB\\Tua-Lai-Tuyet-Vong\\Scripts-Tualaituyetvong\\No-translate\\Script-No-translate-tap2.txt"
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
        Hãy đóng vai một Biên dịch viên kiêm Biên tập kịch bản lồng tiếng chuyên nghiệp, chuyên xử lý phim hoạt hình 3D Trung Quốc thể loại Tu Tiên (Huyền Huyễn, Kiếm Hiệp).
        Nhiệm vụ: Xử lý dữ liệu thô (gồm thời gian và tiếng Trung), dịch sang tiếng Việt và tối ưu hóa câu từ để phù hợp với tốc độ đọc của AI (TTS).
        Dữ liệu đầu vào (Input): Lặp lại theo chu kỳ 3 dòng:
        Dòng 1: Thời gian bắt đầu (Start).
        Dòng 2: Thời gian kết thúc (End).
        Dòng 3: Nội dung tiếng Trung (thường là Voice-to-Text nên có lỗi đồng âm).
        Yêu cầu đầu ra (Output) và Quy tắc xử lý (Cực kỳ quan trọng):
        Định dạng (Format): Ghép thành 1 dòng duy nhất: [Start -> End] Nội dung tiếng Việt
        Tối ưu hóa độ dài cho TTS (Ưu tiên số 1):
        Tính toán thời gian: Bạn phải ước lượng khoảng thời gian ($End - Start$).
        Nguyên tắc "Cắt gọt mạnh tay": Nếu khoảng thời gian ngắn (dưới 2s), câu dịch PHẢI cực ngắn.
        Loại bỏ hư từ: Xóa bỏ hoàn toàn các từ đệm không cần thiết như: "thì, là, mà, bị, được, rằng, những, các, của...".
        Văn phong khẩu ngữ: Chuyển văn viết thành văn nói cộc lốc, dứt khoát (ví dụ: "Ta không thể đi được" -> "Ta không thể đi").
        Mục tiêu: Đảm bảo AI đọc thong thả, rõ chữ và kết thúc kịp trước khi sang dòng thời gian tiếp theo.
        Ngữ cảnh & Thuật ngữ:
        Dùng văn phong Tu Tiên/Cổ trang (Tại hạ, Bổn tọa, Đạo hữu, Ngươi/Ta, Hắn...).
        Tuyệt đối không dùng từ hiện đại (Anh/Em/Cậu/Tớ).
        Sửa lỗi dữ liệu nguồn (Voice-to-Text):
        Văn bản gốc thường sai từ đồng âm. PHẢI suy luận ngữ cảnh để dịch đúng nghĩa.
        Ví dụ: Thấy "Tiễn" (tên) ở ngữ cảnh thời gian -> Dịch là "Gian"; Thấy "Phong" (đóng) ở ngữ cảnh thời tiết -> Dịch là "Gió".
        Ví dụ mẫu về cách xử lý độ dài và chỉ trả về phần nội dung dịch:
        Input (1.2s): "Ngươi mau chóng rời khỏi nơi này đi nếu không sẽ gặp nguy hiểm"
        Output Sai: [10s -> 11.2s] Ngươi mau chóng rời khỏi nơi này đi nếu không sẽ gặp nguy hiểm (Quá dài, đọc không kịp).
        Output Đúng: [10s -> 11.2s] Ngươi mau đi! Ở đây nguy hiểm!
        Hãy bắt đầu xử lý nội dung dưới đây:
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