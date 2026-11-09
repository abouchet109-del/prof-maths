# Mode d'emploi

## Ce que fait le système
- **Exercices :** 667 exercices (TD, DM et annales de Paris Cité, complétés par l'UVSQ), classés par sous-chapitre en vital, important, secondaire et exotique.
  - Les annales de Paris Cité passent avant le bloc, une par jour, dès que leur sous-chapitre est passé dans sa matière (toutes à partir du 07/12).
  - La plus récente de chaque matière est gardée pour les examens blancs des deux semaines à 28 h (21/12 au 03/01).
  - Une catégorie ne s'ouvre qu'une fois la précédente maîtrisée dans le sous-chapitre.
- **Suivi :** chaque résultat est enregistré (`reussi`, `aide`, `presque`, `non_fait`) et le calcul est automatique.
  - Un exercice raté revient 1 à 3 jours plus tard.
  - Un exercice réussi seul est **acquis** ; il revient à J+7 puis à J+21.
  - Une 2e réussite seule, au moins 7 jours après, le rend **maîtrisé**.
  - Le profil est suivi par matière, par sous-chapitre et par méthode.
- **Cours et Anki :** 529 cartes ont été rédigées pour ce qui manquait à ton paquet, prérequis de L1-L2 compris. Elles sont rangées dans `tg::Maths::L3 Paris Cité::<matière>::<chapitre>::Cours`. Tes anciens paquets ne sont pas modifiés.
- **Planning :** chaque jour, 2 h d'exercices et 30 min de cours. Il s'arrête le 03/01, avec les examens visés au 04/01 par prudence, et une marge d'environ 26 h.

## Une séance (n'importe quel jour, à n'importe quelle heure)
1. **Garde Anki ouvert**, avec AnkiConnect, et synchronisé. Le plan lit dans Anki les cartes que tu as vraiment apprises.
2. **Dis « on commence »** dans une nouvelle conversation Claude (dossier `D:\Projets\prof-maths`, Sonnet, effort high). Claude lance `plan.py seance`, qui écrit `NOW.md` pour maintenant : ce qui est revenu, le bloc, la marge. Un jour `off` du calendrier ne bloque rien. Ce que tu n'as pas fait revient tout seul.
3. **Anki** (hors du temps de travail) :
   - Révisions : étudier `tg::Maths` (cartes dues).
   - Nouvelles cartes, **deux paquets filtrés** (Outils → Créer un paquet filtré, une recherche de `NOW.md` chacun) :
     - « cours, à apprendre » : 20 cartes de cours au plus (erreurs, prérequis inconnus, notions faibles, puis le cours en ordre), plus jusqu'à 10 de tes anciennes cartes jamais apprises ;
     - « exercices à revoir » : les cartes d'exercices nouvelles, 10 au plus (`exercices_par_jour` dans `dispo.yaml`).
   - **Cartes d'exercices :** le recto donne l'énoncé : cherche d'abord par où l'attaquer, puis retourne la carte (idée clé, correction complète, piège, référence). Elles ne remplacent pas le papier : l'exercice revient ensuite dans les reprises (30 min au plus) ; refais-le sur papier et envoie ta photo en séance.
4. **Cours (30 min) :** les notions indiquées, aux pages données. Pour réviser tout un sujet, coller la recherche « tout le sujet du jour » dans un paquet filtré, en décochant « replanifier les cartes selon mes réponses ».
5. **Exercices (2 h) :** dans l'ordre de la liste ; le PDF et la page sont indiqués. En cas de blocage, demande à Claude : aide graduée (une question qui oriente, la méthode, l'étape clé, la solution). Dès le premier indice, l'exercice compte comme `aide`. Les reprises viennent en fin de séance : tu les fais seul sur papier, Claude vérifie la rédaction finale. Une reprise marquée « seulement Q2 » ne porte que sur les questions que tu avais manquées : celles déjà justes ne sont pas redemandées.
   - **Après chaque exercice non réussi seul** (environ 5 min) : Claude t'explique l'étape exacte où ça a bloqué et comment tu aurais pu trouver l'idée, te pose 1 ou 2 questions pour trouver la cause (notion pas tenue, lien pas fait, méthode pas reconnue), puis te demande ce que tu retiens de l'exercice, avec tes mots.
