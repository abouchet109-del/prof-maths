---
name: debrief
description: "Debrief de fin de séance ML. On pose 4 à 6 questions, 2 par message, avec correction immédiate et une note de 0 à 2. On met ensuite à jour les compétences, le journal, la semaine et les cartes Anki, puis on fait un seul commit. À utiliser quand l'utilisateur dit « debrief », « on débriefe », « fin de séance », « j'ai fini » ou « séance terminée ». Variante sans questions quand il écrit « log rapide : … » (par exemple « log rapide : fait 2 h, ch. 3, exos 1-4 »)."
---

# Debrief de fin de séance

- **Durée** : 10-15 min, **hors des 14 h**.
- **Modèle conseillé** : Sonnet 5.5, effort high. Signale-le si la session tourne sur un autre modèle.
- **Règles de fond** : `docs/ARCHITECTURE.md` §6. Formats exacts : `docs/FORMATS.md`, à n'ouvrir qu'en cas de doute.
- **Notations** :
  - `<date>` = aujourd'hui (`AAAA-MM-JJ`) ;
  - `<module>` = le module de la séance ;
  - `<m_>` = `<module>` avec des `_` à la place des `-`.

## 0. Variante « log rapide » (pas de questions)

Au plus **2 par semaine**, les soirs de fatigue. Si c'est déjà le 3e de la semaine ISO, le signaler et proposer un debrief court (4 questions). L'utilisateur décide.

1. Identifier la séance du jour dans `state/semaine.yaml`.
2. Écrire `journal/<date>.md` (format §3) :
   - la section `## Séance` ;
   - sous `## Debrief`, la ligne : « log rapide, sans questions. Rappel au prochain debrief. » ;
   - dans `## Mises à jour`, ce qui a changé.
3. Dans `state/semaine.yaml`, mettre à jour `statut` (`faite` ou `partielle`) et `heures_reelles`, à partir de ce que l'utilisateur a déclaré.
4. **Aucune** mise à jour de niveau : sans questions, pas de preuve. Le prochain debrief commence par le rappel de cette séance (Q1) et fait la mise à jour.
5. Passer à l'étape 6 (commandes). Message de commit : `debrief: <date> (log rapide)`.

## 1. Rassembler (lecture minimale)

1. **La séance du jour.** Dans `NOW.md` et `state/semaine.yaml`, relever : `id`, `module`, `type`, `tache`, `ressources`.
2. **La séance précédente**, pour le rappel. Prendre son journal `journal/<date-précédente>.md`, sections `## Séance` et `## Mises à jour` seulement. S'il manque, ou s'il s'agissait d'un log rapide, le rappel porte sur cette séance-là.
3. **La fiche.** Dans `modules/<module>/fiche.md` : `### Séance n` du jour, et `## Points clés`.
4. **Les banques.** `modules/<module>/questions.yaml` : seulement les questions des compétences de la séance, plus celles des compétences à maintenir.
5. **Les compétences.** Dans `state/competences.yaml`, **seulement les entrées concernées** (recherche par id) :
   - les compétences de la séance ;
   - celles dont `prochaine_verif` ≤ aujourd'hui (liste dans `NOW.md`, section « Vérifications de maintien dues »).
6. **Le travail du jour.**
   - **PC** :
     - `git status --short labs/` ;
     - `git diff -- labs/<module>/` ;
     - `git log -p --since=<date> -- labs/` ;
     - les tests des exercices du jour : `python -m pytest modules/<module>/exercices/tests/test_<m_>_exNN.py -q`.
     - Ce résultat est une preuve objective : réussi ou non, avec quel palier d'aide.
   - **Cloud** : seul le travail poussé est visible (`git log -p --since=<date> -- labs/`). Sinon, demander à l'utilisateur de résumer ce qu'il a fait ou de coller l'essentiel.
7. **Le palier d'aide maximal** de la séance. Le relever dans la conversation du jour. S'il est inconnu, le demander.

## 2. Choisir les questions (4 à 6, d'un coup)

| # | Rôle | Source |
|---|---|---|
| Q1 | Rappel différé de la séance précédente (ou de la séance en log rapide ou sans debrief) | `questions.yaml` de son module |
| Q2-Q3 | 2 questions `cours` sur les compétences du jour | `questions.yaml` du module |
| Q4 (et Q5) | 1 à 2 « pourquoi » sur le code ou le raisonnement du jour | type `pourquoi` ou `transfert` de la banque, ou question tirée du diff (notée `[libre]`) |
| Q6 | 1 question de maintien sur une compétence échue (la plus en retard) | banque de son module |

- **Re-test différé (niveau 3).** Une compétence peut avoir une preuve `exercice` réussie (aide ≤ 1) datant de 14 à 21 jours. Dans ce cas, le créneau de maintien sert à son re-test : une question `code` ou `transfert`, ou un mini-exercice de 5 min.
- Varier les types et la difficulté.
- Éviter les questions déjà posées dans les 2 dernières `preuves` de la compétence (champ `ref`).
- Rester à 4 questions si la séance a été courte ou si l'utilisateur est fatigué ; 6 au plus.

