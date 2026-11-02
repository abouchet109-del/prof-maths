---
name: checkin
description: "Check-in hebdomadaire. Il fait le bilan de la semaine, recalcule les jalons, archive le bilan, écrit le plan de la semaine suivante et vérifie la préparation des modules. Le premier check-in du mois devient la revue mensuelle. Il inclut aussi le protocole de reprise après une pause. À utiliser quand l'utilisateur dit « check-in », « bilan de la semaine », « plan de la semaine prochaine », « revue mensuelle », « je reprends » ou « je suis de retour ». Aussi le dimanche après la séance de 9h-11h, à la dernière séance de la semaine si le week-end saute, et lors de l'exécution planifiée du check-in."
---

# Check-in hebdomadaire (et revue mensuelle)

## Quand et comment

- **Moment** : le dimanche, juste après la séance de 9h-11h (environ 20 min). Il **remplace le debrief du jour**.
  - Si le week-end saute : à la dernière séance de la semaine.
  - Si l'exécution planifiée a raté, l'utilisateur tape « check-in » et on fait tout.
- **Modèle** : Sonnet 5.5, effort high.
- **Revue mensuelle** : si c'est le premier check-in du mois (voir §7), recommander **Opus 5.5, effort high** avant de commencer. L'utilisateur décide ; on continue sinon.
- **Exécution planifiée**, sans utilisateur présent :
  - **ne rien faire et s'arrêter** si la date précède `debut` dans `state/dispo.yaml`, ou si `journal/bilan-AAAA-Www.md` existe déjà pour la semaine **sans** la mention « brouillon ». C'est le cas quand le check-in a déjà été fait, par exemple le vendredi d'un week-end sauté ;
  - **test à blanc** (le message de déclenchement contient « TEST À BLANC ») : vérifier seulement l'accès au repo et à `main`, puis lancer `python tools/check.py` et `python tools/cal.py semaine <date>`, et rendre compte. **Rien n'est écrit, commité ni poussé** ;
  - sinon, faire seulement les §1 à §3 ;
  - écrire `journal/bilan-AAAA-Www.md` avec en tête « brouillon — à compléter au check-in » ;
  - lancer `check.py` ;
  - commit `checkin: AAAA-Www (brouillon)`, puis push sur `main`.
  - Ensuite, quand l'utilisateur lance le check-in, **partir du brouillon** au lieu de tout refaire.
- **Retour après une pause** : appliquer d'abord le §8.

## 1. Lire (le minimum)

- `NOW.md` et `state/semaine.yaml` (en entier, il est court).
- Les journaux de la semaine : seulement les lignes de `## Séance` et `## Mises à jour`, par recherche. **Pas les journaux en entier.**
- Les exceptions de `state/dispo.yaml` qui touchent la semaine suivante.
- Le dernier `journal/bilan-*.md`, pour comparer (section « Décisions » seulement).

## 2. Bilan de la semaine

1. **Enregistrer la séance du jour**, comme un log rapide : statut, `heures_reelles` et `journal/<date>.md` (`## Séance`). Pas de debrief complet.
2. **Calculer** :
   - les heures prévues (séances non `rattrapage`) et les heures faites (somme des `heures_reelles`) ;
   - le nombre de séances par statut ;
   - les rattrapages, et ce qui reste « À rattraper ».
3. **Relever** :
   - les **compétences qui ont bougé** (lignes « compétences : » des journaux) ;
   - le **maintien dû** dans les 7 jours (`NOW.md`) ;
   - les **traces manquantes** : séance `faite` sans journal, debrief sauté, log rapide non suivi d'un rappel. Les signaler sans reproche.
4. **Un seul message** à l'utilisateur, avec 4 questions courtes :
   - Anki : à jour ? Des cartes qui résistent ?
   - Forme /5 et motivation /5 ?
   - Du travail libre non consigné (Kaggle, vidéo…) ? Il est crédité.
   - Des contraintes connues pour la semaine prochaine (ESSEC, sorties, partiels) ?
   - Les contraintes données se traitent comme dans le skill `imprevu`, §3, mais directement dans le nouveau plan.
