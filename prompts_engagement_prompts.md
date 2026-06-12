
# Prompts optimisés pour engagement (FR)

But : maximiser le taux de vue/engagement sur TikTok tout en restant fidèle au contenu scientifique.

Principes généraux (à appliquer systématiquement)
- Hook fort en début (question surprenante, chiffre, contradiction)
- Format court, phrases simples, liste de 3 points
- Appels émotionnels légers : étonnement, soulagement, curiosité
- CTA clair (Suis-nous, like pour la suite, commente si tu veux la source)
- Hashtags tendance intégrés de façon naturelle
- Variante A/B : ton "dramatic" vs "tranquille" vs "humour sec"

Template principal (45s)
Prompt:
"Tu es un vulgarisateur viral. Transforme ce transcript en un script TikTok FR ~45s, public lycée/adulte. Format:
1) Hook 2–3s: une phrase choc (question ou chiffre)
2) 3 points clairs, numérotés
3) 1 analogie simple
4) CTA final: 'Suis-nous pour en savoir plus' + suggestion d'interaction (Like pour la partie 2, commente si tu veux la source)
Rends le texte punchy, utilise des mots accrocheurs ('incroyable', 'tu ne devineras jamais'). Évite jargon sans explication. Fournis aussi une version courte 15s, une version 30s, et 3 hashtags pertinents extraits du trend_profile."

Hook patterns (exemples à injecter dynamiquement)
- "Et si je vous disais que [chiffre/choc] ?"
- "La plupart des scientifiques se trompent sur..."
- "En 30 secondes, voici pourquoi [phénomène] est important"

Variant "Myth-buster"
Prompt:
"Transforme en 'Myth-buster': commence par 'Mythe : ...' puis 'Réalité : ...' + explication en 3 points + CTA. Ton : sec, surprenant."

Variant "Listicle"
Prompt:
"Transforme en 'Top 3' : 'Top 3 choses à savoir sur ...' + 3 items courts + CTA."

Optimisations de caption (description)
- Inclure 2–3 hashtags tendance (from trend_profile) + 2 hashtags ciblés (#science, #vulgarisation)
- Inclure crédit source + courte phrase 'Résumé de [source] — plus de références en commentaire'

A/B testing suggestions
- Teste les hooks : chiffre vs question vs affirmation choquante
- Teste la voix (voix chaude vs voix neutre vs voix jeune)
- Teste le format (15s vs 30s vs 45s)
- Teste la présence d'overlay text (pour retention)

Exemples de prompts complets (à envoyer à l'LLM)
1) Hooky 45s:
"Résume le texte suivant en FR en un script pour TikTok 45s. Commence par un hook 'Tu ne devineras jamais : [X]' où X est un chiffre ou un fait surprenant extrait du transcript. Puis 3 points très courts. Termine par 'Suis-nous pour en savoir plus' et propose 3 hashtags. Transcript: <<TRANSCRIPT>>"

2) 15s "punch":
"En 15s: 1 phrase d'accroche + 2 points ultra-concis + CTA 'Suis-nous'. Rédige en FR."

3) Fact-check prompt (obligatoire pour santé/claims)
"Liste chaque affirmation factuelle du script et fournis 1 source vérifiable (PubMed/arXiv/doi/institution) ou marque 'À VÉRIFIER'."

Notes finales
- Toujours joindre le trend_profile au prompt (passer top_hashtags/top_queries) pour que l'LLM intègre des termes tendance dans le texte.
- Générer 3 variantes par segment automatiquement (A/B/C) et publier en accord avec l'optimizer.
