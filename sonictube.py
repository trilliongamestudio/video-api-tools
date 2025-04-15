from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp
import os
import uuid
import random
import time

app = Flask(__name__)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 Chrome/100.0.4896.127 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 Version/15.2 Mobile Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/98.0.4758.102 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 Chrome/99.0.4844.84 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 Chrome/93.0.4577.62 Mobile Safari/537.36"
]

def detect_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "instagram.com" in url:
        return "instagram"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "snapchat.com" in url:
        return "snapchat"
    elif "pinterest.com" in url:
        return "pinterest"
    else:
        return "unknown"

def get_ydl_opts(video_format, output_path, platform):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    opts = {
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'http_headers': headers
    }

    # ✅ Only add cookiefile if it exists
    if os.path.exists("cookies.txt"):
        opts['cookiefile'] = 'cookies.txt'


    if platform == "youtube":
        format_map = {
            "360p": 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            "720p": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            "1080p": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            "4k": 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            "mp3": 'bestaudio/best'
        }

        if video_format not in format_map:
            return None

        if video_format == "mp3":
            opts.update({
                'format': format_map["mp3"],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            opts.update({'format': format_map[video_format]})
    else:
        opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        })

    return opts

@app.route("/")
def home():
    return "✅ SonicTube backend is running!"

def download_with_retry(video_url, ydl_opts, max_retries=3, initial_delay=2):
    attempt = 0
    delay = initial_delay

    while attempt < max_retries:
        try:
            time.sleep(random.uniform(1.5, 3.5))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(video_url, download=True)
        except yt_dlp.utils.DownloadError as e:
            if 'HTTP Error 429' in str(e):
                print(f"[Retry] 429 Too Many Requests. Waiting {delay}s (attempt {attempt + 1})")
                time.sleep(delay)
                delay *= 2
                attempt += 1
            else:
                print("[Error] DownloadError:", str(e))
                break
        except Exception as e:
            print("[Error] Other Exception:", str(e))
            break
    return None

@app.route("/download", methods=["GET"])
def download_handler():
    video_url = request.args.get("url")
    video_format = request.args.get("format", "mp4")

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    platform = detect_platform(video_url)
    print(f"🔍 Platform: {platform}")

    unique_filename = f"{uuid.uuid4()}.%(ext)s"
    output_template = os.path.join(DOWNLOADS_DIR, unique_filename)

    ydl_opts = get_ydl_opts(video_format, output_template, platform)

    if ydl_opts is None:
        return jsonify({"error": f"Invalid format: {video_format}"}), 400

    info = download_with_retry(video_url, ydl_opts)

    if not info:
        return jsonify({"error": "Failed to download video"}), 500

    downloaded_file = info.get('_filename')

    if video_format == "mp3" and downloaded_file:
        downloaded_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'

    if not downloaded_file or not os.path.exists(downloaded_file):
        return jsonify({"error": "Download failed: file not found"}), 500

    print("📁 File downloaded:", downloaded_file)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(downloaded_file)
            print("🧹 Deleted:", downloaded_file)
        except Exception as e:
            print("⚠️ Cleanup failed:", str(e))
        return response

    return send_file(
        downloaded_file,
        as_attachment=True,
        mimetype='audio/mpeg' if video_format == "mp3" else 'video/mp4'
    )

if __name__ == "__main__":
    app.run(debug=True)
















