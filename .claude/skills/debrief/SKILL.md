---
name: debrief
description: "Debrief de fin de journée de maths (L3). On enregistre le résultat de chaque exercice du plan (reussi, aide, presque, non_fait), on pose 3 à 5 questions de compréhension, 2 par message, avec correction immédiate, on ajoute les cartes d'erreurs ou d'exercices, puis on écrit le bilan réel de la séance dans le journal (calculé par `plan.py bilan`) et on fait un seul commit. Le debrief ne prépare pas la suite : le prochain plan se calcule au début de la prochaine séance. À utiliser quand l'utilisateur dit « debrief », « on débriefe », « fin de séance », « j'ai fini », ou colle ses résultats d'exercices. Variante sans questions : « log rapide : … »."
---

# Debrief de fin de journée

- **Durée** : 10-15 min, **hors des 2 h 30** du jour.
- **Modèle conseillé** : Sonnet 5.5, effort high (Opus si la séance a révélé une confusion de fond à démêler). Le signaler si la session tourne sur un autre modèle.
- **Principe** : le code calcule (états, reprises, déverrouillage des catégories), Claude juge. Un exercice ne compte comme `reussi` que si l'utilisateur l'a fait **seul et jusqu'au bout** ; au moindre doute, demander.
- **Formats** : `docs/FORMATS.md`, à n'ouvrir qu'en cas de doute.

## 0. Log rapide (pas de questions)

Au plus 2 par semaine. Enregistrer seulement les résultats déclarés (§2), sans cartes ni questions, puis le bilan réel (§5) et le commit. Commit `debrief: <date> (log rapide)`. Le prochain debrief commence par une question de rappel sur ce jour-là.

## 1. Rassembler (lecture minimale)

1. `NOW.md` (écrit par `plan.py seance` au début de la séance) : les exercices prévus, le cours, les cartes.
2. Pour chaque exercice fait : son entrée dans `matieres/<m>/exercices.yaml` (recherche par `id`, pas le fichier entier), champs `enonce`, `methodes`, `notions`, `corrige`.
3. Les résultats récents de la même méthode : `python tools/resultat.py profil` (au besoin, filtrer).

## 2. Résultats des exercices

Demander, en un seul message, pour chaque exercice du plan : le niveau, le temps passé, et en une ligne ce qui a bloqué.

| Niveau | Quand |
|---|---|
| `reussi` | seul, sans indice ni corrigé, rédaction complète |
| `aide` | réussi après un indice, un coup d'œil au corrigé ou au cours, ou une aide de Claude |
| `presque` | l'idée est là, mais une erreur ou un trou que l'on n'a pas su combler |
| `non_fait` | pas commencé, ou bloqué dès le début |

- **Si l'utilisateur colle sa rédaction** (ou une photo), la vérifier soi-même : une preuve fausse ou incomplète n'est pas `reussi`, même s'il le pense. Dire précisément où ça casse.
- **Corrigés** : ne jamais présenter une solution comme sûre si `corrige.statut` vaut `absent` ou si on l'a reconstituée. La donner avec la mention « vérifiée par Claude, à confirmer », et toute étape douteuse signalée comme telle. Un corrigé officiel peut être faux : en cas de désaccord, le dire.
- **Enregistrer** chaque résultat, une commande par exercice : `python tools/resultat.py ajouter <id> <reussi|aide|presque|non_fait> --aide <0-4> [--note "<ce qui a bloqué>"] [--date AAAA-MM-JJ]`. Le palier `--aide` suit `CLAUDE.md` (0 = seul ; 1 question qui oriente ; 2 méthode ; 3 étape clé ; 4 solution). Le script refuse un doublon et donne l'id d'origine. Ne jamais éditer `state/resultats.yaml` à la main, ni réécrire une ancienne ligne.

## 3. Questions de compréhension (3 à 5)

**Écrire d'abord** les points attendus dans `journal/<date>.md`, en une seule écriture, avant de poser la moindre question :

```markdown
# <date> (<jour>)
## Séance
- prévu : <n> exercices, cours <notion>
- fait : (à compléter) · temps réel : …
## Résultats
- <id exercice> : <niveau> · <temps> min · <ce qui a bloqué>
## Debrief
### Points attendus (écrits avant les questions)
- Q1 <question> → <point a> ; <point b>
### Réponses et notes
## Mises à jour
```

