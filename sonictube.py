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
        'quiet': True
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
            final_ext = "mp3" if video_format == "mp3" else info.get('ext', 'mp4')
            downloaded_file = os.path.join(DOWNLOADS_DIR, f"{unique_filename.split('.')[0]}.{final_ext}")

        return send_file(downloaded_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting SonicTube backend...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)






