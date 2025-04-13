from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'merge_output_format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route("/download", methods=["GET"])
def handle_download():
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        download_video(video_url)
        return jsonify({"message": "Video downloaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


