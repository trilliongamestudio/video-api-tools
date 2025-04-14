from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# 🔽 Create downloads folder if not exists
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 🔽 Format options
def get_ydl_opts(video_format, output_path):
    format_map = {
        "360p": 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        "720p": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        "1080p": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        "4k": 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        "mp3": 'bestaudio/best'
    }

    # ✅ yt-dlp options with headers to bypass restrictions
    opts = {
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9'
        }
    }

    if video_format == "mp3":
        opts.update({
            'format': format_map.get("mp3"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        opts.update({'format': format_map.get(video_format, 'best')})

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

    # 🧠 Unique filename for output
    unique_filename = f"{uuid.uuid4()}.%(ext)s"
    output_template = os.path.join(DOWNLOADS_DIR, unique_filename)

    ydl_opts = get_ydl_opts(video_format, output_template)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = info.get('_filename')

            if video_format == "mp3" and downloaded_file:
                downloaded_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'

        # 🧠 Check if file really exists
        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception("Download failed: File not found.")

        print("✅ File downloaded:", downloaded_file)
        print("📏 Size:", os.path.getsize(downloaded_file), "bytes")

        return send_file(downloaded_file, as_attachment=True)

    except Exception as e:
        print("❌ Error during download:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)










