import subprocess
import shutil
import os

# ================= CẤU HÌNH =================
VIDEO_INPUT = "Tualaituyetvong_tap1.mp4"       # Video gốc (Dài)
AUDIO_NEW = "Phim_Hoan_Chinh.mp3"     # Audio thuyết minh (Ngắn hơn video)
OUTPUT_FILE = "Video_Da_Mix.mp4"      # Kết quả sẽ bị cắt ngắn theo Audio
# ============================================

def mix_video_audio(video_path, audio_path, output_path):
    # 1. Tìm FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        possible_paths = [r"C:\ffmpeg\bin\ffmpeg.exe", r"D:\ffmpeg\bin\ffmpeg.exe"]
        for p in possible_paths:
            if os.path.exists(p):
                ffmpeg_path = p
                break
    
    if not ffmpeg_path:
        print("❌ Lỗi: Không tìm thấy FFmpeg.")
        return

    print(f"🎬 Đang trộn và cắt video theo độ dài audio...")

    # 2. Tạo lệnh FFmpeg
    # SỬA ĐỔI QUAN TRỌNG:
    # - Trong filter_complex: Đổi 'duration=first' -> 'duration=shortest'
    # - Thêm tham số '-shortest' ở cuối cùng
    
    cmd = [
        ffmpeg_path, "-y",
        "-i", video_path,
        "-i", audio_path,
        # [Sửa 1] duration=shortest: Để audio trộn xong là ngắt ngay khi hết nhạc
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest:dropout_transition=0[aout]",
        
        "-map", "0:v:0",    # Lấy hình video gốc
        "-map", "[aout]",   # Lấy audio đã trộn
        
        "-c:v", "copy",     # Copy hình ảnh (Nhanh)
        "-c:a", "aac",      # Mã hóa audio
        
        # [Sửa 2] Quan trọng nhất: Cắt video ngay khi luồng ngắn nhất (audio) kết thúc
        "-shortest", 
        
        output_path
    ]

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        
        print("="*60)
        print(f"✅ THÀNH CÔNG! Video đã được cắt ngắn theo file MP3.")
        print(f"📁 File: {output_path}")
        print("="*60)
        
        if os.name == 'nt':
            os.startfile(output_path)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi FFmpeg: {e}")

if __name__ == "__main__":
    if os.path.exists(VIDEO_INPUT) and os.path.exists(AUDIO_NEW):
        mix_video_audio(VIDEO_INPUT, AUDIO_NEW, OUTPUT_FILE)
    else:
        print("⚠️ Kiểm tra lại tên file đầu vào.")