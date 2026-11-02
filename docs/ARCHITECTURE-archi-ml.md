# Architecture du système d'apprentissage

Version 1, validée par l'utilisateur le 30/10/2026. Elle a été conçue avec lui, puis revue par une critique indépendante (voir §17). Les contraintes personnelles sont dans `docs/PROFIL.md`, les formats de fichiers dans `docs/FORMATS.md`, le plan de construction dans `docs/PLAN_CONSTRUCTION.md`.

## 1. Objectif

Amener l'utilisateur, en ~18 mois et à 14 h par semaine, à **maîtriser réellement** le ML (en ingénierie comme en recherche). Il doit pouvoir :
- décrocher le meilleur M1 math-info possible ;
- obtenir une césure (stages à partir de septembre 2028) ;
- viser le MVA.

Le système fournit trois choses :
1. **une roadmap sourcée** : cours, exercices, projets ;
2. **un suivi** qui s'adapte à ce qui est fait et maîtrisé ;
3. **un tuteur** (Claude) qui vérifie que les notions sont assimilées.

## 2. Principes

1. **Le repo GitHub est la seule mémoire.** Les conversations sont jetables : n'importe quelle nouvelle session reprend tout depuis les fichiers.
2. **L'utilisateur n'édite jamais les fichiers d'état.** Il parle à Claude, et Claude met à jour. L'utilisateur n'écrit que son propre travail, dans `labs/` et dans ses repos de projets.
3. **Le code calcule, Claude juge.** Les dates, heures, capacités, vérifications, paquets Anki et `NOW.md` sont produits par des scripts déterministes. Placer les séances, prioriser, évaluer et arbitrer relève du jugement de Claude.
4. **Une preuve pour chaque niveau.** Un niveau de maîtrise ne monte que sur preuve : debrief réussi, tests passés, examen, projet.
5. **Des heures fixes, un contenu qui s'adapte.** Les 14 h sont des créneaux fixes. C'est le contenu qui avance plus ou moins vite, et ce sont les jalons qui sont recalculés.
6. **Sobriété.** Le système coûte peu de temps (moins de 30-35 min par semaine d'administration, hors debriefs) et peu de tokens (voir §10). Tout rituel inutilisé 3 semaines de suite est supprimé.
7. **Tout est sourcé.** Chaque ressource, fiche, carte, question ou échéance indique sa source, avec un lien, la section et la page quand c'est possible.

## 3. Surfaces et sessions

- **PC : Claude Code dans VS Code (extension).** C'est le poste principal, avec le repo cloné en local. Claude voit le code de l'utilisateur sans qu'il ait à pousser, lance les tests, et construit puis ouvre le paquet Anki.
- **iPhone : app Claude, sessions cloud** sur le même repo. Elle sert aux changements de planning et parfois aux debriefs.
- **Une conversation par jour de travail.** Elle s'ouvre au début de la séance, sert aux imprévus et se termine par le debrief. Le lendemain, on en ouvre une nouvelle.
  - Raison : avec l'abonnement, le cache de prompt dure 1 h. Une longue conversation est donc relue entièrement à chaque reprise, ce qui consomme environ 2 à 3 fois plus de quota.
- **Les mêmes règles s'appliquent partout.** `CLAUDE.md` et les skills sont lus aussi bien par l'extension que par les sessions cloud.

## 4. Fonctionnement

### Une journée type
1. **Avant la séance**, l'utilisateur lit `NOW.md` dans VS Code ou dans l'app GitHub. Ça ne coûte aucun token.
   - Il y trouve : le créneau, la tâche, les ressources exactes (chapitre, section, pages, vidéo et minutage), l'exercice et le livrable attendu.
2. **Pendant les 2 h**, il travaille sur son PC.
   - S'il bloque, il demande à Claude dans la conversation du jour. Claude applique l'aide graduée (§6.4), et le niveau d'aide est noté.
3. **En fin de séance, le debrief (10-15 min, hors des 14 h).** Le protocole complet est dans le skill `debrief`. Claude :
   - pose des questions 2 par 2 et corrige aussitôt ;
   - met à jour les compétences et le journal ;
   - ajoute les cartes Anki de la séance (cours et erreurs) ;
   - ajuste localement la suite ;
   - régénère `NOW.md`, vérifie le tout, fait un commit et pousse.
4. **Anki (hors des 14 h).** Il importe le petit paquet de nouvelles cartes (un double-clic), puis fait ses révisions du jour.
5. **Log rapide**, au plus 2 fois par semaine, les soirs de fatigue. Une ligne (« fait 2 h, ch. 3, exos 1-4 »), sans questions. Le debrief suivant commence par le rappel de cette séance.

### Un imprévu (souvent depuis l'iPhone)
- L'utilisateur écrit par exemple « jeudi 16h30 je ne peux pas ».
- Claude déplace **seulement cette séance** : dans un créneau libre (tampon, à confirmer avec l'utilisateur) ou à la semaine suivante.
- Il met à jour `state/`, vérifie, régénère `NOW.md` et pousse. Ça prend environ 1 minute (protocole : skill `imprevu`).

### Chaque semaine : le check-in
- Il a lieu le dimanche, juste après la séance de 9h-11h, et dure environ 20 min (il remplace le debrief ce jour-là). Protocole : skill `checkin`.
- Une tâche planifiée prépare le bilan juste avant. Il couvre :
  - les heures prévues et les heures faites ;
  - l'évolution des compétences ;
  - les jalons (prévision par `cal.py`) ;
  - l'état d'Anki, sur déclaration de l'utilisateur.
- Claude produit ensuite le plan de la semaine suivante et vérifie que les modules sont **préparés** (fiches, questions, cartes). S'ils ne le sont pas, il lance la préparation (skill `preparation`).
- **Si le week-end saute**, le check-in se fait à la dernière séance de la semaine.

### Chaque mois : la revue (Opus)
Le premier check-in du mois devient une revue. Elle :
- ajuste la roadmap ;
- revérifie les échéances ;
- ajoute la vague suivante de compétences ;
- détaille les 6 à 8 semaines suivantes ;
- écrit le résumé mensuel du journal.

### Toutes les 6 à 8 semaines : l'examen blanc
- Il dure 1 h à 1 h 30, **dans** les 14 h. Il comprend du code chronométré et des questions cumulatives, sans notes.
- Il est corrigé **dans un contexte séparé** : un sous-agent qui ne voit que la question, le barème et la réponse.
- Si l'écart entre les niveaux tirés des debriefs et ceux de l'examen dépasse 1 niveau, on recalibre.

## 5. Pédagogie : ce que contiennent les 14 h

**Anki ne remplace jamais le cours.** Les 14 h servent à **apprendre** (cours), **pratiquer** (exercices de maths et de code) et **construire** (projets). Anki, hors des 14 h, sert seulement à **retenir** ce qui a été appris en séance.

### Types de séance
| Type | Contenu |
|---|---|
| `cours` | Lecture active ou vidéo, avec les dérivations refaites sur papier, puis 2-3 exercices d'application immédiats |
| `exercices` | Maths (dérivations, preuves courtes, calculs de gradients, MLE…) et code (implémenter « from scratch », avec des tests écrits à l'avance) |
| `projet` | Projets du portfolio, en suivant un cahier des charges |
| `article` | Lecture et reproduction d'articles de recherche (phases avancées) |
| `consolidation` | Reprise d'une notion mal acquise au debrief |
| `examen`, `diagnostic` | Évaluation |
| `installation` | Mise en place de l'environnement |
| `rattrapage` | Séance déplacée (tampon) |

### Structure type d'une séance de 2 h
1. **5 min** : rappel actif de la séance précédente, sans notes.
2. **60 à 70 min** : apprentissage actif (lire, refaire les calculs, prendre des notes avec ses propres mots).
3. **40 à 50 min** : application immédiate (exercices, code avec tests).
4. **5 min** : écrire en 3 lignes « compris / pas compris / question ».
5. **Puis le debrief** (hors des 14 h).

### Dosage indicatif, qui évolue avec les phases
| Phase | Cours | Exercices | Projets et articles |
|---|---|---|---|
| Phases 0-1 (fondations) | ~40 % | ~40 % | ~20 % |
| Phase 2 (deep learning) | ~35 % | ~35 % | ~30 % |
| Phases 3 et suivantes | ~25 % | ~25 % | ~50 % |

### Principes appliqués
- **Récupération active** : debrief, rappel en début de séance, Anki.
- **Espacement** : maintien des compétences, Anki.
- **Entrelacement** : alterner maths et code dans la semaine.
- **Difficultés désirables** : essayer avant de demander un indice.
- **Implémenter avant d'utiliser une bibliothèque**.
- **Application dans la même séance**.
- **Pratique délibérée**, avec des tests comme critère objectif.

### Format de travail
- **Code** : des fichiers `.py` avec des cellules `# %%` (mode interactif de VS Code), plutôt que des `.ipynb`. Le diff reste lisible, le code est testable, et ça coûte peu de tokens.
- **Notebooks** : ils restent permis pour l'exploration, mais toujours enregistrés **sans sorties**.

## 6. Évaluation de la maîtrise

### 6.1 Niveaux, par compétence
| Niveau | Signification | Preuve exigée |
|---|---|---|
| 0 | Jamais vu | — |
| 1 | Lu, cours suivi | Séance de cours faite |
| 2 | Sait expliquer : définitions, intuition, pourquoi | Questions de cours et de « pourquoi » réussies au debrief (note ≥ 1,5/2 en moyenne) |
| 3 | Sait implémenter ou appliquer seul | Exercice réussi avec une aide ≤ 1 (tests passés) **et** re-test différé réussi 2-3 semaines plus tard |
| 4 | L'utilise dans un projet et justifie ses choix | Projet livré, avec des choix techniques défendus au debrief ou à l'examen |

- **On redescend d'un niveau** après 2 échecs consécutifs aux questions de maintien.
- **Ensemble de départ** : 25 à 30 compétences pour les 4 premiers mois. On en ajoute une vague à chaque revue mensuelle.

### 6.2 Le debrief (protocole détaillé dans le skill `debrief`)
1. **Préparer d'un coup** 4 à 6 questions, tirées des banques `modules/*/questions.yaml` et du travail du jour (diff) :
   - 1 rappel différé, sur la séance précédente ;
   - 2 questions de cours ;
   - 1 à 2 « pourquoi » sur le code ou le raisonnement du jour ;
   - 1 question de maintien sur une compétence échue.
2. **Écrire les points attendus** dans le journal, **avant** de poser les questions, en une seule écriture.
3. **Envoyer les questions 2 par message.** Corriger explicitement après chaque réponse. Une relance au plus.
4. **Noter** chaque réponse 0, 1 ou 2 par rapport aux points attendus.
5. **Mettre à jour** :
   - les compétences (niveaux, preuves, prochaine vérification) ;
   - le statut de la séance et les heures réelles ;
   - les cartes d'erreurs ;
   - le planning, mais seulement localement.
6. **Lancer** `anki.py`, `now.py`, puis `check.py`. Faire **un seul commit**, puis pousser.

### 6.3 Maintien
- Chaque compétence de niveau ≥ 2 a une date de `prochaine_verif`.
- Intervalles successifs : **1, 3, 8, puis 16 semaines**.
- Un échec ramène l'intervalle à 1 semaine. Deux échecs consécutifs font perdre un niveau.

### 6.4 Aide graduée (notée dans le journal)
| Niveau d'aide | Ce que Claude donne |
|---|---|
| 0 | Aucune aide |
| 1 | Un indice conceptuel |
| 2 | Un indice précis ou du pseudo-code |
| 3 | Une solution partielle |
| 4 | La solution complète, seulement si l'utilisateur la demande explicitement |

- L'utilisateur doit toujours **essayer avant** de recevoir un indice.
- Un exercice réussi avec une aide ≥ 2 ne prouve pas le niveau 3.

### 6.5 Règles d'honnêteté (validées par l'utilisateur)
- Pendant les exercices et les debriefs : **pas de notes**, **pas de retour en arrière** dans la conversation.
- **Pas d'autocomplétion IA** : elle est coupée dans ce repo par `.vscode/settings.json`. Si elle est utilisée quand même, elle compte comme une aide.
- Une **banque de questions** est réutilisée d'une fois sur l'autre, pour que les niveaux restent comparables.
- **Points attendus écrits avant** la réponse.
- **Examens blancs** corrigés hors contexte.

## 7. Planification

- **Créneaux.** 7 créneaux ML fixes de 2 h (`state/dispo.yaml`), avec des exceptions datées : `off` (jour ou semaine sautée) ou `quota` (nombre d'heures imposé, par exemple 7 h ou 28 h).
- **Planification en vagues :**
  - Créneaux précis sur la semaine en cours (`state/semaine.yaml`, placés par Claude au check-in).
  - Liste de modules pour les 6 à 8 semaines suivantes (`ROADMAP.md`).
  - Au-delà : seulement les jalons (`state/jalons.yaml`).
- **Imprévu.** Il ne déclenche qu'un **déplacement local** : rattrapage dans le tampon (sans horaire fixe, placé dans un créneau libre déclaré et confirmé par l'utilisateur), ou report à la semaine suivante. La semaine n'est réorganisée en entier qu'au check-in.
- **Tampon.** 6 h par semaine, partagées avec les autres activités de l'utilisateur. Il est réservé en priorité aux imprévus ESSEC et aux sorties ; il ne sert au ML que pour rattraper.
- **Prévision des jalons.** Une fois par semaine, `cal.py jalons` compare la capacité restante (heures) à `heures_restantes_estimees`, mise à jour par Claude. Si un jalon est à risque, Claude propose des arbitrages (couper, décaler, remplacer) et **l'utilisateur tranche**. La règle : on réduit le contenu, on ne comprime jamais les séances.
- **Facteur de vitesse** (rapport temps réel / temps estimé) : il ne s'utilise qu'à partir de la 6e semaine de données. Il est calculé chaque semaine et borné entre 0,7 et 1,5.

## 8. Anki

### Rôle
- **Retenir** ce qui a été appris en séance.
- Les cartes **couvrent tout le cours**, avec l'étiquette `essentiel` ou `complement`. S'y ajoutent les cartes d'**erreurs** issues des debriefs.

### Fabrication
- Claude fabrique les cartes **en lisant la source réelle** (pas de mémoire). Chaque carte cite sa source : auteur, titre, section, page ou URL.
- **Règles de rédaction :**
  - une seule idée par carte (principe d'information minimale) ;
  - recto formulé comme une question précise ;
  - maths en MathJax : `\( ... \)` pour l'inline, `\[ ... \]` pour les blocs ;
  - code en `<code>`/`<pre>` ;
  - pas de listes à mémoriser en bloc.

### Circuit à sens unique, par paquets « delta »
- Les cartes source sont dans `modules/<id>/cartes.yaml`.
- `tools/anki.py` construit **seulement les cartes jamais exportées** : celles qui ne sont pas dans `anki/registre.csv`. Il en fait un `.apkg` dans `anki/paquets/` (non versionné), puis met le registre à jour.
- L'import se fait sur le PC : double-clic, ou bien Claude ouvre le fichier.
- **Anki est maître** des cartes déjà importées : l'utilisateur les corrige et les supprime librement. On ne réexporte jamais tout le paquet.
- Une carte n'est réexportée **que** sur demande explicite (`--reexporter`).
- **Le type de note est figé** : identifiant, champs (`Id`, `Recto`, `Verso`, `Source`), modèles de carte. On ne le modifie jamais, sinon Anki ignore les mises à jour.
- Le **GUID** est dérivé de l'identifiant stable de la carte.
- Raison de ce circuit (vérifiée dans le code d'Anki et de genanki) : un paquet complet réimporté écraserait les corrections, ferait revenir les cartes supprimées et effacerait les étiquettes « marked » et « leech ».

### Réglages recommandés
- **FSRS** activé, rétention visée 0,90.
- Environ 10 nouvelles cartes par jour.

### Charge et suivi
- **Volume attendu** : environ 40 à 60 cartes par semaine, soit environ 15-20 min de révision par jour une fois le rythme installé.
- **Si c'est trop**, l'utilisateur suspend les cartes `complement`.
- **Pendant les semaines mortes** : 5 min par jour, ou une pause assumée.
- **Retour vers Claude** : une seule question au check-in (« à jour ? cartes qui résistent ? »). Claude ne lit pas les statistiques d'Anki.

## 9. Contenu et sources

### Critères de choix
- Gratuit d'abord.
- Référence de niveau universitaire (Stanford, MIT, ENS, Inria…), cohérente avec un dossier de type MVA.
- Récent pour le deep learning.
- Exercices corrigés ou testables.
- En français si la qualité est équivalente.

### Vérification avant l'entrée au catalogue
Pour chaque ressource :
- le lien fonctionne ;
- l'accès et la licence sont notés ;
- le plan des chapitres est relevé, avec sections, URL et pages ;
- la date de vérification est notée.

On n'invente jamais un numéro de page : si on ne le connaît pas, on donne la section et l'URL.

### Où vit le contenu
| Élément | Emplacement |
|---|---|
| Catalogue | `ressources/catalogue.yaml` (format dans `FORMATS.md`), avec une ressource principale et une de secours par sujet |
| Bibliothèque de PDF | `bibliotheque/`, sur le PC uniquement (non versionné, pour ne pas redistribuer de fichiers protégés). Les PDF sont téléchargés une fois. |
| Contenu d'un module | `modules/<id>/` |

Un module contient :
- `fiche.md` : objectifs, compétences visées, découpage en séances avec les lectures exactes, exercices, livrable, points clés, sources ;
- `questions.yaml` : banque de questions avec les points attendus ;
- `cartes.yaml` ;
- `exercices/`, avec des tests pytest écrits à l'avance.

### Préparation
Elle se fait **une fois par semaine**, à l'avance (skill `preparation`, Sonnet). La lecture des sources coûte cher, donc on ne la fait qu'une fois. Les sessions suivantes lisent la fiche, et n'ouvrent la source qu'aux pages nécessaires.

### Familles de sources (candidats, vérifiés à l'étape 6)
- **Python scientifique** : *Python Data Science Handbook* (VanderPlas), *100 NumPy exercises* (Rougier), *The Missing Semester* (MIT).
- **Maths du ML hors L3** :
  - *Mathematics for Machine Learning* (Deisenroth, Faisal, Ong) ;
  - *Convex Optimization* (Boyd & Vandenberghe), en extraits ;
  - les cours de G. Peyré et F. Bach (ENS / Inria).
- **ML classique** : MOOC scikit-learn d'Inria, *ISLP*, notes du cours CS229 (Stanford), *Introduction au Machine Learning* (Azencott, en français).
- **Deep learning** : *Understanding Deep Learning* (Prince), *Neural Networks: Zero to Hero* (Karpathy), *Dive into Deep Learning*, FIDLE (CNRS, en français).
- **Spécialisations** :
  - NLP / LLM : CS224N, cours Hugging Face, CS336 ;
  - vision : CS231n ;
  - RL : Sutton & Barto ;
  - modèles génératifs.
- **Ingénierie** : *Made With ML*, tests, Docker, déploiement.
- **Recherche** : méthode de lecture d'articles, reproduction (format ML Reproducibility Challenge).
- **Entretiens** : livre de Chip Huyen sur les entretiens ML.

### Projets du portfolio
- 5 à 6 projets progressifs, chacun avec un cahier des charges, une grille d'évaluation et la liste « ce que tu dois savoir faire ».
- Chacun vit dans un **repo public séparé**, créé quand le projet devient présentable. Le portfolio vise les recruteurs pour la césure ; les jurys de M1 regardent surtout les notes.

## 10. Économie de tokens (Claude Pro)

1. **Une conversation par jour** (cache de 1 h).
2. **`CLAUDE.md` court** (150 lignes au plus). Les protocoles détaillés sont des **skills**, chargées seulement quand on s'en sert.
3. **Un point d'entrée minuscule** : `NOW.md` (60 lignes au plus).
   - Ne jamais lire tout l'historique : un journal par jour, un résumé par mois.
   - Ne lire `competences.yaml` que pour les compétences concernées.
4. **Préparation hebdomadaire.** Les debriefs réutilisent fiches, questions et cartes sans relire les sources.
5. **Les scripts font le mécanique** : calendrier, vérifications, paquets, `NOW.md`. Aucun token.
6. **Lire des diffs, pas des fichiers entiers.** Le debrief lit `git diff` / `git log -p` du jour dans `labs/`. Pas de sorties de notebook.
7. **Le bon modèle pour chaque tâche** (§11).
8. **Un seul commit par interaction.** Le tableau de bord est republié au plus une fois par semaine (V2).

## 11. Modèles et efforts

| Usage | Modèle et effort |
|---|---|
| Plan du jour, imprévu, log rapide | Sonnet 5.5, low à medium |
| Debrief | Sonnet 5.5, high |
| Check-in et préparation de la semaine | Sonnet 5.5, high |
| Revue mensuelle, correction des examens blancs (sous-agent séparé) | Opus 5.5, high |
| Refonte de la roadmap (rare) | Opus 5.5, max |

Claude signale quand une conversation mériterait un autre modèle.

## 12. Git et intégrité des données

- **Début de session** : `git pull --rebase`.
- **Avant tout commit** : `python tools/check.py`. Si `check.py` échoue, on ne commite pas : on corrige.
- **Un commit par interaction**, préfixé :

  | Préfixe | Usage |
  |---|---|
  | `debrief:` | fin de séance |
  | `imprevu:` | déplacement de séance |
  | `checkin:` | bilan hebdomadaire |
  | `prep:` | préparation de modules |
  | `revue:` | revue mensuelle |
  | `build:` | construction du système |

- **Push direct sur `main`** (autorisé par l'utilisateur). Jamais de force-push.
- **Conflits** : un fichier généré (`NOW.md`) se régénère, il ne se fusionne pas à la main.
- **La tâche planifiée** pousse elle aussi sur `main`. Son prompt le dit explicitement, sinon elle pousserait sur une branche `claude/…`.

## 13. Protocoles de résilience (dans `CLAUDE.md` et les skills)

- **Reprise après une pause** (semaines mortes, maladie) :
  - mini-diagnostic de 20 min ;
  - première semaine allégée ;
  - jalons recalés à la revue suivante ;
  - **aucune culpabilisation**.
- **Mode minimal**, déclenché d'un mot par l'utilisateur : 2 séances dans la semaine et Anki. Le système s'adapte sans reproche.
- **Log rapide** (§4).
- **Travail libre crédité.** Un travail non prévu (un week-end Kaggle, une vidéo) est consigné et compté.
- **Debrief sauté.** Le suivant commence par le rappel de la séance manquée. Le check-in signale s'il manque des traces.
- **Exécution planifiée ratée** (quota, panne) : l'utilisateur tape « check-in » et la session fait tout.

## 14. Cadre stratégique

Les échéances doivent être sourcées dans `ECHEANCES.md` (étape 5).

- **Candidatures M1 (rentrée 2027)** :
  - Mon Master : en 2026, du 17/02 au 16/03 ; le calendrier 2027 n'est pas encore publié.
  - Les M1 d'IP Paris passent par **Mon Master** pour les étudiants français, ou ayant étudié un an en France (vérifié le 30/10/2026).
  - PSL a une campagne propre (en 2026, du 27/02 au 11/05).
  - Paris-Saclay passe par Mon Master.
  - **Les semaines mortes de février risquent de chevaucher Mon Master**, donc les dossiers et lettres de motivation sont à préparer avant.
- **Le dossier de M1** pèse surtout par les **notes de L3**. Le système protège les partiels (semaines allégées).
- **Lettres de recommandation** : à demander tôt (novembre-décembre).
- **MVA** : conditions et calendrier d'admission à documenter, ainsi que les alternatives (par exemple le M2 IASD de Dauphine-PSL).
- **Césure** (stages à partir de septembre 2028) :
  - candidatures en général de l'automne 2027 au printemps 2028 ;
  - un stage est limité à 6 mois par organisme d'accueil et par année d'enseignement (C. éduc. L124-5), donc une césure = deux stages, ou un CDD ;
  - le régime de la césure est à vérifier avec l'ESSEC.
- **Été 2027** : pas de stage. Travail intensif ou vacances, à décider vers avril 2027.
- **Décision ML engineer ou recherche** : au check-in de juin 2027.

## 15. Esquisse de roadmap (à finaliser à l'étape 7)

| Phase | Période | Contenu |
|---|---|---|
| 0 | semaine 1 | Installation, diagnostic, Python scientifique (NumPy, pandas), outils (git, tests) |
| 1 | nov. 2026 - janv. 2027 | Maths du ML ciblées et ML classique (détail ci-dessous). **Projet 1 publié fin janvier** |
| 2 | mars - juin 2027 | Deep learning (détail ci-dessous). Projet 2 : reproduire un article classique à petite échelle. **Décision MLE / recherche** |
| 3 | été 2027, selon le choix | Spécialisation et projet ambitieux, ou reproduction de recherche |
| 4 | sept. - déc. 2027 (M1) | Ingénierie (déploiement, tests, Docker) ou compétences de recherche, portfolio, candidatures de césure, préparation aux entretiens |
| 5 | janv. - mai 2028 | Entretiens, projet final, préparation au MVA (théorie de l'apprentissage, optimisation, ML probabiliste) |

- **Phase 1, maths du ML** : algèbre linéaire numérique et SVD, calcul matriciel et gradients, optimisation (gradient, convexité, SGD), probas et stats pour le ML (MLE / MAP, gaussiennes, théorie de l'information).
- **Phase 1, ML classique** : régression linéaire et logistique, biais-variance, régularisation, validation croisée, arbres et boosting, SVM et noyaux, k-means et PCA. Avec scikit-learn **et** des implémentations from scratch.
- **Phase 1, projet 1** : par exemple un MLP from scratch en NumPy, plus un problème tabulaire avec une validation croisée propre.
- **Phase 2, deep learning** : backprop, optimisation, régularisation, CNN, attention et Transformers, PyTorch.

## 16. Hors V1 (plus tard, avec un déclencheur)

| Élément | Déclencheur |
|---|---|
| Tableau de bord web (Artifact) publié au check-in | semaines 3-4, si l'utilisateur le veut |
| Facteur de vitesse | 6 semaines de données |
| Premier examen blanc | vers la semaine 6 |
| Repos publics de projets | premier projet présentable |
| Ajout direct de cartes dans Anki (add-on AnkiConnect) | si l'import devient pénible |
| Google Agenda | non retenu |

## 17. Historique des décisions

Le 30/10/2026, une critique indépendante (sous-agent Opus 5.5, effort max, qui avait d'abord conçu son propre design à l'aveugle) a corrigé la V0. Corrections intégrées :
- paquets Anki **delta**, au lieu d'une reconstruction complète ;
- planificateur réduit à un calculateur et un validateur ; Claude place les séances, et un imprévu reste local ;
- calibrage externe de l'évaluation : diagnostic, examens blancs, banque de questions, tests écrits à l'avance ;
- debrief préparé d'un coup, envoyé 2 par 2, avec un seul commit ;
- log rapide et protocoles de résilience ;
- version de PyTorch adaptée à la GTX 1060 ;
- tableau de bord en Markdown d'abord ;
- 25 à 30 compétences au départ ;
- cadre stratégique complété.

Une affirmation de la critique a été **corrigée après vérification** : la date limite du 14/01/2027 pour IP Paris ne concerne que les candidats hors UE qui n'ont pas étudié en France.

Autre décision de Claude : **une conversation par jour**, plutôt qu'une par semaine, pour le cache et le quota.
