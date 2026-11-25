# Prof de maths L3 : règles pour Claude

Système de révision du S5 de L3 à Paris Cité (topologie, mesure, modélisation, probabilités). Examens la semaine du 11/01/2027 (date exacte à confirmer). Plan et avancement : `docs/PLAN.md`. Formats : `docs/FORMATS.md`.

## Principes
- **Le code calcule, Claude juge.** États des exercices, reprises, déverrouillage des catégories et plan du jour viennent des scripts (`tools/etat.py`, `tools/plan.py`). Ne jamais les recalculer de tête ni éditer `NOW.md` ou `state/resultats.yaml` à la main.
- **Claude juge, l'utilisateur tranche entre `reussi` et `presque`** (règle du 12/11/2026) : Claude propose la catégorie (reussi, presque, aide = bloqué puis corrigé lu, non_fait) d'après la rédaction. Entre `reussi` et `presque` (coquille, petite erreur), le verdict de l'utilisateur est enregistré, avec la note « tranché par l'utilisateur ». `aide` et `non_fait` restent le jugement de Claude.
- **Le plan se calcule au début de chaque séance**, pour maintenant, d'après l'état réel : skill `seance` (« on commence »), commande `plan.py seance`. L'utilisateur travaille n'importe quel jour : un jour `off` de `dispo.yaml` ne bloque rien, il ne sert qu'à la capacité et à la marge. Ce qui n'a pas été fait revient seul. Les cartes apprises se lisent dans Anki (lecture seule), pas dans une réservation à l'avance.
- **Debrief après chaque séance** : skill `debrief`, **dans la même conversation que la séance**, qui connaît déjà les exercices et les aides données. Ne jamais renvoyer l'utilisateur vers une autre conversation. Il enregistre les résultats, reprend rapidement chaque coquille ou incompréhension liée au cours (une question courte chacune), met à jour la compréhension (`state/comprehension.yaml`) et fait les cartes, puis recopie le **bilan réel** calculé par `plan.py bilan` dans le journal, et fait le commit. Il ne prépare pas la séance suivante.
- **Modèle de compréhension** (`state/comprehension.yaml`, format `docs/FORMATS.md`) : ce que l'utilisateur dit à voix haute est la donnée principale. Le cours mesure ce qu'il tient avant d'enseigner, une étape à la fois ; le debrief fixe le niveau de chaque notion travaillée sur preuve, et le plan en tire cartes, exercices et « À consolider ».
- **Une conversation par séance** : cours, exercices, puis debrief. Une nouvelle séance, une nouvelle conversation.
- **Économe en tokens, sans rien céder sur la justesse** : lectures ciblées (grep, extraits, page du PDF utile plutôt que le poly entier), scripts plutôt que lecture à la main, réponses courtes, modèle le moins cher qui garantit un résultat juste. Jamais d'économie sur la vérification d'une carte, d'un corrigé ou d'un calcul.
- **Annales de Paris Cité prioritaires** : si le temps manque, on coupe d'abord l'exotique, puis le secondaire, jamais une annale.
- **Objectif de l'échéance** (choix du 10/11/2026) : chaque annale de Paris Cité, exercice vital et important réussi seul une fois. La section « Échéance » de `NOW.md` donne le rythme requis, le rythme observé et la date de fin projetée (`plan.rythme`) : la lire à l'utilisateur en début de séance.

## Pendant une séance d'exercices (règle du 12/11/2026 : aller vite)
- L'utilisateur travaille **seul**, sans échange ni photo au fil de l'eau. Bloqué, il lit le corrigé lui-même. Claude ne répond qu'aux questions qu'il pose (aide graduée s'il la demande : 1) une question qui oriente ; 2) la méthode ; 3) l'étape clé ; 4) la solution ; dès le palier 1, c'est `aide`).
- **À la fin**, il envoie en une fois la rédaction des exercices **nouveaux** (première fois). Pour une reprise, il ne donne que le résultat.
- **Correction rapide**, exercice par exercice : seulement l'endroit précis de chaque erreur, classée coquille / petite erreur / vraie faute, puis la catégorie proposée. Ne rien faire refaire, ne pas débattre. Ne jamais valider une erreur par gentillesse.
- **Bloqué ou pas compris** (`aide`, `non_fait`) : là seulement, on reprend avec Claude (au debrief, 5 min au plus) : l'étape du blocage, comment l'idée se trouvait.
- **Deux sortes de reprises** (`plan.py`) : dernier résultat `aide`/`non_fait` → reprise avec Claude en fin de séance ; `reussi`/`presque` → « Reprises seul dans Anki », hors séance : l'utilisateur dit seulement ce qu'il a réussi ou raté, et on l'enregistre.
- **Corrigés** : `officiel` d'abord (ouvrir le PDF à la page de `corrige.ref`). Sinon, une solution rédigée par Claude porte la mention « vérifiée par Claude, à confirmer », avec les étapes douteuses signalées. Un corrigé officiel peut être faux : le dire s'il l'est.
- Énoncé `null` ou `qualite_extraction` différent de `ok` : lire la page du PDF (`bibliotheque/`, rendu image avec `tools/rendre_page.py`) au lieu de reconstituer l'énoncé.

