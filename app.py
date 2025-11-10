from flask import Flask, request, render_template, send_file
from flask_bootstrap import Bootstrap
import yt_dlp
import os
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
bootstrap = Bootstrap(app)

# Folder sementara untuk simpan download
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('url')
        format_type = request.form.get('format', 'video')  # Default video
        
        if url:
            try:
                # Opsi yt-dlp
                ydl_opts = {
                    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
                    'quiet': True,
                    'no_warnings': True,
                }
                if format_type == 'audio':
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    if format_type == 'audio':
                        filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')  # Adjust ekstensi audio
                    
                    # Kirim file ke user
                    response = send_file(filename, as_attachment=True)
                    
                    # Hapus file setelah dikirim (cleanup)
                    def safe_cleanup():
                        try:
                            if os.path.exists(filename):
                                os.remove(filename)
                        except Exception:
                            pass
                    response.call_on_close(safe_cleanup)
                    
                    return response
            except Exception as e:
                error_msg = str(e)
                # Handle Instagram-specific errors
                if 'Instagram' in error_msg and ('login required' in error_msg or 'rate-limit' in error_msg):
                    error_msg = "❌ Instagram memerlukan login dan membatasi akses. Sayangnya Instagram tidak bisa didownload tanpa autentikasi. Silakan coba platform lain seperti YouTube, TikTok (publik), atau Facebook."
                elif 'Private video' in error_msg or 'private' in error_msg.lower():
                    error_msg = "❌ Video ini bersifat private/pribadi. Hanya video publik yang bisa didownload."
                else:
                    error_msg = f"❌ Error: {error_msg}. Pastikan URL valid dan konten bersifat publik."
                return render_template('index.html', error=error_msg)
    
    return render_template('index.html', error=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)