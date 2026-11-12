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
3. Le rythme (section « Échéance ») : exercices réussis seul sur l'objectif, nombre requis par semaine contre nombre observé, date de fin projetée, et l'alerte s'il y en a une.

## 3. Dérouler la séance

1. **Anki d'abord** (hors du temps de travail) : donner les deux recherches de `NOW.md`, chacune à coller dans son propre paquet filtré (Outils → Créer un paquet filtré) : « cours, à apprendre » et « exercices à revoir ». Rappeler `is:due` pour les révisions.
2. **Cours (30 min)** : les notions de « Cours » et de « À consolider » de `NOW.md`. Lire seulement leurs entrées de `state/comprehension.yaml` (`python -I -c "import yaml,sys; d=(yaml.safe_load(open('state/comprehension.yaml',encoding='utf-8')) or {}).get('notions') or {}; [print(i, d.get(i)) for i in sys.argv[1:]]" <ids>`) et ses lignes `style`. Une notion marquée « déjà vu : <niveau> (via `<id>`) » a été travaillée sous l'autre id, dans une autre matière : lire l'entrée de `<id>` et partir de là (vérifier ce qui était fragile), sans tout remesurer. Ce que l'utilisateur dit à voix haute est la donnée principale : une bonne réponse sur un raisonnement confus est une alerte. Pour chaque notion :
   - **Mesurer d'abord** : il explique ce qu'il en comprend, avec ses mots. Encadrer où ça s'arrête par une question à la fois : ce qu'il tient (plancher), ce qui casse (plafond). Ne pas réenseigner ce qu'il tient.
   - **Enseigner** à partir de ce qu'il tient, une étape de raisonnement à la fois, chacune motivée (pourquoi on en a besoin, comment on aurait pu la trouver). Après chaque étape, une question de contrôle qui fait appliquer, pas répéter. Une confusion se répare avant d'aller plus loin. Le but : que la notion lui paraisse évidente et qu'il sache d'où elle vient.
   - **Répondre à ses questions** en partant de sa `vision`, de ses confusions et liens manquants connus, et dans son `style`. Une question est aussi une donnée : elle montre où sa compréhension s'arrête.
   - Toujours appuyé sur le poly (fichier, page) : jamais un énoncé de mémoire seule.
   - Ne rien écrire pendant la séance : le debrief, dans cette conversation, relit les échanges.
3. **Exercices** (règle du 12/11/2026 : aller vite), dans l'ordre de `NOW.md` : annale, bloc, puis les **reprises avec Claude** en fin de séance.
   - **Il travaille seul.** Pas d'échange, pas de photo au fil de l'eau. Bloqué, il lit le corrigé lui-même (page dans `NOW.md`). Répondre seulement à ses questions (aide graduée s'il la demande, `CLAUDE.md`). Une reprise marquée « **seulement Q2 (…)** » ne porte que sur ces questions : lui rappeler la parenthèse avant qu'il commence.
   - **À la fin**, il envoie en une fois la rédaction des exercices **nouveaux** ; pour une reprise, seulement le résultat.
   - **Correction rapide**, exercice par exercice : l'endroit précis de chaque erreur, classée **coquille / petite erreur / vraie faute**, puis la catégorie proposée (reussi, presque, aide, non_fait). Ne rien faire refaire, ne pas débattre. Ne jamais valider une erreur par gentillesse.
   - **Entre `reussi` et `presque`, il tranche** : son verdict est enregistré. `aide` et `non_fait` restent ton jugement.
   - **Bloqué ou pas compris** seulement : 5 min au plus, l'étape exacte du blocage et comment l'idée se trouvait. Rien pour un exercice réussi ou presque.
   - Noter pour le debrief : catégorie, temps, coquilles et points d'attention de chaque rédaction (ils vont sur la carte).
   - **Reprises seul dans Anki** (section de `NOW.md`) : il les fait hors séance, sans Claude. S'il dit « X réussi, Y raté », l'enregistrer au debrief (raté = `aide` palier 4 : la reprise revient alors avec Claude).
4. **Fin de séance** : proposer le debrief (« debrief » ou « log rapide : … »), dans cette même conversation.

## 4. Cas particuliers

- Séance interrompue puis reprise le même jour : relancer `plan.py seance`, le plan tient compte de ce qui est déjà enregistré.
- Plusieurs jours sans travailler : rien à rattraper à la main, les exercices non faits et les cartes non apprises reviennent dans le plan.
- Marge négative : les annales de Paris Cité s'ouvrent plus tôt et ne sont jamais coupées. Le secondaire et l'exotique n'entrent pas dans le reste à faire.
