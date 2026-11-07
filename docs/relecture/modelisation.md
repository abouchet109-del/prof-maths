# Relecture des cartes de modélisation

Fichier relu : `matieres/modelisation/cartes.yaml`. Poly de référence : `bibliotheque/_texte/modelisation/cours/chap1-galton-watson.txt`, `chap2-markov.txt`, `chap3-poisson.txt`.

Cartes relues : **152** (toutes, avec le texte du poly). Cartes modifiées : **106**. Aucune carte supprimée. Les champs `id`, `notion`, `chapitre`, `priorite`, `tags`, `source` sont inchangés. Le fichier se charge avec `yaml.safe_load`. Aucune erreur mathématique grave n'a été trouvée : les corrections portent surtout sur le cadre du recto, quelques quantificateurs et hypothèses, et le HTML (`<` collé à une lettre).

Les deux erreurs connues du poly (PageRank p. 21, apériodicité p. 9) n'ont pas été réintroduites. Les versos de `mod-a-038-2` (seuil `max n_x + max m_y`) et de `mod-a-059-1`/`mod-a-060-*` suivent la version corrigée.

Abréviations : « cadre GW » = ajout de `Z_0=1`, `(X_{i,j})` i.i.d. à valeurs dans N (et de `m`, `σ²`, `φ` quand le verso les utilise) ; « E fini » = ajout de « sur E fini » (le poly pose E fini pour tout le chapitre 2) ; « cadre M/M/∞ » = ajout de λ>0, μ>0, n₀ clients initiaux.

## Cartes corrigées

