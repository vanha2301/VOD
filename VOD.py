import edge_tts
import asyncio
import nest_asyncio
import os
import shutil
import subprocess
import re

nest_asyncio.apply()

# ==============================================================================
# ⚙️ CẤU HÌNH
# ==============================================================================
INPUT_FILE_NAME = "script.txt"
OUTPUT_FILE = "Phim_Hoan_Chinh.mp3"
GIONG_DOC = "vi-VN-HoaiMyNeural"
MAX_SPEED_INCREASE = 100 
# ==============================================================================

class OneFileAudioGenerator:
    def __init__(self):
        self.ffmpeg_path = self._find_tool("ffmpeg")
        self.ffprobe_path = self._find_tool("ffprobe")

    def _find_tool(self, tool_name):
        path = shutil.which(tool_name)
        if path: return path
        possible_paths = [
            os.path.expandvars(rf"%LOCALAPPDATA%\Microsoft\WinGet\Links\{tool_name}.exe"),
            rf"C:\ffmpeg\bin\{tool_name}.exe",
            rf"D:\ffmpeg\bin\{tool_name}.exe"
        ]
        for p in possible_paths:
            if os.path.exists(p): return p
        print(f"❌ Không tìm thấy {tool_name}! Vui lòng cài FFmpeg.")
        return None

    def _get_audio_duration(self, file_path):
        try:
            cmd = [
                self.ffprobe_path, "-v", "error", "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except: return 0.0

    async def _generate_clip(self, text, filename, rate_str="+0%"):
        if not text or text.strip() == "": return False
        communicate = edge_tts.Communicate(text, GIONG_DOC, rate=rate_str, volume="+70%")
        await communicate.save(filename)
        return True

    def _create_silent_file(self, filename):
        """
        Tạo một file im lặng 'dự trữ' cực dài (ví dụ 10 phút = 600s).
        FFmpeg sẽ cắt lấy từng đoạn nhỏ từ file này để lấp chỗ trống.
        """
        print("🔇 Đang tạo file im lặng mẫu (Master Silence)...")
        cmd = [
            self.ffmpeg_path, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", 
            "-t", "600", # <--- SỬA LỖI: Tạo hẳn 600 giây (10 phút)
            "-c:a", "libmp3lame", filename
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def read_script_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"❌ Không tìm thấy file '{file_path}'")
            return []
        data = []
        pattern = re.compile(r"\[([\d\.]+)s\s*->\s*([\d\.]+)s\]\s*(.*)")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue 
                match = pattern.match(line)
                if match:
                    try:
                        data.append({
                            'start': float(match.group(1)), 
                            'end': float(match.group(2)), 
                            'text': match.group(3).strip()
                        })
                    except ValueError: pass
        data.sort(key=lambda x: x['start'])
        return data

    def create_full_movie(self, subtitles):
        if not self.ffmpeg_path or not self.ffprobe_path or not subtitles: return

        temp_folder = "temp_mix"
        # Xóa folder cũ để đảm bảo tạo lại file silence mới
        if os.path.exists(temp_folder): shutil.rmtree(temp_folder, ignore_errors=True)
        if not os.path.exists(temp_folder): os.makedirs(temp_folder)

        print(f"🎬 Đang xử lý {len(subtitles)} slot thời gian...")
        
        silent_file = os.path.abspath(f"{temp_folder}/silence.mp3").replace("\\", "/")
        # Gọi hàm tạo file silence dài
        self._create_silent_file(silent_file)

        concat_list_path = "mylist.txt"
        current_cursor = 0.0
        
        with open(concat_list_path, "w", encoding='utf-8') as f:
            for i, item in enumerate(subtitles):
                slot_duration = item['end'] - item['start']
                temp_filename = f"{temp_folder}/clip_{i}.mp3"
                abs_path = os.path.abspath(temp_filename).replace("\\", "/")
                
                # --- Lấp khoảng trống TRƯỚC (Gap Before) ---
                gap_before = item['start'] - current_cursor
                if gap_before > 0.01:
                    # Logic: Lấy 'silence.mp3', cắt lấy một khúc dài bằng 'gap_before'
                    f.write(f"file '{silent_file}'\n")
                    f.write(f"inpoint 0\n")          # Bắt đầu cắt từ giây 0
                    f.write(f"outpoint {gap_before}\n") # Cắt đến giây gap_before
                    current_cursor = item['start']

                # --- Xử lý Audio ---
                actual_duration = 0.0
                if item['text']:
                    print(f"Slot [{item['start']}->{item['end']}]: '{item['text'][:20]}...' ", end="")
                    asyncio.run(self._generate_clip(item['text'], temp_filename, rate_str="+0%"))
                    actual_duration = self._get_audio_duration(abs_path)

                    if actual_duration > slot_duration:
                        ratio = actual_duration / slot_duration
                        increase_percent = int((ratio - 1) * 100) + 10
                        if increase_percent > MAX_SPEED_INCREASE: increase_percent = MAX_SPEED_INCREASE
                        print(f"⚠️ Dài ({actual_duration:.2f}s) -> Tăng tốc +{increase_percent}%")
                        asyncio.run(self._generate_clip(item['text'], temp_filename, rate_str=f"+{increase_percent}%"))
                        actual_duration = self._get_audio_duration(abs_path)
                    else:
                        print(f"✅ OK ({actual_duration:.2f}s)")
                    
                    f.write(f"file '{abs_path}'\n")
                else:
                    print(f"Slot [{item['start']}->{item['end']}]: (Im lặng hoàn toàn)")

                # --- Lấp khoảng trống SAU (Padding) ---
                remaining_in_slot = slot_duration - actual_duration
                if remaining_in_slot > 0.01:
                    f.write(f"file '{silent_file}'\n")
                    f.write(f"inpoint 0\n")
                    f.write(f"outpoint {remaining_in_slot}\n")
                
                current_cursor = item['end']

        print("\n⏳ Đang gộp file...")
        cmd = [
            self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path, "-c", "copy", OUTPUT_FILE
        ]
        subprocess.run(cmd)
        print(f"✅ XONG! File: {OUTPUT_FILE}")
        os.startfile(OUTPUT_FILE)

if __name__ == "__main__":
    generator = OneFileAudioGenerator()
    parsed_script = generator.read_script_file(INPUT_FILE_NAME)
    if parsed_script:
        generator.create_full_movie(parsed_script)