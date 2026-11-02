# Plan de construction : prof de maths L3

Dépôt indépendant de `archi-ml-ai-researcher`. On copie ce qui sert ; l'archi code n'est jamais modifiée.

## Cadre
- **Examens :** semaine du 11/01/2027 retenue, à confirmer (le 09/01/2027 est un samedi).
- **Budget :** chaque jour travaillé, 2 h d'exercices et d'annales, plus 30 min de cours. Du 03/11 au 10/01, hors week-ends sautés (07-08/11 et 21-22/11, communs avec le ML) : environ **158 h d'exercices et 32 h de cours**, en comptant 4 h d'exercices par jour dans les 2 semaines à 28 h (21/12 au 03/01).
- **Cartes Anki :** l'utilisateur les rédige lui-même, hors de ce temps ; le système lui donne la liste des notions manquantes.
- **Matières :** topologie, mesure, modélisation, probabilités.
- **Principes repris :** le code calcule, Claude juge ; un niveau ne monte que sur preuve ; debrief après chaque session ; révisions Anki et debriefs hors du temps planifié.

## Règles décidées par l'utilisateur (03/11/2026)
- **Tous les exercices sont classés**, quelle que soit la source.
- **Les annales de Paris Cité passent avant tout** : l'objectif est de toutes les réussir.
- **Le planning réserve du temps pour toutes les annales de Paris Cité**, même si les autres exercices ne sont pas terminés. Si le temps manque, ce sont les autres exercices qui sont coupés.
- **Tableurs UVSQ :** les statuts et remarques sont ceux d'un ami, jamais une preuve de maîtrise de l'utilisateur. Ils servent seulement de modèle de présentation et d'indice de classement.

## Annales de Paris Cité dans le planning
- **Volume :** 16 annales (topologie 8, modélisation 4, probabilités 4), soit 24 h de composition à 1 h 30 chacune. Aucune en mesure : on s'appuie sur celles de l'UVSQ.
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

## Étapes

| # | Étape | Exécutant | Modèle, effort | Entrée | Sortie |
|---|---|---|---|---|---|
| 0 | Tri et inventaire | session principale | fait | Téléchargements, zips | `bibliotheque/`, `inventaire/` |
| 1 | Contrat de formats | session principale | Opus, high | ce plan | `docs/FORMATS.md` |
| 2 | Pilote d'extraction : topologie | 1 agent | Sonnet, medium | TD, annales, DM, tableur | `matieres/topologie/exercices.yaml` |
| 3 | Extraction des 3 autres matières | 1 agent par matière | Sonnet, medium | idem, format corrigé après le pilote | `matieres/*/exercices.yaml` |
| 4 | Lecture d'Anki | utilisateur (export), puis 1 agent | Sonnet, medium | export `.colpkg` | taxonomie et liste des cartes |
| 5 | Inventaire des notions et méthodes | 1 agent par matière | Sonnet, medium | polys de Paris Cité seuls | `matieres/*/notions.yaml` |
| 6 | Classement vital à exotique | 1 agent par matière | Opus, high | fichiers des étapes 3 à 5, pas les PDF | exercices classés et justifiés |
| 7 | Notions sans carte et trous de L1-L2 | 1 agent par matière | Sonnet, high | notions + rectos des cartes + prérequis envoyés | liste classée pour l'utilisateur, qui rédige les cartes |
| 8 | Corrigés sans source officielle | à la demande, exercice par exercice | rédaction Sonnet, high ; vérification à l'aveugle Opus, high | énoncé seul pour le vérificateur | corrigé avec statut |
| 9 | Socle : calendrier, validation, `NOW.md`, Anki | 1 agent | Sonnet, high | copie de `tools/` | `tools/`, tests |
| 10 | Planificateur par exercices et passage de catégorie | 1 agent | Sonnet, high ; Opus si deux échecs | étapes 6 et 9 | plan de chaque session |
| 11 | Règles de session et skills de tutorat | session dédiée | Opus, high | copie des skills | `CLAUDE.md`, `.claude/skills/` |
| 12 | Contrôle de cohérence et tests | 1 agent | Haiku, low | tout | rapport |

**Fonctionnement courant ensuite :** plan du jour et imprévu en Sonnet low à medium ; debrief et check-in en Sonnet high ; correction d'examen blanc en Opus high.

**Ordre :** 2, puis 3. Les étapes 4, 5 et 9 peuvent tourner en parallèle, puis 6, 7, 10, 11 et 12. L'étape 8 ne se déclenche qu'au besoin.

## Économies de tokens
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
