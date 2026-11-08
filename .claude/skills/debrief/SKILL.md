---
name: debrief
description: "Debrief de fin de journée de maths (L3). On enregistre le résultat de chaque exercice du plan (reussi, aide, presque, non_fait), on évalue la compréhension de chaque notion travaillée d'après ce que l'utilisateur a dit pendant la séance et on met à jour son modèle de compréhension (`state/comprehension.yaml` : niveau sur preuve, vision, liens, confusions), avec au plus 3 questions là où la preuve manque. On crée les cartes d'exercices et les prérequis L1-L2 révélés, jamais de carte à partir de ses questions. Puis on écrit le bilan réel de la séance dans le journal (calculé par `plan.py bilan`) et on fait un seul commit. Le debrief ne prépare pas la suite : le prochain plan se calcule au début de la prochaine séance. À utiliser quand l'utilisateur dit « debrief », « on débriefe », « fin de séance », « j'ai fini », ou colle ses résultats d'exercices. Variante sans questions : « log rapide : … »."
---

# Debrief de fin de journée

- **Durée** : 10-15 min, **hors des 2 h 30** du jour.
- **Modèle conseillé** : Sonnet 5.5, effort high (Opus si la séance a révélé une confusion de fond à démêler). Le signaler si la session tourne sur un autre modèle.
- **Principe** : le code calcule (états, reprises, déverrouillage des catégories), Claude juge. Un exercice ne compte comme `reussi` que si l'utilisateur l'a fait **seul et jusqu'au bout** ; au moindre doute, demander. De même, un niveau de compréhension ne monte que sur preuve.
- **Formats** : `docs/FORMATS.md`, à n'ouvrir qu'en cas de doute (« Modèle de compréhension » pour `comprehension.yaml`).

## 0. Log rapide (pas de questions)

Au plus 2 par semaine. Enregistrer seulement les résultats déclarés (§2), sans cartes ni questions. Si la séance a eu lieu dans cette conversation, mettre à jour `comprehension.yaml` d'après les échanges (§3, sans question) ; sinon, n'y rien changer. Puis le bilan réel (§5) et le commit. Commit `debrief: <date> (log rapide)`.

## 1. Rassembler (lecture minimale)

1. `NOW.md` (écrit par `plan.py seance` au début de la séance) : les exercices prévus, le cours, « À consolider », les cartes.
2. Pour chaque exercice fait : son entrée dans `matieres/<m>/exercices.yaml` (recherche par `id`, pas le fichier entier), champs `enonce`, `methodes`, `notions`, `corrige`.
3. Les entrées de `state/comprehension.yaml` des notions travaillées (commande du skill `seance`, §3), et `style`.

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

## 3. Évaluer la compréhension

1. **Pour chaque notion travaillée** (cours, « À consolider », notions des exercices faits), relire dans la conversation ce qu'il a dit : ses explications, ses questions, ses raisonnements en exercice, les aides qu'il a demandées, et pour chaque exercice non réussi seul la **cause du blocage** trouvée en séance (notion pas tenue, lien pas fait, méthode pas reconnue : elle va dans `confusions` ou `liens_manquants`) et ce qu'il a dit en retenir. Ses questions ne donnent pas de cartes : elles montrent où sa compréhension s'arrête.
2. **Fixer le niveau** par la table de `docs/FORMATS.md` (inconnue, recitee, fragile, tenue, reliee). Monter seulement sur preuve ; ce qu'il a bien expliqué juste après qu'on le lui a enseigné vaut au plus `fragile` ; `tenue` exige une preuve à froid. Descendre dès qu'une preuve contredit. Une bonne réponse sur un raisonnement confus est `fragile`.
3. **Au plus 3 questions**, et seulement là où la preuve manque pour trancher (entre deux niveaux, ou une confusion à confirmer). Écrire d'abord les points attendus dans le journal, puis une question par message, sans indice : application à un cas nouveau, « pourquoi », hypothèse retirée, lien avec une autre notion. Après la réponse : ce qui est juste, ce qui manque, la bonne réponse en 2 à 4 lignes, appuyée sur le poly (fichier, page), jamais de mémoire seule.
4. **Mettre à jour `state/comprehension.yaml`** (une entrée par notion travaillée) : `niveau`, `vision` (ses mots, 1-2 lignes), `liens` et `liens_manquants`, `confusions` (nouvelle : `ouverte` ; `reparee` seulement sur preuve à froid), une `preuve` par élément décisif (6 au plus, les plus récentes), `maj` ; `style` si la séance a appris quelque chose sur sa façon de raisonner (6 lignes au plus).
5. **Une confusion** ne donne pas de carte : elle va dans `confusions`, et `plan.py` refait passer les cartes de la notion à la prochaine séance. Si une carte rattachée à une **autre** notion (ou une ancienne carte trouvée par mot-clé dans `inventaire/anki/notes.jsonl`) couvre exactement le point, l'ajouter à `state/a_revoir.yaml` : `{pour: <demain>, id: <id>, raison: "<confusion>"}` (ou `nid: <nid>`).

## 4. Cartes

