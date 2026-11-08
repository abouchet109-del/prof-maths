# Formats de données

Contrat commun aux agents et aux scripts. Tout est en UTF-8. Les chaînes contenant un antislash (LaTeX) s'écrivent entre apostrophes simples ou dans un bloc `|`, jamais entre guillemets doubles. Un identifiant ne change jamais une fois créé.

## Matières
`topologie`, `mesure`, `modelisation`, `proba`. Les sources de Paris Cité font foi ; celles de l'UVSQ complètent. En cas de doute sur ce qui tombe, les annales de Paris Cité priment.

## `matieres/<matiere>/exercices.yaml`

```yaml
- id: topo-td1-ex03                # <matiere courte>-<source>-ex<nn>[q<m>] ; court : topo, mes, mod, pro
  titre: 'Boules et équivalence des normes'
  enonce: |
    Texte complet de l'énoncé, en LaTeX ($...$), fidèle à la source.
  sources:                         # le même exercice vu ailleurs = une entrée de plus, pas un nouvel exercice
    - {etab: paris-cite, fichier: topologie/td/td1.pdf, page: 1, numero: 'Ex 3'}
  annale_prioritaire: false        # true pour toute annale de Paris Cité : jamais coupée du planning
  type_source: td                  # td|annale|dm|cours|tp
  annale: null                     # ou {nature: exam|partiel, annee: '2023-24'}
  disponible: true                 # false si la notion n'a pas encore été vue en cours (Paris Cité)
  sous_chapitre: null              # rempli à l'étape de classement (taxonomie du paquet Anki)
  methodes: []                     # ids de methodes, remplis à l'étape de classement
  notions: []                      # ids de notions
  importance: null                 # vital|important|secondaire|exotique, rempli à l'étape de classement
  justification: null              # pourquoi cette importance (annales concernées)
  difficulte: null                 # 1..3
  temps_min: null                  # estimation en minutes
  indice_tableur:                  # repris tel quel du tableur UVSQ s'il existe, sinon null
    importance: Vital
    difficulte: '★★'
    statut: Loin
    remarque: null
  corrige:
    statut: absent                 # officiel|verifie|absent
    ref: null                      # {fichier: ..., page: ...} si officiel
  qualite_extraction: ok           # ok|a_verifier : formule illisible ou énoncé douteux
```

`indice_tableur` vient du tableur d'un ami. Il ne garde que l'importance et la difficulté : ses statuts et remarques ne décrivent pas l'utilisateur et sont retirés par `tools/post_exercices.py`. Ce script calcule aussi `annale_prioritaire` : ne pas le remplir à la main.

Compléments issus du pilote :
- `annale.nature` : un contrôle continu vaut `partiel`.
- `type_source` et `annale` décrivent la source la plus prioritaire : annale de Paris Cité d'abord.
- `corrige.ref.page` peut valoir null ; sinon, c'est la première page de la solution. Un corrigé succinct reste `officiel`, avec `succinct: true` dans `ref`.
- Sous-questions : `q1`, `q2a`… Les exercices de Paris Cité restent entiers sauf si leurs questions sont réellement indépendantes.
- Exercices voisins sans être identiques : pas de fusion, à signaler dans le compte rendu.
- Énoncé absent de la source et reconstitué depuis un corrigé : `qualite_extraction: a_verifier`, avec le mot « reconstitué » dans `titre`.
- `qualite_extraction: a_extraire` et `enonce: null` : entrée UVSQ créée depuis un tableur ; son énoncé sera lu seulement si elle est planifiée.

Règles d'extraction :
- Un exercice à sous-questions indépendantes peut être découpé (`q1`, `q2`) ; sinon il reste entier.
- Ne jamais compléter ni corriger un énoncé : si une formule est illisible dans le texte extrait, ouvrir la page du PDF. Si le doute reste : `qualite_extraction: a_verifier`.
- Ne jamais rédiger de corrigé pendant l'extraction.

## `matieres/<matiere>/methodes.yaml` et `classement.yaml`

`methodes.yaml` : les méthodes types de la matière.

