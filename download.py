import yt_dlp

def download_video(url):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',  # Output filename format
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    video_url = input("Enter video URL: ")
    download_video(video_url)
