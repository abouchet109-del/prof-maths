# Plan de construction : prof de maths L3

Dépôt indépendant de `archi-ml-ai-researcher`. On copie ce qui sert ; l'archi code n'est jamais modifiée.

## Cadre
- **Examens :** semaine du 11/01/2027 retenue, à confirmer (le 09/01/2027 est un samedi).
- **Budget :** chaque jour travaillé, 2 h d'exercices et d'annales, plus 30 min de cours. Du 03/11 au 10/01, hors week-ends sautés (07-08/11 et 21-22/11, communs avec le ML) : environ **158 h d'exercices et 32 h de cours**, en comptant 4 h d'exercices par jour dans les 2 semaines à 28 h (21/12 au 03/01).
- **Cartes Anki :** le système les crée toutes et les importe : cours de L3 et prérequis de L1-L2 manquants. L'utilisateur ne fait que les réviser, hors du temps planifié, et peut apprendre le cours directement par Anki : les cartes sont disponibles sans attendre qu'une séance soit faite.
- **Sessions de cours (30 min) :** approfondissement et compréhension, pas première lecture. Elles visent ce que les debriefs et les exercices ratés révèlent.
- **Harmonisation L1-L2 :** pour chaque exercice et annale, on repère les prérequis ; ceux qui ne sont ni au programme d'ECG ni dans le cours de L3 deviennent des notions à cartes (18/11/2026 : seul ECG compte comme su ; une carte AoutLicenceMath ou Centrale existante est rattachée, pas recopiée). Source : documents envoyés par l'utilisateur, sinon un cours de référence vérifié, jamais de mémoire.
- **Matières :** topologie, mesure, modélisation, probabilités.
- **Principes repris :** le code calcule, Claude juge ; un niveau ne monte que sur preuve ; debrief après chaque session ; révisions Anki et debriefs hors du temps planifié.

## Règles décidées par l'utilisateur (03/11/2026)
- **Tous les exercices sont classés**, quelle que soit la source.
- **Les annales de Paris Cité passent avant tout** : l'objectif est de toutes les réussir.
- **Le planning réserve du temps pour toutes les annales de Paris Cité**, même si les autres exercices ne sont pas terminés. Si le temps manque, ce sont les autres exercices qui sont coupés.
- **Tableurs UVSQ :** les statuts et remarques sont ceux d'un ami, jamais une preuve de maîtrise de l'utilisateur. Ils servent seulement de modèle de présentation et d'indice de classement.

