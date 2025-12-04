import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from deep_translator import GoogleTranslator

def get_bilibili_translated(url):
    # --- CẤU HÌNH ---
    # Dùng 'zh-CN' (Trung Quốc đại lục) để dịch chuẩn xác hơn 'auto'
    translator = GoogleTranslator(source='zh-CN', target='vi')
    
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Bỏ comment nếu muốn chạy ẩn
    
    print("🚀 Đang khởi động Chrome và hệ thống dịch thuật...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    all_videos = []
    seen_links = set()
    
    try:
        driver.get(url)
        print(f"🔗 Đang truy cập: {url}")
        time.sleep(3)

        page_count = 1
        
        while True:
            print(f"\n--- 📄 ĐANG XỬ LÝ TRANG {page_count} ---")
            
            # 1. Cuộn xuống đáy
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # 2. Lấy danh sách thẻ video
            cards = driver.find_elements(By.CSS_SELECTOR, ".bili-cover-card")
            print(f"   -> Tìm thấy {len(cards)} video. Đang dịch tiêu đề...")
            
            for card in cards:
                try:
                    # Lấy Link
                    link = card.get_attribute("href")
                    if not link: continue
                    if link.startswith("//"): link = "https:" + link
                    link = link.split("?")[0]
                    
                    if link not in seen_links:
                        seen_links.add(link)
                        
                        # Lấy Tên Gốc (Tiếng Trung)
                        cn_title = "No Title"
                        try:
                            img = card.find_element(By.TAG_NAME, "img")
                            cn_title = img.get_attribute("alt")
                            if not cn_title: cn_title = card.text.split('\n')[0]
                        except:
                            pass

                        # --- DỊCH THUẬT ---
                        vi_title = cn_title
                        try:
                            if cn_title and cn_title != "No Title":
                                vi_title = translator.translate(cn_title.strip())
                                print(f"      ✅ [Dịch]: {vi_title}")
                                # Ngủ nhẹ 0.2s để Google không chặn
                                time.sleep(random.uniform(0.2, 0.5))
                        except Exception as e:
                            print(f"      ⚠️ Lỗi dịch: {e}")
                        
                        # Lưu dữ liệu
                        all_videos.append({
                            "vi_title": vi_title,
                            "cn_title": cn_title,
                            "link": link
                        })
                        
                except Exception as e:
                    continue

            # 3. CHUYỂN TRANG
            try:
                next_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Trang tiếp theo') or contains(text(), 'Next') or contains(text(), '下一页')]")
                if not next_buttons:
                     next_buttons = driver.find_elements(By.CSS_SELECTOR, ".vui_pagenation--btn-side")

                clicked_next = False
                if next_buttons:
                    btn = next_buttons[-1]
                    if "disabled" not in btn.get_attribute("class"):
                        driver.execute_script("arguments[0].click();", btn)
                        print("👉 Đang chuyển sang trang tiếp theo...")
                        time.sleep(4)
                        page_count += 1
                        clicked_next = True
                
                if not clicked_next:
                    print("⛔ Đã đến trang cuối.")
                    break 

            except Exception as e:
                break

        # --- PHẦN XUẤT RA 2 FILE RIÊNG BIỆT ---
        print("\n" + "="*60)
        print(f"🎉 HOÀN TẤT! TỔNG CỘNG: {len(all_videos)} TẬP")
        print("="*60)
        
        # FILE 1: DATA PHIM (Dễ đọc cho người)
        file_readable = "data_phim.txt"
        with open(file_readable, "w", encoding="utf-8") as f1:
            f1.write(f"DANH SÁCH PHIM ({len(all_videos)} tập)\n")
            f1.write("="*40 + "\n")
            for idx, vid in enumerate(all_videos, 1):
                f1.write(f"Tập {idx}: {vid['vi_title']} ({vid['cn_title']})\n")
                f1.write(f"Link: {vid['link']}\n")
                f1.write("-" * 20 + "\n")

        # FILE 2: DATA SHEET (Dùng để Paste vào Excel/Google Sheet)
        file_excel = "data_sheet.txt"
        with open(file_excel, "w", encoding="utf-8") as f2:
            # Ghi tiêu đề cột (tùy chọn)
            # f2.write("STT\tTên Phim\tLink\n") 
            for idx, vid in enumerate(all_videos, 1):
                # Cấu trúc: [Số TT] [Tab] [Tên Tiếng Việt] [Tab] [Link]
                # Dấu \t giúp Excel tự nhảy sang cột bên cạnh
                line = f"{idx}\t{vid['vi_title']} ({vid['cn_title']})\t{vid['link']}"
                f2.write(line + "\n")
                
        print(f"📁 Đã tạo xong 2 file:")
        print(f"   1. {file_readable} (Để đọc)")
        print(f"   2. {file_excel} (Mở lên -> Ctrl+A -> Copy -> Paste vào Google Sheet)")

    except Exception as e:
        print(f"❌ Lỗi Fatal: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    target_url = "https://space.bilibili.com/477293262/lists/4405308"
    get_bilibili_translated(target_url)