| # | Rôle |
|---|---|
| Q1 | rappel d'un exercice ou d'une notion d'un jour précédent (le dernier log rapide en priorité) |
| Q2-Q3 | « pourquoi » sur les exercices du jour : quelle hypothèse sert où, pourquoi cette méthode, que se passe-t-il si on retire une hypothèse |
| Q4 | énoncé précis d'une définition ou d'un théorème du cours du jour (quantificateurs, hypothèses) |
| Q5 | contre-exemple ou transfert, si la séance s'y prête |

- 2 questions par message, sans indice. Après chaque réponse : note /2, ce qui est juste, ce qui manque, la bonne réponse en 2 à 4 lignes.
- Barème : **2** tout l'essentiel ; **1** partiel ou après une relance ; **0** faux ou absent. « Je ne sais pas » vaut 0, sans reproche. Une relance au plus.
- Questions tirées des exercices faits, du cours (`notions.yaml`, pages du poly) et de leurs cartes, **jamais de mémoire seule** sur un point de cours : vérifier dans le poly si nécessaire.

## 4. Mises à jour

1. **Journal** : compléter `journal/<date>.md` (temps réel, notes des questions, corrections).
2. **Avant toute carte, chercher celles qui existent** (aucun doublon), pour la notion en cause :
   - **les nouvelles cartes** : dans `matieres/<m>/cartes.yaml`, chercher par `notion:` et par mot-clé dans le recto ;
   - **les anciennes cartes de l'utilisateur** (prépa, `AoutLicenceMath`…) : dans `matieres/<m>/couverture.yaml`, relever les `notes` de la notion, puis lire leur recto dans `inventaire/anki/notes.jsonl` (recherche par `"id": <nid>`). Ajouter une recherche par mot-clé dans ce fichier, car une carte peut couvrir le point sans être rattachée à la notion. Le verso de beaucoup d'anciennes cartes est une image : on ne compare que le recto.
   - **La règle :**
     - si une carte existante couvre déjà exactement le point, n'en créer aucune. La **mettre à réviser à la prochaine séance** : ajouter à `state/a_revoir.yaml` l'entrée `{pour: <demain>, nid: <nid>, raison: "<confusion>"}`, ou `id: <id>` pour une carte de `cartes.yaml`. `plan.py seance` en tire une recherche Anki le jour de la prochaine séance (à partir de `pour`, qu'elle ait lieu demain ou plus tard). Le noter aussi dans `## Mises à jour` ;
     - une carte d'erreur ne se crée que si elle vise une confusion que les cartes existantes ne traitent pas.

   `inventaire/anki/notes.jsonl` est l'instantané du paquet au 03/11/2026. Les cartes créées par le système depuis cette date sont toutes dans `cartes.yaml`.
3. **Cartes d'erreurs** : une carte par confusion révélée (exercice `presque` ou `aide`, ou note 0-1), si elle vaut d'être retenue et qu'elle passe le contrôle ci-dessus. Ajouter en fin de `matieres/<m>/cartes.yaml` :
   - `id: <m>-eNNN` (numéro libre suivant), `notion`, `chapitre`, `priorite: 1`, `tags: [erreur]` ;
   - recto : une question qui vise précisément la confusion ; verso : la réponse juste en 1 à 3 lignes ; source : poly et page, ou l'exercice ;
   - maths en `\( … \)`, texte YAML entre apostrophes ou en bloc `|`.
   - Un **prérequis L1-L2** révélé (point d'ECG ou de L1-L2 que l'utilisateur ignore) ne s'ajoute jamais comme carte sans notion : créer une notion `type: prerequis` (`<préfixe>-p-NNNN`, `requis_par: [exercice]`, au sous-chapitre où elle sert) puis la carte (tag `prerequis-l1l2`, `notion:` = cette notion). Format : `docs/FORMATS.md`.
4. **Cartes d'exercices** (une par exercice non réussi seul). Format et exemple : `docs/FORMATS.md`, « Cartes d'exercices ».
   - **Lesquels :** résultat du jour `aide` ou `presque` ; `non_fait` seulement si l'exercice a été travaillé et le corrigé vu pendant la séance. Rien pour `reussi`, ni pour un `non_fait` jamais ouvert.
   - **Doublon :** chercher dans `matieres/<m>/cartes.yaml` une carte avec `exercice: <id>`. Une seule carte par exercice.
     - Elle existe : si l'erreur du jour est nouvelle, compléter son verso (ligne « Piège », ou la correction si elle était incomplète), puis `python -I tools/anki.py --reexporter <id>` (§5). Dans tous les cas, ajouter `{pour: <date du prochain NOW>, id: <id de la carte>, raison: "<erreur du jour>"}` à `state/a_revoir.yaml`, et le noter dans `## Mises à jour`.
     - Elle n'existe pas : la créer en fin de `cartes.yaml` avec `id: ex-<id exercice>`, `exercice`, `notion` (notion principale de l'exercice), `chapitre` (exactement celui des cartes de cours : l'export la range dans le sous-paquet `<chapitre>::Exercices`), `priorite: 1`, `tags: [exercice]`.
   - **Recto :** `Exo <id> : <titre>`, l'énoncé (condensé s'il est long, mais avec toutes les hypothèses et tous les symboles introduits), puis « Méthode ? Étape clé ? ».
   - **Verso :** l'idée clé en une ligne ; la **correction complète** (toutes les étapes rédigées, fidèle au corrigé officiel) ; le piège éventuel (l'erreur faite en séance, si on la connaît) ; la référence du corrigé (fichier, page) dans `source`.
   - **Justesse à 100 % :** le verso se rédige à partir du **corrigé officiel**, page du PDF ouverte (texte dans `bibliotheque/_texte/`, ou image avec `tools/rendre_page.py`). Un corrigé officiel peut être faux : le vérifier. Sans corrigé officiel (`corrige.statut: absent`), résoudre l'exercice soi-même, vérifier chaque étape, et écrire dans `source` « Pas de corrigé officiel : vérifiée par Claude, à confirmer ». Ne jamais écrire un verso de mémoire.
   - La carte ne remplace pas la reprise sur papier : le planificateur la programme déjà (J+1 à J+3).
