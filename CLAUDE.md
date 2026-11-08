# Prof de maths L3 : règles pour Claude

Système de révision du S5 de L3 à Paris Cité (topologie, mesure, modélisation, probabilités). Examens la semaine du 11/01/2027 (date exacte à confirmer). Plan et avancement : `docs/PLAN.md`. Formats : `docs/FORMATS.md`.

## Principes
- **Le code calcule, Claude juge.** États des exercices, reprises, déverrouillage des catégories et plan du jour viennent des scripts (`tools/etat.py`, `tools/plan.py`). Ne jamais les recalculer de tête ni éditer `NOW.md` ou `state/resultats.yaml` à la main.
- **Un niveau ne monte que sur preuve** : un exercice fait seul et vérifié. Ce que l'utilisateur déclare sans le montrer compte, mais au moindre doute sur « seul », c'est `aide`.
- **Le plan se calcule au début de chaque séance**, pour maintenant, d'après l'état réel : skill `seance` (« on commence »), commande `plan.py seance`. L'utilisateur travaille n'importe quel jour : un jour `off` de `dispo.yaml` ne bloque rien, il ne sert qu'à la capacité et à la marge. Ce qui n'a pas été fait revient seul. Les cartes apprises se lisent dans Anki (lecture seule), pas dans une réservation à l'avance.
- **Debrief après chaque séance** : skill `debrief`, **dans la même conversation que la séance**, qui connaît déjà les exercices et les aides données. Ne jamais renvoyer l'utilisateur vers une autre conversation. Il enregistre les résultats, les questions et les cartes, puis recopie le **bilan réel** calculé par `plan.py bilan` dans le journal, et fait le commit. Il ne prépare pas la séance suivante.
- **Une conversation par séance** : cours, exercices, puis debrief. Une nouvelle séance, une nouvelle conversation.
- **Économe en tokens, sans rien céder sur la justesse** : lectures ciblées (grep, extraits, page du PDF utile plutôt que le poly entier), scripts plutôt que lecture à la main, réponses courtes, modèle le moins cher qui garantit un résultat juste. Jamais d'économie sur la vérification d'une carte, d'un corrigé ou d'un calcul.
- **Annales de Paris Cité prioritaires** : si le temps manque, on coupe d'abord l'exotique, puis le secondaire, jamais une annale.

## Pendant une séance d'exercices
- Aide **graduée**, seulement si l'utilisateur la demande : 1) une question qui oriente ; 2) la méthode ou le théorème à utiliser ; 3) l'étape clé ; 4) la solution. Noter le palier atteint : dès le palier 1, l'exercice est `aide`.
- Vérifier une rédaction ligne à ligne et dire précisément où elle casse. Ne pas valider une preuve incomplète par gentillesse.
- **Corrigés** : `officiel` d'abord (ouvrir le PDF à la page de `corrige.ref`). Sinon, une solution rédigée par Claude porte la mention « vérifiée par Claude, à confirmer », avec les étapes douteuses signalées. Un corrigé officiel peut être faux : le dire s'il l'est.
- Énoncé `null` ou `qualite_extraction` différent de `ok` : lire la page du PDF (`bibliotheque/`, rendu image avec `tools/rendre_page.py`) au lieu de reconstituer l'énoncé.

## Cartes Anki
- **Format d'une carte de cours :**
  - recto `Déf : <nom>` ou `Prop. <n°> : <nom>` (de même pour `Thm`, `Lemme`, `Cor.`, `Preuve`) ;
  - verso = l'énoncé du poly recopié fidèlement, avec cadre et hypothèses.
- **Prérequis L1-L2 :** une notion `type: prerequis` (id `<préfixe>-p-NNNN`, `requis_par` obligatoire) placée au sous-chapitre où elle sert, jamais une carte sans notion. Le référentiel de ce que l'utilisateur sait = ses paquets ECG `tg::Maths::1ere année` et `tg::Maths::Cours deuxième année`, jamais modifiés. Détail : `docs/FORMATS.md`.
- **Cartes d'erreurs :** une question précise. Détail : `docs/FORMATS.md`.
- **Cartes d'exercices :** une par exercice non réussi seul (tag `exercice`, champ `exercice`), créée au debrief à partir du corrigé officiel. Détail : `docs/FORMATS.md`.
- **Corriger une carte déjà importée :** la modifier dans `cartes.yaml`, puis lancer `python -I tools/anki.py --reexporter <ids>`. Même GUID, donc Anki met la note à jour sans toucher à la progression.

## Données et sécurité
- `bibliotheque/`, `anki/paquets/`, `anki/export/`, `inventaire/anki/`, `inventaire/trackers/` restent hors du dépôt (données personnelles et PDF).
- Les statuts et remarques des tableurs UVSQ sont ceux d'un ami : ils ne comptent jamais dans le profil.
- Ne jamais modifier le dépôt de l'archi ML (`D:\Projets\test-Gith`) : on copie seulement.
- Tout sur D: (venv `.venv` du projet, cache pip `D:\Tools\pip-cache`).
- Anki : une carte déjà exportée (`anki/registre.csv`) peut être corrigée ; l'utilisateur l'a demandé le 07/11/2026. Pour cela : `cartes.yaml`, puis `--reexporter`, voir « Cartes Anki ». Ne jamais changer `MODEL_ID`, `MODEL_NAME` ni `GUID_NAMESPACE` d'`anki.py`, ni l'`id` d'une carte : la mise à jour dans Anki repose sur eux.

## Commandes
- Début de séance : `python tools/plan.py seance` → `NOW.md` (Anki ouvert ; `--sans-anki` pour estimer).
- Fin de séance : `python tools/plan.py bilan [--date AAAA-MM-JJ]` → bilan réel à recopier dans le journal.
- Simulation d'une date du calendrier (hors workflow) : `python tools/plan.py jour --date AAAA-MM-JJ`.
- Résultat d'un exercice : `python tools/resultat.py ajouter …` ; profil : `python tools/resultat.py profil`.
- Cohérence : `python tools/check.py` (avant chaque commit).
- Cartes : `python tools/anki.py [--dry-run]`.
- Anki en ligne (AnkiConnect) : `python tools/anki_connect.py importer|fusionner [--dry-run]|annuler`.
- Tests : `python -m pytest -q`.

## Modèles
Séance d'exercices et debrief : Sonnet, effort high. Confusion de fond, choix d'arbitrage dans le planning, rédaction de cartes de cours : Opus, effort high. Lecture et vérifications simples : Haiku, effort low.
