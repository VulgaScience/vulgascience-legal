
# Pipeline automatisé — TikTok Vulgarisation Scientifique

Ce dépôt contient un pipeline complet et autonome pour:
- détecter et télécharger des vidéos scientifiques depuis des sources configurables,
- transcrire et segmenter les contenus,
- générer automatiquement des scripts vulgarisés (LLM),
- produire des vidéos 9:16 avec TTS, sous-titres et branding,
- publier automatiquement sur TikTok (via API si clé disponible, sinon fichier de sortie prêt à uploader).

Important : ce dépôt est fourni tel quel. Tu dois fournir les clés API (OpenAI, ElevenLabs, YouTube, TikTok) et accepter les risques juridiques liés au copyright. Le pipeline intègre des vérifications automatiques et des quarantaines pour réduire les risques, mais rien ne remplace une stratégie juridique appropriée.

Quickstart (local)
1. Copier le dépôt sur ta machine.
2. Créer et remplir `.env` à partir de `.env.example`.
3. Installer Docker & Docker Compose (ou Python + venv pour exécution locale sans conteneur).
4. Lancer :
   - docker-compose up --build
   - ou, en local sans Docker : pip install -r requirements.txt, puis lancer `python -m src.prefect_flow` (voir instructions dans src).

Contenu principal
- docker-compose.yml : services (worker, redis, db, web minimal).
- src/pipeline.py : fonctions principales (download, transcribe, score, generate script, tts, render, publish).
- src/prefect_flow.py : orchestration Prefect (scheduler).
- prompts.md : prompts pour screening, génération, fact-check.
- config/sources.json : sources YouTube / RSS par défaut.
- .env.example : variables d'environnement à renseigner.

Étapes opérationnelles
- Scheduler (tous les X min) déclenche fetcher → téléchargement (yt-dlp) → transcription (WhisperX / OpenAI) → screening → génération de script (LLM) → TTS → montage FFmpeg → QC automatique → publication (TikTok API) → stockage des métriques.
- Si publication automatique impossible (pas de accès API), les vidéos publiables sont déposées dans ./outbox pour upload manuel.

Notes juridiques et éthiques
- Par défaut, le pipeline accepte uniquement les vidéos avec licence réutilisable (CC) ou explicitement autorisées par l'uploader.
- Les vidéos flagged "HIGH_RISK" (données personnelles, instructions dangereuses, santé non sourcée) sont mises en quarantaine et ne sont pas publiées.
- Pour sujets santé/finance, le module de fact-check est obligatoire ; sans sources fiables, le contenu est bloqué.

Besoin d'aide
- Si tu veux que je personnalise les prompts, génère des voix supplémentaires, ou ajoute un module de publication Android fallback (Appium + ADB), dis-le et je l'ajoute au dépôt.

Prochaine étape
- Renseigne `.env` et lance `docker-compose up --build`. Je fournis ci‑dessous les fichiers nécessaires.
