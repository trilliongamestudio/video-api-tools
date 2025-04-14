from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

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
    # 🔽 Default headers for better success rate
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    # 🔁 Default YDL options
    opts = {
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'http_headers': headers
    }

    # 🎯 YouTube: allow user-selected formats
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
        # ✅ Other platforms: always fetch best MP4
        opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        })

    return opts

@app.route("/")
def home():
    return "✅ SonicTube backend is running!"

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = info.get('_filename')

            if video_format == "mp3" and downloaded_file:
                downloaded_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'

        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception("Download failed: file not found")

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

    except Exception as e:
        print("❌ Error during download:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
















