from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def get_ydl_opts(video_format, output_path):
    format_map = {
        "360p": 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        "720p": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        "1080p": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        "4k": 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        "mp3": 'bestaudio/best'
    }

    opts = {
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'cookiefile': 'cookies.txt'  # 👈 use cookies for auth/age-restricted/private videos
    }

    if video_format == "mp3":
        opts.update({
            'format': format_map.get(video_format),
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

    unique_filename = f"{uuid.uuid4()}.%(ext)s"
    output_template = os.path.join(DOWNLOADS_DIR, unique_filename)

    ydl_opts = get_ydl_opts(video_format, output_template)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = info.get('_filename')
            if video_format == "mp3":
                downloaded_file = downloaded_file.rsplit('.', 1)[0] + '.mp3'

        print("Downloaded file path:", downloaded_file)
        print("Exists:", os.path.exists(downloaded_file))
        print("Size:", os.path.getsize(downloaded_file), "bytes")

        return send_file(downloaded_file, as_attachment=True)

    except Exception as e:
        print("❌ Error during download:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)