| id | défaut | correction |
|---|---|---|
| mod-a-005-2 | recto sans cadre (X à valeurs dans N) | ajout de « X à valeurs dans N » |
| mod-a-006-1 | recto sans cadre (X, p) | ajout de « X à valeurs dans N, p∈N* » |
| mod-a-006-2 | recto sans cadre ; `<` collé dans le verso (`k<p`) | cadre ajouté ; `k < p` |
| mod-a-006-3 | recto sans cadre | ajout de « X à valeurs dans N, p∈N* » |
| mod-a-007-3 | loi géométrique ambiguë (N ou N*) | « loi portée par N*, p∈]0,1] » |
| mod-a-008-2 | recto sans la définition de Z_n | définition de GW rappelée |
| mod-a-008-3 | idem ; `<` collé dans le verso | définition rappelée ; `i < n` |
| mod-a-009-1 | cadre GW ; « espérance » non précisée finie | cadre GW ; « espérance finie » |
| mod-a-009-2 | cadre GW | cadre GW |
| mod-a-009-3 | m, σ² non définis dans le recto | cadre GW, m, σ²<∞ |
| mod-a-010-1 | cadre GW, m non défini | cadre GW, m fini |
| mod-a-010-2 | hypothèse de moment d'ordre 2 absente | cadre GW, m, σ²<∞ |
| mod-a-010-3 | m, σ² non définis | cadre GW, m, σ²<∞ |
| mod-a-011-1 | cadre GW | cadre GW |
| mod-a-011-2 | φ, G_n, GW non posés | cadre GW, φ, G_n, domaine [0,1] |
| mod-a-012-1 | m, σ² non définis ; N non posé | Z_0=N, X i.i.d., m, σ²<∞ |
| mod-a-012-2 | φ non défini | Z_0=N, φ fonction génératrice des X_{i,j} |
| mod-a-013-1 | cadre GW | cadre GW |
| mod-a-013-2 | m non défini | cadre GW, m=E[X_{i,j}] |
| mod-a-014-1 | cadre GW absent | cadre GW |
| mod-a-014-2 | φ non défini | cadre GW, φ |
| mod-a-014-3 | φ, E non définis | cadre GW, φ, E |
| mod-a-014-4 | φ, E non définis | cadre GW, φ, E |
| mod-a-015-1 | cadre GW ; E[X] pouvant valoir +∞ | cadre GW, « éventuellement +∞ » |
| mod-a-015-2 | cadre GW, E non défini | cadre GW, E |
| mod-a-015-3 | cadre GW, E non défini | cadre GW, E |
| mod-a-016-1 | X, φ, m non définis | cadre GW, X=X_{i,j}, φ, m |
| mod-a-016-2 | X, φ non définis | cadre GW, X, φ |
| mod-a-016-3 | hypothèses de la preuve (φ strictement convexe, m≤1) hors du recto | hypothèses ajoutées |
| mod-a-016-4 | hypothèses (φ strictement convexe, m>1) hors du recto | hypothèses ajoutées |
| mod-a-016-5 | X, φ non définis | cadre GW, X, φ |
| mod-a-016-6 | cadre GW incomplet | cadre GW |
| mod-a-017-1 | cadre GW absent | Z_0=1, reproductions i.i.d. |
| mod-a-017-2 | hypothèses (m∈]0,1[, moment d'ordre 2, φ) hors du recto | hypothèses ajoutées |
| mod-a-017-3 | idem | hypothèses ajoutées |
| mod-a-018-1 | cadre GW absent | Z_0=1, reproductions i.i.d. |
| mod-a-018-2 | σ² non défini | Z_0=1, σ²=Var(Z_1) |
| mod-a-019-1 | σ², Z_0 non posés | Z_0=1, m>1, σ²<∞ |
| mod-a-019-2 | W et E non définis | W=lim Z_n/m^n, E, Z_0=1 |
| mod-a-019-3 | σ², W non définis | cadre GW, m, σ², W |
| mod-a-022-1 | E fini non posé | « sur un ensemble fini E » |
| mod-a-022-2 | E fini et P non posés | P markovienne sur E fini |
| mod-a-024-1 | verso : « pour tout n » du poly omis ; recto sans E fini | « pour tout n∈N » ajouté au verso ; recto précisé |
| mod-a-024-2 | recto sans chaîne posée | « chaîne homogène (X_n) » |
| mod-a-025-1 | recto sans cadre | « chaîne homogène sur E fini » |
| mod-a-026-2 | hypothèses du théorème (E fini, U i.i.d., X_0 indépendante, φ) absentes du recto | hypothèses ajoutées |
| mod-a-028-1 | recto sans cadre | chaîne homogène sur E fini |
| mod-a-028-2 | `P(X_n=x)` possiblement nul : conditionnement indéfini | « tels que P(X_n=x)>0 » ajouté au verso ; cadre au recto |
| mod-a-028-3 | recto sans cadre | chaîne homogène sur E fini |
| mod-a-035-1 | E fini non posé | « Chaîne sur E fini » |
| mod-a-035-2 | idem | « Chaîne sur E fini » |
| mod-a-037-1 | E fini non posé | « sur E fini » |
| mod-a-038-1 | E fini non posé | « sur E fini » |
| mod-a-038-2 | E fini (max fini) et hypothèse P(x_0,x_0)>0 non posés | ajoutés au recto |
| mod-a-039-1 | recto sans cadre | P markovienne sur E fini |
| mod-a-040-1 | recto sans cadre | chaîne de matrice P sur E fini |
| mod-a-042-1 | recto sans cadre | P markovienne sur E fini |
| mod-a-043-2 | recto sans cadre | irréductible sur E fini, π invariante |
| mod-a-044-2 | recto sans cadre | P irréductible, E={1,…,N} |
| mod-a-045-1 | `<` collé dans le verso (`k<n`) | `k < n` |
| mod-a-046-1 | E fini non posé | « sur E fini » |
| mod-a-047-1 | vitesse |λ₂|^n énoncée sans réserve alors que le poly ne la démontre que pour P diagonalisable | mention « démontré dans le poly dans le cas P diagonalisable » (voir doutes) |
| mod-a-047-2 | recto sans cadre | P irréductible apériodique sur E fini, diagonalisable |
| mod-a-048-1 | E fini non posé | « sur E fini » |
| mod-a-048-2 | recto sans cadre | chaîne irréductible sur E fini, π |
| mod-a-049-1 | E fini non posé | « sur E fini » |
| mod-a-050-1 | recto sans cadre | chaîne (X_n) à valeurs dans E |
| mod-a-051-2 | recto sans cadre | irréductible sur E fini, π |
| mod-a-052-1 | chaîne X non posée | chaîne homogène de matrice P sur E fini |
| mod-a-053-1 | recto sans cadre | P markovienne sur E fini |
| mod-a-054-1 | recto sans cadre | chaîne de matrice P sur E fini |
| mod-a-054-2 | p_x(a) non défini dans le recto | définition rappelée |
| mod-a-055-1 | p_x(a) et cadre absents | définition et cadre ajoutés |
| mod-a-055-2 | a absorbant, cadre absents | ajoutés |
| mod-a-056-2 | hypothèse 0<ε<1 absente du recto (irréductibilité exige ε<1, apériodicité exige ε>0) | « 0<ε<1 » au recto |
| mod-a-057-1 | modèle et ε non posés | urne d'Ehrenfest, N, 0<ε<1 |
| mod-a-057-2 | idem | idem |
| mod-a-058-1 | ε>0 non précisé | « et ε>0 » |
| mod-a-059-1 | graphe du web non posé | graphe orienté (pages, liens) posé |
| mod-a-059-2 | d⁺(i)≥1 implicite (sinon P non stochastique) | hypothèse ajoutée au recto (voir doutes) |
| mod-a-060-1 | « pour tout β>0 » faux au sens strict : P_β n'est markovienne que pour β∈]0,1] | β∈]0,1] et minoration β/N au verso (voir doutes) |
| mod-a-060-2 | β, Q, μ_n non posés | définitions ajoutées au recto |
| mod-a-061-1 | `<` collé dans le verso (`T_1<T_2`…) | ` < ` |
| mod-a-061-3 | `<` collés dans le verso (`t<T_{n+1}`) ; recto sans cadre | ` < ` ; cadre précisé |
| mod-a-063-1 | recto sans cadre | processus de renouvellement, τ_k i.i.d. > 0 |
| mod-a-063-2 | `<` collés dans le verso ; recto sans cadre | ` < ` ; cadre précisé |
| mod-a-064-2 | quantificateurs « pour tous t, Δt≥0 » absents ; X>0 non posé | ajoutés |
| mod-a-065-1 | λ>0 et t≥0 non posés | ajoutés |
| mod-a-066-1 | λ>0 non posé | ajouté |
| mod-a-067-1 | λ>0, t>0, n≥1 non posés | ajoutés |
| mod-a-067-2 | `<` collé dans le verso ; hypothèses non posées | `0 < u_1 < … < u_n < t` ; hypothèses ajoutées |
| mod-a-068-1 | `<` collés dans le recto ; λ>0 non posé | ` < ` ; λ>0 |
| mod-a-068-2 | quantificateurs de la stationnarité absents ; `<` collé | « pour 0≤s<t et h≥0 » ; ` < ` |
| mod-a-069-1 | λ>0 non posé | ajouté |
| mod-a-070-1 | `<` collé dans le recto ; (N_t) non défini | ` < ` ; Poisson d'intensité λ>0 |
| mod-a-071-1 | N non défini | Poisson d'intensité λ>0 |
| mod-a-072-1 | λ>0 et μ>0 absents du verso | ajoutés |
| mod-a-072-2 | T_i, S_i, R_i, n_0 non posés ; A_t « avant t » alors que T_i ≤ t | cadre posé ; « jusqu'à t » |
| mod-a-073-1 | modèle M/M/∞ non posé | cadre M/M/∞ |
| mod-a-073-2 | idem | cadre M/M/∞ |
| mod-a-074-1 | idem | cadre M/M/∞ |
| mod-a-074-2 | idem | cadre M/M/∞ |
| mod-a-075-1 | idem | cadre M/M/∞ |
| mod-a-075-2 | idem | cadre M/M/∞ |
| mod-a-077-1 | (v_n) non posée comme suite réelle | « suite réelle » |
| mod-a-077-2 | cadre du cas critique absent (m=1, σ²<∞, φ) | ajouté |

## Doutes pour Opus

| id | question précise | page du poly |
|---|---|---|
| mod-a-047-1 | Le poly énonce la vitesse « en \|λ₂\|^n » sans hypothèse. Sa preuve ne couvre que P diagonalisable. Sans diagonalisabilité, un facteur polynomial en n peut apparaître (blocs de Jordan). L'énoncé du poly est-il à garder tel quel (j'ai seulement ajouté « démontré dans le cas diagonalisable ») ? | ch. 2, p. 12 |
| mod-a-047-2 | La preuve écrit une base de vecteurs propres de R^N. Les valeurs propres peuvent être complexes : il faudrait C^N. À corriger ou à garder ? | ch. 2, p. 12 |
| mod-a-060-1 / 060-2 | Le poly dit « pour tout β>0 » pour P_β=(1-β)P+βQ. P_β n'est une matrice markovienne que si β∈]0,1]. J'ai écrit β∈]0,1] ; confirmer. | ch. 2, p. 21 |
| mod-a-059-2 | Le poly définit P(i,j)=1/d⁺(i) sans traiter les pages sans lien sortant (d⁺(i)=0). J'ai ajouté l'hypothèse d⁺(i)≥1 dans le recto. La garder ? | ch. 2, p. 21 |
| mod-a-064-2 | Le poly affirme que les lois exponentielles sont « la famille » vérifiant l'absence de mémoire. La caractérisation est exacte pour une durée X>0 (hors cas dégénérés). Carte laissée en l'état avec « pour tous t, Δt≥0 ». OK ? | ch. 3, p. 3 |
| mod-a-056-2 | Le poly conclut irréductible et apériodique sans condition sur ε. Irréductible exige ε<1, apériodique exige ε>0 (pour ε=0 la chaîne est de période 2). J'ai écrit 0<ε<1. | ch. 2, p. 18-19 |
| mod-a-061-2 | Le poly définit N_t comme le nombre d'événements « avant l'instant t » mais avec T_n ≤ t. Carte inchangée : la formule du verso est exacte, seule la phrase est approximative. À reformuler ? | ch. 3, p. 1 |

