# Plan pendant la review TikTok

## Si la review est acceptee

1. Verifier que les scopes approuves contiennent `video.upload`.
2. Renseigner `.env`:

```dotenv
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
TIKTOK_SCOPES=video.upload,user.info.basic
TIKTOK_REDIRECT_URI=https://vulgascience.github.io/vulgascience-legal/callback.html
REVIEW_MODE=tiktok_inbox
```

3. Obtenir les tokens:

```powershell
python src_tiktok_oauth.py auth-url --open
python src_tiktok_oauth.py exchange --code <code_affiche_sur_callback>
```

4. Tester l'envoi inbox:

```powershell
python src_approval_queue.py stage 20260613T002031Z-VulgaScience_001_monetisable_60s_technique_v3
```

5. Ouvrir TikTok, ajouter un son tendance tres bas, verifier la cover, puis poster.

## Si la review est refusee

Repondre selon le motif:

- Scope non justifie: retirer le scope, garder `video.upload`, refaire une video demo si necessaire.
- Redirect URI: verifier que `callback.html` est publiee et que l'URL exacte correspond au portail.
- Demo insuffisante: refaire la demo en montrant explicitement le bouton d'upload et le brouillon TikTok inbox.
- URL site invalide: verifier GitHub Pages, `index.html`, `terms.html`, `privacy.html`.

## Travail a avancer maintenant

- Produire 3 scripts videos de reserve.
- Construire une shortlist de sujets trend compatibles science.
- Preparer les templates de captions et hashtags.
- Preparer le formulaire de saisie des performances a 2h, 24h et 7j.
- Nettoyer les pages publiques et remplacer les emails `.example` par une adresse reelle.
- Pousser `docs/index.html` et `docs/callback.html` sur GitHub Pages.
