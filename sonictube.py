from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

def download_video(url):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
    }

    if download_format == "mp3":
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif download_format == "360p":
        ydl_opts.update({
            'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'merge_output_format': 'mp4',
        })
    elif download_format == "720p":
        ydl_opts.update({
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'merge_output_format': 'mp4',
        })
    elif download_format == "1440p":
        ydl_opts.update({
            'format': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
            'merge_output_format': 'mp4',
        })
    elif download_format == "4k":
        ydl_opts.update({
            'format': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            'merge_output_format': 'mp4',
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return jsonify({"message": f"{download_format} downloaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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