## 3. Écrire les points attendus AVANT de poser les questions

Créer ou compléter `journal/<date>.md` **en une seule écriture**. L'utilisateur ne déplie pas cette écriture (règle d'honnêteté).

```markdown
# <date> (<jour>)
## Séance
- prévue : <créneau> · <module> · <type>
- réalisée : (à compléter)
- aide reçue : max <palier> (<sur quoi>)
- notes de l'utilisateur : (à compléter)
## Debrief
### Points attendus (écrits avant les questions)
- Q1 [<id question>] <question> → <point a> ; <point b> ; <point c>
- Q4 [libre] <question> → …
### Réponses et notes
## Mises à jour
```

## 4. Poser les questions, 2 par message

1. **Premier message.** Les infos de séance, puis Q1 et Q2, sans indice.
   - Infos de séance : horaire réel (début-fin) et les 3 lignes « compris / pas compris / question ».
2. **Après chaque réponse**, corriger **explicitement chaque question** :
   - la note /2 ;
   - ce qui est juste ;
   - ce qui manque ou est faux ;
   - la bonne réponse en 2 à 4 lignes.
3. **Une relance au plus** par question, si la réponse est ambiguë ou incomplète. La note en tient compte.
4. **Barème** :
   - **2** : tous les points essentiels attendus ;
   - **1** : partiel, ou complet seulement après relance ;
   - **0** : faux ou absent.
   - « Je ne sais pas » vaut 0, sans reproche.
5. Puis les 2 questions suivantes, et ainsi de suite.

## 5. Mettre à jour (une fois toutes les réponses notées)

### 5.1 `journal/<date>.md`
- Compléter `réalisée : <début>-<fin> (<h> h) · statut : <statut>` et les notes de l'utilisateur.
- Ajouter une ligne par question : `- Q1 : 2/2 — correction : …`.
- Dans `## Mises à jour`, renseigner :
  - `compétences : <id> <avant> → <après> (preuves : Q…)` ;
  - `cartes : …` ;
  - `planning : …`.

### 5.2 `state/semaine.yaml` (la séance du jour seulement)
- `statut` :
  - `faite` si la séance est essentiellement faite ;
  - `partielle` sinon.
- `heures_reelles` : un nombre (ex. `2.0`), d'après l'horaire réel.
- Si de l'**autocomplétion IA** a été utilisée, la compter comme une aide (palier 2 au moins).

### 5.3 `state/competences.yaml` (entrées concernées seulement)

**Les preuves.** Ajouter **en dernier** :
- au debrief : `{date: <date>, type: debrief, ref: "journal/<date>.md#q<n>", note: <0-2>, aide: <palier>}` ;
- pour un exercice testé : `{date: <date>, type: exercice, ref: "labs/<module>/exNN.py", note: <2 si tests passés, sinon 0 ou 1>, aide: <palier>}` ;
- pour un re-test : `type: retest`.

**Les règles de niveau**, appliquées dans l'ordre :

| Passage | Condition |
|---|---|
| `null`/0 → 1 | séance de `cours` faite sur la compétence |
| 1 → 2 | sur les preuves `debrief` depuis la dernière montée : au moins une question `cours` **et** une `pourquoi` (ou `transfert`), moyenne ≥ 1,5 |
| 2 → 3 | une preuve `exercice` (tests passés, aide ≤ 1), **puis** une preuve `retest` réussie (note 2, aide ≤ 1), au moins 14 jours plus tard |
| 3 → 4 | projet livré, choix défendus. Uniquement au check-in ou à l'examen, pas au debrief ordinaire |

**À la première montée au niveau 2** :
- `prochaine_verif` = date + 7 jours ;
- `intervalle_sem: 1` ;
- `echecs_consecutifs: 0`.

**Après une preuve `exercice` réussie** : `prochaine_verif` = le plus proche entre la valeur actuelle et la date + 14 jours. Le re-test tombe ainsi dans la fenêtre de 2-3 semaines.

**Le maintien** (compétence de niveau ≥ 2, questionnée en maintien ou en re-test) :

| Note | Effet |
|---|---|
| 2 (réussite) | `intervalle_sem` passe au suivant (1 → 3 → 8 → 16 ; 16 reste 16), `prochaine_verif` = date + intervalle, `echecs_consecutifs: 0` |
| 1 (fragile) | intervalle inchangé, `prochaine_verif` = date + intervalle, `echecs_consecutifs` inchangé |
| 0 (échec) | `intervalle_sem: 1`, `prochaine_verif` = date + 7 jours, `echecs_consecutifs` + 1 |

- **À 2 échecs consécutifs**, le niveau perd 1 et `echecs_consecutifs` revient à 0.
- **Si le niveau passe sous 2** : `prochaine_verif: null`.