IDS_CORRIGES: mod-a-005-2,mod-a-006-1,mod-a-006-2,mod-a-006-3,mod-a-007-3,mod-a-008-2,mod-a-008-3,mod-a-009-1,mod-a-009-2,mod-a-009-3,mod-a-010-1,mod-a-010-2,mod-a-010-3,mod-a-011-1,mod-a-011-2,mod-a-012-1,mod-a-012-2,mod-a-013-1,mod-a-013-2,mod-a-014-1,mod-a-014-2,mod-a-014-3,mod-a-014-4,mod-a-015-1,mod-a-015-2,mod-a-015-3,mod-a-016-1,mod-a-016-2,mod-a-016-3,mod-a-016-4,mod-a-016-5,mod-a-016-6,mod-a-017-1,mod-a-017-2,mod-a-017-3,mod-a-018-1,mod-a-018-2,mod-a-019-1,mod-a-019-2,mod-a-019-3,mod-a-022-1,mod-a-022-2,mod-a-024-1,mod-a-024-2,mod-a-025-1,mod-a-026-2,mod-a-028-1,mod-a-028-2,mod-a-028-3,mod-a-035-1,mod-a-035-2,mod-a-037-1,mod-a-038-1,mod-a-038-2,mod-a-039-1,mod-a-040-1,mod-a-042-1,mod-a-043-2,mod-a-044-2,mod-a-045-1,mod-a-046-1,mod-a-047-1,mod-a-047-2,mod-a-048-1,mod-a-048-2,mod-a-049-1,mod-a-050-1,mod-a-051-2,mod-a-052-1,mod-a-053-1,mod-a-054-1,mod-a-054-2,mod-a-055-1,mod-a-055-2,mod-a-056-2,mod-a-057-1,mod-a-057-2,mod-a-058-1,mod-a-059-1,mod-a-059-2,mod-a-060-1,mod-a-060-2,mod-a-061-1,mod-a-061-3,mod-a-063-1,mod-a-063-2,mod-a-064-2,mod-a-065-1,mod-a-066-1,mod-a-067-1,mod-a-067-2,mod-a-068-1,mod-a-068-2,mod-a-069-1,mod-a-070-1,mod-a-071-1,mod-a-072-1,mod-a-072-2,mod-a-073-1,mod-a-073-2,mod-a-074-1,mod-a-074-2,mod-a-075-1,mod-a-075-2,mod-a-077-1,mod-a-077-2