```yaml
- id: topo-m-01
  titre: 'Montrer qu''une partie est fermée par la caractérisation séquentielle'
  notions: [topo-n-0021]
  annales: 6                       # nombre d'exercices d'annales de Paris Cité qui l'utilisent
```

`classement.yaml` : un dictionnaire indexé par l'id d'exercice, fusionné ensuite par `tools/classement.py fusionner`.

```yaml
topo-td1-ex03:
  sous_chapitre: 'Chapitre 1 - Espace métrique > 1.3 Normes'
  methodes: [topo-m-01]
  notions: [topo-n-0012]
  importance: vital                # vital|important|secondaire|exotique
  justification: 'méthode présente dans 4 annales de Paris Cité'
  difficulte: 2                    # 1..3
  temps_min: 25
  doublon_de: null                 # id d'un exercice identique déjà classé : il ne sera pas planifié deux fois
```

Définitions :
- **vital** : indispensable pour réussir au moins correctement l'examen final ; méthodes récurrentes des annales de Paris Cité.
- **important** : fréquent ou très utile, sans être le cœur des sujets.
- **secondaire** : utile pour consolider, rarement décisif.
- **exotique** : peu classique ou difficile, ne tombe jamais ou presque aux examens.
- Une annale prioritaire reçoit aussi une importance : elle reste planifiée quoi qu'il arrive, mais son importance dit ce que sa méthode vaut pour le reste du classement.

## `matieres/<matiere>/notions.yaml`

Inventaire de ce qu'il faut savoir, relevé dans le cours.

```yaml
- id: topo-n-0012                  # <matiere courte>-n-<nnnn>, dans l'ordre du cours
  titre: 'Théorème de Bolzano-Weierstrass'
  type: theoreme                   # definition|theoreme|propriete|methode|demonstration|exemple|prerequis (voir plus bas)
  chapitre: 'Chapitre 3 - Espace compact'
  sous_chapitre: '3.1 Définitions et propriétés'   # section telle que dans le poly
  enonce: 'Énoncé bref et fidèle, en LaTeX, 2 lignes au plus.'
  source: {etab: paris-cite, fichier: topologie/cours/chap3-espaces-compacts.pdf, page: 3}
  essentiel: true                  # false pour un point marginal
```

### Notions de prérequis L1-L2 (`type: prerequis`)

