# Formats de fichiers et contrats des scripts

Ce document est le **contrat** commun aux skills, aux scripts et au contenu. Toute évolution de format se fait d'abord ici, puis dans `check.py`.

## Conventions générales

- **Encodage** : UTF-8 partout, à lire et écrire explicitement en UTF-8 (le PC est sous Windows).
- **YAML et antislashs** : une chaîne qui contient un antislash (MathJax `\(`, `\frac`…) s'écrit entre apostrophes simples ou dans un bloc `|`, **jamais entre guillemets doubles**. Sinon `\(` devient un échappement invalide et le fichier ne s'analyse plus.
- **Dates** : ISO `AAAA-MM-JJ`, fuseau `Europe/Paris`. **Créneaux** : `"HH:MM-HH:MM"` (`24:00` est autorisé comme fin).
- **Jours** : `lun mar mer jeu ven sam dim`. **Semaines** : ISO, notées `AAAA-Www` (ex. `2026-W45`).
- **Identifiants** : ASCII, minuscules, `-` et `.` autorisés, sans espaces. **Un identifiant ne change jamais** une fois créé.
- **Modules** : `<domaine>-<slug>`, par exemple `diag-depart`, `outils-installation`, `py-numpy`, `py-pandas`, `math-optim`, `ml-regression`.
- **Compétences** : `<domaine>.<sujet>[.<sous-sujet>]`, par exemple `py.numpy.broadcasting`, `math.optim.gradient`.
- **Domaines** :

  | Domaine | Contenu |
  |---|---|
  | `outils` | environnement, git, terminal, tests |
  | `py` | Python scientifique |
  | `math` | maths du ML hors L3 |
  | `ml` | ML classique |
  | `dl` | deep learning |
  | `spe` | spécialisation |
  | `ing` | ingénierie ML |
  | `rech` | recherche |
  | `carriere` | candidatures, CV, entretiens. Ce domaine a des tâches, pas de compétences |

## `state/dispo.yaml`

```yaml
version: 1
fuseau: Europe/Paris
debut: 2026-11-02
heures_ml_semaine: 14
creneaux_ml:               # créneaux ML fixes (2 h chacun)
  lun: ["14:00-16:00"]
  mar: ["19:30-21:30"]
  mer: ["16:30-18:30"]
  jeu: ["16:30-18:30"]
  ven: ["17:30-19:30"]
  sam: ["14:30-16:30"]
  dim: ["09:00-11:00"]
libres:                    # créneaux libres déclarés (où placer un rattrapage)
  lun: ["12:30-18:00", "22:30-24:00"]
  mar: ["19:30-24:00"]
  mer: ["16:30-18:30", "22:00-24:00"]
  jeu: ["09:00-12:00", "16:30-19:30", "21:00-24:00"]
  ven: ["11:00-12:00", "17:30-19:30", "21:00-24:00"]
  sam: ["11:00-13:00", "14:30-17:30", "18:30-20:30", "22:00-24:00"]
  dim: ["09:00-12:00", "14:00-17:00", "18:00-21:00"]
tampon:
  heures_semaine: 6
  horaire: libre           # pas d'horaire fixe ; rattrapage confirmé avec l'utilisateur
exceptions:                # du/au inclus
  - {du: 2026-11-07, au: 2026-11-08, type: off, note: "week-end sauté", statut: confirme}
  - {du: 2026-12-07, au: 2026-12-13, type: quota, heures: 7, note: "partiels", statut: confirme}
imprevus:                  # créneaux ML perdus ponctuellement
  - {date: 2026-11-05, creneau: "16:30-18:30", note: "réunion ESSEC"}
```

- **Types d'exception :**
  - `off` : aucune heure ML sur la période ;
  - `quota` : `heures` imposées sur la période (semaine de 7 h, semaine de 28 h…), placées à la main par Claude.
- **`statut`** : `confirme` ou `provisoire`.

## `state/semaine.yaml`

Le plan de la semaine en cours, **placé par Claude** et vérifié par `check.py`.

