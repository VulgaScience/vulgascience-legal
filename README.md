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

## Validation avant publication

Par defaut, le pipeline ne publie pas directement. Il depose une proposition dans
`storage/review/` et attend une validation humaine.

Verifier une video :

```powershell
python src_agents.py check --video .\storage\outbox\ma-video.mp4
```

Mettre une video en attente de validation :

```powershell
python src_agents.py review --video .\storage\outbox\ma-video.mp4 --metadata .\storage\outbox\ma-video.json
```

Lister, approuver, refuser, puis publier :

```powershell
python src_approval_queue.py list --status pending
python src_approval_queue.py stage <draft_id>
python src_approval_queue.py approve <draft_id>
python src_approval_queue.py reject <draft_id> --reason "A retravailler"
python src_approval_queue.py publish <draft_id>
```

Le mode recommande est `stage` : la video est envoyee dans TikTok inbox, puis tu
ajoutes le son / fais la derniere validation dans TikTok avant de poster.

Quand les identifiants TikTok sont prets, tu peux mettre :

```dotenv
REVIEW_MODE=tiktok_inbox
```

Le pipeline tentera alors d'envoyer automatiquement les videos validees par le
quality gate dans TikTok inbox. Si TikTok refuse ou si les tokens manquent, le
brouillon reste dans `storage/review/`.

La publication directe reste bloquee tant que le brouillon n'a pas le statut
`approved`.

## Memoire de performance

Apres publication, enregistre les resultats pour que le systeme apprenne ce qui
marche :

```powershell
python src_growth_memory.py record --video_id <id> --topic "cerveau" --hook "Tu ne vois pas le monde en direct" --duration_seconds 60 --views 1000 --likes 80 --comments 12 --shares 8 --saves 20 --completion_rate 0.62
python src_growth_memory.py summary
```

Les enseignements sont stockes dans `storage/learning/` et servent a orienter
les prochains hooks, sujets, formats et CTA.

Le playbook operationnel est dans `docs/tiktok_growth_playbook.md`.

## Preparation post-review TikTok

Verifier ce qui est pret apres la review TikTok :

```powershell
python src_launch_check.py
```

Classer les prochains sujets a produire :

```powershell
python src_content_planner.py rank --limit 3
python src_content_planner.py brief
```

Verifier un script structure avant rendu :

```powershell
python src_script_check.py content\scripts\dopamine_prediction_reward.json
```

Le batch de production est dans `content/production_queue.json`.

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
