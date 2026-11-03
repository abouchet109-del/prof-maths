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

## `matieres/<matiere>/notions.yaml`

Inventaire de ce qu'il faut savoir, relevé dans le cours.

```yaml
- id: topo-n-0012                  # <matiere courte>-n-<nnnn>, dans l'ordre du cours
  titre: 'Théorème de Bolzano-Weierstrass'
  type: theoreme                   # definition|theoreme|propriete|methode|demonstration|exemple
  chapitre: 'Chapitre 3 - Espace compact'
  sous_chapitre: '3.1 Définitions et propriétés'   # section telle que dans le poly
  enonce: 'Énoncé bref et fidèle, en LaTeX, 2 lignes au plus.'
  source: {etab: paris-cite, fichier: topologie/cours/chap3-espaces-compacts.pdf, page: 3}
  essentiel: true                  # false pour un point marginal
```

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
  notion: topo-n-0012              # null pour un prérequis
  titre: 'Théorème de Bolzano-Weierstrass'
  raison: 'absente du paquet'      # absente|partielle : préciser ce qui manque ; prérequis : pourquoi il manque
  programme_ecg: false             # true si c'est au programme d'ECG maths approfondies, donc supposé connu
  exercices: [topo-td4-ex02]       # exercices qui en ont besoin, annales prioritaires d'abord
  priorite: 1                      # 1 sert à une annale prioritaire ; 2 sert à un TD ; 3 le reste
  source: {fichier: topologie/cours/chap3-espaces-compacts.pdf, page: 3}   # null pour un prérequis sans source
  confiance: sure                  # sure|a_confirmer : à confirmer par mini-test ou par l'utilisateur
```

## Résultat d'un exercice (`state/resultats.yaml`, à venir)
`reussi` (seul), `aide` (réussi avec un indice), `presque` (pas loin avec l'aide), `non_fait` (pas réussi). Correspondance avec les tableurs : Réussi → `reussi`, Pas loin → `presque`, Loin et Non fait → `non_fait`.

## Corrigés
Un corrigé officiel peut contenir une erreur (constaté sur le corrigé de `mes-td1-ex05`, où lim sup et lim inf sont inversées) : en cas de désaccord au debrief, on vérifie plutôt que de trancher par autorité.

Priorité au corrigé officiel. Sans corrigé officiel, un corrigé n'est écrit qu'à la demande, puis vérifié (voir `docs/PLAN.md`, étape 8). Son statut reste visible.