```yaml
semaine: 2026-W45
du: 2026-11-02
au: 2026-11-08
seances:
  - id: 2026-11-02-a              # <date>-<lettre>
    date: 2026-11-02
    creneau: "14:00-16:00"
    type: diagnostic              # cours|exercices|projet|article|consolidation|examen|diagnostic|installation|rattrapage
    module: diag-depart           # dossier modules/<module>/ existant (null autorisé)
    tache: "Diagnostic de départ (1 h), puis début de l'installation"
    ressources: ["modules/diag-depart/fiche.md#seance-1"]
    livrable: "Réponses du diagnostic + environnement Python opérationnel"
    statut: prevue                # prevue|faite|partielle|sautee|deplacee
    heures_reelles: null          # nombre (ex. 2.0), rempli au debrief
    hors_creneau: false           # true = horaire spécial confirmé par l'utilisateur
    remplace: null                # pour un rattrapage : id de la séance remplacée
```

- **Créneaux autorisés** : une séance qui n'est ni `rattrapage` ni `hors_creneau: true` doit tomber exactement sur un créneau ML du jour. Pendant une exception `quota`, elle peut aussi tomber dans un créneau libre.
- **Rattrapage** : il doit tomber dans un créneau libre déclaré, ou bien porter `hors_creneau: true`.

## `state/competences.yaml`

```yaml
competences:
  - id: py.numpy.broadcasting
    nom: "NumPy : broadcasting et vectorisation"
    domaine: py
    niveau: null           # null = pas encore évalué ; sinon 0..4
    cible: 3               # niveau visé à la fin du module
    modules: [py-numpy]
    preuves:               # la plus récente en dernier
      - {date: 2026-11-04, type: debrief, ref: "journal/2026-11-04.md#q3", note: 2, aide: 0}
      # note et aide peuvent valoir null (ex. preuve de niveau 1 « séance de cours faite »)
    prochaine_verif: 2026-11-11   # null si niveau < 2
    intervalle_sem: 1             # 1, 3, 8, 16
    echecs_consecutifs: 0
```

**Types de preuve** : `diagnostic`, `debrief`, `exercice`, `retest`, `examen`, `projet`.

## `state/jalons.yaml`

```yaml
jalons:
  - id: j01-python-operationnel
    nom: "Python scientifique opérationnel (NumPy, pandas)"
    date: 2026-11-29
    type: souple                  # dur (échéance externe) | souple
    critere: "py.numpy.* et py.pandas.* au niveau 3"
    heures_restantes_estimees: 20 # mis à jour par Claude au check-in
    statut: a_venir               # a_venir|a_risque|atteint|rate|abandonne
    source: null                  # lien si échéance externe
```

## `modules/<id>/`

- **`fiche.md`**, avec les sections suivantes :
  - `## Objectifs` ;
  - `## Compétences visées` (identifiants et niveau cible) ;
  - `## Prérequis` ;
  - `## Séances` : une sous-section `### Séance n` par séance de 2 h. Chacune donne le type, les lectures exactes (ressource du catalogue, section, pages ou URL) et les exercices. La référence `fiche.md#seance-n` désigne cette sous-section : c'est une référence logique pour Claude, et sur GitHub l'ancre réelle porte l'accent (`#séance-n`) ;
  - `## Livrable` ;
  - `## Points clés` (pour le debrief) ;
  - `## Sources` : liens, avec la date de vérification.
- **`questions.yaml`** :

```yaml
- id: py-numpy-q001              # <module>-q<nnn>
  competence: py.numpy.broadcasting
  seance: 2                      # séance de la fiche où la notion est étudiée (optionnel)
  type: cours                    # cours|pourquoi|transfert|code|calcul
  difficulte: 1                  # 1..3
  question: "Quelles règles NumPy applique-t-il pour combiner deux tableaux de formes différentes ?"
  points_attendus:
    - "comparaison des dimensions en partant de la fin"
    - "compatibles si égales ou si l'une vaut 1"
    - "la dimension de taille 1 est étirée sans copie"
  source: {ressource: pdsh, ref: "ch. 2, Computation on Arrays: Broadcasting", url: "https://..."}
```

- **`cartes.yaml`** :

```yaml
- id: py-numpy-c001              # <module>-c<nnn> ; erreurs : <module>-e<nnn>
  recto: "Forme du résultat de <code>np.ones((3,1)) + np.arange(4)</code> ?"
  verso: "<code>(3, 4)</code> : (3,1) et (4,) → (1,4), puis étirement des dimensions de taille 1."
  source: "VanderPlas, Python Data Science Handbook, ch. 2 « Broadcasting » — https://..."
  tags: [essentiel]              # essentiel|complement|erreur ; module et compétence ajoutés par anki.py
  competence: py.numpy.broadcasting
  seance: 2                      # séance où le contenu est étudié ; absent ou null pour les cartes d'erreur
```

