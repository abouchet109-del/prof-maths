# Prof de maths L3 : règles pour Claude

Système de révision du S5 de L3 à Paris Cité (topologie, mesure, modélisation, probabilités). Examens la semaine du 11/01/2027 (date exacte à confirmer). Plan et avancement : `docs/PLAN.md`. Formats : `docs/FORMATS.md`.

## Principes
- **Le code calcule, Claude juge.** États des exercices, reprises, déverrouillage des catégories et plan du jour viennent des scripts (`tools/etat.py`, `tools/plan.py`). Ne jamais les recalculer de tête ni éditer `NOW.md` ou `state/resultats.yaml` à la main.
- **Un niveau ne monte que sur preuve** : un exercice fait seul et vérifié. Ce que l'utilisateur déclare sans le montrer compte, mais au moindre doute sur « seul », c'est `aide`.
- **Debrief après chaque journée** : skill `debrief`.
- **Annales de Paris Cité prioritaires** : si le temps manque, on coupe d'abord l'exotique, puis le secondaire, jamais une annale.

## Pendant une séance d'exercices
- Aide **graduée**, seulement si l'utilisateur la demande : 1) une question qui oriente ; 2) la méthode ou le théorème à utiliser ; 3) l'étape clé ; 4) la solution. Noter le palier atteint : dès le palier 1, l'exercice est `aide`.
- Vérifier une rédaction ligne à ligne et dire précisément où elle casse. Ne pas valider une preuve incomplète par gentillesse.
- **Corrigés** : `officiel` d'abord (ouvrir le PDF à la page de `corrige.ref`). Sinon, une solution rédigée par Claude porte la mention « vérifiée par Claude, à confirmer », avec les étapes douteuses signalées. Un corrigé officiel peut être faux : le dire s'il l'est.
- Énoncé `null` ou `qualite_extraction` différent de `ok` : lire la page du PDF (`bibliotheque/`, rendu image avec `tools/rendre_page.py`) au lieu de reconstituer l'énoncé.

## Données et sécurité
- `bibliotheque/`, `anki/paquets/`, `anki/export/`, `inventaire/anki/`, `inventaire/trackers/` restent hors du dépôt (données personnelles et PDF).
- Les statuts et remarques des tableurs UVSQ sont ceux d'un ami : ils ne comptent jamais dans le profil.
- Ne jamais modifier le dépôt de l'archi ML (`D:\Projets\test-Gith`) : on copie seulement.
- Tout sur D: (venv `.venv` du projet, cache pip `D:\Tools\pip-cache`).
- Anki : une carte exportée (`anki/registre.csv`) n'est jamais réexportée ni modifiée ici ; Anki en est maître. Ne jamais changer `MODEL_ID`, `MODEL_NAME` ni `GUID_NAMESPACE` d'`anki.py`.

## Commandes
- Plan du jour : `python tools/plan.py jour [--date AAAA-MM-JJ]` → `NOW.md`.
- Résultat d'un exercice : `python tools/resultat.py ajouter …` ; profil : `python tools/resultat.py profil`.
- Cohérence : `python tools/check.py` (avant chaque commit).
- Cartes : `python tools/anki.py [--dry-run]`.
- Tests : `python -m pytest -q`.

## Modèles
Séance d'exercices et debrief : Sonnet, effort high. Confusion de fond, choix d'arbitrage dans le planning, rédaction de cartes de cours : Opus, effort high. Lecture et vérifications simples : Haiku, effort low.
