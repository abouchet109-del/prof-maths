# Relecture Opus : doutes tranchés et contrôle de la mise au format

Date : 2026-11-07. Règle : le verso donne la version juste, et la mention « (le poly écrit … ) » quand le poly est faux ou s'écarte de l'usage.

## Doutes tranchés

### Mesure
- mesure-a-004-2 : le poly appelle « triviale » la tribu P(X), à l'inverse de l'usage. Verso : « tribu discrète » + mention du poly. Recto numéroté (Exemple 1.2, point 2), comme 004-1 et 004-3.
- mesure-a-001-1 : coquille réelle du poly (« parties de Ω »). Le verso disait encore « parties de Ω » dans l'énoncé ; corrigé en « parties de E » + mention.
- mesure-a-010-2 : énoncé corrigé (p_k ≥ 0, A_n deux à deux disjoints) + mention de ce que le poly écrit.
- mesure-a-009-2 (même page) : hypothèse 0 < μ(B) < +∞ intégrée à l'énoncé, mention « le poly écrit μ(B) ≠ 0 ».
- mesure-a-019-1 : on garde la convention UVSQ (carte UVSQ), avec au verso l'avertissement que le poly Paris Cité (p. 3) exclut les ensembles finis (« au plus dénombrable »).
- Doutes des notes de CM : « Rem. : » est conservé (type prévu). « Contre-ex. : » (mesure-a-014-1) devient « Exemple : contre-exemple … ». Les cartes 013-1 et 013-2 (deux moitiés d'une même preuve) sont gardées telles quelles.

### Topologie
- topo-a-004-3 : la coquille du poly ((r−ε)−ε) est confirmée. Carte juste ; la mention précise maintenant pourquoi (d(x,y) = r+ε).
- topo-a-021-1 : l'énoncé principal portait encore « ∀x,y ». Il porte maintenant « x ≠ y », avec la mention du poly.
- topo-a-025-1 / 025-2 : X ≠ ∅ est nécessaire. Ajouté dans l'énoncé (« complet non vide ») et dans la preuve (« car X ≠ ∅ »), avec la mention du poly. Le rapport Sonnet le disait fait, mais ce n'était pas le cas.
- topo-a-016-4 : convention diam(∅) = 0 ajoutée à l'énoncé, avec la mention que le poly ne la donne pas.
- topo-a-005-1 : « non vides » est maintenant dans l'énoncé, avec la mention du poly. Même défaut que 025-1 dans topo-a-020-1 (Picard) : « non vide » ajouté.

### Probabilités
- proba-a-046-2 : la phrase du poly est rétablie telle quelle. La généralisation va dans une parenthèse marquée « hors poly » (vrai dès que ∂D est Lebesgue-négligeable).
- proba-a-015-2 : **ce n'est pas une coquille**. L'image de la p. 24 montre E[(|X|^p)^{q/p}] ; c'est l'extraction du texte qui a perdu les crochets. Fausse mention retirée. L'argument de finitude (|x|^p ≤ 1+|x|^q) est conservé, signalé comme manque du poly (hypothèse de Jensen).
- proba-a-046-1 : **ce n'est pas une coquille**. L'image de la p. 44 montre 𝒥_ψ ∘ ψ^{-1}(u) = 𝒥_ψ(ψ^{-1}(u)), ce qui est juste. Fausse mention retirée ; la notation du poly est rétablie.
- proba-a-070-4 : **la référence du poly est juste**. Par la Prop. 4.50, une combinaison linéaire de gaussiennes indépendantes est gaussienne, donc (X,Z) serait un vecteur gaussien (Déf. 4.51). Fausse mention retirée, et l'argument est écrit.
- proba-a-070-3 : aucune modification nécessaire.

### Modélisation (mis au format en même temps)
- mod-a-047-1 → « Thm 2.8 » : convergence pour toute loi initiale. La vitesse C|λ₂|^n est énoncée sous l'hypothèse « P diagonalisable ». Mention : le poly l'énonce sans hypothèse ; en général, il y a un facteur polynomial (blocs de Jordan) et un O(r^n) pour tout r > |λ₂|.
- mod-a-047-2 → « Preuve : Thm 2.8 (cas diagonalisable) » : base de ℂ^N de vecteurs propres à gauche, modules. Mention : le poly écrit ℝ^N et « valeurs absolues ».
- mod-a-056-2 → « Exemple : convergence de l'urne d'Ehrenfest » : hypothèse 0 < ε < 1. Mention : pour ε = 1, la chaîne n'est pas irréductible ; pour ε = 0, elle est de période 2.
- mod-a-059-2 → « Prop. : PageRank et chaîne de Markov » : d⁺(i) ≥ 1 dans l'énoncé. Mention : le poly ne traite pas d⁺(i) = 0.
- mod-a-060-1 → « Prop. : matrice de transition P_β » : β ∈ ]0,1]. Mention : le poly écrit « β > 0 ».
- mod-a-060-2 → « Prop. : calcul itératif de PageRank ». **Erreur du poly trouvée sur l'image p. 21** : il écrit μ_{n+1} = (1−β)μ_nP + βμ_n. La carte donne (1−β)μ_nP + (β/N)(1,…,1), avec la mention.
- mod-a-061-2 → « Déf : processus de comptage » : énoncé du poly avec « jusqu'à l'instant t inclus ». Mention : le poly écrit « avant l'instant t ».
- mod-a-064-2 → « Prop. : absence de mémoire et lois exponentielles » : cadre X > 0, P(X > t) > 0. Les lois sont exactement les exponentielles, λ > 0. Mention ajoutée.
- mod-a-038-2 (erreur signalée au verso par Sonnet) : confirmée. Avec N = max(n_x, m_x), on n'a pas n ≥ n_x + m_y. Carte inchangée.