Une carte n'est exportée vers Anki **qu'une fois sa séance faite** (voir `anki/progression.yaml`). Les cartes sans `seance` (erreurs) sont exportées dès leur création.

- **`exercices/`** :
  - `exNN-<slug>.md` : énoncé, source, compétence ;
  - `tests/test_<module_avec_underscores>_exNN.py` : tests pytest écrits **avant**. Le nom doit être unique dans tout le repo (par exemple `test_py_numpy_ex01.py`).
    - Ils importent la solution de l'utilisateur avec `importlib`, depuis `labs/<module>/exNN.py`.
    - Ils passent en `pytest.skip` si ce fichier n'existe pas.
    - La variable d'environnement `ML_ARCHI_LABS`, si elle est définie, remplace la racine `labs/`. Elle sert à valider les tests contre une solution de référence hors du repo.
    - Le modèle exact est dans `.claude/skills/preparation/SKILL.md`.
  - **Aucune solution de référence dans le repo.**

## `ressources/catalogue.yaml`

```yaml
- id: pdsh
  titre: "Python Data Science Handbook (2e éd.)"
  auteurs: ["Jake VanderPlas"]
  annee: 2023
  url: "https://jakevdp.github.io/PythonDataScienceHandbook/"
  acces: gratuit                 # gratuit|payant|mixte
  licence: "texte CC BY-NC-ND 3.0, code MIT"
  langue: en                     # en|fr
  format: html                   # html|pdf|video|cours|exercices|livre
  domaines: [py]
  niveau: debutant               # debutant|intermediaire|avance
  role: principale               # principale|secours|complement
  verifie_le: 2026-10-31
  pourquoi: "Référence claire, gratuite, axée pratique"
  plan:                          # sections utiles, avec URL et/ou pages (jamais inventées)
    - {ref: "ch. 2", titre: "Introduction to NumPy", url: "https://...", pages: null}
  fichier_local: null            # chemin sous bibliotheque/ (PC, non versionné)
```

## `journal/`

### `journal/AAAA-MM-JJ.md` (un par jour travaillé)

```markdown
# 2026-11-02 (lundi)
## Séance
- prévue : 14:00-16:00 · diag-depart · diagnostic
- réalisée : 14:00-16:05 (2,1 h) · statut : faite
- aide reçue : max 1 (indice sur le broadcasting)
- notes de l'utilisateur : compris … / pas compris … / question …
## Debrief
### Points attendus (écrits avant les questions)
- Q1 [py-numpy-q003] … → a ; b ; c
### Réponses et notes
- Q1 : 2/2 — correction : …
## Mises à jour
- compétences : py.numpy.broadcasting null → 2 (preuves : Q1, Q2)
- cartes : py-numpy-c001…c012 ; erreurs : py-numpy-e001
- planning : …
```

### Autres fichiers du journal

| Fichier | Contenu |
|---|---|
| `journal/bilan-AAAA-Www.md` | bilan hebdomadaire du check-in |
| `journal/resume-AAAA-MM.md` | résumé mensuel. Les sessions lisent ces résumés plutôt que les journaux anciens |

## `NOW.md` (généré par `now.py`, ne pas éditer)

60 lignes au plus, avec les sections suivantes, dans l'ordre :
1. `# Aujourd'hui — <date>` : séance(s) du jour (créneau, type, tâche, ressources, livrable), ou « pas de séance ».
2. `## Cette semaine` : les séances restantes, avec leur statut.
3. `## À rattraper` : séances sautées ou déplacées sans rattrapage placé.
4. `## Vérifications de maintien dues` (7 prochains jours).
5. `## Jalons` : prochains jalons, avec la marge en heures et le statut.
6. `## Anki` : nombre de cartes **exportables** en attente, et date du dernier paquet.
7. Pied de page : « généré le … par tools/now.py ».

## `anki/`

- **`anki/registre.csv`** (versionné). En-tête `id;date;paquet`. Une ligne par carte exportée.
- **`anki/progression.yaml`** (versionné). Mapping `<module>: <dernière séance faite>`, en entiers ≥ 0, par exemple `py-numpy: 2`. Un fichier absent vaut un mapping vide.
  - Il est mis à jour au debrief, par `anki.py --avancer`.
  - Une carte est **exportable** si elle est absente du registre **et** que, soit elle n'a pas de `seance`, soit son module figure dans la progression avec `seance ≤ progression[module]`.
