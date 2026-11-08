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
- **Cours et Anki :** 529 cartes ont été rédigées pour ce qui manquait à ton paquet, prérequis de L1-L2 compris. Elles sont rangées dans `tg::Maths::L3 Paris Cité::<matière>::<chapitre>`. Tes anciens paquets ne sont pas modifiés.
- **Planning :** chaque jour, 2 h d'exercices et 30 min de cours. Il s'arrête le 03/01, avec les examens visés au 04/01 par prudence, et une marge d'environ 26 h.

## Une journée
1. **Ouvrir `NOW.md`.** La première ligne donne le bloc du jour : une matière et un sous-chapitre (les matières tournent : topologie, mesure, probabilités, modélisation). Les exercices sont groupés en reprises, annale et bloc.
2. **Anki** (hors des 2 h 30) :
   - Révisions : étudier `tg::Maths`. Anki présente toutes les cartes dues, anciennes et nouvelles, où qu'elles soient rangées.
   - Nouvelles cartes : coller la recherche « à apprendre » dans **Outils → Créer un paquet filtré**, puis étudier ce paquet (jusqu'à 20 cartes : tes cartes d'erreurs et d'exercices, puis celles du sous-chapitre du bloc du jour, puis celles du sous-chapitre suivant de la même matière ; s'y ajoutent jusqu'à 10 de tes anciennes cartes jamais apprises du sous-chapitre).
   - **Cartes d'exercices :** le lendemain, elles arrivent en tête des cartes à apprendre, avec les cartes d'erreurs. Le recto donne l'énoncé : cherche d'abord par où l'attaquer, puis retourne la carte (idée clé, correction complète, piège, référence du corrigé). Elles sont rangées dans le sous-paquet `Exercices` de chaque chapitre.
   - Ces cartes ne remplacent pas le papier. L'exercice revient ensuite dans les reprises (30 min par jour au plus) : refais-le sur papier, et envoie ta photo en séance pour qu'elle soit vérifiée.
3. **Cours (30 min) :** relire les notions indiquées, aux pages données, pour approfondir. Pour réviser tout un sujet, coller la recherche « tout le sujet du jour » dans un paquet filtré, en décochant « replanifier les cartes selon mes réponses ». Elle réunit tes anciennes cartes `AoutLicenceMath` et les nouvelles.
4. **Exercices (2 h) :** les faire dans l'ordre de la liste ; le PDF et la page sont indiqués. En cas de blocage, ouvrir une conversation Claude dans `D:\Projets\prof-maths` (Sonnet, effort high). L'aide est graduée : une question qui oriente, puis la méthode, puis l'étape clé, puis la solution. Dès le premier indice, l'exercice compte comme `aide`.
5. **Le soir (10-15 min) :** dans la même conversation que la séance, dire « debrief » et donner les temps. Une conversation par jour : cours, exercices, puis debrief.
   - Donner le résultat de chaque exercice.
   - Répondre à 3 à 5 questions de compréhension, qui sont notées et corrigées.
   - Le debrief crée des cartes sur tes erreurs, écrit `NOW.md` pour le lendemain et fait le commit.
   - Pour chaque exercice que tu n'as pas réussi seul, il crée une **carte d'exercice** (tag `exercice`).
   - Les soirs de fatigue : « log rapide : … », au plus 2 fois par semaine.

## Réglages Anki à faire une fois
- Importer les deux paquets `anki/paquets/prof-maths-2026-11-03.apkg` et `prof-maths-2026-11-03-2.apkg`, par double-clic.
- Sur le paquet `L3 Paris Cité`, ouvrir Options et mettre « nouvelles cartes par jour » à 0.
- Importer aussi le paquet des cartes d'exercices, `anki/paquets/prof-maths-2026-11-08.apkg` (sous-paquets `Exercices` de chaque chapitre).
- **Fusion de tes paquets `AoutLicenceMath` dans le paquet L3** (environ 420 notes), rangés par chapitre de Paris Cité. Changer de paquet garde l'historique de révision. Elle demande AnkiConnect (extension Anki, à installer) et Anki ouvert. Deux commandes, depuis `D:\Projets\prof-maths` :
  - `python tools/anki_connect.py fusionner --dry-run` : montre combien de notes iront dans chaque paquet, sans rien toucher (marche Anki fermé).
  - `python tools/anki_connect.py fusionner` : fait la fusion. Un fichier d'annulation est écrit avant dans `anki/export/fusion-<date>.csv` ; pour revenir en arrière : `python tools/anki_connect.py annuler anki/export/fusion-<date>.csv`. Aucun paquet n'est supprimé. Les notes absentes de la couverture sont rangées d'après leur recto (`inventaire/anki/rattachement_ancien.yaml`, modifiable). Seules les notes hors de tous les chapitres de Paris Cité (connexité, calcul différentiel, interversion limite-intégrale) vont dans `Autres (AoutLicenceMath)` de leur matière.
- Avec le paquet L3 à 0 nouvelle carte par jour, une ancienne carte jamais apprise ne sortirait plus. `NOW.md` ajoute donc à la recherche « à apprendre » jusqu'à 10 anciennes notes du sous-chapitre du jour (`(nid:… is:new)`), en plus des 20 cartes du système.
- AnkiConnect permet aussi d'importer en une commande : `python tools/anki_connect.py importer anki/paquets/<fichier>.apkg`.

## Fiabilité
- **Corrigés :** le corrigé officiel passe d'abord. Sinon, la solution porte la mention « vérifiée par Claude, à confirmer ». Un corrigé officiel peut lui-même être faux.
- **Énoncés :** les annales de Paris Cité ont été vérifiées sur les pages du PDF. Les autres énoncés le sont quand ils sont planifiés.
- **Cartes :** elles sont tirées des polys. Une partie a été relue contre la source ; si une carte te semble fausse, signale-la au debrief.

## Commandes utiles
| Commande | Effet |
|---|---|
| `python tools/plan.py jour --date AAAA-MM-JJ` | régénère `NOW.md` |
| `python tools/resultat.py profil` | profil de maîtrise |
| `python tools/check.py` | cohérence des données |
