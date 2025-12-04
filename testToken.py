import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Nạp biến môi trường & Cấu hình
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Lỗi: Không tìm thấy biến 'GEMINI_API_KEY' trong file .env")
    exit()

genai.configure(api_key=api_key)

# 2. Chọn Model (Dùng model bạn định chạy để đếm cho chuẩn)
model = genai.GenerativeModel("gemini-2.5-flash")

input_filename = "input.txt"

# 3. Xử lý đọc file và đếm
if os.path.exists(input_filename):
    try:
        print(f"📂 Đang đọc file '{input_filename}'...")
        
        # Đọc toàn bộ nội dung file vào biến 'content'
        with open(input_filename, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            print("⚠️ File input.txt bị rỗng, không có gì để đếm.")
        else:
            # Gọi hàm đếm token của Google
            print("⏳ Đang gửi yêu cầu đếm token lên server...")
            token_info = model.count_tokens(content)
            
            # In kết quả
            total = token_info.total_tokens
            print("\n" + "="*30)
            print(f"📊 KẾT QUẢ ĐẾM TOKEN")
            print("="*30)
            print(f"• Tổng số ký tự (ước lượng): {len(content):,}")
            print(f"• Tổng số Token chính xác:   {total:,}")
            print("-" * 30)
            
            # Đánh giá sơ bộ dựa trên limit Free (250k TPM)
            limit_tpm = 250000 
            percent = (total / limit_tpm) * 100
            print(f"💡 Chiếm khoảng {percent:.2f}% giới hạn TPM (Token/phút) của gói Free.")
            
            if total > limit_tpm:
                print("⚠️ CẢNH BÁO: File này quá lớn để gửi trong 1 phút (vượt TPM). Bạn phải chia nhỏ file ra!")
            else:
                print("✅ File này an toàn để gửi (nếu gửi 1 lần).")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
else:
    print(f"❌ Không tìm thấy file '{input_filename}' cùng thư mục với file code này.")