- **`anki/paquets/nouvelles-AAAA-MM-JJ.apkg`** : non versionné (`.gitignore`). Construit sur le PC.
- **Type de note figé** (à ne jamais modifier) :

  | Élément | Valeur |
  |---|---|
  | `model_id` | `1730000001` |
  | Nom | `ML-Archi (v1)` |
  | Champs | `Id`, `Recto`, `Verso`, `Source` (champ de tri : `Recto`, index 1) |
  | Recto de la carte | `{{Recto}}` |
  | Verso de la carte | `{{FrontSide}}<hr id=answer>{{Verso}}<div class=source>{{Source}}</div>` |
  | CSS | lisible, `pre`/`code` en monospace, `.source` en petit et gris |

- **Paquet** : rangé par matière puis par chapitre, `ML-Archi::<n matière>::<chapitre>` (exemple : `ML-Archi::2 Python scientifique::numpy`). La matière vient du préfixe du module (`MATIERES` dans `anki.py`) et le chapitre du reste de son id. Le `deck_id` est stable, dérivé du nom (hash).
- **Étiquette de séance** : `seance-<n>` est ajoutée automatiquement, pour filtrer une séance dans Anki.
- **GUID** : `genanki.guid_for("ml-archi", <id carte>)`.
- **Étiquettes Anki** : les `tags` de la carte, plus `<module>` et `<competence>` (espaces et caractères interdits remplacés par `_`).

## Contrats des scripts (`tools/`)

Conditions communes :
- Python 3.10 ou plus récent.
- Dépendances : `pyyaml`, `genanki`, `pytest` (`requirements.txt`).
- Doit tourner **sous Windows et Linux** : `pathlib`, UTF-8 explicite, pas de commandes shell.
- Les scripts se lancent depuis la racine du repo. Option `--racine` pour les tests.
- Sorties déterministes. `--date AAAA-MM-JJ` remplace « aujourd'hui » (pour les tests).

| Commande | Effet | Code de sortie |
|---|---|---|
| `python tools/cal.py creneaux --du D --au D` | Liste les créneaux ML datés (date, jour, créneau, heures), avec les exceptions `off` et les `imprevus` appliqués. Les périodes `quota` sont signalées avec leur nombre d'heures | 0 |
| `python tools/cal.py capacite --du D --au D` | Heures ML disponibles sur la période. Une semaine `quota` partielle est comptée au prorata des jours | 0 |
| `python tools/cal.py semaine D` | Squelette de la semaine ISO qui contient `D` : créneaux datés et capacité | 0 |
| `python tools/cal.py jalons [--date D]` | Pour chaque jalon `a_venir` ou `a_risque` : capacité d'ici sa date, `heures_restantes_estimees`, marge, statut suggéré (`a_risque` si marge < 10 % de la capacité ou négative) | 0 |
| `python tools/check.py` | Valide tous les fichiers (voir la liste ci-dessous). Affiche les erreurs et les avertissements | 1 s'il y a des erreurs |
| `python tools/now.py [--date D]` | Écrit `NOW.md` | 0 |
| `python tools/anki.py [--avancer MODULE:N[,MODULE:N]] [--sans-paquet] [--dry-run] [--date D] [--reexporter ID,ID]` | `--avancer` d'abord : `progression[module] = max(valeur actuelle, N)`. Ensuite, construit le paquet delta des cartes **exportables** (plus celles de `--reexporter`), complète le registre et affiche un résumé. `--sans-paquet` ne met à jour que la progression, pour les sessions cloud. `--dry-run` n'écrit rien | 0 |

**Ce que `check.py` vérifie au minimum :**
- les YAML s'analysent sans erreur ;
- les champs obligatoires sont présents ;
- les dates, les heures et l'ordre début < fin sont valides ;
- le jour de la semaine correspond bien à la date ;
- deux séances du même jour ne se chevauchent pas ;
- les créneaux respectent les règles de `semaine.yaml` ;
- aucune séance ne tombe pendant une exception `off`, sauf avec `hors_creneau` ;
- les heures planifiées de la semaine ne dépassent pas la capacité + 6 h de tampon ;
- les modules référencés existent ;
- les identifiants de compétence référencés existent ;
- les identifiants de questions et de cartes sont uniques dans tout le repo ;
- chaque carte a ses champs obligatoires et une `source` non vide ;
- les niveaux sont compris entre 0 et 4 (ou null) ;
- les statuts sont valides ;
- le registre ne référence que des cartes existantes.

**Tests** : `python -m pytest tools/tests -q`, avec des fixtures dans `tools/tests/fixtures/`.
