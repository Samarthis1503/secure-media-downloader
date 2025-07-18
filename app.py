from flask import Flask, render_template, request, redirect, send_file
import yt_dlp
import os

app = Flask(__name__)

# Paths to cookie files (manually export them once using browser extensions)
COOKIE_FILES = {
    'youtube': 'cookies/youtube_cookies.txt',
    'instagram': 'cookies/instagram_cookies.txt',
    'facebook': 'cookies/facebook_cookies.txt'
}

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    return render_template("index.html")

@app.route('/youtube-mp3', methods=['POST'])
def youtube_mp3():
    url = request.form['url']
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': COOKIE_FILES['youtube']
    }
    return download_media(url, ydl_opts)

@app.route('/youtube-video', methods=['POST'])
def youtube_video():
    url = request.form['url']
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': COOKIE_FILES['youtube']
    }
    return download_media(url, ydl_opts)

@app.route('/instagram-reel', methods=['POST'])
def instagram_reel():
    url = request.form['url']
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': COOKIE_FILES['instagram']
    }
    return download_media(url, ydl_opts)

@app.route('/facebook-video', methods=['POST'])
def facebook_video():
    url = request.form['url']
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': COOKIE_FILES['facebook']
    }
    return download_media(url, ydl_opts)

def download_media(url, ydl_opts):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Download failed: {str(e)}"

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True)