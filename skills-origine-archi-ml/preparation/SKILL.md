---
name: preparation
description: "Préparer des modules à l'avance (une fois par semaine). On choisit les sources dans le catalogue, on lit la source réelle, puis on écrit fiche.md, questions.yaml, cartes.yaml, les exercices et leurs tests pytest. À utiliser quand l'utilisateur dit « prépare le module … », « préparation de la semaine », « prépare la semaine prochaine » ou « prépare les fiches ». Aussi quand le check-in constate qu'un module planifié n'est pas préparé."
---

# Préparation de modules

## Avant de commencer

- **Modèle conseillé** : Sonnet 5.5, effort high. Le signaler si la session tourne sur un autre modèle.
- **Quand** : une fois par semaine, à l'avance. Lire les sources coûte cher, on ne le fait donc qu'une fois : ensuite, les sessions lisent la fiche.
- **Où** : de préférence sur le PC, à cause des PDF de `bibliotheque/`. En cloud, seules les sources HTML sont accessibles.
- **Règles de fond** : `docs/ARCHITECTURE.md` §8 et §9. Formats exacts : `docs/FORMATS.md`, section `modules/<id>/`.
- **Notations** : `<m>` = id du module (ex. `py-numpy`) ; `<m_>` = id avec `_` à la place des `-` (ex. `py_numpy`).

**Interdits absolus :**
- inventer une page, une URL, une section ou une date (si on ne sait pas : section et URL, ou « à vérifier ») ;
- écrire des cartes ou des questions de mémoire ;
- mettre une solution de référence dans le repo.

## 1. Cadrer

1. **Établir la liste des modules** : d'après la demande, `ROADMAP.md`, ou le nouveau `state/semaine.yaml`.
2. **Pour chaque module, regarder ce qui existe déjà** dans `modules/<m>/` et ne compléter que ce qui manque.
   - Un `id` existant ne change jamais.
   - On ne supprime jamais une carte présente dans `anki/registre.csv`.
   - La numérotation continue après le plus grand numéro existant.
3. **Vérifier les compétences visées** : elles doivent exister dans `state/competences.yaml`. S'il en manque une :
   - l'ajouter (`niveau: null`, `cible`, `modules: [<m>]`, `preuves: []`, `prochaine_verif: null`, `intervalle_sem: 1`, `echecs_consecutifs: 0`) ;
   - le signaler dans le compte rendu.

## 2. Choisir les sources (`ressources/catalogue.yaml`)

1. **Prendre la ressource `role: principale`** dont les `domaines` couvrent le module, puis les sections utiles de son `plan`.
   - `secours` : si la principale ne convient pas.
   - `complement` : pour un point précis.
2. **Si aucune ressource du catalogue ne convient** :
   - **s'arrêter et le signaler** ;
   - ou bien ajouter une entrée complète après vérification (ARCHITECTURE §9) : lien qui fonctionne, accès et licence, plan relevé avec URL et pages, `verifie_le`.

## 3. Lire la source réelle

| Format | Comment |
|---|---|
| HTML | WebFetch sur l'URL exacte de chaque section du `plan` |
| PDF | `fichier_local` sous `bibliotheque/` (PC) ; Read avec `pages: "a-b"`, **seulement les pages utiles** |
| Vidéo | Page officielle, chapitres et minutage s'ils sont publiés ; sinon section et URL |

- **Pendant la lecture, relever précisément** : section, URL, pages réellement lues. Ces références alimentent toutes les sources.
- **Une source est inaccessible** (PDF absent en cloud, lien mort) : le signaler, ne rien écrire de mémoire.

## 4. `modules/<m>/fiche.md`

Les sections suivantes, **dans cet ordre et avec ces titres** :

1. `## Objectifs`
2. `## Compétences visées` : une ligne par compétence, `- <id> (cible <n>) : <nom>`.
3. `## Prérequis`
4. `## Séances` : une sous-section `### Séance <n>` par séance de 2 h. Le lien `modules/<m>/fiche.md#seance-<n>` de `semaine.yaml` renvoie ici. Chaque séance donne :
   - le **type** : `cours`, `exercices`, `projet`, `article`, `consolidation`, `examen`, `diagnostic` ou `installation` ;
   - le **déroulé** : rappel de 5 min, apprentissage actif de 60 à 70 min, application de 40 à 50 min, bilan de 5 min en 3 lignes ;
   - les **lectures exactes** : id du catalogue, section, pages ou URL, minutage d'une vidéo ;
   - les **exercices** : `exNN` ;
   - le **livrable**.
