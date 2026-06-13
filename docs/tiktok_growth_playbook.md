# TikTok growth playbook

Objectif: produire des videos VulgaScience monetisables, avec validation finale dans TikTok, puis apprentissage a partir des performances reelles.

## Regle de publication

Le mode cible est `REVIEW_MODE=tiktok_inbox`.

1. Le pipeline fabrique la video, les sous-titres, la voix off et la caption.
2. Le quality gate verifie le format vertical, la duree, l'audio et les encodages.
3. La video est envoyee dans TikTok inbox via `video.upload`.
4. La validation finale se fait dans TikTok: choix du son tendance, couverture, derniers reglages, puis publication.
5. Apres publication, les performances sont enregistrees dans `src_growth_memory.py`.

On ne donne jamais le mot de passe TikTok au projet. La connexion passe par OAuth.

## Acces TikTok necessaire

Pour le mode inbox:

- TikTok Developer App creee et rattachee au compte.
- Content Posting API activee sur l'app.
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`
- OAuth autorise avec le scope `video.upload`.
- `TIKTOK_REFRESH_TOKEN` obtenu apres connexion OAuth.

Pour publier directement sans passage dans l'app:

- scope `video.publish`;
- audit/approval TikTok;
- validation stricte des options de confidentialite.

Ce mode n'est pas prioritaire: il retire le meilleur moment de controle, c'est-a-dire l'ajout manuel du son tendance dans TikTok.

## Musique et sons tendance

L'API video TikTok permet d'envoyer un fichier et une caption, mais pas de choisir directement un son tendance TikTok pour une video. La bonne approche est donc:

- garder une ambiance sonore tres basse dans la video exportee;
- envoyer dans TikTok inbox;
- ajouter dans TikTok un son tendance autorise a 2-5% de volume;
- verifier que la voix reste claire.

Si un son est indispensable au concept, il doit etre integre comme element creatif avant rendu uniquement si les droits sont clairs.

## Capture des trends

Chaque idee de video doit recevoir un score avant production:

- `trend_fit`: le sujet colle-t-il a une tendance identifiable ?
- `science_fit`: peut-on le relier proprement a une notion scientifique ?
- `search_value`: est-ce une question que les gens cherchent vraiment ?
- `retention_hook`: le hook cree-t-il une tension dans les 2 premieres secondes ?
- `demo_potential`: peut-on montrer quelque chose, pas seulement expliquer ?
- `comment_trigger`: la video donne-t-elle une raison simple de commenter ?
- `monetization_fit`: duree, originalite, valeur educative, faible risque de demonetisation.

Priorite aux sujets qui cochent au moins 5 cases.

## Format recommande

Pour la monetisation, viser d'abord 60 a 75 secondes:

- hook brutal en 0-2 s;
- promesse claire en 2-5 s;
- demonstration ou image mentale toutes les 4-6 s;
- une seule notion technique principale;
- relance au milieu vers 25-35 s;
- CTA commentaire a la fin.

On peut tester du 30-45 s, mais ces formats servent surtout a l'acquisition et au test de hooks. La base monetisable reste la video de plus d'une minute.

## Boucle d'apprentissage

Apres chaque post, relever les chiffres a 2h, 24h et 7j:

- vues;
- likes;
- commentaires;
- partages;
- sauvegardes;
- duree moyenne de visionnage;
- taux de completion;
- nouveaux abonnes;
- revenu estime;
- son utilise;
- hook utilise;
- sujet;
- duree.

Puis enregistrer:

```powershell
python src_growth_memory.py record --video_id <id> --topic "<topic>" --hook "<hook>" --duration_seconds 60 --views 1000 --likes 80 --comments 12 --shares 8 --saves 20 --completion_rate 0.62
python src_growth_memory.py summary
```

Le prochain script doit utiliser `storage/learning/growth_summary.json` avant d'ecrire le hook et le CTA.

## Decision simple

- Forte completion, faibles partages: rendre la fin plus utile ou plus surprenante.
- Forts commentaires, faible completion: sujet clivant mais rythme trop lent.
- Forts partages, faible commentaires: ajouter une question plus personnelle.
- Bon demarrage, chute avant 10 s: hook promet plus que la suite ne livre.
- Bon 7j, faible 2h: sujet SEO/search; en refaire une variante plus claire.