## Cartes Anki
- **Format d'une carte de cours :**
  - recto `Déf : <nom>` ou `Prop. <n°> : <nom>` (de même pour `Thm`, `Lemme`, `Cor.`, `Preuve`) ;
  - verso = l'énoncé du poly recopié fidèlement, avec cadre et hypothèses.
- **Prérequis L1-L2 :** une notion `type: prerequis` (id `<préfixe>-p-NNNN`, `requis_par` obligatoire) placée au sous-chapitre où elle sert, jamais une carte sans notion. Le référentiel de ce que l'utilisateur sait = ses paquets ECG `tg::Maths::1ere année` et `tg::Maths::2ere année ECG`, jamais modifiés. Règle du 18/11/2026 : seul ECG compte comme su ; une ancienne carte AoutLicenceMath ou Centrale déjà apprise se réapprend dans l'ordre du poly, et le poly de Paris Cité reste la source de chaque notion. Détail : `docs/FORMATS.md`.
- **Le poly d'abord (règle du 25/11/2026) :** chaque notion du poly de Paris Cité a ses propres cartes, recopiées du poly, même quand une carte ECG ou ancienne la couvre déjà ; l'ancienne carte vient en second. `check.py` refuse une notion du poly sans carte.
- **Cartes d'erreurs :** plus créées depuis le 08/11/2026 (les existantes restent) : une confusion va dans `state/comprehension.yaml`, et les cartes de la notion repassent.
- **Cartes d'exercices :** une par exercice **nouveau, réussi ou pas** (règle du 12/11/2026), plus une pour toute reprise ratée qui n'en a pas ; tag `exercice`, champ `exercice`, créée au debrief à partir du corrigé officiel, avec la section « Coquilles / points d'attention ». Détail : `docs/FORMATS.md`.
- **Corriger une carte déjà importée :** la modifier dans `cartes.yaml`, puis lancer `python -I tools/anki.py --reexporter <ids>`. Même GUID, donc Anki met la note à jour sans toucher à la progression.
- **Deux PC, un seul import** (règle du 24/11/2026) : un paquet `.apkg` s'importe dans Anki sur **un seul** PC, puis la synchro AnkiWeb l'amène sur l'autre. Ne jamais importer le même paquet sur les deux PC : une synchro normale garde alors les deux exemplaires (le 21/11/2026 : 503 doublons et des paquets suffixés « + », supprimés le 24/11). Une session sur l'autre PC qui crée des cartes les commite et laisse l'import au PC qui fait référence, ou importe elle-même et le dit pour que l'autre PC ne le refasse pas.

## Données et sécurité
- `bibliotheque/`, `anki/paquets/`, `anki/export/`, `inventaire/anki/`, `inventaire/trackers/` restent hors du dépôt (données personnelles et PDF).
- Les statuts et remarques des tableurs UVSQ sont ceux d'un ami : ils ne comptent jamais dans le profil.
- Ne jamais modifier le dépôt de l'archi ML (`D:\Projets\test-Gith`) : on copie seulement.
- Tout sur D: (venv `.venv` du projet, cache pip `D:\Tools\pip-cache`).
- Anki : une carte déjà exportée (`anki/registre.csv`) peut être corrigée ; l'utilisateur l'a demandé le 07/11/2026. Pour cela : `cartes.yaml`, puis `--reexporter`, voir « Cartes Anki ». Ne jamais changer `MODEL_ID`, `MODEL_NAME` ni `GUID_NAMESPACE` d'`anki.py`, ni l'`id` d'une carte : la mise à jour dans Anki repose sur eux.

## Commandes
- Début de séance : `python tools/plan.py seance` → `NOW.md` (Anki ouvert ; `--sans-anki` pour estimer ; `--toutes-reprises` : ajoute à la toute fin, hors budget, tous les autres exercices à revoir et une recherche Anki de leurs cartes, quand l'utilisateur a du temps en plus).
- Fin de séance : `python tools/plan.py bilan [--date AAAA-MM-JJ]` → bilan réel à recopier dans le journal.
- Simulation d'une date du calendrier (hors workflow) : `python tools/plan.py jour --date AAAA-MM-JJ` : affiche le plan, n'écrit rien (`--ecrire` pour écrire `NOW.md` et `state/`).
- Résultat d'un exercice : `python tools/resultat.py ajouter …` (`--questions "Q1=reussi,Q2=presque"` : suivi par sous-question, la reprise ne redemande que ce qui manque) ; profil : `python tools/resultat.py profil`.
- Cohérence : `python tools/check.py` (avant chaque commit).
- Cartes : `python tools/anki.py [--dry-run]`.
- Anki en ligne (AnkiConnect) : `python tools/anki_connect.py importer|fusionner [--dry-run]|ranger [--dry-run]|annuler`. Chaque chapitre a ses sous-paquets `::Cours` et `::Exercices`.
- Tests : `python -m pytest -q`.

## Modèles
Séance d'exercices et debrief : Sonnet, effort high. Confusion de fond, choix d'arbitrage dans le planning, rédaction de cartes de cours : Opus, effort high. Lecture et vérifications simples : Haiku, effort low.
