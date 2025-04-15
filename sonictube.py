from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp
import os
import uuid
import random
import time
import re

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

def sanitize_filename(title):
    return re.sub(r'[^\w\-_. ]', '_', title).strip().replace(' ', '_')

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

    if os.path.exists("cookies.txt"):
        opts['cookiefile'] = 'cookies.txt'

    if platform == "youtube":
        fallback_chain = {
            "4k": ["2160", "1440", "1080", "720", "360"],
            "2k": ["1440", "1080", "720", "360"],
            "1440p": ["1440", "1080", "720", "360"],
            "1080p": ["1080", "720", "360"],
            "720p": ["720", "360"],
            "360p": ["360"]
        }

        if video_format == "mp3":
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif video_format in fallback_chain:
            resolutions = fallback_chain[video_format]
            fallback_query = "/".join(
                [f"bestvideo[height<={res}]+bestaudio/best[height<={res}]" for res in resolutions]
            )
            opts.update({
                'format': fallback_query
                # No FFmpeg for video! Let yt-dlp handle the merge automatically.
            })
        else:
            return None
    else:
        # Instagram / TikTok / Snapchat / Pinterest = Best MP4
        opts.update({
            'format': 'bestvideo+bestaudio/best',
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

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = sanitize_filename(info_dict.get('title') or str(uuid.uuid4()))
    except Exception as e:
        print("[Warning] Couldn't fetch title:", e)
        video_title = str(uuid.uuid4())

    final_filename_template = os.path.join(DOWNLOADS_DIR, f"{video_title}.%(ext)s")
    ydl_opts = get_ydl_opts(video_format, final_filename_template, platform)

    if ydl_opts is None:
        return jsonify({"error": f"Invalid format: {video_format}"}), 400

    info = download_with_retry(video_url, ydl_opts)

    if not info:
        return jsonify({"error": "Failed to download video"}), 500

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        downloaded_file = ydl.prepare_filename(info)

    if video_format == "mp3":
        downloaded_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'

    print("✅ Final output file:", downloaded_file)
    print("📄 Exists?", os.path.exists(downloaded_file))

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