1. **Prérequis L1-L2 révélé** (point d'ECG ou de L1-L2 qu'il ignore) : d'abord chercher les cartes existantes (`cartes.yaml` par `notion:` et mot-clé ; anciennes cartes : `couverture.yaml` puis recto dans `inventaire/anki/notes.jsonl`, plus une recherche par mot-clé ; on ne compare que le recto). S'il n'y en a pas : créer une notion `type: prerequis` (`<préfixe>-p-NNNN`, `requis_par: [<exercices ou notions>]`, au sous-chapitre où elle sert) puis sa carte (tag `prerequis-l1l2`, `notion:` = cette notion, question précise au recto, verso court, source). Dans `comprehension.yaml` : niveau `inconnue`. Format : `docs/FORMATS.md`.
2. **Cartes d'exercices** (une par exercice non réussi seul). Format et exemple : `docs/FORMATS.md`, « Cartes d'exercices ».
   - **Lesquels :** résultat du jour `aide` ou `presque` ; `non_fait` seulement si l'exercice a été travaillé et le corrigé vu pendant la séance. Rien pour `reussi`, ni pour un `non_fait` jamais ouvert.
   - **Doublon :** chercher dans `matieres/<m>/cartes.yaml` une carte avec `exercice: <id>`. Une seule carte par exercice.
     - Elle existe : si l'erreur du jour est nouvelle, compléter son verso (ligne « Piège », ou la correction si elle était incomplète), puis `python -I tools/anki.py --reexporter <id>` (§5). Dans tous les cas, ajouter `{pour: <date du prochain NOW>, id: <id de la carte>, raison: "<erreur du jour>"}` à `state/a_revoir.yaml`, et le noter dans `## Mises à jour`.
     - Elle n'existe pas : la créer en fin de `cartes.yaml` avec `id: ex-<id exercice>`, `exercice`, `notion` (notion principale de l'exercice), `chapitre` (exactement celui des cartes de cours : l'export la range dans le sous-paquet `<chapitre>::Exercices`), `priorite: 1`, `tags: [exercice]`.
   - **Recto :** `Exo <id> : <titre>`, l'énoncé (condensé s'il est long, mais avec toutes les hypothèses et tous les symboles introduits), puis « Méthode ? Étape clé ? ».
   - **Verso :** l'idée clé en une ligne (comparée à ce qu'il a dit retenir en séance : si sa formulation est juste et plus parlante, la reprendre ; la justesse vient du corrigé, jamais de sa formulation) ; la **correction complète** (toutes les étapes rédigées, fidèle au corrigé officiel) ; le piège éventuel (l'erreur faite en séance, si on la connaît) ; la référence du corrigé (fichier, page) dans `source`.
   - **Justesse à 100 % :** le verso se rédige à partir du **corrigé officiel**, page du PDF ouverte (texte dans `bibliotheque/_texte/`, ou image avec `tools/rendre_page.py`). Un corrigé officiel peut être faux : le vérifier. Sans corrigé officiel (`corrige.statut: absent`), résoudre l'exercice soi-même, vérifier chaque étape, et écrire dans `source` « Pas de corrigé officiel : vérifiée par Claude, à confirmer ». Ne jamais écrire un verso de mémoire.
   - La carte ne remplace pas la reprise sur papier : le planificateur la programme déjà (J+1 à J+3).
3. Maths en `\( … \)`, texte YAML entre apostrophes ou en bloc `|`. **Ne jamais** réorganiser le planning à la main : c'est le rôle de `plan.py`.

**Journal** (`journal/<date>.md`, points attendus écrits avant toute question) :

```markdown
# <date> (<jour>)
## Séance
- prévu : <n> exercices, cours <notions> · fait : … · temps réel : …
## Résultats
- <id exercice> : <niveau> · <temps> min · <ce qui a bloqué>
## Compréhension
- `<id notion>` <titre> : <ancien> → <nouveau> · <pourquoi, la preuve en une ligne>
### Questions (points attendus écrits avant)
- Q1 <question> → <points attendus> · réponse : <juste/partiel/faux, ce qui manquait>
## Mises à jour
```

## 5. Bilan réel et commit (une commande à la fois, depuis la racine)

Le debrief ne régénère aucun plan. Il écrit ce qui s'est réellement passé.

1. Cartes nouvelles (prérequis et cartes d'exercices, s'il y en a) : `python tools/anki.py` (pour une carte déjà exportée et corrigée : `python -I tools/anki.py --reexporter <ids>`), puis ouvrir le paquet indiqué par la sortie (`Start-Process "anki\paquets\<fichier>.apkg"`). Demander à l'utilisateur de synchroniser Anki (pour que le bilan lise les cartes apprises).
2. Bilan réel : `python tools/plan.py bilan`. **Recopier la sortie telle quelle** dans `journal/<date>.md`, sous `## Bilan réel` (ne rien recalculer de tête). Elle donne :
   - les exercices prévus contre faits (les non faits sont reportés automatiquement : ils reviennent au prochain plan) ;
   - les cartes apprises dans la séance, lues dans Anki (ou « Anki fermé » : non relevées) ;
   - la marge recalculée.
3. `python tools/check.py`. **Pas de commit tant qu'il échoue.**
4. `git add` avec des chemins explicites : `journal/<date>.md`, `state/comprehension.yaml`, `state/` (dont `a_revoir.yaml`, `seance.yaml`), `matieres/*/cartes.yaml` et `notions.yaml` touchés, `anki/registre.csv`, `NOW.md`.
5. `git commit -m "debrief: <date>"`, un seul commit, puis `git push`.

## 6. Clore (3 à 5 lignes)

- Les résultats du jour et les changements de niveau de compréhension (et les confusions ouvertes ou réparées).
- Ce qui est passé `acquis` ou `maitrise`, et la catégorie qui s'est ouverte, s'il y en a une.
- Le bilan réel : exercices reportés, cartes apprises, marge.
- Rappel : importer le paquet Anki s'il y en a un, synchroniser Anki. La prochaine séance commence par « on commence » : le plan se calcule à ce moment-là.
