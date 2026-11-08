---
name: seance
description: "Début de séance de maths (L3). Calcule le plan de maintenant d'après ce qui a réellement été fait, le présente en 3 lignes, puis déroule le cours, les exercices et le debrief dans la même conversation. À utiliser quand l'utilisateur dit « on commence », « séance », « travail du jour », « je commence à travailler » ou « qu'est-ce que je fais aujourd'hui »."
---

# Début de séance

- **Principe** : on travaille n'importe quel jour, à n'importe quelle heure. Le plan se calcule **maintenant**, d'après les résultats réellement enregistrés et les cartes réellement apprises dans Anki. Un jour `off` du calendrier ne bloque rien. Ce qui n'a pas été fait revient tout seul.
- **Modèle conseillé** : Sonnet 5.5, effort high.
- **Une conversation par séance** : cours, exercices, puis debrief (skill `debrief`).

## 1. Calculer le plan

1. Anki doit être ouvert (AnkiConnect lit les cartes déjà apprises). S'il est fermé, le plan estime les cartes et le dit sur une ligne de `NOW.md` : « Anki fermé : cartes estimées ».
2. `python tools/plan.py seance` (depuis la racine). Il écrit `NOW.md`, mémore la séance dans `state/seance.yaml`. Il ne modifie jamais Anki.
3. Lire `NOW.md`. Ne rien recalculer de tête, ne jamais l'éditer à la main.

## 2. Présenter en 3 lignes

1. Le dernier jour travaillé (ligne « Dernier jour travaillé » de `NOW.md`) et ce qui est revenu (reprises, exercices non faits).
2. Le bloc du jour : matière, sous-chapitre, nombre d'exercices et minutes.
3. La marge à l'échéance (section « Échéance »), et l'alerte si elle est négative.

## 3. Dérouler la séance

1. **Anki d'abord** (hors du temps de travail) : donner la recherche « à apprendre » de `NOW.md` (à coller dans Outils → Créer un paquet filtré) et rappeler `is:due` pour les révisions.
2. **Cours (30 min)** : les notions listées, aux pages données. Poser des questions de compréhension si l'utilisateur le demande.
3. **Exercices** : dans l'ordre de `NOW.md`. Aide graduée seulement sur demande (règles de `CLAUDE.md`). Noter pour chaque exercice le palier d'aide atteint et ce qui a bloqué, pour le debrief.
4. **Fin de séance** : proposer le debrief (« debrief » ou « log rapide : … »), dans cette même conversation.

## 4. Cas particuliers

- Séance interrompue puis reprise le même jour : relancer `plan.py seance`, le plan tient compte de ce qui est déjà enregistré.
- Plusieurs jours sans travailler : rien à rattraper à la main, les exercices non faits et les cartes non apprises reviennent dans le plan.
- Marge négative : les annales de Paris Cité s'ouvrent plus tôt et ne sont jamais coupées. Le secondaire et l'exotique n'entrent pas dans le reste à faire.
