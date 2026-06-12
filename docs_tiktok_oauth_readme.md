
# TikTok OAuth — Guide rapide

But : obtenir access_token + refresh_token pour le compte TikTok cible et les écrire dans `.env`.

Pré-requis
- Avoir un compte TikTok (connecte-toi avec le compte sur lequel tu veux publier).
- Créer une app sur TikTok for Developers (voir étapes ci‑dessous).
- Avoir Python + venv + requests + python-dotenv + flask installés.

1) Créer l'app TikTok for Developers
1. Va sur la console développeur TikTok (TikTok for Developers / Open API).
2. Crée une nouvelle application :
   - Nom : ex. "VulgaScience Publisher"
   - Redirect URI : `http://localhost:8000/callback`
   - Scopes : `video.upload,video.publish,user.info` (sépare par des virgules si demandé)
   - Site / Privacy : tu peux mettre `http://localhost:8000` pour test
3. Récupère CLIENT_KEY (client_id) et CLIENT_SECRET (client_secret) fournis par TikTok.

Remarque : certaines fonctionnalités (upload/publish) peuvent demander validation par TikTok. Si l'API refuse l'upload initialement, tu utiliseras le fallback Appium/ADB.

2) Préparer `.env`
A la racine du projet (même dossier que docker-compose.yml), édite `.env` et ajoute :
```
TIKTOK_CLIENT_KEY=ta_valeur_client_key
TIKTOK_CLIENT_SECRET=ta_valeur_client_secret
```
(N'ajoute pas encore ACCESS/REFRESH — le script les écrira.)

3) Installer dépendances (venv recommandé)
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
pip install flask python-dotenv requests
```

4) Lancer le script OAuth local
```bash
python src/tiktok_oauth.py
```
- Le script ouvrira automatiquement `http://localhost:8000/start` dans ton navigateur.
- Autorise l'app en utilisant ton compte TikTok (connecte-toi si nécessaire).
- TikTok redirigera vers `http://localhost:8000/callback?code=...`.
- Le script échange le code et écrit les tokens dans `.env` :
  - TIKTOK_ACCESS_TOKEN
  - TIKTOK_REFRESH_TOKEN
  - TIKTOK_EXPIRES_IN (éventuel)
  - TIKTOK_TOKEN_RAW (réponse brute, utile pour debugging)

5) Après obtention des tokens
- Vérifie que `.env` contient bien `TIKTOK_ACCESS_TOKEN` et `TIKTOK_REFRESH_TOKEN`.
- Teste l'upload de test via `src/tiktok_publisher.py` (fonction `publish_from_path`) — attention : endpoints évoluent, vérifie la doc TikTok.

6) Si l'API TikTok refuse l'accès (app non validée)
- Option A : demander la validation de l'app via la console développeur (peut demander description d'usage et échantillons).
- Option B : utiliser le fallback ADB/Appium pour téléverser via un émulateur Android connecté (je peux générer le script d'automatisation si nécessaire).

Sécurité
- Ne partage jamais CLIENT_SECRET, ACCESS_TOKEN ou REFRESH_TOKEN.
- Conserve `.env` hors du contrôle de version (ajoute `.env` à `.gitignore`).
- Si token fuit, révoque puis régénère immédiatement via console TikTok.

Besoin d'aide
- Si tu veux, je peux lancer ou adapter `src/tiktok_publisher.py` pour ton flux exact (captions, hashtags, credits).
- Dis‑moi quand tu as les tokens et on testera un upload de test (ou je t'aide à préparer l’app si tu en as besoin).