5. **Signaux à surveiller** :
   - forme ou motivation ≤ 2 deux semaines de suite ;
   - Anki en retard ;
   - un rituel inutilisé 3 semaines de suite.
   Proposer alors un allègement : suspendre les cartes `complement`, passer en mode minimal, supprimer le rituel. **L'utilisateur tranche.**

## 3. Jalons

1. Lancer `python tools/cal.py jalons`.
2. Pour chaque jalon `a_venir` ou `a_risque`, mettre à jour `heures_restantes_estimees` dans `state/jalons.yaml`. L'estimation se fait ainsi :
   - les séances restantes des modules du critère (`ROADMAP.md`, fiches), × 2 h ;
   - le **facteur de vitesse** n'intervient qu'à partir de la **6e semaine de données**, borné entre 0,7 et 1,5.
3. Mettre à jour le `statut` :
   - `atteint` si le `critere` est rempli (vérifier les niveaux dans `competences.yaml`) ;
   - `a_risque` selon la suggestion de `cal.py` ;
   - `rate` si la date est passée.
4. **Si un jalon est à risque**, proposer 2 ou 3 arbitrages chiffrés :
   - couper du contenu `complement` ;
   - décaler le jalon (s'il est `souple`) ;
   - remplacer une ressource par une plus courte.
   **On réduit le contenu, on ne comprime jamais les séances.** L'utilisateur tranche. Appliquer sa décision (`jalons.yaml`, `ROADMAP.md`) et la consigner dans le bilan.

## 4. Archiver la semaine : `journal/bilan-AAAA-Www.md`

```markdown
# Bilan AAAA-Www (du … au …)
## Heures
- prévues : X h · faites : Y h · rattrapages : Z h · travail libre : …
## Séances
| id | type | module | statut | heures |
## Compétences
- <id> : <avant> → <après> ; maintien dû : …
## Anki, forme
- Anki : … · forme x/5 · motivation y/5
## Jalons
- <id> : marge … h · statut …
## Décisions
- …
## Semaine suivante
- capacité … h · modules … · préparation : ok / lancée
```

Ce fichier conserve le détail de la semaine écoulée, que le nouveau `semaine.yaml` va remplacer.

## 5. Plan de la semaine suivante : `state/semaine.yaml`

1. Lancer `python tools/cal.py semaine <lundi suivant>`. On obtient les créneaux datés, les exceptions et la capacité.
2. **Choisir le contenu** :
   - les modules de `ROADMAP.md` pour cette semaine ;
   - dans chaque fiche, les prochaines `### Séance n` non faites ;
   - les séances `deplacee` non rattrapées ;
   - une `consolidation` pour toute compétence fragile (note moyenne < 1, ou niveau perdu) ;
   - les re-tests dus.
3. **Règles de placement** :
   - une séance par créneau ML ; **14 h planifiées à 100 %**, et jamais plus que la capacité ;
   - semaine `quota` : exactement les heures du quota, dans les créneaux ML ou les créneaux libres ;
   - **entrelacer** maths et code dans la semaine ;
   - suivre l'ordre des séances de chaque fiche ;
   - l'**examen blanc** (`type: examen`, dans les 14 h, 1 h-1 h 30) toutes les 6 à 8 semaines, à partir de la semaine 6 environ ;
   - après une pause : semaine allégée (§8).
4. **Écrire le fichier entier**, au format de `docs/FORMATS.md` :
   - `semaine`, `du`, `au` ;
   - `seances`, avec pour chacune : `id` `<date>-<lettre>`, `date`, `creneau`, `type`, `module`, `tache`, `ressources` (ex. `modules/<m>/fiche.md#seance-<n>`), `livrable` ;
   - `statut: prevue`, `heures_reelles: null`, `hors_creneau: false`, `remplace: null`.
5. **Montrer le plan** en tableau compact (jour, créneau, type, module, tâche). L'utilisateur peut l'ajuster avant le commit.

## 6. Modules préparés ?

1. Pour chaque module du nouveau plan, vérifier que ces éléments existent :
   - `modules/<m>/fiche.md`, avec les `### Séance n` planifiées ;
   - `questions.yaml` et `cartes.yaml` ;
   - pour les séances d'exercices de code : `exercices/` et ses tests.
2. S'il manque quelque chose :
   - le noter dans le bilan ;
   - **après** le commit du check-in, lancer le skill `preparation`. Il fait son propre commit `prep:`.
   - Si le quota est juste, proposer une session dédiée (Sonnet 5.5, high) avant la première séance concernée.

## 7. Revue mensuelle (premier check-in du mois)

**Comment la reconnaître** : le fichier `journal/resume-<mois précédent>.md` n'existe pas encore. Modèle : Opus 5.5, effort high.

1. **Résumé du mois précédent.** Écrire `journal/resume-AAAA-MM.md` (40 lignes au plus) à partir des **bilans** du mois, pas des journaux quotidiens :
   - heures ;
   - compétences et niveaux atteints ;
   - jalons ;
   - décisions ;
   - points faibles.
2. **Roadmap.** Ajuster `ROADMAP.md` et détailler les 6 à 8 semaines suivantes.
3. **Échéances.** Revérifier les échéances proches de `ECHEANCES.md` (WebFetch sur les sources officielles) et noter la date de vérification. Ne jamais inventer : si l'information n'est pas trouvée, écrire « à vérifier ».
4. **Compétences.** Ajouter la **vague suivante** dans `state/competences.yaml` (`niveau: null`, `cible`, `modules`).
5. **Jalons.** Recaler les jalons après une pause. À partir de la 6e semaine de données, calculer le facteur de vitesse.
6. **Rappels stratégiques** (`docs/ARCHITECTURE.md` §14) : candidatures M1, lettres de recommandation, décision MLE ou recherche en juin 2027.

## 8. Reprise après une pause (« je reprends », semaines mortes, maladie)

**Déclencheurs** : l'utilisateur le dit, ou au moins 7 jours sans séance faite (exception `off`, séances sautées).

- **Aucune culpabilisation.** Une phrase d'accueil, puis on avance.

1. **Mini-diagnostic de 20 min.**
   - 5 ou 6 questions tirées des banques, sur les compétences de niveau ≥ 2, en priorité celles dont la `prochaine_verif` est la plus en retard. Une question par compétence.
   - Même déroulé que le debrief (skill `debrief`, §3 à §5.3) : points attendus écrits d'abord dans `journal/<date>.md`, questions 2 par 2, notes, règles de maintien.
2. **Première semaine allégée.**
   - Exception `{du, au, type: quota, heures: 10, note: "reprise", statut: confirme}` dans `state/dispo.yaml`.
   - Les premières séances servent au rappel et à la consolidation.
3. **Anki.** Reprendre progressivement ; suspendre les cartes `complement` s'il y a un gros retard.
4. **Jalons.** Ils sont recalés à la revue suivante. Si un jalon `dur` est menacé, faire tout de suite les arbitrages du §3.
5. **Si la reprise tombe en milieu de semaine et que `semaine.yaml` est périmé**, faire les §5 et §6 pour la semaine en cours.

## 9. Vérifier, régénérer, commiter

Les commandes se lancent **une par une** :

1. `python tools/check.py`. Corriger jusqu'à ce qu'il passe.
2. `python tools/now.py`.
3. `git add`, avec des chemins explicites :
   - `state/` ;
   - `journal/bilan-AAAA-Www.md` et `journal/<date>.md` ;
   - `NOW.md` ;
   - selon le cas : `ROADMAP.md`, `ECHEANCES.md`, `journal/resume-AAAA-MM.md`, `labs/` (PC).
4. Commit :
   - `git commit -m "checkin: AAAA-Www"` ;
   - pour la revue mensuelle : `git commit -m "revue: AAAA-MM (checkin AAAA-Www)"`.
5. `git push origin main`.

**Conclure en 3 à 5 lignes** :
- heures faites / prévues ;
- ce qui a progressé ;
- les décisions prises ;
- la première séance de la semaine (`NOW.md`) ;
- la préparation : faite, ou à lancer.
