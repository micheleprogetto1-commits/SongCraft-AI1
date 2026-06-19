# SongCraft-AI - Audio assets automation

Questo progetto include uno script Python e un workflow GitHub Actions per scaricare audio MP3 royalty-free da Pixabay e salvarli nella cartella `audio_assets/`.

## Cosa fa

- cerca audio su Pixabay tramite API
- scarica fino a `1000` file MP3
- evita duplicati
- salta i file oltre i `100 MB` per rispettare i limiti di GitHub
- esegue commit e push automatico nella repository

## Requisito necessario

Prima di eseguire il workflow devi configurare il secret:

`PIXABAY_API_KEY`

## Come configurare `PIXABAY_API_KEY` su GitHub

1. Apri la repository su GitHub.
2. Vai su `Settings`.
3. Nel menu laterale entra in `Secrets and variables`.
4. Seleziona `Actions`.
5. Clicca `New repository secret`.
6. Nel campo `Name` scrivi `PIXABAY_API_KEY`.
7. Nel campo `Secret` incolla la tua API key di Pixabay.
8. Clicca `Add secret`.

## Come avviare manualmente il workflow

1. Apri la repository su GitHub.
2. Vai nella scheda `Actions`.
3. Seleziona il workflow `Download Pixabay Audio`.
4. Clicca `Run workflow`.
5. Se vuoi, inserisci un termine di ricerca diverso da `music`.
6. Conferma con il pulsante di avvio.

## Dove finiscono i file

I file scaricati vengono salvati in:

`audio_assets/`

## Limiti e sicurezza

- Il workflow non salva file più grandi di `100 MB`.
- Lo script inserisce una pausa tra i download per ridurre il rischio di blocchi.
- I duplicati vengono ignorati sia per URL sia per contenuto.

## File principali

- `scripts/download_audio.py`
- `.github/workflows/audio-download.yml`
- `requirements.txt`

## Nota importante

Pixabay può avere limiti di rate e regole d'uso sull'API. Se prevedi download massivi, verifica sempre i termini del servizio e monitora il comportamento del workflow.
