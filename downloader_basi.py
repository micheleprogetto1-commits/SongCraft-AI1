import os
import json
import subprocess
import sys
import yt_dlp

OUTPUT_DIR = "basi_output"
CATALOG_FILE = "catalogo.json"
BITRATE = "96k"  
BASE_URL_GITHUB = "https://raw.githubusercontent.com/micheleprogetto1-commits/SongCraft-AI/main/basi_output/"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def caricamento_catalogo():
    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

def salva_catalogo(catalogo):
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)

def comprimi_audio(input_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", "-b:a", BITRATE, output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_single_video(video_url):
    catalogo = caricamento_catalogo()
    ids_scaricati = {brano['id'] for brano in catalogo}

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_track.%(ext)s',
        'ignoreerrors': True, 
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            if not info: return
            
            video_id = info.get('id')
            titolo = info.get('title', f"Beat_{video_id}")
            titolo_pulito = "".join([c for c in titolo if c.isalpha() or c.isdigit() or c in ' _-']).rstrip()
            nome_file_finale = f"beat_{video_id}.mp3"
            output_file_path = os.path.join(OUTPUT_DIR, nome_file_finale)

            if video_id in ids_scaricati:
                print(f"⏭️ Già presente: {titolo_pulito}")
                return

            print(f"📥 Scaricamento: {titolo_pulito}...")
            ydl.download([video_url])
            
            file_rilevato = None
            for f_ext in ['webm', 'm4a', 'mp3', '3gp', 'flv']:
                if os.path.exists(f"temp_track.{f_ext}"):
                    file_rilevato = f"temp_track.{f_ext}"
                    break
            
            if file_rilevato:
                comprimi_audio(file_rilevato, output_file_path)
                os.remove(file_rilevato)
                
                nuovo_brano = {"id": video_id, "titolo": titolo_pulito, "genere": "Instrumental", "url": f"{BASE_URL_GITHUB}{nome_file_finale}"}
                catalogo.append(nuovo_brano)
                salva_catalogo(catalogo)
                print(f"   ✅ Completato.")
            else:
                print(f"   ❌ Errore file temporaneo.")
        except Exception as e:
            print(f"   ❌ Errore: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_single_video(sys.argv[1])
