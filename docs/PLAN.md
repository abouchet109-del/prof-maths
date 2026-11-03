# Plan de construction : prof de maths L3

Dépôt indépendant de `archi-ml-ai-researcher`. On copie ce qui sert ; l'archi code n'est jamais modifiée.

## Cadre
- **Examens :** semaine du 11/01/2027 retenue, à confirmer (le 09/01/2027 est un samedi).
- **Budget :** chaque jour travaillé, 2 h d'exercices et d'annales, plus 30 min de cours. Du 03/11 au 10/01, hors week-ends sautés (07-08/11 et 21-22/11, communs avec le ML) : environ **158 h d'exercices et 32 h de cours**, en comptant 4 h d'exercices par jour dans les 2 semaines à 28 h (21/12 au 03/01).
- **Cartes Anki :** le système les crée toutes et les importe : cours de L3 et prérequis de L1-L2 manquants. L'utilisateur ne fait que les réviser, hors du temps planifié, et peut apprendre le cours directement par Anki : les cartes sont disponibles sans attendre qu'une séance soit faite.
- **Sessions de cours (30 min) :** approfondissement et compréhension, pas première lecture. Elles visent ce que les debriefs et les exercices ratés révèlent.
- **Harmonisation L1-L2 :** pour chaque exercice et annale, on repère les prérequis ; ceux qui ne sont ni au programme d'ECG, ni dans le paquet, ni dans le cours de L3 deviennent des notions à cartes. Source : documents envoyés par l'utilisateur, sinon un cours de référence vérifié, jamais de mémoire.
- **Matières :** topologie, mesure, modélisation, probabilités.
- **Principes repris :** le code calcule, Claude juge ; un niveau ne monte que sur preuve ; debrief après chaque session ; révisions Anki et debriefs hors du temps planifié.

## Règles décidées par l'utilisateur (03/11/2026)
- **Tous les exercices sont classés**, quelle que soit la source.
- **Les annales de Paris Cité passent avant tout** : l'objectif est de toutes les réussir.
- **Le planning réserve du temps pour toutes les annales de Paris Cité**, même si les autres exercices ne sont pas terminés. Si le temps manque, ce sont les autres exercices qui sont coupés.
- **Tableurs UVSQ :** les statuts et remarques sont ceux d'un ami, jamais une preuve de maîtrise de l'utilisateur. Ils servent seulement de modèle de présentation et d'indice de classement.

## Programme quotidien (`NOW.md`)
Chaque jour, sans que l'utilisateur ait à décider quoi que ce soit :
1. **Exercices et annales (2 h) :** liste précise, nouveaux exercices et exercices à revoir, avec le nombre attendu.
2. **Cours (30 min) :** ce qu'il faut approfondir, avec les pages du poly.
3. **Anki, à apprendre :** les nouvelles cartes du jour, par paquet et étiquette, avec leur nombre, en priorité celles des exercices à venir et les prérequis de L1-L2.
4. **Anki, à réviser :** toutes les cartes dues, plus les paquets anciens à reprendre parce qu'ils servent aux exercices du jour.
5. **Debrief** en fin de session, qui met à jour le profil et le plan du lendemain.

Limite : sans accès direct à Anki, le système ne voit pas les cartes dues ni les statistiques ; il indique quoi réviser et demande l'état au check-in. L'add-on AnkiConnect lèverait cette limite si l'utilisateur l'installe.

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