5. **Notion de cours mal comprise** (note 0 sur Q4) : l'indiquer dans `## Mises à jour` ; le planificateur la reprend au cours de la prochaine séance si elle figure dans `NOW.md`.
6. **Ne jamais** réorganiser le planning à la main : c'est le rôle de `plan.py`.

## 5. Bilan réel et commit (une commande à la fois, depuis la racine)

Le debrief ne régénère aucun plan. Il écrit ce qui s'est réellement passé.

1. Cartes nouvelles (cartes d'erreurs et d'exercices comprises, s'il y en a) : `python tools/anki.py` (pour une carte déjà exportée et corrigée : `python -I tools/anki.py --reexporter <ids>`), puis ouvrir le paquet indiqué par la sortie (`Start-Process "anki\paquets\<fichier>.apkg"`). Demander à l'utilisateur de synchroniser Anki (pour que le bilan lise les cartes apprises).
2. Bilan réel : `python tools/plan.py bilan`. **Recopier la sortie telle quelle** dans `journal/<date>.md`, sous `## Bilan réel` (ne rien recalculer de tête). Elle donne :
   - les exercices prévus contre faits (les non faits sont reportés automatiquement : ils reviennent au prochain plan) ;
   - les cartes apprises dans la séance, lues dans Anki (ou « Anki fermé » : non relevées) ;
   - la marge recalculée.
3. `python tools/check.py`. **Pas de commit tant qu'il échoue.**
4. `git add` avec des chemins explicites : `journal/<date>.md`, `state/` (dont `a_revoir.yaml`, `seance.yaml`), `matieres/*/cartes.yaml` touchés, `anki/registre.csv`, `NOW.md`.
5. `git commit -m "debrief: <date>"`, un seul commit, puis `git push`.

## 6. Clore (3 à 5 lignes)

- Les résultats du jour et le score des questions.
- Ce qui est passé `acquis` ou `maitrise`, et la catégorie qui s'est ouverte, s'il y en a une.
- Le bilan réel : exercices reportés, cartes apprises, marge.
- Rappel : importer le paquet Anki s'il y en a un, synchroniser Anki. La prochaine séance commence par « on commence » : le plan se calcule à ce moment-là.
