import os
from PIL import Image, ImageFilter, ImageDraw, ImageFont

def thay_the_phu_de(
    duong_dan_anh_goc,
    duong_dan_anh_moi,
    khu_vuc_lam_mo,
    noi_dung_text_moi,
    co_chu=30,
    mau_chu=(255, 255, 255), # Màu trắng (RGB)
    duong_dan_font=None, # Nếu không có, sẽ cố dùng font mặc định hệ thống
    do_lam_mo=15 # Số càng lớn càng mờ
):
    """
    Hàm này làm mờ một khu vực trên ảnh và viết text mới lên đó.

    Args:
        D:\VOD\image.png (str): Đường dẫn đến file ảnh đầu vào.
        duong_dan_anh_moi (str): Đường dẫn để lưu file ảnh đầu ra.
        khu_vuc_lam_mo (tuple): Tọa độ hộp cần làm mờ (trái, trên, phải, dưới). Ví dụ: (50, 400, 750, 500).
        noi_dung_text_moi (str): Nội dung chữ muốn viết lên.
        co_chu (int): Kích thước font chữ.
        mau_chu (tuple): Màu chữ dạng RGB. Mặc định là trắng.
        duong_dan_font (str): Đường dẫn đến file font (.ttf hoặc .otf). Nên cung cấp để có kết quả đẹp nhất.
        do_lam_mo (int): Bán kính làm mờ (Gaussian Blur).
    """
    try:
        # 1. Mở ảnh gốc
        img = Image.open(duong_dan_anh_goc).convert("RGB")
        print(f"Đã mở ảnh: {duong_dan_anh_goc}, Kích thước: {img.size}")

        # --- PHẦN 1: LÀM MỜ KHU VỰC CŨ ---

        # 2. Cắt lấy khu vực cần làm mờ
        # khu_vuc_lam_mo có dạng (left, top, right, bottom)
        region_to_blur = img.crop(khu_vuc_lam_mo)

        # 3. Áp dụng bộ lọc làm mờ (Gaussian Blur) lên khu vực vừa cắt
        blurred_region = region_to_blur.filter(ImageFilter.GaussianBlur(radius=do_lam_mo))

        # 4. Dán khu vực đã làm mờ trở lại vị trí cũ trên ảnh gốc
        img.paste(blurred_region, khu_vuc_lam_mo)
        print("Đã làm mờ khu vực chỉ định.")


        # --- PHẦN 2: VIẾT TEXT MỚI ---

        # 5. Tạo đối tượng để vẽ lên ảnh
        draw = ImageDraw.Draw(img)

        # 6. Tải font chữ
        try:
            if duong_dan_font and os.path.exists(duong_dan_font):
                font = ImageFont.truetype(duong_dan_font, co_chu)
            else:
                # Thử dùng font phổ biến trên Windows nếu không cung cấp font riêng
                font = ImageFont.truetype("arial.ttf", co_chu)
                print("Đang sử dụng font Arial mặc định của hệ thống.")
        except IOError:
            # Nếu không tìm thấy Arial, dùng font bitmap mặc định (rất xấu, chỉ để dự phòng)
            font = ImageFont.load_default()
            print("Cảnh báo: Không tìm thấy font đẹp, đang dùng font mặc định (sẽ nhỏ và xấu).")


        # 7. Tính toán vị trí để căn giữa text vào khu vực đã làm mờ
        # Lấy kích thước của khu vực làm mờ
        box_width = khu_vuc_lam_mo[2] - khu_vuc_lam_mo[0]
        box_height = khu_vuc_lam_mo[3] - khu_vuc_lam_mo[1]

        # Lấy kích thước của đoạn text khi dùng font này
        # textbbox trả về (left, top, right, bottom) của text
        text_box = draw.textbbox((0, 0), noi_dung_text_moi, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]

        # Tính tọa độ X, Y để bắt đầu vẽ (căn giữa)
        x = khu_vuc_lam_mo[0] + (box_width - text_width) / 2
        # Điều chỉnh y một chút để text nằm giữa theo chiều dọc tốt hơn
        y = khu_vuc_lam_mo[1] + (box_height - text_height) / 2 - text_box[1]

        # 8. Vẽ text lên ảnh
        # Bạn có thể thêm viền (stroke) để chữ rõ hơn nếu nền vẫn hơi loang lổ
        draw.text(
            (x, y),
            noi_dung_text_moi,
            font=font,
            fill=mau_chu,
            # stroke_width=2, stroke_fill="black" # Bỏ comment dòng này nếu muốn viền đen xung quanh chữ
        )
        print(f"Đã viết text mới: '{noi_dung_text_moi}'")


        # --- PHẦN 3: LƯU ẢNH ---

        # 9. Lưu ảnh kết quả
        img.save(duong_dan_anh_moi)
        print(f"Thành công! Ảnh mới đã được lưu tại: {duong_dan_anh_moi}")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file ảnh gốc tại '{duong_dan_anh_goc}'")
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}")