Un prérequis L1-L2 (ni au programme d'ECG, ni dans le paquet, ni dans le poly) est une **notion** de `notions.yaml`, placée au sous-chapitre du poly où elle sert la première fois. Il n'y a plus de carte sans notion (hors cartes d'erreurs).

```yaml
- id: topo-p-0001                  # <préfixe>-p-NNNN (topo, mesure, mod, proba), numéro libre suivant
  titre: 'Extraction diagonale (procédé diagonal de Cantor)'
  type: prerequis
  chapitre: 'Chapitre 3 - Espace compact'          # le même que le champ `chapitre` de ses cartes (contrôlé par check.py)
  sous_chapitre: '3.2 Suites dans un espace métrique compact'   # existe dans le poly ou chez un exercice
  enonce: 'Énoncé bref, en LaTeX.'
  source: {etab: l1-l2}
  essentiel: true
  requis_par: [topo-td4-ex08]      # obligatoire, non vide : exercices (ou notions) qui l'utilisent
```

Dans un sous-chapitre, `plan.py` sert les prérequis avant les notions du poly : cartes (`ordre_cartes`), cours du jour, anciennes notes. Une carte prérequis ne sort donc ni avant son sous-chapitre ni en tête de matière. Les exercices du jour qui figurent dans `requis_par` ajoutent la notion aux sujets du jour (cartes à revoir) ; une notion de `requis_par`, même d'une autre matière, rattache aussi le prérequis à son sous-chapitre (règle (d) de « Modèle de compréhension »). Un prérequis n'entre dans aucun calcul d'exercices, de marge ou de feuille de route. Pour ajouter un prérequis : l'entrée à la fin de `notions.yaml`, `notion: <id>` sur ses cartes (tag `prerequis-l1l2`), éventuellement `couverture.yaml` pour les anciennes notes qui le couvrent (`anki_connect.py fusionner` les range dans le paquet du chapitre, comme une notion du poly). Le référentiel de ce que l'utilisateur sait : ses paquets ECG `tg::Maths::1ere année` et `tg::Maths::Cours deuxième année`, jamais modifiés.

Règles : une entrée par résultat ou définition nommable. Pas de texte recopié au-delà du nécessaire. Démonstration : une entrée seulement si le cours la présente comme importante ou si la technique est réutilisable. Une page incertaine vaut `page: null`.

## `matieres/<matiere>/couverture.yaml`

Une entrée par notion : ce que le paquet Anki couvre déjà.

```yaml
topo-n-0012: {statut: couverte, notes: [1786484126572]}   # couverte|partielle|absente ; ids de notes Anki
```

Le jugement porte sur le recto (les réponses sont souvent en image) : un recto qui nomme précisément la notion vaut `couverte`. Un score élevé ne suffit pas, un titre voisin ne suffit pas.

## `matieres/<matiere>/cartes_a_creer.yaml`

```yaml
- id: topo-a-001
  origine: cours_l3                # cours_l3|prerequis_l1l2
  notion: topo-n-0012              # historique : les prérequis y gardent null, leur notion est `<préfixe>-p-NNNN` (voir « Notions de prérequis »)
  titre: 'Théorème de Bolzano-Weierstrass'
  raison: 'absente du paquet'      # absente|partielle : préciser ce qui manque ; prérequis : pourquoi il manque
  programme_ecg: false             # true si c'est au programme d'ECG maths approfondies, donc supposé connu
  exercices: [topo-td4-ex02]       # exercices qui en ont besoin, annales prioritaires d'abord
  priorite: 1                      # 1 sert à une annale prioritaire ; 2 sert à un TD ; 3 le reste
  source: {fichier: topologie/cours/chap3-espaces-compacts.pdf, page: 3}   # null pour un prérequis sans source
  confiance: sure                  # sure|a_confirmer : à confirmer par mini-test ou par l'utilisateur
```

## `matieres/<matiere>/cartes.yaml`

Cartes rédigées par le système, exportées vers Anki par paquets ne contenant que les nouvelles cartes.

```yaml
- id: topo-a-012-1                 # <id de cartes_a_creer>-<k> : une notion peut donner plusieurs cartes
  notion: topo-n-0070
  recto: 'Thm 2.12 : théorème de Baire'
  verso: 'Soit \((X,d)\) un espace métrique complet. Toute intersection dénombrable d''ouverts denses de \(X\) est dense dans \(X\).'
  source: 'Poly de topologie Paris Cité, ch. 2, p. 7'
  chapitre: 'Chapitre 2 - Espace complet'   # sert au nom du sous-paquet
  priorite: 1                      # reprise de cartes_a_creer
  tags: [definition]               # type de la notion ; matière et priorité ajoutées à l'export
```

Règles de rédaction (format demandé par l'utilisateur le 07/11/2026, celui de ses propres cartes) :
- **cartes de cours :**
  - recto = type et nom de l'énoncé : `Déf : <nom>`, `Prop. <n°> : <nom>`, `Thm <n°> : <nom>`, `Lemme`, `Cor.`, `Exemple : <nom>` ou `Preuve : <nom>`, avec le numéro et le nom du poly quand il y en a ;
  - verso = l'énoncé du poly recopié fidèlement, avec son cadre et toutes ses hypothèses ;
  - si l'énoncé a plusieurs points, une carte par point, chacune recopiée fidèlement avec son cadre ;
  - une carte `Preuve :` donne l'idée de la preuve du poly en 2 à 5 lignes ;
- **cartes d'erreurs** (`*-eNNN`, tag `erreur`) et **prérequis** (tag `prerequis-l1l2`) : une question précise au recto, un verso court. Depuis le 08/11/2026, le debrief ne crée plus de carte d'erreur : une confusion va dans `state/comprehension.yaml` et les cartes existantes de la notion repassent ; les cartes d'erreurs déjà créées restent ;
- maths en MathJax : `\( ... \)` en ligne, `\[ ... \]` en bloc ; pas de liste à apprendre en bloc, la découper ;
- un théorème : hypothèses complètes et conclusion ; une carte à part pour un contre-exemple ou un piège utile ;
- rédigée en lisant la source réelle à la page indiquée, jamais de mémoire ; `source` non vide sur chaque carte ;
- une notion `partielle` : seulement ce qui manque au paquet (indiqué dans `raison`).

Paquet Anki : `tg::Maths::L3 Paris Cité::<Matière>::<chapitre>`, étiquette `prof-maths` sur chaque carte.

### Cartes d'exercices (`tags: [exercice]`)

Une carte par exercice qui n'a pas été réussi seul, créée au debrief. Le recto est l'énoncé, le verso la correction complète : le lendemain, on retrouve par où attaquer. Elle ne remplace pas la reprise sur papier.

```yaml
- id: ex-topo-td1-ex06             # `ex-` + id de l'exercice ; ne change jamais
  exercice: topo-td1-ex06          # obligatoire, un seul exemplaire par exercice (contrôlé par check.py)
  notion: topo-n-0018              # notion principale de l'exercice (lue par plan.py)
  recto: |-
    <b>Exo topo-td1-ex06 : <titre></b><br> énoncé condensé, avec toutes les hypothèses et tous les symboles<br>
    <b>Méthode ? Étape clé ?</b>
  verso: |-
    <b>Idée clé :</b> une ligne<br> <b>Correction :</b> toutes les étapes rédigées<br> <b>Piège :</b> l'erreur faite en séance
  source: 'Énoncé : fichier p.N (Ex k). Corrigé officiel : fichier p.N.'   # ou « Pas de corrigé officiel : vérifiée par Claude, à confirmer »
  chapitre: 'Chapitre 1 - Espace métrique'     # exactement le chapitre des cartes de cours ; l'export ajoute `::Exercices`
  priorite: 1
  tags: [exercice]                 # tag et champ `exercice` vont ensemble
```

Règles :
- **Quand :** résultat du jour `aide` ou `presque` ; `non_fait` seulement si l'exercice a été travaillé et le corrigé vu pendant la séance. Rien pour `reussi`, ni pour un `non_fait` jamais ouvert.
- **Verso :** l'idée clé en une ligne, puis la correction complète (toutes les étapes rédigées, fidèle au corrigé officiel), puis le piège éventuel. La référence du corrigé (fichier, page) est dans `source`.
- **Justesse à 100 % :** le verso vient du corrigé officiel (page du PDF ouverte), sinon d'une solution résolue et vérifiée étape par étape, avec la mention « vérifiée par Claude, à confirmer ».
- **Rangement :** sous-paquet `tg::Maths::L3 Paris Cité::<matière>::<chapitre>::Exercices` (le nom du chapitre est celui des cartes de cours). Le tag `exercice` reste sur la carte. `check.py` refuse un chapitre que les cartes de cours n'utilisent pas.
- **Déjà une carte ?** Ne pas en créer une seconde. Si l'erreur du jour est nouvelle, compléter le verso, puis `python -I tools/anki.py --reexporter <id>`. Dans tous les cas, ajouter `{pour: <lendemain>, id: <id>, raison: ...}` à `state/a_revoir.yaml`.
- **Plan :** `tools/plan.py` donne ces cartes en tête des « à apprendre », avec les cartes d'erreurs (tags `erreur` et `exercice`), avant celles du sous-chapitre du bloc.

## Modèle de compréhension (`state/comprehension.yaml`)

Ce que le système pense que l'utilisateur comprend, notion par notion, d'après ce qu'il **dit** (explications à voix haute, questions, raisonnements en exercice) : c'est la donnée principale, la réponse seule n'en est qu'une partie. Écrit au debrief seulement (jamais pendant la séance), lu par la séance et par `plan.py`. Une entrée n'existe que pour une notion travaillée.

```yaml
notions:
  topo-n-0012:                     # id de notions.yaml (notion du poly ou prérequis `-p-`)
    niveau: fragile                # inconnue|recitee|fragile|tenue|reliee (table ci-dessous)
    vision: 'Ses mots : « compact = on peut toujours extraire une sous-suite qui converge »'   # 1-2 lignes
    liens:                         # liens qu'il fait correctement
      - {vers: topo-n-0010, texte: 'compact ⇒ fermé borné, et il sait pourquoi'}
    liens_manquants:               # liens utiles qu'il ne fait pas
      - {vers: topo-n-0015, texte: 'ne voit pas que la réciproque exige la dimension finie'}
    confusions:
      - {date: 2026-11-08, texte: 'croit fermé borné ⇒ compact dans tout espace métrique', statut: ouverte}   # ouverte|reparee
    preuves:                       # 6 au plus, les plus récentes
      - {date: 2026-11-08, source: cours, extrait: 'a expliqué B-W sans les hypothèses', verdict: partiel}
      # source : cours|exercice|question (question du debrief) ; verdict : juste|partiel|faux
      # source exercice : ajouter `exercice: <id>`
    maj: 2026-11-08
style:                             # sa façon de raisonner, ce qui marche pour lui : 6 lignes au plus
  - 'comprend mieux par un contre-exemple que par la preuve'
```

| Niveau | Preuve qu'il faut (ce qu'il a dit ou fait) |
|---|---|
| `inconnue` | il ne sait pas dire ce que c'est ni à quoi ça sert, ou ce qu'il en dit est faux sur le fond |
| `recitee` | il l'énonce juste (hypothèses comprises), mais ne sait pas dire d'où elle vient ni l'utiliser seul sur un cas nouveau |
| `fragile` | il l'explique avec ses mots et s'en sert, mais hésite, oublie une hypothèse, a besoin d'une relance, ou une confusion ouverte la touche ; une bonne réponse sur un raisonnement confus est classée ici |
| `tenue` | « évident, et je sais pourquoi » : il l'explique sans aide, dit d'où elle vient (idée de preuve ou problème qu'elle résout), sait ce qui casse si on retire une hypothèse, et l'applique seul à un cas nouveau ; aucune confusion ouverte |
| `reliee` | `tenue`, et il la relie correctement à au moins une autre notion (en quoi l'une sert ou entraîne l'autre) ; au moins une entrée dans `liens` |

Règles :
- **Un niveau ne monte que sur preuve**, comme un exercice. Une explication juste donnée juste après qu'on la lui a enseignée prouve au plus `fragile` : `tenue` exige une preuve **à froid** (explication donnée avant l'enseignement, exercice `reussi` où il l'a mobilisée seul, question du debrief, séance ultérieure).
- **Un niveau descend dès qu'une preuve le contredit** : une confusion révélée met la notion au plus à `fragile`.
- Confusion `reparee` seulement sur preuve à froid qu'il raisonne juste sur ce point ; on la garde (historique), 8 confusions au plus par notion (supprimer d'abord les plus anciennes réparées).
- `vision` : ses mots, pas ceux du poly. `extrait` : une ligne, 160 caractères au plus.
- Les ids de `liens` et `liens_manquants` (`vers`) sont des notions connues, autres que la notion elle-même.

### Règles pour `plan.py` et `check.py`

Ensembles : **à consolider** = niveau `inconnue`, `recitee` ou `fragile`, ou au moins une confusion `ouverte` ; **faible** = niveau `recitee` ou `fragile`, ou une confusion `ouverte`. Une notion absente de `comprehension.yaml` n'est ni l'un ni l'autre. Sous-chapitre d'une notion : `f"{chapitre} > {sous_chapitre}"` ; d'un exercice : son `sous_chapitre` ; comparaison par `etat.cle_sc`.

**(a) NOW.md, section « À consolider »** (juste avant « Cours », comptée dans les 60 lignes ; omise si vide ou sans matière du bloc). Notions *à consolider* de la matière du bloc dont le sous-chapitre est dans `sc_precedents(ctx, plan) + [plan["sous_chapitre"]]`, plus les prérequis `inconnue` rattachés (règle d) à ces sous-chapitres, quelle que soit leur matière. Ordre : confusion ouverte d'abord, puis niveau (`inconnue`, `recitee`, `fragile`), puis sous-chapitre, puis id. Au plus **5** lignes ; au-delà, une ligne « + k autres ». Une ligne : `` - `<id>` <titre court> · <niveau> · <vision, sinon dernière confusion ouverte> · <fichier> p.<page> ``, ramenée à 160 caractères (`_court`). Pour la séance, la confusion ouverte la plus récente prime sur la vision.

**(b) Cartes.** 1) Les cartes déjà apprises des notions *faibles* reviennent dans « à réviser », comme `a_revoir` (recherche Anki : `"Id:<id>"` des cartes de `cartes.yaml` de `notion:` = la notion, et `nid:` de ses notes dans `couverture.yaml`), **à la première séance après `maj`** : séance du jour `d` telle que `maj < d` et aucun jour travaillé `f` avec `maj < f < d` (même consommation que `a_revoir_dus`, avec `pour` = lendemain de `maj`). Une seule recherche, fusionnée avec celle de `a_revoir`, sans doublon. 2) Dans `ordre_cartes`, les cartes nouvelles (`libres`) d'un prérequis `inconnue` passent juste après les cartes à tags prioritaires (`erreur`, `exercice`), avant les `a_revoir` dues, quelle que soit la matière du bloc ; le plafond `cartes_par_jour` est inchangé.