**Ne jamais changer** un `id` ni réécrire les anciennes preuves.

### 5.4 Cartes (`modules/<module>/cartes.yaml`, ajout en fin de fichier)

**Cartes d'erreurs.** Une carte par erreur ou confusion révélée (note 0 ou 1), si elle vaut d'être retenue.
- `id: <module>-eNNN` : numéro libre suivant dans ce module. Le module est celui de la compétence.
- `tags: [erreur]` et `competence: <id>`.
- **Recto** : une question qui vise précisément la confusion.
- **Verso** : la réponse juste, en 1 à 3 lignes.
- **Source** : la source de la question (`source` dans `questions.yaml`), mise en forme « Auteur, Titre, section — URL ».

**Cartes de cours manquantes.** Une notion de la séance n'a pas de carte ? (Chercher par `competence` dans `cartes.yaml`.)
- **La tirer de la source**, jamais de mémoire : ouvrir la section ou les pages exactes indiquées par la fiche et le catalogue.
  - HTML : WebFetch sur l'URL.
  - PDF de `bibliotheque/` : Read avec `pages`, sur le PC.
- `id: <module>-cNNN`, `tags: [essentiel]` ou `[complement]`, `seance: <n>` (la séance du jour).
- **Règles de rédaction** (ARCHITECTURE §8) :
  - une idée par carte ;
  - recto formulé comme une question précise ;
  - maths en `\( … \)` et `\[ … \]` ;
  - code en `<code>`/`<pre>` ;
  - pas de liste à apprendre en bloc.
- **En YAML**, écrire ces textes entre apostrophes simples, ou en bloc `|`, à cause des `\`.
- **Source inaccessible** (en cloud, PDF absent) : ne rien inventer. Noter « carte à faire au prochain passage sur le PC » dans `## Mises à jour`.

### 5.5 Planning : ajustement **local** seulement
- **Séance `partielle`, ou notion mal acquise** (note moyenne < 1 sur une compétence) : ajuster la `tache` de la **prochaine** séance du même module cette semaine. Par exemple : terminer la séance, ou passer en `consolidation`.
- **Ne jamais** réorganiser toute la semaine (c'est le rôle du check-in).
- **Ne jamais** ajouter d'heures au-delà de la capacité.
- **Ne jamais** comprimer une séance.
- Consigner l'ajustement dans le journal (`planning : …`).

## 6. Commandes (une par une, depuis la racine)

### 1. Anki : avancer la progression, puis exporter (PC)
Les cartes d'une séance ne deviennent exportables **qu'une fois la séance faite**. On l'indique avec `--avancer <module>:<n>`, où `n` est le numéro de la séance de la fiche qui vient d'être étudiée. Plusieurs couples se séparent par des virgules. Une séance `partielle` compte comme faite si son contenu de cours a été vu.

- **Sur le PC** : `python tools/anki.py --avancer <module>:<n>`. Le script exporte les cartes exportables absentes de `anki/registre.csv` (les cartes d'erreurs sont toujours exportables) vers `anki/paquets/nouvelles-<date>.apkg`, puis complète le registre.
  - Si le paquet n'est pas vide, ouvrir **le fichier indiqué par la sortie** du script. Il peut porter un suffixe `-1` si un paquet existe déjà ce jour-là.
  - **Git Bash / cmd** : `start "" "anki\paquets\<fichier>.apkg"`.
  - **Outil PowerShell** : `Start-Process "anki\paquets\<fichier>.apkg"`.
- **En session cloud** : `python tools/anki.py --avancer <module>:<n> --sans-paquet`. La progression est enregistrée, et le paquet sera construit au prochain `anki.py` lancé sur le PC. Dire : « export au prochain passage sur le PC ».
- **Log rapide** : avancer la progression de la même façon. Les cartes de la séance sont exportées même sans questions.

### 2. `NOW.md`
`python tools/now.py`

### 3. Vérification
`python tools/check.py`. En cas d'erreur, corriger et relancer. **Pas de commit tant qu'il échoue.**

### 4. `git add`, avec des chemins explicites
- `journal/<date>.md` ;
- `state/semaine.yaml` et `state/competences.yaml` ;
- `modules/<module>/cartes.yaml` (et ceux des autres modules touchés) ;
- `anki/registre.csv` et `anki/progression.yaml` ;
- `NOW.md` ;
- sur le PC : `labs/`, le travail du jour de l'utilisateur.

### 5. Commit
`git commit -m "debrief: <date>"`. **Un seul commit.**

### 6. Push
`git push origin main`.

## 7. Clore (3 à 5 lignes)

- Le score.
- Les niveaux qui ont bougé.
- Ce qui est à revoir.
- La prochaine séance, d'après `NOW.md`.
- Le rappel « import Anki puis révisions », sur le PC.
- Demain : nouvelle conversation.
