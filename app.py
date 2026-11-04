import os
import threading
import time
import imageio_ffmpeg
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Global Download Progress State
download_state = {
    'status': 'idle',      # 'idle', 'downloading', 'finished', 'error'
    'percent': '0%',
    'title': '',
    'filename': '',
    'error': ''
}

def progress_hook(d):
    if d['status'] == 'downloading':
        download_state['status'] = 'downloading'
        percent_str = d.get('_percent_str', '0%').strip()
        # ANSI rəng kodlarını təmizləyirik
        download_state['percent'] = ''.join(c for c in percent_str if c.isdigit() or c == '.') + '%'
    elif d['status'] == 'finished':
        download_state['status'] = 'finished'
        download_state['percent'] = '100%'

def run_download(url, format_type, quality):
    global download_state
    download_state = {
        'status': 'downloading',
        'percent': '0%',
        'title': 'Media hazırlanır...',
        'filename': '',
        'error': ''
    }

    out_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    if format_type == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_template,
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
    else:
        if quality == '1080':
            fmt = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
        elif quality == '720':
            fmt = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
        else:
            fmt = 'bestvideo+bestaudio/best'

        ydl_opts = {
            'format': fmt,
            'outtmpl': out_template,
            'merge_output_format': 'mp4',
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [progress_hook],
            'quiet': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == 'mp3':
                base, _ = os.path.splitext(filename)
                filename = base + '.mp3'
            elif not filename.endswith('.mp4'):
                base, _ = os.path.splitext(filename)
                filename = base + '.mp4'

            basename = os.path.basename(filename)
            download_state['title'] = info.get('title', 'Media Faylı')
            download_state['filename'] = basename
            download_state['status'] = 'completed'
    except Exception as e:
        download_state['status'] = 'error'
        download_state['error'] = str(e)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="az" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediaDownloader | Universal Web Downloader</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        neon: {
                            DEFAULT: '#00ff66',
                            dark: '#00cc52',
                            glow: 'rgba(0, 255, 102, 0.4)'
                        }
                    },
                    fontFamily: {
                        sans: ['Outfit', 'sans-serif']
                    }
                }
            }
        }
    </script>
    <style>
        .glass {
            background: rgba(18, 24, 20, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(0, 255, 102, 0.2);
        }
        .glass-card {
            background: rgba(24, 32, 27, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 255, 102, 0.12);
        }
        .neon-glow {
            box-shadow: 0 0 30px rgba(0, 255, 102, 0.25);
        }
        .neon-glow-sm {
            box-shadow: 0 0 12px rgba(0, 255, 102, 0.2);
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0b110e; }
        ::-webkit-scrollbar-thumb { background: rgba(0, 255, 102, 0.3); border-radius: 4px; }
    </style>
</head>
<body class="bg-[#0b110e] text-neutral-100 min-h-screen font-sans flex flex-col justify-between selection:bg-neon selection:text-black">

    <!-- Ambient Background Glow -->
    <div class="fixed top-0 left-1/4 w-96 h-96 bg-neon/10 rounded-full blur-[120px] pointer-events-none"></div>

    <!-- Header -->
    <header class="w-full glass border-b border-emerald-500/10 sticky top-0 z-50 py-4 px-6 md:px-12 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-2xl bg-neon/15 border border-neon/30 flex items-center justify-center text-neon neon-glow-sm">
                <i class="fa-solid fa-cloud-arrow-down text-xl"></i>
            </div>
            <div>
                <h1 class="font-bold text-lg text-white tracking-wide">Media<span class="text-neon">Downloader</span></h1>
                <p class="text-xs text-neutral-400 font-medium">Universal Web Downloader</p>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-4xl w-full mx-auto px-4 py-8 md:py-12 flex flex-col gap-8 z-10">

        <!-- Hero Card -->
        <section class="glass rounded-3xl p-6 md:p-10 neon-glow relative overflow-hidden">
            <div class="absolute -right-12 -top-12 w-64 h-64 bg-neon/5 rounded-full blur-3xl pointer-events-none"></div>

            <div class="text-center max-w-2xl mx-auto mb-8">
                <div class="inline-flex p-3 rounded-2xl bg-neon/10 text-neon mb-4 border border-neon/20 neon-glow-sm">
                    <i class="fa-solid fa-download text-2xl"></i>
                </div>
                <h2 class="text-2xl md:text-4xl font-extrabold tracking-tight mb-3">İstənilən Media Linkini <span class="text-neon">Dərhal Yüklə</span></h2>
                <p class="text-neutral-400 text-sm md:text-base">Sevdiyiniz videoları və musiqiləri yüksək keyfiyyətdə, sürətli və təhlükəsiz şəkildə cihazınıza endirin.</p>
            </div>

            <!-- Error Box -->
            <div id="errorAlert" class="hidden mb-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
                <i class="fa-solid fa-circle-exclamation text-lg flex-shrink-0"></i>
                <span id="errorMessage">Xəta baş verdi!</span>
            </div>

            <!-- Form -->
            <form id="downloadForm" class="flex flex-col gap-4">
                <div class="relative w-full">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-neutral-400">
                        <i class="fa-solid fa-link text-neon"></i>
                    </div>
                    <input type="url" id="urlInput" required placeholder="https://www.youtube.com/watch?v=..." 
                        class="w-full pl-11 pr-4 py-4 rounded-2xl bg-neutral-900/90 border border-emerald-500/20 text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-neon focus:ring-1 focus:ring-neon text-sm md:text-base transition">
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs text-neutral-400 mb-1.5 font-medium">Format Seçimi</label>
                        <select id="formatSelect" class="w-full px-4 py-3 rounded-xl bg-neutral-900 border border-emerald-500/20 text-sm text-white focus:outline-none focus:border-neon">
                            <option value="mp4">Video (MP4 - Səsli)</option>
                            <option value="mp3">Audio / Musiqi (MP3)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-neutral-400 mb-1.5 font-medium">Keyfiyyət Səviyyəsi</label>
                        <select id="qualitySelect" class="w-full px-4 py-3 rounded-xl bg-neutral-900 border border-emerald-500/20 text-sm text-white focus:outline-none focus:border-neon">
                            <option value="max">Maksimum Keyfiyyət (Best)</option>
                            <option value="1080">1080p Full HD</option>
                            <option value="720">720p HD</option>
                        </select>
                    </div>
                </div>

                <button type="submit" id="downloadBtn" class="mt-2 w-full bg-neon hover:bg-neon-dark text-black font-bold py-4 rounded-2xl transition duration-300 flex items-center justify-center gap-2 shadow-lg shadow-neon/20 cursor-pointer text-base">
                    <i class="fa-solid fa-cloud-arrow-down text-lg"></i> Endirməni Başlat
                </button>
            </form>

            <!-- Dynamic Progress Section (Hidden initially) -->
            <div id="progressSection" class="hidden mt-6 p-5 rounded-2xl glass-card border border-neon/30">
                <div class="flex justify-between items-center mb-2 text-xs">
                    <span id="progressStatusText" class="text-neutral-300 font-medium">Media serverdə hazırlanır...</span>
                    <span id="progressPercent" class="text-neon font-bold text-sm">0%</span>
                </div>
                <div class="w-full h-3 bg-neutral-900 rounded-full overflow-hidden border border-emerald-500/20">
                    <div id="progressBar" class="h-full bg-neon transition-all duration-300 w-0"></div>
                </div>
            </div>

            <!-- Supported Platforms & Quality Info Section -->
            <div class="mt-8 pt-6 border-t border-emerald-500/10">
                <div class="flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-neutral-400">
                    <div class="flex items-center gap-2 font-medium text-neutral-300">
                        <i class="fa-solid fa-shield-halved text-neon"></i> Dəstəklənən Platformalar:
                    </div>
                    <div class="flex flex-wrap items-center justify-center gap-2">
                        <span class="px-2.5 py-1 rounded-lg glass-card flex items-center gap-1.5"><i class="fa-brands fa-youtube text-red-500"></i> YouTube</span>
                        <span class="px-2.5 py-1 rounded-lg glass-card flex items-center gap-1.5"><i class="fa-brands fa-instagram text-pink-500"></i> Instagram</span>
                        <span class="px-2.5 py-1 rounded-lg glass-card flex items-center gap-1.5"><i class="fa-brands fa-tiktok text-white"></i> TikTok</span>
                        <span class="px-2.5 py-1 rounded-lg glass-card flex items-center gap-1.5"><i class="fa-brands fa-soundcloud text-orange-500"></i> SoundCloud</span>
                        <span class="px-2.5 py-1 rounded-lg glass-card flex items-center gap-1.5"><i class="fa-brands fa-x-twitter text-blue-400"></i> Twitter/X</span>
                        <span class="px-2.5 py-1 rounded-lg glass-card flex items-center gap-1.5"><i class="fa-brands fa-reddit text-orange-600"></i> Reddit</span>
                    </div>
                </div>
                <div class="mt-3 flex items-center justify-center gap-6 text-[11px] text-neutral-500">
                    <span><i class="fa-solid fa-check text-neon mr-1"></i> Su nişansız (Watermark-free)</span>
                    <span><i class="fa-solid fa-check text-neon mr-1"></i> MP4 / MP3 dəstəyi</span>
                    <span><i class="fa-solid fa-check text-neon mr-1"></i> HD & 4K uyğun</span>
                </div>
            </div>
        </section>

        <!-- History Section -->
        <section class="glass rounded-3xl p-6 md:p-8">
            <h3 class="font-bold text-base text-white mb-4 flex items-center gap-2">
                <i class="fa-solid fa-clock-rotate-left text-neon"></i> Yükləmə Tarixçəsi
            </h3>
            <div id="historyList" class="flex flex-col gap-3">
                <div class="text-center py-4 text-neutral-500 text-xs italic" id="emptyHistory">Hələ yüklənmiş fayl yoxdur.</div>
            </div>
        </section>

    </main>

    <!-- Footer -->
    <footer class="w-full py-6 text-center text-xs text-neutral-500 border-t border-emerald-500/10 glass mt-12">
        <p>&copy; 2026 MediaDownloader &bull; Universal Web Downloader Engine</p>
    </footer>

    <!-- JavaScript Logic -->
    <script>
        const downloadForm = document.getElementById('downloadForm');
        const urlInput = document.getElementById('urlInput');
        const formatSelect = document.getElementById('formatSelect');
        const qualitySelect = document.getElementById('qualitySelect');
        const downloadBtn = document.getElementById('downloadBtn');
        const errorAlert = document.getElementById('errorAlert');
        const errorMessage = document.getElementById('errorMessage');
        const progressSection = document.getElementById('progressSection');
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressStatusText = document.getElementById('progressStatusText');
        const historyList = document.getElementById('historyList');
        const emptyHistory = document.getElementById('emptyHistory');

        downloadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorAlert.classList.add('hidden');

            const url = urlInput.value.trim();
            const format = formatSelect.value;
            const quality = qualitySelect.value;

            downloadBtn.disabled = true;
            downloadBtn.classList.add('opacity-50', 'cursor-not-allowed');
            progressSection.classList.remove('hidden');
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';
            progressStatusText.textContent = 'Serverə sorğu göndərilir...';

            try {
                // Start download request
                const res = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, format, quality })
                });

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.message || "Xəta baş verdi!");
                }

                // Poll status until completed
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await fetch('/api/status');
                        const statusData = await statusRes.json();

                        if (statusData.status === 'downloading') {
                            const pct = statusData.percent || '0%';
                            progressBar.style.width = pct;
                            progressPercent.textContent = pct;
                            progressStatusText.textContent = `Video endirilir və birləşdirilir (${pct})...`;
                        } else if (statusData.status === 'completed') {
                            clearInterval(pollInterval);
                            progressBar.style.width = '100%';
                            progressPercent.textContent = '100%';
                            progressStatusText.textContent = 'Endirmə tamamlandı! Fayl endirilir...';

                            // Trigger file download
                            const link = document.createElement('a');
                            link.href = `/get-file/${statusData.filename}`;
                            link.download = statusData.filename;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);

                            addHistory(statusData.title, format.toUpperCase());
                            urlInput.value = '';

                            setTimeout(() => {
                                progressSection.classList.add('hidden');
                                downloadBtn.disabled = false;
                                downloadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                            }, 1500);
                        } else if (statusData.status === 'error') {
                            clearInterval(pollInterval);
                            throw new Error(statusData.error || "Endirmə xətası baş verdi!");
                        }
                    } catch (pollErr) {
                        clearInterval(pollInterval);
                        throw pollErr;
                    }
                }, 500);

            } catch (err) {
                errorMessage.textContent = err.message || "Serverlə əlaqə kəsildi!";
                errorAlert.classList.remove('hidden');
                progressSection.classList.add('hidden');
                downloadBtn.disabled = false;
                downloadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });

        function addHistory(title, fmt) {
            emptyHistory.style.display = 'none';
            const item = document.createElement('div');
            item.className = 'glass-card p-3.5 rounded-xl flex items-center justify-between text-xs text-neutral-300';
            item.innerHTML = `
                <div class="flex items-center gap-3 overflow-hidden">
                    <div class="w-8 h-8 rounded-lg bg-neon/10 text-neon flex items-center justify-center flex-shrink-0">
                        <i class="fa-solid fa-check"></i>
                    </div>
                    <span class="truncate max-w-[240px] sm:max-w-[420px] font-medium text-white">${title}</span>
                </div>
                <span class="bg-neon/10 text-neon border border-neon/20 px-2.5 py-1 rounded-lg font-semibold flex-shrink-0">${fmt}</span>
            `;
            historyList.prepend(item);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format', 'mp4')
    quality = data.get('quality', 'max')

    if not url:
        return jsonify({'status': 'error', 'message': 'Link daxil edilməyib!'}), 400

    # Start download in a background thread
    thread = threading.Thread(target=run_download, args=(url, format_type, quality))
    thread.start()

    return jsonify({'status': 'started'})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(download_state)

@app.route('/get-file/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    print("🚀 MediaDownloader serveri işə düşdü: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)