## Mise au format du poly

Cartes reformatées : **140** sur 152 (recto `Déf :`, `Prop. n :`, `Thm n :`, `Lemme n :`, `Cor. n :`, `Exemple :`, `Preuve :`, `Rem. :` ; verso = énoncé du poly avec son cadre, ou idée de la preuve). Champs `id`, `notion`, `chapitre`, `priorite`, `tags`, `source` inchangés ; 152 cartes avant et après ; le fichier se charge avec `yaml.safe_load`.

Choix de format : les remarques du poly sans catégorie prévue (Remarque 1.1, 1.3, 1.4, 2.1, 2.2, 3.2, commentaires non numérotés) ont le recto `Rem. :` ; les résultats non numérotés du poly ont `Prop. :` ou `Cor. :` avec un nom court. Erreur du poly signalée au verso : `mod-a-038-2` (poly : N = max_x(n_x, m_x), erreur).

Cartes laissées telles quelles (12) :
- `mod-a-076-1`, `mod-a-077-1`, `mod-a-077-2` : tag `prerequis-l1l2` (aucune carte `erreur`, aucun id contenant `-e`).
- `mod-a-047-1`, `mod-a-047-2`, `mod-a-056-2`, `mod-a-059-2`, `mod-a-060-1`, `mod-a-060-2`, `mod-a-061-2`, `mod-a-064-2` : listées dans « Doutes pour Opus ».
- `mod-a-030-2` : le poly ne l'énonce pas (conséquence de la Déf 2.4 sur x -> x, absente du texte).

