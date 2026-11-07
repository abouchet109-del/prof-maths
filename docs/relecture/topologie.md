# Relecture des cartes de topologie

Fichier relu : `matieres/topologie/cartes.yaml`. Sources vérifiées : poly Paris Cité, chapitres 1, 2 et 3 (`bibliotheque/_texte/topologie/cours/`), plus une page rendue en image (chap. 1, p. 15) pour lever un doute d'extraction sur la Prop. 25 (la fermeture y figure bien). Les cartes de prérequis `topo-a-037` et `topo-a-038` et les cartes d'erreurs `topo-e001` à `topo-e003` ont été vérifiées mathématiquement.

Cartes relues : **81**.
Cartes corrigées : **28**. Cartes douteuses (laissées telles quelles) : **5**.

Aucune erreur mathématique de fond n'a été trouvée. Les défauts sont des rectos sans cadre (espace métrique, `f : X → X`, suite `O_n`…), deux preuves où une justification ou un nom de variable prêtait à confusion (`topo-a-032-2`, `topo-e001`) et une formulation ambiguë (`topo-e002`).

## Cartes corrigées

| id | défaut | correction |
|---|---|---|
| topo-a-004-2 | recto sans cadre | « Dans un espace métrique (X,d) » |
| topo-a-004-3 | recto sans cadre | idem |
| topo-a-005-1 | `d(A,B)` : parties non précisées non vides (inf sur l'ensemble vide) | « deux parties non vides » |
| topo-a-006-1 | recto sans cadre | « Dans un espace topologique (X,τ), A ⊂ X » |
| topo-a-006-2 | recto sans cadre | idem |
| topo-a-009-1 | `d`, `δ`, `X` non introduits | « Pour deux distances d et δ sur un même ensemble X » |
| topo-a-010-1 | justification de convergence imprécise (« car Σ2^{-k} converge ») | « termes majorés par 2^{-k} » |
| topo-a-014-1 | recto sans cadre (application entre espaces métriques) | cadre ajouté |
| topo-a-015-1 | `d`, `δ` non introduits | « Soient d et δ deux distances sur un même ensemble X » |
| topo-a-015-2 | idem | idem |
| topo-a-015-3 | idem | idem |
| topo-a-016-4 | recto sans hypothèse (partie bornée) | « Pour une partie bornée A d'un espace métrique » |
| topo-a-018-2 | « (f(u_n)) de Cauchy » sans dire que c'est l'uniforme continuité qui le donne | ajout « (f est uniformément continue) » |
| topo-a-019-1 | distance sur ℝ non précisée | « (distance usuelle) » |
| topo-a-019-2 | `x` non fixé dans la limite `y → +∞` | « En fixant x et en faisant tendre y → +∞ » |
| topo-a-020-1 | recto sans cadre (`f : X → X`, espace métrique) | cadre ajouté |
| topo-a-020-2 | recto sans cadre (`X`, `d`, `C ∈ ]0,1[`, `u_{n+1} = f(u_n)`) | cadre ajouté |
| topo-a-020-3 | recto sans cadre ; verso : « X complet donc u_n → a » sans dire que `(u_n)` est de Cauchy | cadre ajouté ; « (u_n) de Cauchy et X complet » ; f lipschitzienne |
| topo-a-020-4 | recto sans cadre | « f contraction d'un espace métrique (X,d) » |
| topo-a-021-1 | recto sans cadre (`f : X → X`, `X` métrique complet) | cadre ajouté |
| topo-a-023-1 | recto sans cadre (`O_n` ouverts denses d'un espace métrique complet) | cadre ajouté |
| topo-a-023-2 | idem | idem |
| topo-a-023-3 | idem | idem |
| topo-a-030-2 | verso mal formulé (« donc dans un compact : compacte ⇔ fermée ») ; recouvrement de `A` non nettoyé de `A^c` | reformulé ; ajout « (et en retirer A^c) » |
| topo-a-030-3 | `y_1,…,y_n` introduits sans dire qu'ils sont dans `A` | « il existe y_1,…,y_n ∈ A » |
| topo-a-032-2 | la lettre `ε` désignait à la fois le rayon du lemme et celui d'une boule incluse dans `U_i` ; « `N` grand » sans condition | rayon renommé `ρ`, conditions `φ(N) > 2/ρ` et `d(u_{φ(N)},x) < ρ/2` explicites, Bolzano-Weierstrass cité |
| topo-e001 | verso : l'argument « `x_n ∈ U ∩ V = ∅` donc `x = y` » ne dit pas qu'on raisonne par l'absurde avec `x ≠ y` | argument réécrit (par l'absurde, `x ≠ y`) |
| topo-e002 | verso : « seule la réunion finie de fermés est fermée » est ambigu | « une réunion finie est fermée, mais pas forcément une réunion infinie » |

## Doutes pour Opus

Aucun n'est une erreur de carte prouvée : ce sont des écarts du poly, signalés sans trancher.

- **topo-a-004-3** : dans la preuve de la Prop. 5 (chap. 1, p. 5), le poly écrit `d(x,z) ≥ d(x,y) − d(y,z) > (r−ε) − ε = r` pour la boule fermée. Avec `ε = d(x,y) − r`, la bonne valeur est `(r+ε) − ε = r`. La carte utilise `(r+ε) − ε`. Coquille du poly. Page 5.
- **topo-a-021-1** : la remarque du poly (chap. 2, p. 7) écrit l'hypothèse « `|f(x)−f(y)| < |x−y|, ∀x,y` », fausse pour `x = y`. La carte écrit `x ≠ y`. Page 7.
- **topo-a-025-1** et **topo-a-025-2** : le Corollaire 4 du poly (chap. 2, p. 9) ne suppose pas `X ≠ ∅`, alors que c'est nécessaire (avec `X = ∅`, la conclusion « il existe n avec F̊_n ≠ ∅ » est fausse). Les cartes tiennent compte de `X ≠ ∅` (recto de 025-1, `X̊ = X ≠ ∅` au verso de 025-2). À confirmer comme choix voulu. Page 9.
- **topo-a-016-4** : `diam(Å) ≤ diam(A) = diam(Ā)` (chap. 2, p. 2) : `Å` peut être vide et `diam(∅)` n'est pas défini dans le poly. Faut-il ajouter une convention (`diam(∅) = 0`) ou restreindre l'énoncé ? Page 2.

IDS_CORRIGES: topo-a-004-2,topo-a-004-3,topo-a-005-1,topo-a-006-1,topo-a-006-2,topo-a-009-1,topo-a-010-1,topo-a-014-1,topo-a-015-1,topo-a-015-2,topo-a-015-3,topo-a-016-4,topo-a-018-2,topo-a-019-1,topo-a-019-2,topo-a-020-1,topo-a-020-2,topo-a-020-3,topo-a-020-4,topo-a-021-1,topo-a-023-1,topo-a-023-2,topo-a-023-3,topo-a-030-2,topo-a-030-3,topo-a-032-2,topo-e001,topo-e002


## Mise au format du poly

Cartes reformatées : **74** sur 81 (recto = type et nom de l'énoncé, verso = énoncé du poly recopié avec son cadre ; les cartes de preuve donnent l'idée de la preuve du poly en 2 à 5 lignes). Les remarques et exemples du poly sans numéro sont notés `Rem. n` ou `Exemple`. Remarques d'une ligne ajoutées : topo-a-004-3 (coquille `(r−ε)−ε`), topo-a-016-4 (`diam(∅)` non défini), topo-a-021-1 (`∀x,y` pour `x≠y`), topo-a-025-1 (`X≠∅` omis), topo-a-005-1 (parties non vides). Les points seuls d'énoncés multiples (Prop. 7, Prop. 36, Rem. 3) gardent le cadre de l'énoncé ; la preuve de Prop. 36 (2e point) n'est plus sur une carte propre.

Cartes laissées telles quelles (7) :
- tag `prerequis-l1l2` (énoncés standard hors poly) : topo-a-037-1, topo-a-037-2, topo-a-038-1, topo-a-038-2 ;
- tag `erreur` (id en `-e`) : topo-e001, topo-e002, topo-e003.

IDS_REFORMATES: topo-a-001-1,topo-a-001-2,topo-a-001-3,topo-a-001-4,topo-a-002-1,topo-a-003-1,topo-a-003-2,topo-a-003-3,topo-a-004-1,topo-a-004-2,topo-a-004-3,topo-a-005-1,topo-a-006-1,topo-a-006-2,topo-a-007-1,topo-a-007-2,topo-a-008-1,topo-a-008-2,topo-a-009-1,topo-a-010-1,topo-a-010-2,topo-a-011-1,topo-a-012-1,topo-a-013-1,topo-a-014-1,topo-a-014-2,topo-a-015-1,topo-a-015-2,topo-a-015-3,topo-a-016-1,topo-a-016-2,topo-a-016-3,topo-a-016-4,topo-a-017-1,topo-a-018-1,topo-a-018-2,topo-a-019-1,topo-a-019-2,topo-a-020-1,topo-a-020-2,topo-a-020-3,topo-a-020-4,topo-a-021-1,topo-a-022-1,topo-a-023-1,topo-a-023-2,topo-a-023-3,topo-a-024-1,topo-a-024-2,topo-a-025-1,topo-a-025-2,topo-a-026-1,topo-a-026-2,topo-a-027-1,topo-a-027-2,topo-a-027-3,topo-a-028-1,topo-a-029-1,topo-a-030-1,topo-a-030-2,topo-a-030-3,topo-a-031-1,topo-a-031-2,topo-a-032-1,topo-a-032-2,topo-a-033-1,topo-a-033-2,topo-a-034-1,topo-a-034-2,topo-a-034-3,topo-a-035-1,topo-a-035-2,topo-a-036-1,topo-a-036-2
