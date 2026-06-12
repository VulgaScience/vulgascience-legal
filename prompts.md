
# Prompts — pipeline de vulgarisation (FR)

1) Screening / scoring (court)
Prompt:
"Tu es un évaluateur. Lis ce transcript ci‑dessous et fournis:
- 1 phrase qui résume le message principal,
- 3 tags pertinents,
- un score d'intérêt 0-100 pour un format TikTok court,
- indiques s'il y a un risque légal (oui/non + raison courte).
Réponds au format JSON:
{ "summary": "...", "tags": ["..."], "score": 42, "legal_risk": {"flag": "non", "reason": ""} }
Transcript: <<TRANSCRIPT>>"

2) Génération script TikTok (45s)
Prompt:
"Tu es vulgarisateur scientifique. Transforme ce transcript (≈60–90s) en un script pour TikTok ~45s:
- Hook 2–3s,
- 3 points clairs (phrases courtes),
- 1 analogie simple,
- CTA final 'Suis-nous pour en savoir plus',
- Fournis aussi un fichier .srt (timestamps) pour le script et 3 hashtags pertinents.
Langage: FR, niveau lycée, explique chaque terme technique en une phrase."

3) Fact-check (par affirmation)
Prompt:
"Pour chaque affirmation factuelle dans le script, liste la source fiable (PubMed, arXiv, DOI, site d'institut). Si introuvable, marque 'À VÉRIFIER'. Donne aussi le timestamp de la phrase dans le script."
