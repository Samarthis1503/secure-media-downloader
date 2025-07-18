from flask import Flask, render_template, request, redirect, url_for, session, send_file
import yt_dlp
import instaloader
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a stronger secret key
PASSWORD = 'samarth123'  # Shared password

# Ensure download folders exist
os.makedirs("downloads", exist_ok=True)
os.makedirs("downloads/reel", exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Wrong password')
    return render_template('login.html')

@app.route('/home')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/youtube-mp3', methods=['POST'])
def youtube_mp3():
    url = request.form['url']
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
        'cookiefile': 'cookies/youtube_cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.download([url])
        filename = ydl.prepare_filename(ydl.extract_info(url, download=False)).replace('.webm', '.mp3').replace('.m4a', '.mp3')
    return send_file(filename, as_attachment=True)

@app.route('/youtube-video', methods=['POST'])
def youtube_video():
    url = request.form['url']
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'cookiefile': 'cookies/youtube_cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.download([url])
        filename = ydl.prepare_filename(ydl.extract_info(url, download=False))
    return send_file(filename, as_attachment=True)

@app.route('/instagram-reel', methods=['POST'])
def instagram_reel():
    url = request.form['url']
    shortcode = url.strip('/').split("/")[-1]
    L = instaloader.Instaloader(dirname_pattern='downloads/reel', save_metadata=False)
    try:
        L.load_session_from_file("USERNAME", filename="cookies/instagram_cookies.txt")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target='')
        for file in os.listdir("downloads/reel"):
            if file.endswith(".mp4"):
                return send_file(f"downloads/reel/{file}", as_attachment=True)
        return "Video not found."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/facebook-video', methods=['POST'])
def facebook_video():
    url = request.form['url']
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'cookiefile': 'cookies/facebook_cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.download([url])
        filename = ydl.prepare_filename(ydl.extract_info(url, download=False))
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