IDS_REFORMATES: mod-a-001-1,mod-a-001-2,mod-a-002-1,mod-a-002-2,mod-a-002-3,mod-a-002-4,mod-a-003-1,mod-a-004-1,mod-a-004-2,mod-a-005-1,mod-a-005-2,mod-a-006-1,mod-a-006-2,mod-a-006-3,mod-a-007-1,mod-a-007-2,mod-a-007-3,mod-a-008-1,mod-a-008-2,mod-a-008-3,mod-a-009-1,mod-a-009-2,mod-a-009-3,mod-a-010-1,mod-a-010-2,mod-a-010-3,mod-a-011-1,mod-a-011-2,mod-a-012-1,mod-a-012-2,mod-a-013-1,mod-a-013-2,mod-a-014-1,mod-a-014-2,mod-a-014-3,mod-a-014-4,mod-a-015-1,mod-a-015-2,mod-a-015-3,mod-a-016-1,mod-a-016-2,mod-a-016-3,mod-a-016-4,mod-a-016-5,mod-a-016-6,mod-a-017-1,mod-a-017-2,mod-a-017-3,mod-a-018-1,mod-a-018-2,mod-a-019-1,mod-a-019-2,mod-a-019-3,mod-a-020-1,mod-a-020-2,mod-a-020-3,mod-a-021-1,mod-a-021-2,mod-a-022-1,mod-a-022-2,mod-a-023-1,mod-a-024-1,mod-a-024-2,mod-a-025-1,mod-a-025-2,mod-a-026-1,mod-a-026-2,mod-a-027-1,mod-a-028-1,mod-a-028-2,mod-a-028-3,mod-a-029-1,mod-a-030-1,mod-a-031-1,mod-a-032-1,mod-a-033-1,mod-a-033-2,mod-a-034-1,mod-a-035-1,mod-a-035-2,mod-a-035-3,mod-a-036-1,mod-a-036-2,mod-a-037-1,mod-a-038-1,mod-a-038-2,mod-a-039-1,mod-a-040-1,mod-a-041-1,mod-a-042-1,mod-a-043-1,mod-a-043-2,mod-a-044-1,mod-a-044-2,mod-a-045-1,mod-a-046-1,mod-a-048-1,mod-a-048-2,mod-a-049-1,mod-a-050-1,mod-a-051-1,mod-a-051-2,mod-a-052-1,mod-a-053-1,mod-a-054-1,mod-a-054-2,mod-a-055-1,mod-a-055-2,mod-a-056-1,mod-a-057-1,mod-a-057-2,mod-a-058-1,mod-a-059-1,mod-a-061-1,mod-a-061-3,mod-a-062-1,mod-a-063-1,mod-a-063-2,mod-a-064-1,mod-a-065-1,mod-a-065-2,mod-a-066-1,mod-a-066-2,mod-a-066-3,mod-a-067-1,mod-a-067-2,mod-a-068-1,mod-a-068-2,mod-a-069-1,mod-a-070-1,mod-a-071-1,mod-a-071-2,mod-a-072-1,mod-a-072-2,mod-a-073-1,mod-a-073-2,mod-a-074-1,mod-a-074-2,mod-a-075-1,mod-a-075-2
