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
    BATCH_SIZE = 400      # Limite di file da scaricare in questa specifica esecuzione
    TARGET_TOTAL = 2000   # Obiettivo finale globale
    
    os.makedirs("downloads", exist_ok=True)
    
    # Conta quanti file .mp3 sono presenti fisicamente nella cartella
    already_downloaded = [f for f in os.listdir("downloads") if f.endswith(".mp3")]
    current_total_count = len(already_downloaded)
    
    print(f"File attualmente presenti nella repository: {current_total_count}/{TARGET_TOTAL}")
    
    if current_total_count >= TARGET_TOTAL:
        print("Obiettivo globale di 2000 file completato!")
        sys.exit(0)
        
    downloaded_in_this_session = 0
    page_size = 150
    current_page = 1
    
    print(f"Avvio sessione di ricerca avanzata a scorrimento (Target sessione: +{BATCH_SIZE})...")

    # Continua a ciclare finché non raggiungiamo il batch della sessione o il target totale
    while downloaded_in_this_session < BATCH_SIZE and (current_total_count + downloaded_in_this_session) < TARGET_TOTAL:
        # Costruiamo l'URL includendo esplicitamente il numero di pagina corrente
        url = f"https://freesound.org/apiv2/search/text/?query={query}&token={api_key}&fields=id,name,previews&page_size={page_size}&page={current_page}"
        print(f"Analisi dei risultati su Freesound - Pagina {current_page}...")
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Errore API Freesound alla pagina {current_page}: {response.status_code}")
                break
                
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                print("Nessun altro risultato disponibile su Freesound.")
                break

            for item in results:
                if downloaded_in_this_session >= BATCH_SIZE or (current_total_count + downloaded_in_this_session) >= TARGET_TOTAL:
                    break
                    
                audio_name = item.get("name", f"sound_{item['id']}").replace("/", "_").replace("\\", "_")
                download_url = item.get("previews", {}).get("preview-hq-mp3")
                
                if not download_url:
                    continue
                    
                file_path = os.path.join("downloads", f"{audio_name}.mp3")
                
                # Se il file esiste già su GitHub, lo ignoriamo e passiamo al prossimo
                if os.path.exists(file_path):
                    continue
                    
                global_index = current_total_count + downloaded_in_this_session + 1
                print(f"[{global_index}/{TARGET_TOTAL}] Scaricamento in corso: {audio_name}...")
                
                try:
                    audio_res = requests.get(download_url, timeout=15)
                    if audio_res.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(audio_res.content)
                        downloaded_in_this_session += 1
                        time.sleep(0.4) # Delay di sicurezza per non essere bloccati
                except Exception as e:
                    print(f"Impossibile scaricare {audio_name}: {e}")
                    continue
                    
        except Exception as req_err:
            print(f"Errore di connessione durante la lettura della pagina {current_page}: {req_err}")
            break
            
        # Passiamo alla pagina successiva per il prossimo ciclo di controllo
        current_page += 1

    print(f"\n--- SESSIONE TERMINATA ---")
    print(f"Nuovi file aggiunti in questo turno: {downloaded_in_this_session}")
    print(f"Stato attuale della repository: {current_total_count + downloaded_in_this_session}/{TARGET_TOTAL}")

if __name__ == "__main__":
    main()