**(c) Exercices.** Un exercice est *prioritaire* si l'une de ses `notions` est *faible*. Reprises : clé de tri `(etat != "a_revoir", non prioritaire, du, ordre)`, plafond `minutes_reprises_max` inchangé. Bloc (`candidats_bloc`) : à l'intérieur de chaque sous-chapitre seulement, clé `(non prioritaire, catégorie, ordre)` ; l'ordre des sous-chapitres et la butée de `plan_jour` ne changent pas. L'étape annale (b) de `plan_jour` est inchangée : une annale n'est jamais retirée ni déplacée par cette règle.

**(d) Prérequis multi-matières.** `requis_par` contient des ids d'exercices ou de notions, de n'importe quelle matière. Rattachements d'un prérequis P : son propre sous-chapitre, et, pour chaque matière où figure un élément de `requis_par`, le **premier** sous-chapitre (min `cle_sc`) qui contient l'un de ces éléments. Partout où le code sert les prérequis d'un sous-chapitre (`notions_sc`, `ordre_cartes`, `anciennes_notes`), il sert P à chacun de ses rattachements, avant les notions du poly ; les doublons de cartes restent éliminés. `notions_des_exercices` ajoute aussi P quand une notion de son `requis_par` figure au cours du jour ou parmi les notions des exercices du jour.