## Programme quotidien (`NOW.md`)
À chaque séance (`plan.py seance`, calculé au moment où l'on commence), sans que l'utilisateur ait à décider quoi que ce soit :
1. **Exercices et annales (2 h) :** liste précise, nouveaux exercices et exercices à revoir, avec le nombre attendu.
2. **Cours (30 min) :** ce qu'il faut approfondir, avec les pages du poly, plus la section « À consolider » (notions faibles de `state/comprehension.yaml`, 5 lignes au plus).
3. **Anki, à apprendre :** les nouvelles cartes du jour, par paquet et étiquette, avec leur nombre, en priorité celles des exercices à venir et les prérequis de L1-L2.
4. **Anki, à réviser :** toutes les cartes dues, plus les paquets anciens à reprendre parce qu'ils servent aux exercices du jour.
5. **Debrief** en fin de séance, dans la même conversation : résultats, niveau de compréhension de chaque notion travaillée (sur preuve), cartes d'exercices, bilan réel et commit. Il ne prépare pas la séance suivante.

Anki est lu en lecture seule par AnkiConnect (cartes apprises) ; Anki fermé, le plan estime les cartes et le signale.

## Annales de Paris Cité dans le planning
- **Volume :** 16 annales (topologie 8, modélisation 4, probabilités 4), soit environ 26 h de composition : les examens de topologie durent 2 h, ceux de modélisation et de probabilités 1 h 30. Aucune en mesure, confirmé par l'utilisateur : la référence est le programme de Paris Cité (poly, TD, DM), et les annales de l'UVSQ servent d'entraînement et d'examens blancs, limitées à ce programme.
- **Réserve :** environ 48 h sur les 158 h d'exercices, en comptant 1 h 30 de reprise par annale (hypothèse à recalibrer).
- **Tout exercice d'annale de Paris Cité porte `annale_prioritaire: true`**, en plus de son importance. Il passe devant les autres exercices et ne peut pas être coupé.
- **Les annales les plus récentes de chaque matière restent inédites** jusqu'aux 2 semaines à 28 h, puis servent d'examens blancs chronométrés. Les plus anciennes se travaillent par chapitre.

## Paquet Anki (lu le 03/11/2026)
- 2 089 cartes, 2 085 notes : 1re année ECG (636), 2e année ECG (402), `AoutLicenceMath` (420 : topologie et mesure), DD Centrale (630, dont 76 dans `_Doublons à supprimer`).
- **Classement existant :** par chapitre et par TD en topologie et en mesure, sans sous-chapitres. Aucun paquet L3 de probabilités ni de modélisation. Les sous-chapitres viendront donc des sections des polys.
- **95 % des notes contiennent une image :** la réponse est rarement en texte, mais le recto donne souvent le nom de la notion. La comparaison se fait d'abord sur les rectos, à faible coût ; les images ne sont lues que pour les cartes sans recto exploitable ou les cas douteux.
- **Export :** `inventaire/anki/notes.jsonl` et `decks.csv`. Le paquet n'est jamais modifié.

## Sources (après tri)
- **Paris Cité :** `bibliotheque/<matiere>/`, détail dans `inventaire/sources.csv`.
- **UVSQ :** `bibliotheque/uvsq/`, détail dans `inventaire/uvsq.csv`.
- **Tableurs d'exercices UVSQ :** `inventaire/trackers/`, 402 lignes classées, sans la catégorie « secondaire » ; ils ne couvrent pas les TD de Paris Cité.
- **Manques constatés :** aucune annale de mesure à Paris Cité ; pas de corrigé pour les TD de topologie de Paris Cité ni pour les TD 3 à 7 de mesure ; pas de TD 4 corrigé en probabilités.

## Avancement (03/11/2026)

| Étape | Statut |
|---|---|
| 0 Tri et inventaire | fait |
| 1 Formats | fait (`docs/FORMATS.md`, complété au fil des étapes) |
| 2-3 Extraction des exercices | fait : topologie 233, mesure 110 + 82 UVSQ, modélisation 33, probas 47 + 162 UVSQ (entrées UVSQ créées depuis les tableurs, énoncé lu seulement si planifié) |
| 3b Vérification sur images | fait : annales de Paris Cité et énoncés douteux ; 10 fautes de maths corrigées. Restent `a_verifier` : `topo-partiel2020-21-ex01` et `ex02` (sujet absent), `topo-exam2021-22-ex01`, `mes-td4-ex03`, `mes-td4-ex05` (coquilles dans les PDF) |
| 4 Lecture d'Anki | fait, depuis `tgmathankidonnées.apkg` (instantané, pas de lecture en direct) |
| 5 Notions | fait : 382 notions (topologie 94, mesure 69, modélisation 75, probas 144) |
| 6 Classement | fait pour les 4 matières (Opus) ; voir le bilan ci-dessous |
| 7a-7b Couverture et trous | fait : 237 cartes à créer, dont 9 prérequis de L1-L2, tous inconnus de l'utilisateur. Ils ont donné 20 cartes (étiquette `prerequis-l1l2`), relues par Opus : 1 erreur corrigée (φ″ devenu φ′ à cause de l'échappement YAML), 1 carte retirée car elle donnait la solution d'une annale. Paquet : `prof-maths-2026-11-03-2.apkg`. Les fonctions génératrices n'étaient pas au programme d'ECG ; elles sont couvertes par les cartes de modélisation |
| 7c-7d Rédaction et relecture | fait : 509 cartes ; relecture Opus de 46 cartes, aucune erreur de fond, 5 cartes précisées |
| 7e Paquet | fait : `anki/paquets/prof-maths-2026-11-03.apkg`, à importer par l'utilisateur |
| 8 Corrigés vérifiés | à la demande, rien encore |
| 9-10 Socle et planificateur | fait : `tools/etat.py`, `plan.py`, `resultat.py`, `check.py`, 14 tests (`tools/tests/`). `plan.py jour` écrit `NOW.md` ; le 04/11 : 6 exercices (120 min), 3 notions, 12 cartes. Marge à l'échéance : +2385 min (6975 min restantes, 9360 min de capacité) |
| 11 Règles de session | fait en partie : `CLAUDE.md` et skill `debrief`. Pas encore de check-in hebdomadaire ni de skill imprévu (à faire si le besoin apparaît) |
| 12 Contrôle | fait : tests et `check.py` passent sur les vraies données |

