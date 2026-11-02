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

`indice_tableur` vient du tableur d'un ami : `statut` et `remarque` ne décrivent jamais la maîtrise de l'utilisateur et n'alimentent pas son profil.

Règles d'extraction :
- Un exercice à sous-questions indépendantes peut être découpé (`q1`, `q2`) ; sinon il reste entier.
- Ne jamais compléter ni corriger un énoncé : si une formule est illisible dans le texte extrait, ouvrir la page du PDF. Si le doute reste : `qualite_extraction: a_verifier`.
- Ne jamais rédiger de corrigé pendant l'extraction.

## Résultat d'un exercice (`state/resultats.yaml`, à venir)
`reussi` (seul), `aide` (réussi avec un indice), `presque` (pas loin avec l'aide), `non_fait` (pas réussi). Correspondance avec les tableurs : Réussi → `reussi`, Pas loin → `presque`, Loin et Non fait → `non_fait`.

## Corrigés
Priorité au corrigé officiel. Sans corrigé officiel, un corrigé n'est écrit qu'à la demande, puis vérifié (voir `docs/PLAN.md`, étape 8). Son statut reste visible.