**(e) `check.py`** refuse : un fichier dont la racine n'a pas exactement `notions` (dict) et `style` (liste de 6 chaînes au plus) ; un id de notion inconnu (clé ou `vers`), ou `vers` égal à la clé ; un `niveau` hors des cinq ; un `statut` hors `ouverte|reparee` ; une `source` hors `cours|exercice|question`, un `verdict` hors `juste|partiel|faux` ; un `exercice` inconnu ; une date (`maj`, confusions, preuves) qui n'est pas AAAA-MM-JJ valide ou qui est postérieure à aujourd'hui ; plus de 6 preuves ou 8 confusions ; un `extrait` de plus de 160 caractères ; `tenue` ou `reliee` avec une confusion ouverte ; `reliee` sans `liens`. Le fichier absent ou `notions: {}` est valide.

## Résultat d'un exercice (`state/resultats.yaml`, à venir)
`reussi` (seul), `aide` (réussi avec un indice), `presque` (pas loin avec l'aide), `non_fait` (pas réussi). Correspondance avec les tableurs : Réussi → `reussi`, Pas loin → `presque`, Loin et Non fait → `non_fait`.

## Corrigés
Un corrigé officiel peut contenir une erreur (constaté sur le corrigé de `mes-td1-ex05`, où lim sup et lim inf sont inversées) : en cas de désaccord au debrief, on vérifie plutôt que de trancher par autorité.

Priorité au corrigé officiel. Sans corrigé officiel, un corrigé n'est écrit qu'à la demande, puis vérifié (voir `docs/PLAN.md`, étape 8). Son statut reste visible.
