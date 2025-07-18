from flask import Flask, render_template, request, redirect, url_for, session, send_file
import yt_dlp
import instaloader
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a stronger secret key
PASSWORD = 'samarth123'  # Shared password

os.makedirs("downloads", exist_ok=True)

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
    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{file_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return send_file(output_path, as_attachment=True)

@app.route('/youtube-video', methods=['POST'])
def youtube_video():
    url = request.form['url']
    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp4"

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return send_file(output_path, as_attachment=True)

@app.route('/instagram-reel', methods=['POST'])
def instagram_reel():
    url = request.form['url']
    shortcode = url.strip('/').split("/")[-1]
    L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target='reel')
        for file in os.listdir("downloads/reel"):
            if file.endswith(".mp4"):
                return send_file(f"downloads/reel/{file}", as_attachment=True)
        return "Video not found."
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/facebook-video', methods=['POST'])
def facebook_video():
    url = request.form['url']
    file_id = str(uuid.uuid4())
    output_path = f"downloads/{file_id}.mp4"

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
