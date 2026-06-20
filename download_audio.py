import os
import sys
import requests

def main():
    # Recupera la chiave dai Secrets di GitHub (o ambiente locale)
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        print("Errore: API Key non trovata nei segreti di ambiente.")
        sys.exit(1)

    # Parametri di ricerca su Freesound
    query = "gaming music"
    url = f"https://freesound.org/apiv2/search/text/?query={query}&token={api_key}&fields=id,name,previews"
    
    print(f"Avvio ricerca su Freesound per: '{query}'...")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Errore API Freesound: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
    data = response.json()
    results = data.get("results", [])
    
    if not results:
        print("Nessun traccia audio trovata con i criteri cercati.")
        return

    # Crea la cartella di download se non esiste
    os.makedirs("downloads", exist_ok=True)

    # Scarica i primi 3 risultati trovati
    for item in results[:3]:
        audio_name = item.get("name", f"sound_{item['id']}").replace("/", "_")
        # Prende il link della preview mp3 ad alta qualità
        download_url = item.get("previews", {}).get("preview-hq-mp3")
        
        if not download_url:
            continue
            
        print(f"In download: {audio_name}...")
        audio_res = requests.get(download_url)
        if audio_res.status_code == 200:
            file_path = os.path.join("downloads", f"{audio_name}.mp3")
            with open(file_path, "wb") as f:
                f.write(audio_res.content)
            print(f"Salvato: {file_path}")
            
    print("Download completato con successo!")

if __name__ == "__main__":
    main()
