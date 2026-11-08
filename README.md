# Prof de maths L3

Système de révision pour le S5 de L3 maths à Paris Cité (topologie, mesure et intégration, modélisation, probabilités), piloté avec Claude Code. Objectif : réussir les examens de la semaine du 11/01/2027, et toutes les annales de Paris Cité.

Il reprend les principes de [archi-ml-ai-researcher](https://github.com/abouchet109-del/archi-ml-ai-researcher) (le code calcule, Claude juge ; un niveau ne monte que sur preuve ; debrief après chaque session), sans jamais modifier ce dépôt : ses outils sont copiés dans `tools/origine-archi-ml/` et `skills-origine-archi-ml/`.

## Ce que fait le système
- **Exercices :** tous les exercices de TD, DM et annales (Paris Cité, plus l'UVSQ en complément) sont extraits, classés par sous-chapitre et de vital à exotique. On ne passe à la catégorie suivante d'un sous-chapitre qu'une fois la précédente maîtrisée. Les annales de Paris Cité sont prioritaires et toujours planifiées.
- **Cours :** les notions manquantes du paquet Anki, y compris les prérequis de L1-L2, sont fichées par le système. L'utilisateur apprend par Anki ; les 30 min de cours quotidiennes servent à approfondir.
- **Planning :** au début de chaque séance (dire « on commence » à Claude), `python tools/plan.py seance` écrit `NOW.md` pour maintenant, d'après ce qui a réellement été fait : 2 h d'exercices et d'annales, 30 min de cours, les cartes à apprendre (lues dans Anki par AnkiConnect). Ce qui n'a pas été fait revient seul.
- **Compréhension :** pendant la séance, Claude écoute comment l'utilisateur raisonne à voix haute. Après chaque exercice non réussi seul, il explique où ça a bloqué, cherche la cause par une ou deux questions et lui fait dire ce qu'il en retient. Le debrief (« debrief », dans la même conversation) enregistre les résultats (`tools/resultat.py`) et fixe sur preuve le niveau de chaque notion travaillée dans `state/comprehension.yaml` ; le plan suivant en tire les cartes à revoir, les exercices prioritaires et la section « À consolider ». Règles pour Claude : `CLAUDE.md`.

## Où sont les choses
| Chemin | Contenu |
|---|---|
| `docs/PLAN.md` | plan, avancement, modèle et effort par étape |
| `docs/FORMATS.md` | contrat des fichiers |
| `matieres/<matiere>/exercices.yaml` | exercices extraits (et `exercices_uvsq.yaml` pour les tableurs UVSQ) |
| `matieres/<matiere>/notions.yaml` | notions du cours |
| `matieres/<matiere>/couverture.yaml`, `cartes_a_creer.yaml` | comparaison avec le paquet Anki |
| `matieres/<matiere>/cartes.yaml` | cartes rédigées |
| `matieres/<matiere>/methodes.yaml`, `classement.yaml` | méthodes types et classement des exercices |
| `inventaire/` | inventaires des sources (`sources.csv`, `uvsq.csv`) et fichiers de travail régénérables |
| `tools/` | scripts : tri, extraction, vérification sur images, classement, export Anki |
| `bibliotheque/`, `anki/paquets/`, `anki/export/` | PDF, paquets et données Anki : **jamais versionnés** |

## Importer les cartes
Double-cliquer sur `anki/paquets/prof-maths-<date>.apkg`. Les cartes arrivent dans `tg::Maths::L3 Paris Cité::<matière>::<chapitre>`, avec l'étiquette `prof-maths`. Un nouvel export ne contient que les cartes jamais exportées (`anki/registre.csv`) : Anki reste maître des cartes importées.

## Installation
Python 3.12, puis dans le dossier du projet :

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python.exe -m pip install pyyaml genanki pypdf pymupdf openpyxl zstandard scikit-learn
```