## Échantillon de contrôle (5 cartes reformatées par matière, tirage aléatoire, graine 20261107)

- Mesure : 008-2, 005-1, 010-1, 001-2, 002-1. Les 5 sont fidèles et justes. Seule retouche dans les voisines : la numérotation « Exemple 1.21 » sur 009-1 et 010-1.
- Topologie : 022-1, 018-1, 016-1, 004-2, 004-1. Les 5 sont fidèles et justes.
- Probabilités : 016-1, 020-2, 041-1, 007-1, 027-2. **027-2 était incomplète** : la preuve 3 ⇒ 1 du Thm 3.23 n'énonçait pas l'hypothèse lim m_n ≤ α, qui est pourtant indispensable pour (m_∞/(α+ε))^n → 0. Hypothèse ajoutée. Voisines 026-4, 027-1, 028-1 : justes.
- Modélisation : 017-3, 038-1, 016-4, 023-1, 031-1. Fond juste. Sur 016-4, le « cas 1 » n'était défini que par « φ strictement convexe » ; il porte maintenant la condition du poly, P(Z₁=0)+P(Z₁=1) < 1. Même retouche sur 016-3. Sur 016-2, les cas 2 et 3 sont maintenant distingués comme dans le poly.
- Constat général : 3 des « coquilles du poly » signalées par Sonnet en probabilités venaient de l'extraction du texte (crochets et compositions perdus), pas du poly. Une coquille annoncée doit être vérifiée sur l'image de la page.

Vérification : les 4 fichiers se chargent avec `yaml.safe_load` (50, 81, 251 et 152 cartes, ids uniques). `tools/check.py` : OK.

IDS_OPUS: mesure-a-001-1,mesure-a-004-1,mesure-a-004-2,mesure-a-004-3,mesure-a-009-1,mesure-a-009-2,mesure-a-010-1,mesure-a-010-2,mesure-a-014-1,mesure-a-019-1,topo-a-004-3,topo-a-005-1,topo-a-016-4,topo-a-020-1,topo-a-021-1,topo-a-025-1,topo-a-025-2,proba-a-015-2,proba-a-027-2,proba-a-046-1,proba-a-046-2,proba-a-070-4,mod-a-016-2,mod-a-016-3,mod-a-016-4,mod-a-047-1,mod-a-047-2,mod-a-056-2,mod-a-059-2,mod-a-060-1,mod-a-060-2,mod-a-061-2,mod-a-064-2
