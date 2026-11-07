# Relecture des cartes de mesure

Fichier relu : `matieres/mesure/cartes.yaml`. Sources vérifiées : poly Paris Cité (pages 3 à 8), notes du CM du 13/10/2026 et du 20/10/2026 (PDF manuscrits rendus en image), diapos UVSQ séances 1, 9 et 10, énoncé du `td3` (exercice 4).

Cartes relues : **50** (le fichier en contient 50, non 53).
Cartes corrigées : **25**. Cartes douteuses (laissées telles quelles) : **4**.

Aucune erreur mathématique de fond n'a été trouvée. Les défauts sont des cadres absents au recto, un passage de preuve omis (`mesure-a-016-2`) et des quantificateurs ou hypothèses implicites.

## Cartes corrigées

| id | défaut | correction |
|---|---|---|
| mesure-a-001-3 | recto sans cadre (`f`, `A`, `B` non introduits) | ajout de « Soit f : Ω → E et A ⊂ B ⊂ E » |
| mesure-a-005-1 | espace d'arrivée de `1_A` non précisé (la mesurabilité en dépend) | `1_A : X → ℝ` avec la tribu `B(ℝ)` |
| mesure-a-006-1 | notation `f^{-1}(B)` (famille) non définie | ajout de `{f^{-1}(B) : B ∈ B}` |
| mesure-a-008-1 | même défaut avec `f^{-1}(E)` | ajout de la définition de `f^{-1}(F)` pour une famille |
| mesure-a-010-1 | `A` non quantifié | « pour tout A ⊂ ℕ » |
| mesure-a-011-2 | cadre absent | « Soit (X,A,μ) espace mesuré et A ⊂ B dans A » |
| mesure-a-011-3 | cadre absent ; additivité finie invoquée sans justification | cadre ajouté ; additivité finie déduite de la σ-additivité avec `μ(∅)=0` |
| mesure-a-012-1 | cadre absent | « Soit (X,A,μ) espace mesuré et A, B ∈ A » |
| mesure-a-012-2 | cadre absent ; calcul non conclu | cadre ajouté ; égalité finale `= μ(A)+μ(B)−μ(A∩B)` |
| mesure-a-013-1 | cadre absent (suite croissante dans A) | cadre ajouté |
| mesure-a-013-2 | cadre absent | cadre ajouté |
| mesure-a-014-1 | cadre absent (suite décroissante dans A, espace mesuré) | cadre ajouté |
| mesure-a-015-1 | cadre absent (défaut signalé par l'utilisateur) | « Soit (X,A,μ) un espace mesuré » |
| mesure-a-015-2 | cadre absent ; `B_n ∈ A` non dit ; `k<n` collé | cadre ajouté ; « les B_n sont dans A » ; `k < n` |
| mesure-a-016-1 | `λ` non défini au recto | « Soit λ la mesure de Lebesgue sur ℝ » |
| mesure-a-016-2 | `λ` non défini ; `λ(]0,1]) = 1` utilisé sans justification | cadre ajouté ; `λ(]0,1]) = λ([0,1]) − λ({0}) = 1` (étape 1) |
| mesure-a-016-3 | `λ` non défini ; entiers `n`, `k_i` non précisés | cadre ajouté ; « n ∈ ℕ*, k_1,k_2 ∈ ℤ » |
| mesure-a-016-4 | `λ` non défini | cadre ajouté |
| mesure-a-016-5 | `λ` non défini ; hypothèse `a < b` absente | cadre ajouté ; « Pour a < b » |
| mesure-a-018-1 | « la réciproque » renvoie à un énoncé absent du recto | rappel de `F_μ` et de ses propriétés au recto |
| mesure-a-022-1 | mesurabilité de `f` non dite | « f mesurable, positive ou intégrable » |
| mesure-a-022-2 | même défaut | même correction |
| mesure-a-024-2 | verso : constante `C` non introduite | « Si f ∈ L^∞(X), il existe C avec μ({\|f\| > C}) = 0, et alors … » |
| mesure-a-024-3 | mesure de `ℝ` non précisée | « ℝ muni de la mesure de Lebesgue » |
| mesure-e001 | recto sans cadre (`E`, `ℰ`, espace d'arrivée), alors que le verso utilise `ℰ` | « Soit (E,ℰ) espace mesurable, (f_n) mesurables dans (ℝ,B(ℝ)) » |

## Doutes pour Opus

Aucun n'est une erreur de carte prouvée : ce sont des écarts entre le poly (ou une source) et l'usage.

- **mesure-a-004-2** : le poly (Ex. 1.2, p. 5) appelle « tribu triviale » la tribu `P(X)` et « tribu grossière » la tribu `{∅,X}`. L'usage courant est « triviale = grossière = {∅,X} » et « discrète = P(X) ». La carte reprend le poly en ajoutant « (discrète) ». Garder la formulation du poly, ou signaler l'écart ? Page 5.
- **mesure-a-001-1** : la Prop. 0.1 point 3 (p. 3) écrit « famille de parties de Ω » alors que `f : Ω → E` et `A_i ⊂ E`. La carte écrit correctement « parties de E ». Page 3.
- **mesure-a-010-2** : la preuve du poly (Ex. 1.21, p. 8) prend des `A_n ∈ P(ℕ)` quelconques, alors que la σ-additivité n'est demandée que pour des `A_n` deux à deux disjoints. La carte reste juste ; le poly omet « deux à deux disjoints ». Page 8.
- **mesure-a-019-1** : définition UVSQ du dénombrable (injection dans ℕ, ensembles finis inclus), alors que le poly Paris Cité (p. 3) dit « en bijection avec ℕ » (finis exclus). La carte suit l'UVSQ (diapo 5, séance 1). Faut-il garder cette convention pour les examens de Paris Cité ? Page 3 du poly.

IDS_CORRIGES: mesure-a-001-3,mesure-a-005-1,mesure-a-006-1,mesure-a-008-1,mesure-a-010-1,mesure-a-011-2,mesure-a-011-3,mesure-a-012-1,mesure-a-012-2,mesure-a-013-1,mesure-a-013-2,mesure-a-014-1,mesure-a-015-1,mesure-a-015-2,mesure-a-016-1,mesure-a-016-2,mesure-a-016-3,mesure-a-016-4,mesure-a-016-5,mesure-a-018-1,mesure-a-022-1,mesure-a-022-2,mesure-a-024-2,mesure-a-024-3,mesure-e001


## Mise au format du poly

Cartes reformatées : **20** sur 50 (recto = type et nom de l'énoncé, verso = énoncé du poly recopié avec son cadre). Remarques d'une ligne ajoutées là où le poly s'écarte de l'usage ou comporte une coquille : mesure-a-001-1 (parties de Ω au lieu de E), mesure-a-004-2 (triviale/grossière inversées), mesure-a-009-2 (`μ(B)≠0`), mesure-a-010-2 (« deux à deux disjoints » omis).

Cartes laissées telles quelles (30) :
- énoncé absent du poly (notes de CM manuscrites du 13/10 et 20/10) : mesure-a-011-1 à mesure-a-018-2 (dont a-016-1 à a-016-5, a-017-1) ;
- énoncé absent du poly (diapos UVSQ) : mesure-a-019-1, mesure-a-019-2, mesure-a-022-1, mesure-a-022-2, mesure-a-024-1, mesure-a-024-2, mesure-a-024-3 ;
- tag `prerequis-l1l2` : mesure-a-025-1, mesure-a-025-2, mesure-a-025-3 ;
- tag `erreur` (id en `-e`) : mesure-e001, mesure-e002.

IDS_REFORMATES: mesure-a-001-1,mesure-a-001-2,mesure-a-001-3,mesure-a-002-1,mesure-a-002-2,mesure-a-003-1,mesure-a-004-1,mesure-a-004-2,mesure-a-004-3,mesure-a-005-1,mesure-a-006-1,mesure-a-006-2,mesure-a-007-1,mesure-a-008-1,mesure-a-008-2,mesure-a-008-3,mesure-a-009-1,mesure-a-009-2,mesure-a-010-1,mesure-a-010-2


## Notes de CM (images)

Pages lues : CM du 13/10/2026 p. 1-2, CM du 20/10/2026 p. 1-3. Les 18 cartes mesure-a-011-1 à mesure-a-018-2 ont été vérifiées contre les notes puis reformatées (recto = type et nom, verso = énoncé avec cadre et hypothèses ; les cartes `Preuve :` donnent l'idée en 2 à 5 lignes). Les notes numérotent les points (i) à (v) d'une même Proposition, d'où « Prop. (i) » à « Prop. (v) ».

Cartes corrigées (cadre ou hypothèses ajoutés) :
- mesure-a-011-1 : les recto/verso exposaient l'énoncé en question ; énoncé complet des notes (croissance + `μ(B)=μ(A)+μ(B\A)`).
- mesure-a-012-2 : précision « mesure finie » pour `μ(A\(A∩B))=μ(A)-μ(A∩B)`.
- mesure-a-014-1 : rappel de l'hypothèse (P) et du cadre `X=ℕ`, `𝒜=P(ℕ)`.
- mesure-a-016-1 à 016-5 : cadre « λ mesure de Lebesgue sur ℝ, I intervalle » et énoncé de chaque étape ajoutés.
- mesure-a-017-1 : définition de partie négligeable et de `N(μ)` ajoutée.
- mesure-a-018-1 : énoncé complet du théorème (points 1 et 2).
- Reformatées sans changement de fond : mesure-a-011-2, 011-3, 012-1, 013-1, 013-2, 015-1, 015-2, 018-2.

Doutes :
- Aucune erreur trouvée dans les notes ; écriture lisible.
- Recto de mesure-a-011-2 et mesure-a-018-2 : « Rem. : » et pour a-014-1 « Contre-ex. : », car les notes les présentent ainsi (« Rem », « Contre-ex ») et ce type n'est pas dans la liste du format. À valider.
- mesure-a-013-1 et 013-2 : les deux moitiés d'une même preuve (1/2, 2/2), pas de carte d'énoncé de Prop. (iii) dans cette série.

IDS_CM: mesure-a-011-1,mesure-a-011-2,mesure-a-011-3,mesure-a-012-1,mesure-a-012-2,mesure-a-013-1,mesure-a-013-2,mesure-a-014-1,mesure-a-015-1,mesure-a-015-2,mesure-a-016-1,mesure-a-016-2,mesure-a-016-3,mesure-a-016-4,mesure-a-016-5,mesure-a-017-1,mesure-a-018-1,mesure-a-018-2
