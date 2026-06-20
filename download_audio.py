import os
import sys
import requests
import time

def main():
    # Recupera la chiave dai Secrets di GitHub
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        print("Errore: API Key non trovata nei segreti di ambiente.")
        sys.exit(1)

    query = "gaming music"
    target_count = 1500  # Il tuo obiettivo totale
    downloaded_count = 0
    
    # Crea la cartella di download se non esiste
    os.makedirs("downloads", exist_ok=True)
    
    # Freesound permette di richiedere fino a 150 risultati per pagina
    page_size = 150
    url = f"https://freesound.org/apiv2/search/text/?query={query}&token={api_key}&fields=id,name,previews&page_size={page_size}"
    
    print(f"Avvio ricerca globale su Freesound per: '{query}' (Target: {target_count})...")

    while url and downloaded_count < target_count:
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Errore API Freesound: {response.status_code}")
            break
            
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            print("Nessun altro risultato trovato.")
            break

        for item in results:
            if downloaded_count >= target_count:
                break
                
            audio_name = item.get("name", f"sound_{item['id']}").replace("/", "_").replace("\\", "_")
            download_url = item.get("previews", {}).get("preview-hq-mp3")
            
            if not download_url:
                continue
                
            file_path = os.path.join("downloads", f"{audio_name}.mp3")
            
            # Salta il download se il file esiste già nella repository
            if os.path.exists(file_path):
                continue
                
            print(f"[{downloaded_count + 1}/{target_count}] In download: {audio_name}...")
            try:
                audio_res = requests.get(download_url, timeout=15)
                if audio_res.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(audio_res.content)
                    downloaded_count += 1
                    # Un piccolo delay per non sovraccaricare il server di Freesound
                    time.sleep(0.5) 
            except Exception as e:
                print(f"Errore durante il download di {audio_name}: {e}")
                continue
        
        # Passa alla pagina successiva fornita dall'API di Freesound
        url = data.get("next")
        if url:
            print("Passaggio alla pagina successiva dei risultati...")

    print(f"Processo completato! Scaricati {downloaded_count} nuovi file audio.")

if __name__ == "__main__":
    main()
