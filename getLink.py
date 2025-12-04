import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import random
import unicodedata
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from deep_translator import GoogleTranslator

class BilibiliScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tool Bilibili Siêu Tốc (Multi-Thread) - Trần Văn Hà")
        self.root.geometry("700x600")
        
        # --- BIẾN TOÀN CỤC ---
        self.driver = None
        self.is_running = False
        self.stop_event = False # Cờ để dừng chương trình

        # --- GIAO DIỆN ---
        frame_input = ttk.LabelFrame(root, text="Cấu hình", padding=(10, 10))
        frame_input.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_input, text="Link Collection/List Bilibili:").pack(anchor="w")
        self.url_entry = ttk.Entry(frame_input, width=80)
        self.url_entry.pack(fill="x", pady=5)
        
        # Checkbox chạy ẩn
        self.headless_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_input, text="Chạy ẩn (Headless Mode - Nhanh hơn)", variable=self.headless_var).pack(anchor="w")

        # Nút bấm
        btn_frame = ttk.Frame(frame_input)
        btn_frame.pack(pady=5)
        self.btn_start = ttk.Button(btn_frame, text="🚀 Bắt đầu (Tốc độ cao)", command=self.start_thread)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ttk.Button(btn_frame, text="⛔ Dừng lại", command=self.stop_process, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # Log
        frame_log = ttk.LabelFrame(root, text="Nhật ký hoạt động", padding=(10, 10))
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(frame_log, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True)

        self.lbl_status = ttk.Label(root, text="Trạng thái: Sẵn sàng", relief=tk.SUNKEN, anchor="w")
        self.lbl_status.pack(side=tk.BOTTOM, fill="x")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def stop_process(self):
        self.stop_event = True
        self.log("⚠️ Đang yêu cầu dừng... Vui lòng đợi xử lý nốt tác vụ hiện tại.")
        self.btn_stop.config(state="disabled")

    def clean_name(self, text):
        """Chuẩn hóa: Không dấu, CamedCase, Không cách"""
        if not text: return "NoName"
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore').decode("utf-8")
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        clean_text = "".join(word.title() for word in text.split())
        return clean_text

    def translate_worker(self, item):
        """Hàm này sẽ được chạy song song bởi nhiều thợ (worker)"""
        if self.stop_event: return None
        
        cn_title = item['cn_title']
        raw_link = item['link']
        
        translator = GoogleTranslator(source='zh-CN', target='vi')
        final_name = "Unknown"
        
        try:
            # 1. Dịch
            vi_title = translator.translate(cn_title.strip())
            # 2. Chuẩn hóa
            final_name = self.clean_name(vi_title)
        except:
            # Nếu lỗi dịch thì lấy tên gốc chuẩn hóa
            final_name = self.clean_name(cn_title)
            
        return {
            "final_name": final_name,
            "link": raw_link
        }

    def start_thread(self):
        if self.is_running: return
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Thiếu thông tin", "Nhập Link đi bạn ơi!")
            return

        self.is_running = True
        self.stop_event = False
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="Trạng thái: Đang chạy hết tốc lực...")
        self.log("="*40)
        self.log(f"Bắt đầu xử lý: {url}")
        
        threading.Thread(target=self.run_process, args=(url,), daemon=True).start()

    def run_process(self, url):
        options = webdriver.ChromeOptions()
        if self.headless_var.get():
            options.add_argument("--headless") # Chạy ẩn để nhanh hơn
            self.log("👻 Chế độ chạy ẩn (Headless): BẬT")

        try:
            self.log("🚀 Đang khởi động Chrome...")
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            all_videos = [] # Chứa kết quả cuối cùng
            seen_links = set()
            
            self.driver.get(url)
            self.log("🔗 Đã vào trang. Đang quét dữ liệu...")
            time.sleep(2) # Chờ load nhẹ

            page_count = 1
            
            while not self.stop_event:
                self.log(f"\n--- 📄 TRANG {page_count} ---")
                
                # Cuộn nhanh xuống đáy để load hết ảnh
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5) 
                
                # 1. GIAI ĐOẠN QUÉT (Chỉ lấy data thô, cực nhanh)
                cards = self.driver.find_elements(By.CSS_SELECTOR, ".bili-cover-card")
                raw_items = []
                
                for card in cards:
                    try:
                        link = card.get_attribute("href")
                        if not link: continue
                        if link.startswith("//"): link = "https:" + link
                        link = link.split("?")[0]
                        
                        if link not in seen_links:
                            seen_links.add(link)
                            # Lấy tên gốc
                            cn_title = "No Title"
                            try:
                                img = card.find_element(By.TAG_NAME, "img")
                                cn_title = img.get_attribute("alt")
                                if not cn_title: cn_title = card.text.split('\n')[0]
                            except: pass
                            
                            raw_items.append({"cn_title": cn_title, "link": link})
                    except: continue

                if not raw_items:
                    self.log("⚠️ Không tìm thấy video mới ở trang này.")
                else:
                    self.log(f" -> Tìm thấy {len(raw_items)} video mới. Đang kích hoạt 5 luồng dịch...")

                    # 2. GIAI ĐOẠN DỊCH SONG SONG (Multi-threading)
                    # Sử dụng 5 thợ (workers) dịch cùng lúc
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        # Giao việc cho các worker
                        futures = [executor.submit(self.translate_worker, item) for item in raw_items]
                        
                        # Chờ và thu hoạch kết quả khi xong
                        for future in as_completed(futures):
                            if self.stop_event: break
                            result = future.result()
                            if result:
                                all_videos.append(result)
                                # Log gọn nhẹ để đỡ lag giao diện
                                # self.log(f"   + Xong: {result['final_name']}")

                self.log(f" -> Tổng cộng đã lấy: {len(all_videos)} video.")

                # 3. CHUYỂN TRANG
                if self.stop_event: break
                
                try:
                    next_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Trang tiếp theo') or contains(text(), 'Next') or contains(text(), '下一页')]")
                    if not next_buttons:
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".vui_pagenation--btn-side")

                    clicked_next = False
                    if next_buttons:
                        btn = next_buttons[-1]
                        if "disabled" not in btn.get_attribute("class"):
                            self.driver.execute_script("arguments[0].click();", btn)
                            self.log("👉 Qua trang tiếp theo...")
                            time.sleep(3) # Thời gian chờ trang sau load
                            page_count += 1
                            clicked_next = True
                    
                    if not clicked_next:
                        self.log("⛔ Đã đến trang cuối.")
                        break
                except:
                    break

            # Ghi file
            self.save_files(all_videos)

        except Exception as e:
            self.log(f"❌ LỖI: {e}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            if self.driver:
                self.driver.quit()
            self.is_running = False
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.lbl_status.config(text="Trạng thái: Hoàn tất")

    def save_files(self, all_videos):
        self.log("\n💾 Đang lưu file...")
        try:
            with open("data_phim.txt", "w", encoding="utf-8") as f1:
                f1.write(f"DANH SÁCH ({len(all_videos)} tập)\n")
                for idx, vid in enumerate(all_videos, 1):
                    f1.write(f"{idx}. {vid['final_name']} - {vid['link']}\n")

            with open("data_sheet.txt", "w", encoding="utf-8") as f2:
                for idx, vid in enumerate(all_videos, 1):
                    line = f"{idx}\t{vid['final_name']}\t{vid['link']}"
                    f2.write(line + "\n")
            
            self.log(f"✅ XONG! Đã lưu {len(all_videos)} video.")
            messagebox.showinfo("Thành công", f"Đã xử lý xong {len(all_videos)} tập!\nTốc độ đã được tối ưu hóa.")
            
        except Exception as e:
            self.log(f"Lỗi ghi file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BilibiliScraperApp(root)
    root.mainloop()