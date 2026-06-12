# VulgaScience Publisher

Pipeline Python pour preparer des videos courtes de vulgarisation scientifique :
telechargement ou entree video locale, transcript, generation de script, voix off,
rendu video, puis depot dans `storage/outbox/` pour upload manuel ou publication.

## Etat actuel

- Les pages legales TikTok sont dans `docs/` pour GitHub Pages.
- Le flow Prefect lit `config_sources.json`.
- Les sorties locales sont ecrites dans `storage/`.
- Les secrets doivent rester dans `.env` uniquement.
- `ffmpeg` est fourni par `imageio-ffmpeg`, donc aucune installation systeme n'est requise pour le MVP local.

## Installation locale

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --no-cache-dir -r requirements.txt
Copy-Item .env.example .env
```

Remplis ensuite `.env` avec tes cles reelles.

## MVP local

Traiter une video locale avec un transcript manuel :

```powershell
python src_pipeline.py .\ma-video.mp4 --transcript "Une etude recente montre..." --force
```

Traiter une video locale avec un fichier transcript :

```powershell
python src_pipeline.py .\ma-video.mp4 --transcript-file .\transcript.txt --caption "Science en 45 secondes #science" --force
```

Traiter une URL compatible `yt-dlp` :

```powershell
python src_pipeline.py "https://www.youtube.com/watch?v=..." --force
```

Les fichiers prets sont deposes dans `storage/outbox/` avec un `.json` de metadata.

## Flow Prefect

```powershell
python src_prefect_flow.py
```

## OAuth TikTok

```powershell
python src_tiktok_oauth.py
```

## Docker

```powershell
docker compose up --build
```
