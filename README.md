# VulgaScience Publisher

Pipeline Python pour préparer des vidéos courtes de vulgarisation scientifique :
téléchargement de sources, transcription, génération de script, voix off, rendu,
puis mise en file d'attente ou publication TikTok.

## Etat actuel

- Les pages légales TikTok sont dans `docs/` pour GitHub Pages.
- Le flow Prefect lit `config_sources.json`.
- Les sorties locales sont écrites dans `storage/`.
- Les secrets doivent rester dans `.env` uniquement.

## Installation locale

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Remplis ensuite `.env` avec tes clés réelles.

## Lancer

```powershell
python src_prefect_flow.py
```

OAuth TikTok :

```powershell
python src_tiktok_oauth.py
```

## Docker

```powershell
docker compose up --build
```