# ==========================================
# VÍ DỤ CÁCH SỬ DỤNG
# ==========================================

if __name__ == "__main__":
    # 1. Chuẩn bị file ảnh
    # Hãy đảm bảo bạn có 1 file ảnh tên là 'anh_mau.jpg' cùng thư mục với file code này.
    # Hoặc thay đổi đường dẫn bên dưới.
    input_image = "anh_mau.jpg"
    output_image = "anh_da_sua_phu_de.jpg"

    # TẠO ẢNH MẪU GIẢ LẬP (Nếu bạn chưa có ảnh để test)
    # Phần này chỉ để tạo ra 1 ảnh có phụ đề giả để bạn test code.
    # Nếu bạn có ảnh thật rồi thì xóa hoặc comment phần tạo ảnh này đi.
    if not os.path.exists(input_image):
        print("Đang tạo ảnh mẫu để test...")
        img_test = Image.new('RGB', (800, 600), color=(100, 100, 100))
        d_test = ImageDraw.Draw(img_test)
        try:
            f_test = ImageFont.truetype("arial.ttf", 40)
        except:
            f_test = ImageFont.load_default()
        # Vẽ một vùng phụ đề giả màu đen ở dưới đáy
        d_test.rectangle([(50, 500), (750, 580)], fill=(0,0,0))
        d_test.text((100, 520), "Đây là phụ đề cũ cần xóa đi", font=f_test, fill="yellow")
        img_test.save(input_image)
        print("Đã tạo xong ảnh mẫu.")
    # -------------------------------------------------------


    # 2. Cấu hình các tham số

    # QUAN TRỌNG: Bạn cần xác định tọa độ hộp chứa phụ đề cũ.
    # Mở ảnh bằng Paint hoặc Photoshop để xem tọa độ (Left, Top, Right, Bottom)
    # Ví dụ này giả định vùng phụ đề nằm ở dưới đáy ảnh 800x600.
    AREA_TO_BLUR = (50, 500, 750, 580) # (Trái, Trên, Phải, Dưới)

    NEW_TEXT = "Đây là phụ đề mới, xịn hơn nhiều!"
    FONT_SIZE = 35

    # Đường dẫn đến font chữ đẹp (ví dụ bạn tải font Roboto-Bold.ttf về để cùng thư mục)
    # Nếu không có, code sẽ cố dùng Arial của Windows.
    FONT_PATH = "Roboto-Bold.ttf" # Thay bằng đường dẫn font của bạn nếu có

    # 3. Gọi hàm thực thi
    thay_the_phu_de(
        duong_dan_anh_goc=input_image,
        duong_dan_anh_moi=output_image,
        khu_vuc_lam_mo=AREA_TO_BLUR,
        noi_dung_text_moi=NEW_TEXT,
        co_chu=FONT_SIZE,
        duong_dan_font=FONT_PATH,
        do_lam_mo=20 # Làm mờ mạnh hơn một chút
    )