**Choix du planificateur** (progression par blocs de sous-chapitre, 07/11/2026) :
- **Matière du jour :** rotation topologie, mesure, proba, modélisation. Chaque bloc planifié est mémorisé dans `state/blocs.yaml`. La matière du jour est la suivante dans le cycle après celle du dernier bloc **effectivement travaillé** (date antérieure ayant au moins un résultat dans `resultats.yaml`) ; un jour planifié mais non travaillé ne fait pas avancer la rotation. Sans bloc travaillé, on prend la première. Une matière qui n'a plus rien à planifier est sautée. Replanifier une date redonne le même bloc.
- **Sous-chapitre courant :** le premier, dans l'ordre du poly (tri naturel, « 2.10 » après « 2.9 »), qui a encore une ligne principale. Ligne principale = ses `vital` pas encore acquis, puis ses `important` jamais tentés ; les annales prioritaires, doublons et exercices indisponibles sont exclus. `state/avancement_cours.yaml` (`{matiere: dernier sous-chapitre vu en CM | null}`) interdit de planifier au-delà, pour les exercices comme pour les cartes.
- **Budget des exercices**, dans cet ordre :
  1. les **reprises** dues, toutes matières, les plus en retard d'abord, plafonnées à `minutes_reprises_max` (30 min). La plus urgente passe même si elle dépasse seule le plafond, sinon un exercice de plus de 30 min ne serait jamais repris. Un exercice à revoir dont des questions sont déjà justes ne reprend que les autres, au prorata du temps (suivi par sous-question, `docs/FORMATS.md`) ;
  2. au plus **une annale prioritaire** nouvelle hors période quota. Elle n'est éligible que si son sous-chapitre est passé dans sa matière (avant le courant), ou à partir de `annales_libres_des` (07/12/2026), ou si la marge à l'échéance devient négative. Les examens blancs (dernière année de chaque matière) restent réservés à la période à 28 h, où plusieurs annales par jour sont possibles ;
  3. le **bloc** : la ligne principale du sous-chapitre courant (vital puis important, dans l'ordre du fichier), qui continue sur le sous-chapitre suivant s'il reste du temps. Un exercice trop long est sauté, mais le bloc ne saute pas à un sous-chapitre plus loin pour combler un trou.
  - **Rythme** (`plan.rythme`, section « Échéance » de `NOW.md` et bilan de séance) : objectif = annales de Paris Cité, vital et important réussis seul une fois. Charge minimale = `temps_min` des jamais tentés + temps de reprise des à revoir. Requis par semaine = exercices restants × 7 / jours de travail restants. Observé = exercices passés acquis sur 7 jours. Projection = aujourd'hui + restants × 7 / observé. Les `temps_min` restent fixes.
  - Dans les reprises et le bloc, les exercices d'une notion faible de `state/comprehension.yaml` (niveau `recitee` ou moins, ou `fragile`, ou confusion ouverte) passent en premier, jamais au détriment de l'annale.
- **Secondaire et exotique :** seulement quand toute la ligne principale de la matière est épuisée, avec le passage de catégorie par sous-chapitre (la catégorie suivante s'ouvre quand tous les exercices de la précédente sont au moins acquis).
- **Cours :** 10 min par notion, tirées du sous-chapitre du bloc (notions de ses exercices, puis notions de `notions.yaml` qui lui sont rattachées).
- **Cartes d'exercices :** à part, dans leur propre recherche « exercices à revoir » de `NOW.md` (un paquet filtré séparé), 10 par jour au plus (`exercices_par_jour`).
- **Cartes de cours :** 20 par jour au plus (`cartes_par_jour`). D'abord les cartes d'erreurs et les cartes `a_revoir` dues, puis les prérequis L1-L2 encore `inconnue`, puis les cartes des notions faibles qui repassent une fois, puis les cartes pas encore données du sous-chapitre du bloc (ses prérequis L1-L2 avant les cartes du poly), puis celles des sous-chapitres suivants de la même matière. Une carte n'est jamais donnée deux fois, sauf ce repassage (`state/anki_plan.yaml`).
- **`NOW.md` :** `Bloc du jour : <Matière> — <sous-chapitre> (vitaux acquis x/y)` en tête, section « À consolider » avant « Cours », exercices dans l'ordre de travail Annale, Bloc, puis Reprises en fin de séance (faites seul sur papier ; le choix des exercices réserve toujours les reprises en premier), échéance avec une ligne par matière (minutes restantes). Une matière est signalée quand son reste dépasse sa part de la capacité restante (capacité ÷ 4 × 1,25). 60 lignes au plus.

**Bilan du classement** (heures estimées par les agents, doublons exclus) :

| Matière | Annales Paris Cité | Vital | Important | Secondaire | Exotique |
|---|---|---|---|---|---|
| Topologie | 30 ex., 16,1 h | 40 ex., 13,8 h | 33 ex., 10,2 h | 83 ex., 22,8 h | 37 ex., 14,5 h |
| Mesure | aucune | 30 ex., 15,2 h | 23 ex., 11,9 h | 74 ex., 34,5 h | 6 ex., 4,9 h |
| Modélisation | 11 ex., 8,2 h | 9 ex., 5,9 h | 8 ex., 2,9 h | 4 ex., 1,8 h | 1 ex., 0,8 h |
| Probas | 15 ex., 8,8 h | 27 ex., 12,8 h | 26 ex., 10,3 h | 97 ex., 37 h | 35 ex., 16,3 h |
| **Total** | **33 h** | **47,7 h** | **35,3 h** | 96 h | 36,5 h |

Annales, vitaux et importants : environ 116 h sur 158 h d'exercices, ce qui laisse environ 40 h pour les reprises et une partie des secondaires.

À reprendre au planificateur : en mesure, les vitaux sont surtout des annales UVSQ ; en probas, les vitaux des chapitres 4 et 5 viennent de l'UVSQ et sont classés sur leur titre seul (à confirmer à l'extraction) ; en topologie, les Hilbert et la norme d'opérateur sont vitaux mais hors du cours actuel, et le calcul différentiel UVSQ est exotique faute d'annale de Paris Cité ; doublons incertains signalés par les agents (proba chap-2-exam-24-25-ex5, mesure chap-2-cc1-25-ex2).

**En attente de l'utilisateur :** import des deux paquets ; installation d'AnkiConnect, utile pour étiqueter les anciennes cartes par chapitre ; éventuel sujet du partiel de topologie 2020-21 ; nouvelle version du poly de mesure, qui va s'allonger. À son arrivée : extraire les nouvelles notions, comparer au paquet, rédiger les cartes, y compris les 3 notions de mesure sans carte si le poly les couvre.

**Examens :** « semaine du 9 janvier ». Le 09/01/2027 est un samedi, donc le planning vise par prudence le lundi 04/01 : le planning finit le 03/01, avec une marge de +1545 min. `NOW.md` donne aussi une recherche Anki par sujet du jour, qui réunit anciennes et nouvelles cartes grâce aux `nid` de `couverture.yaml`.

**Points ouverts :** 3 notions de mesure sans carte faute de source (mesure extérieure et Carathéodory, intégrales contre comptage, Dirac et densité, intégrale de Gauss) ; aucun TD sur le processus de Poisson ; annales de probas de l'UVSQ non extraites ; le poly de modélisation contient deux erreurs (PageRank p. 21, apériodicité p. 9), corrigées dans les cartes.

**Coût observé :** environ 250 000 tokens par agent pour les tâches lourdes ; une limite de session atteinte une fois, reprise sans perte.

## Étapes

| # | Étape | Exécutant | Modèle, effort | Entrée | Sortie |
|---|---|---|---|---|---|
| 0 | Tri et inventaire | session principale | fait | Téléchargements, zips | `bibliotheque/`, `inventaire/` |
| 1 | Contrat de formats | session principale | Opus, high | ce plan | `docs/FORMATS.md` |
| 2 | Pilote d'extraction : topologie | 1 agent | Sonnet, medium | TD, annales, DM, tableur | `matieres/topologie/exercices.yaml` |
| 3 | Extraction des 3 autres matières | 1 agent par matière | Sonnet, medium | idem, format corrigé après le pilote | `matieres/*/exercices.yaml` |
| 3b | Vérification sur images des annales de Paris Cité et des énoncés douteux | 1 agent | Sonnet, medium | pages en PNG + énoncés extraits | corrections appliquées. Les autres énoncés sont vérifiés quand ils sont planifiés ; le plan du jour cite toujours le PDF et la page |
| 4 | Lecture d'Anki | utilisateur (export), puis 1 agent | Sonnet, medium | export `.colpkg` | taxonomie et liste des cartes |
| 5 | Inventaire des notions et méthodes | 1 agent par matière | Sonnet, medium | polys de Paris Cité seuls | `matieres/*/notions.yaml` |
| 6 | Classement vital à exotique | 1 agent par matière | Opus, high | fichiers des étapes 3 à 5, pas les PDF | exercices classés et justifiés |
| 7a | Comparaison cours et paquet : notions sans carte | 1 agent par matière | Sonnet, medium | notions + rectos des cartes | `matieres/*/cartes_a_creer.yaml` |
| 7b | Harmonisation L1-L2 : prérequis des exercices et annales absents d'ECG, du paquet et du cours de L3 | 1 agent par matière | Sonnet, high ; arbitrage Opus, high sur les cas douteux | exercices + notions + rectos + prérequis envoyés | liste des trous, ajoutée à 7a |
| 7c | Rédaction de toutes les cartes manquantes depuis la source | 1 agent par matière | Sonnet, high | listes 7a et 7b, pages exactes des sources | `matieres/*/cartes.yaml` |
| 7d | Relecture des cartes contre la source, par échantillon | 1 agent | Opus, medium | cartes + pages citées | erreurs à corriger |
| 7e | Paquet d'import : nouvelles cartes seulement, cartes existantes jamais modifiées | script `anki.py` adapté | sans modèle | `cartes.yaml` | `.apkg` à ouvrir |
| 8 | Corrigés sans source officielle | à la demande, exercice par exercice | rédaction Sonnet, high ; vérification à l'aveugle Opus, high | énoncé seul pour le vérificateur | corrigé avec statut |
| 9 | Socle : calendrier, validation, `NOW.md`, Anki | 1 agent | Sonnet, high | copie de `tools/` | `tools/`, tests |
| 10 | Planificateur par exercices et passage de catégorie | 1 agent | Sonnet, high ; Opus si deux échecs | étapes 6 et 9 | plan de chaque session |
| 11 | Règles de session et skills de tutorat | session dédiée | Opus, high | copie des skills | `CLAUDE.md`, `.claude/skills/` |
| 12 | Contrôle de cohérence et tests | 1 agent | Haiku, low | tout | rapport |

**Fonctionnement courant ensuite :** plan du jour et imprévu en Sonnet low à medium ; debrief et check-in en Sonnet high ; correction d'examen blanc en Opus high.

**Ordre :** 2, puis 3. Les étapes 4, 5 et 9 peuvent tourner en parallèle, puis 7a à 7e et 6, puis 10, 11 et 12. Les cartes passent avant le planificateur : elles servent dès qu'elles sont importées. L'étape 8 ne se déclenche qu'au besoin.

## Économies de tokens
- **Coût mesuré du pilote de topologie : environ 254 000 tokens pour 233 entrées.** D'où l'extraction ciblée : pour la mesure et les probabilités, les exercices des tableurs UVSQ sont créés par script, énoncés lus seulement s'ils sont planifiés. Les agents ne lisent que les sources de Paris Cité (et les annales de l'UVSQ en mesure, faute d'annales de Paris Cité). Les annales de probabilités de l'UVSQ sont hors du tableur : elles sont ajoutées seulement s'il reste du temps pour s'en servir.
- Le texte est extrait une fois par script ; les agents ne lisent que ce texte, et une page en image seulement si une formule est illisible.
- Les slides, les TP et le manuel R (environ 100 000 tokens) ne sont ouverts qu'en cas de doute : les polys couvrent le même contenu.
- Les étapes de jugement lisent les fichiers structurés, jamais les PDF.
- Un pilote sur la plus petite matière corrige le format avant de payer pour les autres.
- Un corrigé n'est rédigé que lorsqu'un exercice le demande, pas d'avance.

## Fiabilité des corrigés
Aucun processus ne garantit 100 % de justesse. Le dispositif vise à s'en approcher et à rendre le risque visible :
1. Le corrigé officiel est toujours prioritaire.
2. Sinon : rédaction, puis un second agent résout l'exercice sans voir ce corrigé, et les deux sont comparés ; les calculs passent par SymPy ou une vérification numérique quand c'est possible.
3. Désaccord non résolu : l'exercice est signalé « à vérifier » et n'est jamais présenté comme sûr.
4. Chaque corrigé affiche son statut : `officiel`, `verifie` ou `absent`.