5. `## Livrable`
6. `## Points clés` : des puces courtes par séance. Elles servent au debrief, sans relire la source.
7. `## Sources` : chaque lien, avec la date de vérification (aujourd'hui).

## 5. `modules/<m>/questions.yaml`

- **Au moins 3 questions par compétence visée**, de **types variés** : `cours`, `pourquoi`, `transfert`, `code`, `calcul`.
- Étaler la `difficulte` entre 1 et 3.
- Chaque question doit pouvoir se traiter en 2-3 min, à l'oral ou par écrit (format du debrief).
- **Champs** :
  - `id` : `<m>-qNNN` ;
  - `competence`, `seance` (numéro de la séance de la fiche où la notion est étudiée), `type`, `difficulte`, `question` ;
  - `points_attendus` : 2 à 4 points concrets et vérifiables ;
  - `source` : `{ressource: <id catalogue>, ref: "<section>", url: "<url>"}`.

## 6. `modules/<m>/cartes.yaml`

- **Couvrir tout le cours lu**, pas seulement ce que testent les questions : définitions, résultats, intuitions, pièges, idiomes de code, ordres de grandeur.
- **Étiquette** :
  - `essentiel` : indispensable à la compétence ;
  - `complement` : le reste, que l'utilisateur pourra suspendre.
- **Règles de rédaction** (ARCHITECTURE §8) :
  - une idée par carte ;
  - un recto formulé comme une question précise ;
  - un verso court ;
  - les maths en MathJax, `\( … \)` en ligne et `\[ … \]` en bloc ;
  - le code en `<code>`/`<pre>` ;
  - **pas de liste à apprendre en bloc** : la découper en plusieurs cartes.
- **Champs** :
  - `id` : `<m>-cNNN` ;
  - `recto`, `verso` ;
  - `source`, non vide sur **chaque** carte : `"Auteur, Titre, section, p. X — URL"`, sans page si on ne la connaît pas ;
  - `tags` : `[essentiel]` ou `[complement]` ;
  - `competence` ;
  - `seance` : **obligatoire** pour les cartes de cours. C'est le numéro de la séance où le contenu est étudié. La carte ne sera exportée vers Anki qu'une fois cette séance faite (`anki/progression.yaml`).
- **YAML** : dans des guillemets doubles, `\(` est une séquence d'échappement invalide. Écrire les textes contenant `\` **entre apostrophes simples** (en doublant les `'` internes), ou en bloc `|`.
- **Volume indicatif** : 40 à 60 cartes par semaine, tous modules confondus.

## 7. Exercices et tests

### Énoncés : `modules/<m>/exercices/exNN-<slug>.md`

Chaque énoncé contient :
- l'énoncé lui-même ;
- la source (ressource, section, URL) ;
- la compétence ;
- le **fichier attendu** `labs/<m>/exNN.py`, avec les signatures exactes des fonctions ;
- la commande de test.

**Rappels à mettre dans l'énoncé :**
- placer le code d'exploration (cellules `# %%`, affichages, graphiques) sous `if __name__ == "__main__":`, car les tests importent le fichier ;
- les données éventuelles vont dans `labs/<m>/data/` (non versionné).

**Exercices de maths** (dérivations, preuves) :
- un énoncé et sa source, **sans corrigé** ;
- si la source a un corrigé, indiquer seulement où il se trouve ;
- la correction se fait au debrief.

### Tests pytest : `modules/<m>/exercices/tests/test_<m_>_exNN.py`

- **Le nom de fichier doit être unique dans tout le repo.** Pas de `__init__.py`, donc deux fichiers `test_ex01.py` entreraient en conflit.
- Les tests sont **écrits avant** la solution, déterministes (graine fixée), sans réseau et rapides (moins de quelques secondes).
- Ils vérifient le comportement : valeurs, formes, cas limites. Ils ne vérifient pas l'implémentation.

Modèle à reprendre :

```python
"""Tests de <m> / exNN : <titre>. Écrits avant la solution."""
import importlib.util
import os
from pathlib import Path

import pytest

MODULE, EXERCICE = "<m>", "exNN"
RACINE = Path(__file__).resolve().parents[4]          # tests/ → exercices/ → <m>/ → modules/ → racine
LABS = Path(os.environ.get("ML_ARCHI_LABS", RACINE / "labs"))
CHEMIN = LABS / MODULE / f"{EXERCICE}.py"


@pytest.fixture(scope="module")
def sol():
    if not CHEMIN.exists():
        pytest.skip(f"Écris ta solution dans labs/{MODULE}/{EXERCICE}.py")
    spec = importlib.util.spec_from_file_location(f"{MODULE.replace('-', '_')}_{EXERCICE}", CHEMIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_exemple(sol):
    assert sol.ma_fonction(2) == 4
```

### Valider les tests sans rien laisser dans le repo

1. Écrire une solution de référence dans un **dossier temporaire hors du repo** : `<tmp>/<m>/exNN.py`.
2. Lancer les tests contre elle :
   - Bash : `ML_ARCHI_LABS=<tmp> python -m pytest modules/<m>/exercices/tests -q` ;
   - PowerShell : `$env:ML_ARCHI_LABS="<tmp>"`, puis la commande pytest.
3. Les tests doivent passer avec la solution de référence et être `skipped` sans elle.
4. Supprimer le dossier temporaire.

**Jamais** de solution de référence dans `modules/` ni dans `labs/`.

## 8. Vérifier et commiter

Les commandes se lancent **une par une** :

1. `python -m pytest modules/<m>/exercices/tests -q`. Sans solution, les tests doivent sortir en `skipped`, pas en erreur de collecte.
2. Sur le PC, en option : `python tools/anki.py --dry-run`. Il vérifie que les cartes se construisent, sans rien écrire.
3. `python tools/check.py`. Il contrôle les ids uniques, les champs obligatoires et les sources non vides. Corriger jusqu'à ce qu'il passe.
4. `git add modules/<m>/` (et `ressources/catalogue.yaml` ou `state/competences.yaml` s'ils ont été touchés).
5. `git commit -m "prep: <m1>, <m2>"`.
6. `git push origin main`.

**Compte rendu court** :
- les modules préparés, avec le nombre de séances, de questions, de cartes et d'exercices ;
- les sources lues (sections, pages) ;
- les points « à vérifier ».