6. **Pour finir (10-15 min) :** dire « debrief » (ou « log rapide : … » les soirs de fatigue, 2 fois par semaine au plus), dans la même conversation.
   - Donner le résultat de chaque exercice ; Claude évalue ta compréhension de chaque notion travaillée d'après ce que tu as dit en séance (au plus 3 questions là où il lui manque de quoi juger) et met à jour `state/comprehension.yaml`, qui oriente les cartes, les exercices et ses explications des jours suivants.
   - Le debrief crée une carte d'exercice pour chaque exercice non réussi seul (et une carte de prérequis si un point de L1-L2 te manque), écrit le **bilan réel** dans le journal (prévu contre fait, cartes apprises, marge) et fait le commit.
   - Il ne prépare pas la suite : le plan suivant se calcule au prochain « on commence ».
7. **Synchronise Anki** avant de fermer.

## Réglages Anki à faire une fois
- Importer les deux paquets `anki/paquets/prof-maths-2026-11-03.apkg` et `prof-maths-2026-11-03-2.apkg`, par double-clic.
- Sur le paquet `L3 Paris Cité`, ouvrir Options et mettre « nouvelles cartes par jour » à 0.
- Importer aussi le paquet des cartes d'exercices, `anki/paquets/prof-maths-2026-11-08.apkg` (sous-paquets `Exercices` de chaque chapitre).
- **Fusion de tes paquets `AoutLicenceMath` dans le paquet L3** (environ 420 notes), rangés par chapitre de Paris Cité. Changer de paquet garde l'historique de révision. Elle demande AnkiConnect et Anki ouvert. Deux commandes, depuis `D:\Projets\prof-maths` :
  - `python tools/anki_connect.py fusionner --dry-run` : montre combien de notes iront dans chaque paquet, sans rien toucher (marche Anki fermé).
  - `python tools/anki_connect.py fusionner` : fait la fusion. Un fichier d'annulation est écrit avant dans `anki/export/fusion-<date>.csv` ; pour revenir en arrière : `python tools/anki_connect.py annuler anki/export/fusion-<date>.csv`. Aucun paquet n'est supprimé. Les notes absentes de la couverture sont rangées d'après leur recto (`inventaire/anki/rattachement_ancien.yaml`, modifiable). Seules les notes hors de tous les chapitres de Paris Cité (connexité, calcul différentiel, interversion limite-intégrale) vont dans `Autres (AoutLicenceMath)` de leur matière.
- Avec le paquet L3 à 0 nouvelle carte par jour, une ancienne carte jamais apprise ne sortirait plus. `NOW.md` ajoute donc à la recherche « à apprendre » jusqu'à 10 anciennes notes du sous-chapitre du bloc (`nid:…`, toujours avec `is:new`), en plus des 20 cartes du système.
- **Chaque chapitre a deux sous-paquets** (depuis le 09/11/2026) : `Cours` (définitions, propositions, preuves) et `Exercices`. Pour réviser seulement ton cours, clique sur `<chapitre>::Cours`. Les cartes déjà posées dans un chapitre se rangent avec `python tools/anki_connect.py ranger` (`--dry-run` pour voir, annulation dans `anki/export/ranger-<date>.csv`) ; une carte prêtée à un paquet filtré est laissée : relance après avoir vidé le paquet filtré.
- AnkiConnect permet aussi d'importer en une commande : `python tools/anki_connect.py importer anki/paquets/<fichier>.apkg`.

## Fiabilité
- **Corrigés :** le corrigé officiel passe d'abord. Sinon, la solution porte la mention « vérifiée par Claude, à confirmer ». Un corrigé officiel peut lui-même être faux.
- **Énoncés :** les annales de Paris Cité ont été vérifiées sur les pages du PDF. Les autres énoncés le sont quand ils sont planifiés.
- **Cartes :** elles sont tirées des polys. Une partie a été relue contre la source ; si une carte te semble fausse, signale-la au debrief.

## Commandes utiles
| Commande | Effet |
|---|---|
| `python tools/plan.py seance` | plan de maintenant (`NOW.md`), à lancer en début de séance |
| `python tools/plan.py bilan` | bilan réel de la séance, à recopier dans le journal |
| `python tools/plan.py jour --date AAAA-MM-JJ` | simulation d'une date (hors workflow) |
| `python tools/resultat.py profil` | profil de maîtrise |
| `python tools/check.py` | cohérence des données |
