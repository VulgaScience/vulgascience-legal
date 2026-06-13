
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
   - Redirect URI : `https://vulgascience.github.io/vulgascience-legal/callback.html`
   - Scopes recommandés au départ : `video.upload,user.info.basic`
   - Scope optionnel plus tard : `video.publish` si tu veux publier directement sans validation dans TikTok
   - Site / Privacy : tu peux mettre `http://localhost:8000` pour test
3. Récupère CLIENT_KEY (client_id) et CLIENT_SECRET (client_secret) fournis par TikTok.

Remarque : TikTok demande une URL de redirection HTTPS pour Login Kit Web. La page `callback.html` affiche le code OAuth, puis le script local l'échange contre les tokens sans exposer le client secret dans le navigateur.

2) Préparer `.env`
A la racine du projet (même dossier que docker-compose.yml), édite `.env` et ajoute :
```
TIKTOK_CLIENT_KEY=ta_valeur_client_key
TIKTOK_CLIENT_SECRET=ta_valeur_client_secret
TIKTOK_SCOPES=video.upload,user.info.basic
TIKTOK_REDIRECT_URI=https://vulgascience.github.io/vulgascience-legal/callback.html
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

4) Générer l'URL OAuth
```bash
python src_tiktok_oauth.py auth-url --open
```
- Le navigateur ouvre la page d'autorisation TikTok.
- Autorise l'app en utilisant le compte TikTok qui recevra les brouillons.
- TikTok redirigera vers `https://vulgascience.github.io/vulgascience-legal/callback.html?code=...`.
- Copie le code affiché par la page.

5) Échanger le code contre les tokens
```bash
python src_tiktok_oauth.py exchange --code TON_CODE_ICI
```
- Le script écrit les tokens dans `.env` :
  - TIKTOK_ACCESS_TOKEN
  - TIKTOK_REFRESH_TOKEN
  - TIKTOK_EXPIRES_IN (éventuel)
  - TIKTOK_TOKEN_RAW (réponse brute, utile pour debugging)

6) Après obtention des tokens
- Vérifie que `.env` contient bien `TIKTOK_ACCESS_TOKEN` et `TIKTOK_REFRESH_TOKEN`.
- Mets `REVIEW_MODE=tiktok_inbox` pour que les vidéos validées par le quality gate arrivent dans TikTok inbox.
- Teste l'upload avec `python src_approval_queue.py stage <draft_id>`.

7) Si l'API TikTok refuse l'accès
- Option A : demander la validation de l'app via la console développeur (peut demander description d'usage et échantillons).
- Option B : rester sur le dépôt local dans `storage/review/` puis upload manuel.

Sécurité
- Ne partage jamais CLIENT_SECRET, ACCESS_TOKEN ou REFRESH_TOKEN.
- Conserve `.env` hors du contrôle de version (ajoute `.env` à `.gitignore`).
- Si token fuit, révoque puis régénère immédiatement via console TikTok.

Besoin d'aide
- Si tu veux, je peux lancer ou adapter `src/tiktok_publisher.py` pour ton flux exact (captions, hashtags, credits).
- Dis‑moi quand tu as les tokens et on testera un upload de test (ou je t'aide à préparer l’app si tu en as besoin).
