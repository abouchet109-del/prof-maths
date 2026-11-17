"""Tests des règles d'état et de planification, sur de petites données fictives."""
import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import etat as E  # noqa: E402
import plan as P  # noqa: E402

D = dt.date


def ex(id, matiere="topologie", sc="S1", imp="vital", t=10, **kw):
    e = {"id": id, "titre": id, "matiere": matiere, "sous_chapitre": sc, "importance": imp,
         "temps_min": t, "disponible": True, "annale_prioritaire": False, "annale": None,
         "enonce": "x", "notions": [], "sources": [{"etab": "paris-cite", "fichier": "f.pdf", "page": 1, "numero": "Ex"}]}
    e.update(kw)
    return e


def annale(id, annee, matiere="topologie", t=10):
    return ex(id, matiere, sc="A", imp="secondaire", t=t, annale_prioritaire=True,
              annale={"nature": "exam", "annee": annee}, type_source="annale")


def ctx(exos, resultats=(), dispo=None, **extra):
    for i, e in enumerate(exos):
        e["ordre"] = i
    base = {"debut": "2026-11-03", "fin": "2027-01-10", "examens": "2027-01-11",
            "minutes_exercices_jour": 120, "minutes_cours_jour": 30, "cartes_par_jour": 12,
            "exceptions": [{"type": "off", "du": "2026-11-07", "au": "2026-11-08"},
                           {"type": "quota", "du": "2026-12-21", "au": "2027-01-03", "minutes_exercices_jour": 240}]}
    base.update(dispo or {})
    c = {"exercices": exos, "resultats": list(resultats), "dispo": base,
         "notions": {}, "cartes": [], "anki_plan": {}, "a_revoir": [], "blocs": {}, "avancement": {}}
    c.update(extra)
    return c


def res(d, id, r="reussi"):
    return {"date": D.fromisoformat(d), "exercice": id, "resultat": r}


def ids(plan):
    return [e["id"] for e, _ in plan["items"]]


# ---------------------------------------------------------------- états
def test_cycle_reussite_et_maitrise():
    t0 = D(2026, 11, 3)
    assert E.etat_exercice([], t0)["etat"] == "jamais"
    s = E.etat_exercice([(t0, "reussi")], t0)
    assert s["etat"] == "acquis" and s["du"] == D(2026, 11, 10)
    # réussite trop proche : reste acquis, reprise inchangée
    assert E.etat_exercice([(t0, "reussi"), (D(2026, 11, 6), "reussi")], D(2026, 11, 6))["etat"] == "acquis"
    # 2e réussite à J+7 : maîtrisé, prochaine reprise à J+21
    s = E.etat_exercice([(t0, "reussi"), (D(2026, 11, 10), "reussi")], D(2026, 11, 10))
    assert s["etat"] == "maitrise" and s["du"] == D(2026, 12, 1)


def test_echec_en_reprise_remet_a_revoir():
    t = [(D(2026, 11, 1), "reussi"), (D(2026, 11, 8), "presque")]
    s = E.etat_exercice(t, D(2026, 11, 8))
    assert s["etat"] == "a_revoir"
    assert not s["est_du"] and E.etat_exercice(t, D(2026, 11, 10))["est_du"]   # presque : 2 jours


def test_delais_apres_echec():
    d = D(2026, 11, 3)
    for r, n in [("non_fait", 1), ("presque", 2), ("aide", 3)]:
        s = E.etat_exercice([(d, r)], d)
        assert s["etat"] == "a_revoir" and s["du"] == d + dt.timedelta(n)


# ------------------------------------------------------- passage de catégorie
def test_categorie_suivante_seulement_si_tout_acquis():
    exos = [ex("v1"), ex("v2"), ex("i1", imp="important")]
    h = E.historique([res("2026-11-03", "v1")])
    etats = {e["id"]: E.etat_exercice(h.get(e["id"], []), D(2026, 11, 4)) for e in exos}
    assert E.categorie_ouverte(exos, etats) == "vital"          # v2 pas encore acquis
    h = E.historique([res("2026-11-03", "v1"), res("2026-11-03", "v2", "aide")])
    etats = {e["id"]: E.etat_exercice(h.get(e["id"], []), D(2026, 11, 4)) for e in exos}
    assert E.categorie_ouverte(exos, etats) == "vital"          # aide n'est pas acquis
    h = E.historique([res("2026-11-03", "v1"), res("2026-11-03", "v2")])
    etats = {e["id"]: E.etat_exercice(h.get(e["id"], []), D(2026, 11, 4)) for e in exos}
    assert E.categorie_ouverte(exos, etats) == "important"


def test_bloc_vital_puis_important_puis_secondaire_seulement_ligne_epuisee():
    exos = [ex("i1", imp="important"), ex("v1"), ex("s1", imp="secondaire")]
    c = ctx(exos, dispo={"minutes_exercices_jour": 100})
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["v1", "i1"]      # vital avant important, pas de secondaire
    # v1 et i1 acquis (reprise pas encore due) : la ligne principale est épuisée, le secondaire arrive
    c = ctx(exos, [res("2026-11-04", "v1"), res("2026-11-04", "i1")], dispo={"minutes_exercices_jour": 100})
    assert ids(P.plan_jour(c, D(2026, 11, 5))) == ["s1"]
    # important seulement « à revoir » : le passage de catégorie bloque encore le secondaire
    c = ctx(exos, [res("2026-11-04", "v1"), res("2026-11-04", "i1", "presque")], dispo={"minutes_exercices_jour": 100})
    assert ids(P.plan_jour(c, D(2026, 11, 5))) == []
    assert ids(P.plan_jour(c, D(2026, 11, 6))) == [] and [e["id"] for e in P.plan_jour(c, D(2026, 11, 6))["anki_seul"]] == ["i1"]   # presque : reprise seul dans Anki


# ------------------------------------------------------------------ reprises
def test_reprise_due_prioritaire_et_exclusions():
    exos = [ex("n1"), ex("r1"), ex("dbl", doublon_de="r1"), ex("indispo", disponible=False)]
    c = ctx(exos, [res("2026-11-04", "r1", "non_fait")])
    assert ids(P.plan_jour(c, D(2026, 11, 4)))[:1] == ["n1"]       # pas encore dû le jour même
    p = P.plan_jour(c, D(2026, 11, 5))
    assert ids(p)[0] == "r1" and p["items"][0][1] == "reprise"
    assert "dbl" not in ids(p) and "indispo" not in ids(p)


def test_reprise_acquis_a_j_plus_7():
    c = ctx([ex("a1")], [res("2026-11-04", "a1")])
    assert ids(P.plan_jour(c, D(2026, 11, 10))) == []
    assert [e["id"] for e in P.plan_jour(c, D(2026, 11, 11))["anki_seul"]] == ["a1"]     # réussi : reprise seul dans Anki


# ------------------------------------------------ annales et examens blancs
def test_derniere_annee_reservee_hors_quota():
    exos = [annale("a-old", "2023-24"), annale("a-new", "2024-25")]
    c = ctx(exos)
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["a-old"]
    # en quota, toutes les annales sont possibles, examen blanc en dernier
    assert ids(P.plan_jour(c, D(2026, 12, 22))) == ["a-old", "a-new"]


def test_une_annale_par_jour_hors_quota():
    c = ctx([annale("a1", "2021-22"), annale("a2", "2022-23"), annale("a3", "2024-25")])
    p = P.plan_jour(c, D(2026, 11, 4))
    assert len([g for _, g in p["items"] if g.startswith("annale")]) == 1


# ------------------------------------------------------------ budget et jours
def test_budget_respecte_et_exercice_trop_long_saute():
    exos = [ex("grand", t=100), ex("moyen", t=40), ex("petit", t=15)]
    p = P.plan_jour(ctx(exos), D(2026, 11, 4))
    assert p["minutes"] <= 120
    assert ids(p) == ["grand", "petit"]       # « moyen » ne tient pas et est sauté


def test_budget_quota():
    exos = [ex(f"e{i}", t=30) for i in range(12)]
    assert P.plan_jour(ctx(exos), D(2026, 12, 22))["minutes"] == 240
    assert P.plan_jour(ctx(exos), D(2026, 11, 4))["minutes"] == 120


def test_jour_off_et_hors_periode():
    c = ctx([ex("e1")])
    assert ids(P.plan_jour(c, D(2026, 11, 7))) == []
    assert ids(P.plan_jour(c, D(2027, 1, 11))) == []
    assert ids(P.plan_jour(c, D(2026, 11, 2))) == []


def test_un_seul_bloc_par_jour_une_matiere():
    exos = [ex("t1", "topologie", sc="A"), ex("t2", "topologie", sc="A"),
            ex("p1", "proba", sc="B", t=10), ex("p2", "proba", sc="B", t=10)]
    p = P.plan_jour(ctx(exos, dispo={"minutes_exercices_jour": 50}), D(2026, 11, 4))
    assert {e["matiere"] for e, _ in p["items"]} == {"topologie"}      # première du cycle
    assert p["matiere"] == "topologie" and all(g == "bloc" for _, g in p["items"])


def test_bloc_dans_l_ordre_du_poly():
    exos = [ex("a1", sc="A"), ex("a2", sc="A"), ex("b1", sc="B"), ex("b2", sc="B")]
    c = ctx(exos, [res("2026-11-03", "a1", "non_fait"), res("2026-11-03", "b1")])
    p = P.plan_jour(c, D(2026, 11, 4))
    nouveaux = [e["id"] for e, g in p["items"] if g == "bloc"]
    assert nouveaux[0] == "a2"                # le sous-chapitre A (ordre du poly) avant B


def test_recherche_sujet():
    cou = {"n1": {"statut": "couverte", "notes": [30, 10]}, "n2": {"statut": "couverte", "notes": [10, 20]},
           "n3": {"notes": [99]}}
    cartes = [{"id": "a", "notion": "n1"}, {"id": "b", "notion": "n3"}, {"id": "c", "notion": "n2"}]
    assert P.recherche_sujet(["n1", "n2"], cou, cartes) == '(nid:10,20,30 or "Id:a" or "Id:c")'
    assert P.recherche_sujet(["n9"], cou, cartes) == ""
    assert P.recherche_sujet(["n3"], {}, cartes) == '("Id:b")'


def test_recherche_a_revoir():
    entrees = [{"pour": "2026-11-05", "nid": 30, "raison": "x"}, {"pour": "2026-11-05", "nid": 10},
               {"pour": "2026-11-05", "id": "topo-a-001-1"}, {"pour": "2026-11-06", "nid": 99}]
    assert P.recherche_a_revoir(entrees, "2026-11-05") == '(nid:10,30 or "Id:topo-a-001-1")'
    # échu mais pas consommé : toujours montré tant qu'aucun jour travaillé ne l'a consommé
    assert P.recherche_a_revoir(entrees, "2026-11-07") == '(nid:10,30,99 or "Id:topo-a-001-1")'
    # un résultat enregistré le 05 (jour de `pour`) consomme les entrées du 05, pas celle du 06
    assert P.recherche_a_revoir(entrees, "2026-11-07", ["2026-11-05"]) == "(nid:99)"
    assert P.recherche_a_revoir(entrees, "2026-11-07", ["2026-11-06"]) == ""
    assert P.recherche_a_revoir(entrees, "2026-11-04") == ""            # pas encore échu
    assert P.recherche_a_revoir(None, "2026-11-05") == ""


# ================================================= blocs de sous-chapitre
def sc(n, chap=1):
    return f"Chapitre {chap} - X > {n}"


def test_cle_naturelle_des_sous_chapitres():
    scs = [sc("2.10 b", 2), sc("2.9 a", 2), sc("1.2.3 c"), sc("10.1 z", 10), sc("1.10 d"), sc("1.9 e"),
           "Hors cours actuel > Connexité"]
    assert sorted(scs, key=E.cle_sc) == [sc("1.2.3 c"), sc("1.9 e"), sc("1.10 d"), sc("2.9 a", 2),
                                          sc("2.10 b", 2), sc("10.1 z", 10), "Hors cours actuel > Connexité"]


def test_sous_chapitre_courant_et_avancee():
    exos = [ex("a1", sc=sc("1.9")), ex("a2", sc=sc("1.9"), imp="important"),
            ex("b1", sc=sc("1.10")), ex("c1", sc=sc("2.1", 2)),
            ex("an", sc=sc("1.9"), annale_prioritaire=True, annale={"nature": "exam", "annee": "2020-21"}),
            ex("dbl", sc=sc("1.2"), doublon_de="a1"), ex("ind", sc=sc("1.2"), disponible=False)]

    def plan(resultats, d):
        pl = P.plan_jour(ctx(exos, resultats), d)
        return pl["courants"]["topologie"], pl

    cour, pl = plan([], D(2026, 11, 4))
    assert cour == sc("1.9")                 # 1.9 avant 1.10 ; doublon, indisponible et annale exclus
    assert pl["sous_chapitre"] == sc("1.9") and pl["vitaux"] == (0, 1)
    assert ids(pl)[:2] == ["a1", "a2"]       # vital puis important, puis suite sur les sous-chapitres suivants
    # a1 acquis mais a2 (important) jamais tenté : 1.9 reste courant
    assert plan([res("2026-11-04", "a1")], D(2026, 11, 5))[0] == sc("1.9")
    # a1 acquis et a2 tenté : on passe à 1.10
    cour, pl = plan([res("2026-11-04", "a1"), res("2026-11-04", "a2", "aide")], D(2026, 11, 5))
    assert cour == sc("1.10") and pl["vitaux"] == (0, 1)
    # a1 raté : 1.9 reste courant (vital pas acquis), mais a1 revient en reprise, pas dans le bloc
    cour, pl = plan([res("2026-11-04", "a1", "presque"), res("2026-11-04", "a2")], D(2026, 11, 5))
    assert cour == sc("1.9") and ids(pl) == ["b1", "c1"]


def test_le_bloc_continue_sur_le_sous_chapitre_suivant_si_du_temps():
    exos = [ex("a1", sc=sc("1.1"), t=20), ex("b1", sc=sc("1.2"), t=20), ex("c1", sc=sc("1.3"), t=100)]
    p = P.plan_jour(ctx(exos, dispo={"minutes_exercices_jour": 60}), D(2026, 11, 4))
    assert ids(p) == ["a1", "b1"] and p["sous_chapitre"] == sc("1.1")


def test_le_bloc_ne_saute_pas_a_un_sous_chapitre_plus_loin_pour_boucher_un_trou():
    exos = [ex("a1", sc=sc("1.1"), t=30), ex("a2", sc=sc("1.1"), t=40), ex("a3", sc=sc("1.1"), t=10),
            ex("b1", sc=sc("1.2"), t=5)]
    p = P.plan_jour(ctx(exos, dispo={"minutes_exercices_jour": 50}), D(2026, 11, 4))
    assert ids(p) == ["a1", "a3"]            # a2 est sauté ; b1 (5 min) tiendrait mais est dans un sous-chapitre plus loin


def test_avancement_du_cours_limite_les_sous_chapitres():
    exos = [ex("a1", sc=sc("1.1")), ex("b1", sc=sc("1.2")), ex("c1", sc=sc("1.3"))]
    c = ctx(exos, avancement={"topologie": sc("1.2")})
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["a1", "b1"]
    c = ctx(exos, [res("2026-11-03", "a1"), res("2026-11-03", "b1")], avancement={"topologie": sc("1.2")})
    p = P.plan_jour(c, D(2026, 11, 4))
    assert ids(p) == [] and p["matiere"] is None       # tout est acquis dans la limite : c1 n'est pas planifié
    c["avancement"] = {"topologie": None}
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["c1"]


# ------------------------------------------------------------ rotation
def test_rotation_des_matieres():
    exos = [ex("t1", "topologie"), ex("m1", "mesure"), ex("p1", "proba"), ex("o1", "modelisation"),
            ex("t2", "topologie"), ex("m2", "mesure"), ex("p2", "proba"), ex("o2", "modelisation")]
    blocs = {"2026-11-09": {"matiere": "topologie", "sous_chapitre": "S1"}}

    def matiere(resultats, d, blocs=blocs, e=exos):
        return P.plan_jour(ctx(e, resultats, blocs=blocs), d)["matiere"]

    assert matiere([], D(2026, 11, 9), blocs={}) == "topologie"          # aucun bloc travaillé : le premier
    assert matiere([res("2026-11-09", "t1")], D(2026, 11, 10)) == "mesure"
    blocs2 = {**blocs, "2026-11-10": {"matiere": "mesure", "sous_chapitre": "S1"}}
    assert matiere([res("2026-11-09", "t1"), res("2026-11-10", "m1")], D(2026, 11, 11), blocs2) == "proba"
    blocs3 = {**blocs2, "2026-11-11": {"matiere": "proba", "sous_chapitre": "S1"},
              "2026-11-12": {"matiere": "modelisation", "sous_chapitre": "S1"}}
    r = [res("2026-11-09", "t1"), res("2026-11-10", "m1"), res("2026-11-11", "p1"), res("2026-11-12", "o1")]
    assert matiere(r, D(2026, 11, 13), blocs3) == "topologie"          # le cycle reboucle
    assert matiere(r[:3], D(2026, 11, 12), blocs3) == "modelisation"
    # on saute une matière qui n'a plus rien à planifier (mesure vide)
    sans_mesure = [e for e in exos if e["matiere"] != "mesure"]
    assert matiere([res("2026-11-09", "t1")], D(2026, 11, 10), e=sans_mesure) == "proba"


def test_rotation_jour_planifie_mais_non_travaille():
    exos = [ex("t1", "topologie"), ex("m1", "mesure"), ex("p1", "proba")]
    blocs = {"2026-11-09": {"matiere": "topologie", "sous_chapitre": "S1"},
             "2026-11-10": {"matiere": "mesure", "sous_chapitre": "S1"}}
    # le 10/11 était planifié (mesure) mais aucun résultat ce jour-là : le dernier bloc travaillé est celui du 09/11
    p = P.plan_jour(ctx(exos, [res("2026-11-09", "t1")], blocs=blocs), D(2026, 11, 11))
    assert p["matiere"] == "mesure"
    # un résultat du jour même ou d'un jour postérieur ne compte pas
    p = P.plan_jour(ctx(exos, [res("2026-11-10", "m1")], blocs=blocs), D(2026, 11, 10))
    assert p["matiere"] == "topologie"


# ------------------------------------------------------- plafond des reprises
def test_plafond_des_reprises():
    exos = [ex(f"r{i}", "topologie", sc=sc("1.1"), t=20) for i in range(3)] + [ex("n1", sc=sc("1.2"), t=20)]
    r = [res("2026-11-03", f"r{i}", "non_fait") for i in range(3)]
    p = P.plan_jour(ctx(exos, r), D(2026, 11, 4))
    reprises = [e["id"] for e, g in p["items"] if g == "reprise"]
    assert reprises == ["r0"] and ids(p)[1] == "n1"          # 30 min au plus : une seule de 20 min
    p = P.plan_jour(ctx(exos, r, dispo={"minutes_reprises_max": 45}), D(2026, 11, 4))
    assert [e["id"] for e, g in p["items"] if g == "reprise"] == ["r0", "r1"]
    p = P.plan_jour(ctx(exos, r, dispo={"minutes_reprises_max": 60}), D(2026, 11, 4))
    assert len([1 for _, g in p["items"] if g == "reprise"]) == 3


def test_reprise_plus_longue_que_le_plafond_passe_quand_meme_seule():
    exos = [ex("long", t=50), ex("court", t=10)]
    r = [res("2026-11-03", "long", "non_fait"), res("2026-11-03", "court", "non_fait")]
    p = P.plan_jour(ctx(exos, r), D(2026, 11, 4))
    assert [e["id"] for e, g in p["items"] if g == "reprise"] == ["long"]       # 50 > 30 : seule, plus de court


def test_reprises_toutes_matieres_les_plus_en_retard_d_abord():
    exos = [ex("t", "topologie", t=20), ex("p", "proba", t=20)]
    r = [res("2026-11-04", "t", "aide"), res("2026-11-03", "p", "aide")]       # p dû le 06, t le 07
    p = P.plan_jour(ctx(exos, r, dispo={"minutes_reprises_max": 20}), D(2026, 11, 9))
    assert ids(p)[0] == "p" and p["items"][0][1] == "reprise"


# ---------------------------------------------------------------- annales
def annale_sc(id, annee, scx, matiere="topologie", t=10):
    e = annale(id, annee, matiere, t)
    e["sous_chapitre"] = scx
    return e


def genres_annale(p):
    return [e["id"] for e, g in p["items"] if g.startswith("annale")]


def test_annale_eligible_seulement_si_sous_chapitre_passe():
    exos = [ex("a1", sc=sc("1.1")), ex("a2", sc=sc("1.2")), ex("a3", sc=sc("1.3")),
            annale_sc("an12", "2021-22", sc("1.2")), annale_sc("an13", "2022-23", sc("1.3")),
            annale_sc("blanc", "2024-25", sc("1.1"))]
    # courant = 1.1 : aucune annale (ni 1.2 ni 1.3 ne sont passés)
    assert genres_annale(P.plan_jour(ctx(exos), D(2026, 11, 4))) == []
    # courant = 1.2 : toujours aucune annale de 1.1 ou avant (l'examen blanc est de toute façon réservé)
    assert genres_annale(P.plan_jour(ctx(exos, [res("2026-11-03", "a1")]), D(2026, 11, 4))) == []
    # 1.2 acquis, courant = 1.3 : l'annale de 1.2 est éligible, pas celle de 1.3
    r = [res("2026-11-03", "a1"), res("2026-11-03", "a2")]
    assert genres_annale(P.plan_jour(ctx(exos, r), D(2026, 11, 4))) == ["an12"]


def test_annales_libres_des_et_marge_negative():
    exos = [ex("a1", sc=sc("1.1")), annale_sc("an13", "2022-23", sc("1.3")), annale_sc("fin", "2024-25", sc("1.3"))]
    dispo = {"annales_libres_des": "2026-12-07"}
    assert genres_annale(P.plan_jour(ctx(exos, dispo=dispo), D(2026, 12, 4))) == []
    assert genres_annale(P.plan_jour(ctx(exos, dispo=dispo), D(2026, 12, 7))) == ["an13"]
    # marge négative : capacité (fin proche) < minutes restantes
    court = {"fin": "2026-11-04", "examens": "2026-11-05", "minutes_exercices_jour": 15}
    p = P.plan_jour(ctx(exos, dispo=court), D(2026, 11, 4))
    assert p["bilan"]["marge"] < 0 and genres_annale(p) == ["an13"]
    # sans la pression : la même annale n'est pas éligible
    assert genres_annale(P.plan_jour(ctx(exos), D(2026, 11, 4))) == []


def test_annale_quand_la_ligne_principale_est_epuisee_et_limite_du_cours():
    exos = [ex("a1", sc=sc("1.1")), annale_sc("an12", "2022-23", sc("1.2")), annale_sc("an14", "2021-22", sc("1.4")),
            annale_sc("blanc", "2024-25", sc("1.1"))]
    r = [res("2026-11-03", "a1")]       # ligne principale épuisée : toutes les annales sont passées
    assert genres_annale(P.plan_jour(ctx(exos, r), D(2026, 11, 4))) == ["an12"]
    # cours vu jusqu'à 1.2 seulement : l'annale de 1.4 n'est pas éligible
    c = ctx(exos, r + [res("2026-11-03", "an12")], avancement={"topologie": sc("1.2")})
    assert genres_annale(P.plan_jour(c, D(2026, 11, 5))) == []


def test_examen_blanc_reserve_reste_hors_quota():
    exos = [ex("a1", sc=sc("1.1")), annale_sc("old", "2022-23", sc("1.1")), annale_sc("new", "2024-25", sc("1.1"))]
    r = [res("2026-11-03", "a1")]
    assert genres_annale(P.plan_jour(ctx(exos, r), D(2026, 11, 4))) == ["old"]
    assert genres_annale(P.plan_jour(ctx(exos, r), D(2026, 12, 22))) == ["old", "new"]


# ----------------------------------------------------------------- cartes
def carte(id, notion, tags=()):
    return {"id": id, "notion": notion, "recto": "r", "verso": "v", "tags": list(tags)}


def notion(id, chap, sous, m="topologie"):
    return {"id": id, "titre": id, "matiere": m, "chapitre": chap, "sous_chapitre": sous,
            "source": {"fichier": "f.pdf", "page": 1}}


def ctx_cartes(**kw):
    exos = [ex("a1", sc=sc("1.1"), notions=["n-a"]), ex("b1", sc=sc("1.2"), notions=["n-b"]),
            ex("c1", sc=sc("1.3"), notions=["n-c"])]
    notions = {"n-a": notion("n-a", "Chapitre 1 - X", "1.1"), "n-b": notion("n-b", "Chapitre 1 - X", "1.2"),
               "n-c": notion("n-c", "Chapitre 1 - X", "1.3"), "n-a2": notion("n-a2", "Chapitre 1 - X", "1.1"),
               "n-d": notion("n-d", "Chapitre 1 - X", "1.4")}
    cartes = [carte("cD", "n-d"), carte("cC1", "n-c"), carte("cB1", "n-b"), carte("cB2", "n-b"),
              carte("cA1", "n-a"), carte("cA2", "n-a2"), carte("cA3", "n-a"),
              carte("eT", "n-d", ["erreur"]), carte("eM", "n-c", ["erreur"]),
              carte("rev", "n-d")]
    return ctx(exos, notions=notions, cartes=cartes, a_revoir=[{"pour": "2026-11-03", "id": "rev"}], **kw)


def anki_ids(c, p):
    return P.anki(c, p)["nouvelles"]


def test_cartes_ordre_erreurs_arevoir_bloc_puis_suivant():
    c = ctx_cartes(dispo={"cartes_par_jour": 100})
    p = P.plan_jour(c, D(2026, 11, 4))
    # sous-chapitre du bloc : 1.1 (n-a, et n-a2 rattachée par notions.yaml), puis 1.2, 1.3, 1.4
    assert anki_ids(c, p) == ["eT", "eM", "rev", "cA1", "cA2", "cA3", "cB1", "cB2", "cC1", "cD"]
    c["dispo"]["cartes_par_jour"] = 5
    assert anki_ids(c, p) == ["eT", "eM", "rev", "cA1", "cA2"]
    assert anki_ids(c, P.plan_jour(c, D(2026, 11, 7))) == []     # jour off
    # progression linéaire : bloc en 1.3, les cartes restantes de 1.1 et 1.2 passent d'abord, dans l'ordre
    c["dispo"]["cartes_par_jour"] = 100
    p3 = {**p, "sous_chapitre": sc("1.3")}
    assert anki_ids(c, p3) == ["eT", "eM", "rev", "cA1", "cA2", "cA3", "cB1", "cB2", "cC1", "cD"]


def test_cartes_jamais_donnees_deux_fois_et_replanification_stable():
    c = ctx_cartes(dispo={"cartes_par_jour": 4})
    p = P.plan_jour(c, D(2026, 11, 4))
    jour1 = anki_ids(c, p)
    assert jour1 == ["eT", "eM", "rev", "cA1"]
    c["anki_plan"] = {"2026-11-04": jour1}
    assert anki_ids(c, p) == jour1                                  # même date : identique
    # jour non travaillé (aucun résultat le 04) : ses cartes reviennent le lendemain
    assert anki_ids(c, P.plan_jour(c, D(2026, 11, 5))) == jour1
    c["resultats"] = [res("2026-11-04", "zz", "aide")]
    jour2 = anki_ids(c, P.plan_jour(c, D(2026, 11, 5)))
    assert not set(jour1) & set(jour2) and jour2 == ["cA2", "cA3", "cB1", "cB2"]


def test_cartes_limitees_a_l_avancement_du_cours():
    c = ctx_cartes(dispo={"cartes_par_jour": 100}, avancement={"topologie": sc("1.2")})
    assert anki_ids(c, P.plan_jour(c, D(2026, 11, 4))) == ["eT", "eM", "rev", "cA1", "cA2", "cA3", "cB1", "cB2"]


def test_cartes_exercice_passent_avec_les_erreurs_avant_le_bloc():
    c = ctx_cartes(dispo={"cartes_par_jour": 100})
    c["cartes"].append({**carte("xT", "n-d", ["exercice"]), "exercice": "a1"})
    p = P.plan_jour(c, D(2026, 11, 4))
    # depuis le 09/11/2026 : les cartes d'exercices sont à part (liste « exercices »), le cours garde son ordre
    assert anki_ids(c, p) == ["eT", "eM", "rev", "cA1", "cA2", "cA3", "cB1", "cB2", "cC1", "cD"]
    assert P.anki(c, p)["exercices"] == ["xT"]
    c["dispo"]["cartes_par_jour"] = 3
    assert anki_ids(c, p) == ["eT", "eM", "rev"] and P.anki(c, p)["exercices"] == ["xT"]   # plafonds séparés
    c["anki_plan"] = {"2026-11-04": ["eT", "eM", "rev", "xT"]}
    c["resultats"] = [res("2026-11-04", "zz", "aide")]
    assert "xT" not in P.anki(c, P.plan_jour(c, D(2026, 11, 5)))["exercices"]  # donnée une seule fois


# ----------------------------------------------------------- check.py
def test_check_cartes_exercice(tmp_path):
    import yaml
    import check as C
    (tmp_path / "state").mkdir()
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    e = {**ex("topologie-1"), "sources": [{}]}
    e.pop("matiere")
    ecrire("state/dispo.yaml", ctx([])["dispo"])
    ecrire("state/resultats.yaml", [])
    ecrire("matieres/topologie/exercices.yaml", [e])
    ecrire("matieres/topologie/notions.yaml", [{"id": "n", "type": "definition", "chapitre": "Chapitre 1 - X",
                                                "sous_chapitre": "1.1"}])
    ok = {**carte("ex-topologie-1", "n", ["exercice"]), "exercice": "topologie-1", "chapitre": "Chapitre 1 - X"}
    cours = {**carte("cours-1", "n", ["definition"]), "chapitre": "Chapitre 1 - X"}
    ecrire("matieres/topologie/cartes.yaml", [cours, ok])
    assert C.verifier(tmp_path) == []
    # tag sans champ, champ sans tag, exercice inconnu, mauvaise matière, doublon, notion absente
    cas = [({**ok, "tags": []}, "vont ensemble"),
           ({**ok, "tags": ["exercice"], "exercice": None}, "vont ensemble"),
           ({**ok, "exercice": "inconnu"}, "exercice inconnu"),
           ({k: v for k, v in ok.items() if k != "notion"}, "sans champ notion"),
           ({**ok, "chapitre": "Chapitre 9 - Y"}, "chapitre inconnu")]
    for carte_mauvaise, attendu in cas:
        ecrire("matieres/topologie/cartes.yaml", [cours, carte_mauvaise])
        assert any(attendu in x for x in C.verifier(tmp_path)), attendu
    ecrire("matieres/topologie/cartes.yaml", [cours, ok, {**ok, "id": "autre"}])
    assert any("deux cartes pour l'exercice" in x for x in C.verifier(tmp_path))
    ecrire("matieres/topologie/cartes.yaml", [])
    ecrire("matieres/mesure/cartes.yaml", [cours, ok])
    assert any("est en topologie" in x for x in C.verifier(tmp_path))


# ----------------------------------------------------------- notions de prérequis L1-L2
def ctx_prerequis(**kw):
    exos = [ex("c1", sc=sc("1.3"), notions=["n-c"]), ex("d1", sc=sc("3.2", 3), notions=["n-d"])]
    notions = {"n-c": notion("n-c", "Chapitre 1 - X", "1.3"), "n-d": notion("n-d", "Chapitre 3 - X", "3.2"),
               "p-d": {**notion("p-d", "Chapitre 3 - X", "3.2"), "type": "prerequis", "requis_par": ["d1"]}}
    cartes = [carte("cC1", "n-c"), carte("cC2", "n-c"), carte("cD1", "n-d"), carte("pD", "p-d")]
    return ctx(exos, notions=notions, cartes=cartes, **kw)


def test_carte_prerequis_du_chapitre_3_ne_sort_pas_pendant_le_1_3():
    c = ctx_prerequis(dispo={"cartes_par_jour": 2})
    p = {**P.plan_jour(c, D(2026, 11, 4)), "sous_chapitre": sc("1.3")}
    assert anki_ids(c, p) == ["cC1", "cC2"]                          # ni pD ni cD1 en tête de matière
    c["dispo"]["cartes_par_jour"] = 100
    assert anki_ids(c, p) == ["cC1", "cC2", "pD", "cD1"]            # elle vient avec le 3.2, prérequis d'abord


def test_au_3_2_la_carte_prerequis_passe_avant_les_cartes_du_poly():
    c = ctx_prerequis(dispo={"cartes_par_jour": 100})
    c["cartes"] = [x for x in c["cartes"] if x["notion"] != "n-c"]   # cD1 est listée avant pD dans les données
    p = {**P.plan_jour(c, D(2026, 11, 4)), "sous_chapitre": sc("3.2", 3)}
    assert anki_ids(c, p) == ["pD", "cD1"]
    # cours du jour et anciennes notes : le prérequis en premier
    assert P.notions_sc(c, c["exercices"], "topologie", sc("3.2", 3)) == ["p-d", "n-d"]
    c["couverture"] = {"p-d": {"statut": "couverte", "notes": [1]}, "n-d": {"statut": "couverte", "notes": [2]}}
    assert P.anciennes_notes(c, p) == [1, 2]
    # les prérequis qu'utilisent les exercices du jour sont des sujets du jour
    assert P.notions_des_exercices(c, {"items": [(c["exercices"][1], "bloc")]}) == {"n-d", "p-d"}
    assert P.notions_des_exercices(c, {"items": [(c["exercices"][0], "bloc")]}) == {"n-c"}


def test_check_notions_prerequis(tmp_path):
    import yaml
    import check as C
    (tmp_path / "state").mkdir()
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    e = {**ex("topologie-1", sc=sc("1.1")), "sources": [{}]}
    e.pop("matiere")
    ecrire("state/dispo.yaml", ctx([])["dispo"])
    ecrire("state/resultats.yaml", [])
    ecrire("matieres/topologie/exercices.yaml", [e])
    poly = {"id": "topo-n-0001", "type": "definition", "titre": "t", "chapitre": "Chapitre 1 - X",
            "sous_chapitre": "1.1", "enonce": "e"}
    pre = {**poly, "id": "topo-p-0001", "type": "prerequis", "requis_par": ["topologie-1"]}
    cours = {**carte("c1", "topo-n-0001", ["definition"]), "chapitre": "Chapitre 1 - X"}
    cp = {**carte("c2", "topo-p-0001", ["prerequis-l1l2"]), "chapitre": "Chapitre 1 - X"}
    ecrire("matieres/topologie/cartes.yaml", [cours, cp])
    ecrire("matieres/topologie/notions.yaml", [poly, pre])
    assert C.verifier(tmp_path) == []
    cas = [([poly, {**pre, "requis_par": []}], [cours, cp], "requis_par"),
           ([poly, {k: v for k, v in pre.items() if k != "requis_par"}], [cours, cp], "requis_par"),
           ([poly, {**pre, "requis_par": ["inconnu"]}], [cours, cp], "requis_par inconnu"),
           ([poly, {**pre, "sous_chapitre": "9.9"}], [cours, cp], "sous-chapitre inconnu"),
           ([poly, {**pre, "id": "topo-n-0002"}], [cours, {**cp, "notion": "topo-n-0002"}], "id attendu"),
           ([poly, pre, {**pre}], [cours, cp], "en double"),
           ([poly, pre], [cours, {**cp, "notion": None}], "sans notion"),
           ([poly, pre], [cours, {**cp, "notion": "topo-p-0009"}], "notion inconnue"),
           ([poly, pre], [cours, {**cp, "chapitre": "Chapitre 2 - Y"}], "chapitre")]
    for notions, cartes, attendu in cas:
        ecrire("matieres/topologie/notions.yaml", notions)
        ecrire("matieres/topologie/cartes.yaml", cartes)
        assert any(attendu in x for x in C.verifier(tmp_path)), attendu
    # une carte d'erreur peut ne pas avoir de notion
    ecrire("matieres/topologie/notions.yaml", [poly, pre])
    ecrire("matieres/topologie/cartes.yaml", [cours, cp, {**carte("e1", None, ["erreur"]), "chapitre": "Chapitre 1 - X"}])
    assert C.verifier(tmp_path) == []


def test_anciennes_notes_dans_la_file_du_poly():
    """17/11/2026 : les anciennes notes suivent l'ordre du poly avec les cartes du système, dans le même plafond."""
    cou = {"n-a": {"statut": "couverte", "notes": list(range(100, 108))},
           "n-a2": {"statut": "partielle", "notes": [105, 200, 201, 202, 203]},
           "n-b": {"statut": "couverte", "notes": [300]}}
    c = ctx_cartes(dispo={"cartes_par_jour": 8}, couverture=cou)
    p = P.plan_jour(c, D(2026, 11, 4))
    a = P.anki(c, p)
    assert a["nouvelles"][:6] == ["eT", "eM", "rev", "cA1", "cA2", "cA3"]
    assert a["anciennes"][:2] == [100, 101]                  # après les cartes du système du 1.1, dans le plafond
    assert len(a["anciennes"]) == len(set(a["anciennes"]))    # 105 une seule fois
    if 300 in a["anciennes"]:
        assert a["anciennes"].index(203) < a["anciennes"].index(300)     # le 1.1 fini avant le 1.2
    lignes = P.rediger(c, p, a)
    requete = lignes[lignes.index("```", lignes.index(next(l for l in lignes if l.startswith("## Anki — cours, à apprendre")))) + 1]
    assert requete.endswith("(is:new or (is:learn -is:review)) -is:suspended") and "nid:100," in requete
    # le lendemain (sans Anki) : les notes déjà données ne reviennent pas
    c["anciennes_donnees"] = {"2026-11-04": a["anciennes"]}
    c["resultats"] = [res("2026-11-04", "zz", "aide")]
    assert not set(P.anki(c, P.plan_jour(c, D(2026, 11, 5)))["anciennes"]) & set(a["anciennes"])
    assert P.anki(c, P.plan_jour(c, D(2026, 11, 7)))["anciennes"] == []          # jour off : rien
    c2 = ctx_cartes(dispo={"cartes_par_jour": 2})
    assert P.anki(c2, P.plan_jour(c2, D(2026, 11, 4)))["anciennes"] == []         # sans couverture : rien


def test_paquet_anki_des_cartes_d_exercices():
    import anki as A
    cours = A.nom_paquet("topologie", "Chapitre 1 - Espace métrique")
    chapitre = "tg::Maths::L3 Paris Cité::Topologie::Chapitre 1 - Espace métrique"
    assert cours == chapitre + "::Cours"
    assert A.nom_paquet("topologie", "Chapitre 1 - Espace métrique", exercice=True) == chapitre + "::Exercices"


# ------------------------------------------- fusion AoutLicenceMath (anki_connect, sans réseau)
def test_cible_fusion_aoutlicence():
    import anki_connect as AC
    ch1, ch2 = "Chapitre 1 - Espace métrique", "Chapitre 2 - Espace complet"
    base = "tg::Maths::L3 Paris Cité::Topologie::"
    cours = "tg::Maths::AoutLicenceMath::Topologie::Chapitre 3"
    td = "tg::Maths::AoutLicenceMath::Topologie::TD2"
    assert AC.cible(cours, [("topologie", ch1)]) == (base + ch1 + "::Cours", "rattache")
    # plusieurs chapitres : le premier du poly (Chapitre 2 avant Chapitre 10)
    assert AC.cible(cours, [("topologie", "Chapitre 10 - Z"), ("topologie", ch2)]) == (base + ch2 + "::Cours", "ambigu")
    assert AC.cible(cours, [("topologie", ch1), ("topologie", ch1)])[1] == "rattache"
    # paquet TD rattachable : sous-paquet Exercices
    assert AC.cible(td, [("topologie", ch2)]) == (base + ch2 + "::Exercices", "rattache")
    # sans rattachement, ou seulement une autre matière : « Autres » de la matière de l'ancien paquet
    autres = base + "Autres (AoutLicenceMath)"
    assert AC.cible(cours, []) == (autres, "sans_rattachement")
    assert AC.cible(td, []) == (autres, "sans_rattachement")
    assert AC.cible(cours, [("proba", "Chapitre 2 - V")]) == (autres, "autre_matiere")
    mesure = AC.cible("tg::Maths::AoutLicenceMath::TH mesure::Chapitre 1", [("mesure", "Chapitre 1 - T")])
    assert mesure[0] == "tg::Maths::L3 Paris Cité::Mesure et intégration::Chapitre 1 - T::Cours"
    # rattachement par lot (rattachement_ancien.yaml), seulement si la couverture ne donne rien dans la matière
    lot = ("topologie", ch2, False)
    assert AC.cible(cours, [], lot) == (base + ch2 + "::Cours", "classe")
    assert AC.cible(cours, [("proba", "Chapitre 2 - V")], lot) == (base + ch2 + "::Cours", "classe")
    assert AC.cible(cours, [("topologie", ch1)], lot) == (base + ch1 + "::Cours", "rattache")     # la couverture prime
    assert AC.cible(td, [], lot) == (base + ch2 + "::Exercices", "classe")
    assert AC.cible(cours, [], ("topologie", ch2, True)) == (base + ch2 + "::Exercices", "classe")
    assert AC.cible(cours, [], ("mesure", "Chapitre 1 - T", False)) == (autres, "sans_rattachement")   # autre matière
    # ancien paquet inconnu : la note ne bouge pas
    assert AC.cible("tg::Maths::AoutLicenceMath::Autre::X", [("topologie", ch1)]) == (None, "matiere_inconnue")


def test_index_notes_via_couverture_et_notions(tmp_path):
    import yaml
    import anki_connect as AC
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    ecrire("matieres/topologie/notions.yaml", [{"id": "t1", "chapitre": "Chapitre 1 - X", "sous_chapitre": "1.1"},
                                              {"id": "t2", "chapitre": "Chapitre 2 - Y", "sous_chapitre": "2.1"}])
    ecrire("matieres/topologie/couverture.yaml", {"t1": {"statut": "couverte", "notes": [1, 2]},
                                                  "t2": {"statut": "partielle", "notes": [2]},
                                                  "t3": {"statut": "absente", "notes": []}})
    idx = AC.index_notes(tmp_path)
    assert idx[1] == [("topologie", "Chapitre 1 - X")]
    assert idx[2] == [("topologie", "Chapitre 1 - X"), ("topologie", "Chapitre 2 - Y")]
    # rattachement_ancien.yaml : chapitre simple, TD (exercices), null ignoré ; chapitre inconnu refusé
    (tmp_path / "inventaire" / "anki").mkdir(parents=True)
    ecrire("inventaire/anki/rattachement_ancien.yaml",
           {10: "Chapitre 2 - Y", 11: {"chapitre": "Chapitre 1 - X", "exercices": True}, 12: None})
    assert AC.charger_ancien(tmp_path) == {10: ("topologie", "Chapitre 2 - Y", False),
                                            11: ("topologie", "Chapitre 1 - X", True)}
    ecrire("inventaire/anki/rattachement_ancien.yaml", {10: "Chapitre 9 - ?"})
    with pytest.raises(SystemExit):
        AC.charger_ancien(tmp_path)
    assert AC.charger_ancien(tmp_path / "vide") == {}


def test_fusion_range_une_ancienne_note_couvrant_un_prerequis_dans_le_paquet_du_chapitre(tmp_path):
    import yaml
    import anki_connect as AC
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    ecrire("matieres/topologie/notions.yaml", [
        {"id": "topo-p-0001", "type": "prerequis", "chapitre": "Chapitre 3 - Espace compact", "sous_chapitre": "3.2 S",
         "requis_par": ["topo-td4-ex08"]}])
    ecrire("matieres/topologie/couverture.yaml", {"topo-p-0001": {"statut": "couverte", "notes": [7]}})
    idx = AC.index_notes(tmp_path)
    assert idx[7] == [("topologie", "Chapitre 3 - Espace compact")]
    deck = "tg::Maths::AoutLicenceMath::Topologie::Compacité"
    assert AC.cible(deck, idx[7]) == ("tg::Maths::L3 Paris Cité::Topologie::Chapitre 3 - Espace compact::Cours", "rattache")


def test_fusion_prerequis_range_toute_source_sauf_les_paquets_ecg(tmp_path):
    import json
    import yaml
    import anki_connect as AC
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    ecrire("matieres/proba/notions.yaml", [
        {"id": "proba-p-0006", "type": "prerequis", "chapitre": "Chapitre 3 - C", "sous_chapitre": "3.5.1 D",
         "requis_par": ["x"]},
        {"id": "proba-n-0001", "chapitre": "Chapitre 1 - R", "sous_chapitre": "1.3 P"}])
    ecrire("matieres/proba/couverture.yaml", {"proba-p-0006": {"statut": "partielle", "notes": [1, 2, 3]},
                                              "proba-n-0001": {"statut": "couverte", "notes": [4]}})
    prereq = AC.index_notes(tmp_path, prerequis_seuls=True)
    assert set(prereq) == {1, 2, 3}                       # la notion du poly n'entre pas
    cible = "tg::Maths::L3 Paris Cité::Probabilités 5::Chapitre 3 - C::Cours"
    centrale = "tg::Maths::Mathématiques DD centrale::Séance 1 :Nombres complexes::Cours"
    ecg1 = "tg::Maths::1ere année::01 - Logique et Théorie des Ensembles"
    ecg2 = "tg::Maths::Cours deuxième année::Chapitre 06 Algèbre linéaire et produits scalaires"
    topo = "tg::Maths::AoutLicenceMath::Topologie::Chapitre 2"
    assert AC.est_ecg(ecg1) and AC.est_ecg(ecg2) and AC.est_ecg("tg::Maths::1ere année")
    assert not AC.est_ecg(centrale) and not AC.est_ecg("tg::Maths::1ere années bis")
    # Paquet ECG : jamais déplacé, même cité par un prérequis, avec ou sans rattachement par ailleurs.
    assert AC.cible_prerequis(ecg1, prereq[1]) == (None, "ecg")
    assert AC.cible_fusion(ecg2, [("proba", "Chapitre 3 - C")], None, prereq[1]) == (None, "ecg")
    # Autre paquet (Centrale) : rangé dans le chapitre du prérequis.
    assert AC.cible_fusion(centrale, prereq[1], None, prereq[1]) == (cible, "prerequis")
    # Ancienne note AoutLicenceMath d'une autre matière : le prérequis prime sur « Autres » et sur le lot.
    assert AC.cible_fusion(topo, prereq[1], ("topologie", "Chapitre 2 - Y", False), prereq[1]) == (cible, "prerequis")
    # Sans --prerequis : comportement inchangé.
    assert AC.cible_fusion(centrale, [], None, None) == (None, "matiere_inconnue")
    # Bout en bout hors ligne : seules les notes non ECG bougeraient.
    (tmp_path / "inventaire" / "anki").mkdir(parents=True)
    lignes = [{"id": 1, "deck": centrale, "champs": ["a"]}, {"id": 2, "deck": ecg1, "champs": ["b"]},
              {"id": 3, "deck": ecg2, "champs": ["c"]}, {"id": 5, "deck": ecg1, "champs": ["d"]}]
    (tmp_path / "inventaire" / "anki" / "notes.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in lignes), encoding="utf-8")
    notes = AC.notes_hors_ligne(tmp_path, prereq)
    assert [n[0] for n in notes] == [1, 2, 3]             # la note 5 (ECG, non citée) n'est même pas lue
    plan = AC.plan_fusion(notes, AC.index_notes(tmp_path), {}, prereq)
    assert plan == {1: (cible, "prerequis"), 2: (None, "ecg"), 3: (None, "ecg")}
    assert AC.bougent(plan) == 1


def test_nom_de_chapitre_des_cartes_de_cours_prime_sur_les_notions(tmp_path):
    import yaml
    import anki_connect as AC
    (tmp_path / "matieres" / "mesure").mkdir(parents=True)
    for m in E.MATIERES[:1] + E.MATIERES[2:]:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    ecrire("matieres/mesure/notions.yaml", [{"id": "m1", "chapitre": "Chapitre 5 - Espaces $L^p$ (UVSQ)", "sous_chapitre": "x"}])
    ecrire("matieres/mesure/cartes.yaml", [{"id": "c", "notion": "m1", "chapitre": "Chapitre 5 - Espaces Lp (UVSQ)"}])
    ecrire("matieres/mesure/couverture.yaml", {"m1": {"statut": "couverte", "notes": [5]}})
    assert AC.index_notes(tmp_path)[5] == [("mesure", "Chapitre 5 - Espaces Lp (UVSQ)")]


# ------------------------------------------- stabilité de bout en bout
def test_replanifier_la_meme_date_redonne_le_meme_bloc(tmp_path):
    import yaml
    (tmp_path / "state").mkdir()
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
        with open(tmp_path / "matieres" / m / "exercices.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump([ex(f"{m}-1", m, sc=sc("1.1")), ex(f"{m}-2", m, sc=sc("1.2"))], f)
    donnees = {"dispo.yaml": ctx([])["dispo"],
               "resultats.yaml": [{"date": "2026-11-09", "exercice": "topologie-1", "resultat": "reussi", "palier_aide": 0}],
               "blocs.yaml": {"2026-11-09": {"matiere": "topologie", "sous_chapitre": sc("1.1")}}}
    for nom, d in donnees.items():
        with open(tmp_path / "state" / nom, "w", encoding="utf-8") as f:
            yaml.safe_dump(d, f)
    l1 = P.jour(D(2026, 11, 10), tmp_path)
    blocs1 = (tmp_path / "state" / "blocs.yaml").read_text(encoding="utf-8")
    l2 = P.jour(D(2026, 11, 10), tmp_path)
    assert l1 == l2 and (tmp_path / "state" / "blocs.yaml").read_text(encoding="utf-8") == blocs1
    assert l1[2].startswith("Bloc du jour : Mesure — ") and "(vitaux acquis 0/1)" in l1[2]
    assert len(l1) <= P.MAX_LIGNES
    assert E.charger_yaml(tmp_path / "state" / "blocs.yaml")["2026-11-10"]["matiere"] == "mesure"


# ======================================================= séance (état réel, Anki lu)
class FauxAnki:
    """Faux client Anki : `nouvelles` = ids de cartes encore is:new, `nids` = anciennes notes encore is:new."""
    def __init__(self, nouvelles=(), nids=()):
        self.nouvelles, self.nids, self.appels = set(nouvelles), set(nids), 0

    def disponible(self):
        return True

    def ids_nouveaux(self, ids):
        self.appels += 1
        return {i for i in ids if i in self.nouvelles}

    def nids_nouveaux(self, nids):
        return {n for n in nids if n in self.nids}


TOUTES = {"eT", "eM", "rev", "cA1", "cA2", "cA3", "cB1", "cB2", "cC1", "cD"}


def test_seance_un_jour_off_donne_un_plan_complet_alors_que_jour_ne_donne_rien():
    c = ctx_cartes(dispo={"cartes_par_jour": 100})
    off = D(2026, 11, 7)                                       # off dans la dispo de test
    assert ids(P.plan_jour(c, off)) == []
    p = P.plan_jour(c, off, seance=True)
    assert ids(p) == ["a1", "b1", "c1"] and not p["info"]["off"] and p["info"]["minutes_exercices"] == 120
    assert anki_ids(c, p)[:3] == ["eT", "eM", "rev"]           # cartes aussi
    # la séance du jour off compte dans la capacité (le 08 reste off)
    assert p["bilan"]["capacite"] == P.plan_jour(c, D(2026, 11, 9))["bilan"]["capacite"] + 120


def test_cartes_vues_si_et_seulement_si_plus_nouvelles_dans_anki():
    c = ctx_cartes(dispo={"cartes_par_jour": 4})
    p = P.plan_jour(c, D(2026, 11, 4), seance=True)
    tout_nouveau = FauxAnki(TOUTES)
    assert P.anki(c, p, tout_nouveau)["nouvelles"] == ["eT", "eM", "rev", "cA1"]
    # eT et cA1 apprises dans Anki : les 4 premières non vues sont décalées, sans aucune réservation à l'avance
    vu = FauxAnki(TOUTES - {"eT", "cA1"})
    assert P.anki(c, p, vu)["nouvelles"] == ["eM", "rev", "cA2", "cA3"]
    # même si le journal anki_plan dit autre chose : seul Anki fait foi
    c["anki_plan"] = {"2026-11-03": ["eM"]}
    c["resultats"] = [res("2026-11-02", "zz", "aide")]
    assert P.anki(c, p, vu)["nouvelles"] == ["eM", "rev", "cA2", "cA3"]
    # deux séances de suite sans rien apprendre : même proposition
    assert P.anki(c, p, tout_nouveau)["nouvelles"] == P.anki(c, p, tout_nouveau)["nouvelles"]
    # lecture par lots de 40 : on s'arrête dès que le plafond est atteint
    petit = FauxAnki({"x0", "x41", "x80"})
    assert P.premieres_nouvelles(petit, ["x%d" % k for k in range(200)], 2) == ["x0", "x41"]
    assert petit.appels == 2


def test_anciennes_notes_lues_dans_anki():
    cou = {"n-a": {"statut": "couverte", "notes": [100, 101, 102]}, "n-a2": {"statut": "couverte", "notes": [103]}}
    c = ctx_cartes(couverture=cou)
    p = P.plan_jour(c, D(2026, 11, 4), seance=True)
    a = P.anki(c, p, FauxAnki(TOUTES, nids={101, 103, 999}))
    assert a["anciennes"] == [101, 103]                                  # seules les is:new, dans l'ordre
    # sans Anki : règle estimée (journal) ; un jour travaillé avec ces notes proposées les écarte
    c["anciennes_donnees"] = {"2026-11-03": [100, 101]}
    c["resultats"] = [res("2026-11-03", "zz", "aide")]
    assert P.anki(c, p)["anciennes"] == [102, 103]


def test_cartes_non_exportees_ne_sont_pas_proposees_et_sont_signalees():
    c = ctx_cartes(dispo={"cartes_par_jour": 4}, exportees=TOUTES - {"eM"})
    p = P.plan_jour(c, D(2026, 11, 4), seance=True)
    a = P.anki(c, p, FauxAnki(TOUTES))
    assert a["nouvelles"] == ["eT", "rev", "cA1", "cA2"] and a["non_exportees"] == 1
    assert "1 cartes pas encore exportées" in "\n".join(P.rediger(c, p, a))


def test_anki_ferme_repli_sur_l_estimation_et_le_dit():
    c = ctx_cartes(dispo={"cartes_par_jour": 3})
    p = P.plan_jour(c, D(2026, 11, 4), seance=True)
    a = P.anki(c, p)
    assert a["source"] == "estimee" and a["nouvelles"] == ["eT", "eM", "rev"]
    assert "Anki fermé : cartes estimées." in "\n".join(P.rediger(c, p, a))
    assert "Anki fermé" not in "\n".join(P.rediger(c, p, P.anki(c, p, FauxAnki(TOUTES))))


def monter_depot(tmp_path):
    """Dépôt minimal : un exercice par matière, deux cartes en topologie."""
    import yaml
    (tmp_path / "state").mkdir()
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
        with open(tmp_path / "matieres" / m / "exercices.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump([ex(f"{m}-1", m, sc=sc("1.1"), notions=["n1"] if m == "topologie" else [])], f)
    with open(tmp_path / "matieres" / "topologie" / "notions.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump([notion("n1", "Chapitre 1 - X", "1.1")], f)
    with open(tmp_path / "matieres" / "topologie" / "cartes.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump([carte("c1", "n1"), carte("c2", "n1")], f)
    for nom, d in {"dispo.yaml": ctx([])["dispo"], "resultats.yaml": []}.items():
        with open(tmp_path / "state" / nom, "w", encoding="utf-8") as f:
            yaml.safe_dump(d, f)


def test_seance_bout_en_bout_journal_et_bilan_reel(tmp_path):
    import yaml
    monter_depot(tmp_path)
    maintenant = dt.datetime(2026, 11, 7, 14, 30)                  # jour off du calendrier : on travaille quand même
    anki_ = FauxAnki({"c1", "c2"})
    l1 = P.seance(tmp_path, maintenant, anki_)
    assert l1[0].startswith("# NOW — séance sam. 2026-11-07 14:30") and l1[2].startswith("Bloc du jour : Topologie")
    assert "Dernier jour travaillé : aucun" in l1[3] and len(l1) <= P.MAX_LIGNES
    assert '"Id:c1" or "Id:c2"' in "\n".join(l1)
    journal = E.charger_yaml(tmp_path / "state" / "seance.yaml")["2026-11-07"]
    assert journal["exercices"] == ["topologie-1"] and journal["cartes"] == ["c1", "c2"] and journal["heure"] == "14:30"
    assert P.seance(tmp_path, maintenant, anki_) == l1             # relancer ne change rien

    # la séance : un exercice prévu fait, un autre hors plan, une carte apprise (plus is:new dans Anki)
    with open(tmp_path / "state" / "resultats.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump([{"date": "2026-11-07", "exercice": "topologie-1", "resultat": "presque", "palier_aide": 2},
                        {"date": "2026-11-07", "exercice": "mesure-1", "resultat": "reussi", "palier_aide": 0}], f)
    anki_.nouvelles = {"c2"}
    b = "\n".join(P.bilan_seance(P.contexte(tmp_path), D(2026, 11, 7), anki_))
    assert "1 prévus, 1 faits, 0 non faits, 1 hors plan" in b
    assert "`topologie-1` · presque (aide 2)" in b and "hors plan : `mesure-1`" in b
    assert "(lu dans Anki) : 1 sur 2 proposées" in b and "pas encore apprises : `c2`" in b
    assert "Marge recalculée" in b and "au début de la séance" in b
    assert "Anki fermé, apprises non relevées" in "\n".join(P.bilan_seance(P.contexte(tmp_path), D(2026, 11, 7)))

    # un exercice prévu et non fait est reporté automatiquement : il revient au plan suivant
    with open(tmp_path / "state" / "resultats.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump([], f)
    assert "non fait : `topologie-1` · reporté automatiquement" in "\n".join(
        P.bilan_seance(P.contexte(tmp_path), D(2026, 11, 7), anki_))
    l2 = P.seance(tmp_path, dt.datetime(2026, 11, 9, 9, 0), anki_)
    assert "`topologie-1`" in "\n".join(l2)


# ============================================ roadmap : reste à faire, capacité, marge
def test_marge_recalculee_a_chaque_seance_d_apres_les_resultats_et_la_date():
    exos = [ex("v1", t=30), ex("v2", t=30), ex("i1", imp="important", t=20), ex("s1", imp="secondaire", t=500),
            ex("x1", imp="exotique", t=500), annale_sc("an", "2022-23", sc("1.1"), t=40)]
    dispo = {"fin": "2026-11-12", "examens": "2026-11-13"}              # 5 jours de 120 min du 08 au 12
    b0 = P.plan_jour(ctx(exos, dispo=dispo), D(2026, 11, 8), seance=True)["bilan"]
    assert b0["total"] == 120 and b0["capacite"] == 120 * 5       # secondaire et exotique ne comptent pas
    b1 = P.plan_jour(ctx(exos, dispo=dispo), D(2026, 11, 10), seance=True)["bilan"]
    assert b1["capacite"] == 120 * 3 and b1["marge"] == b0["marge"] - 240        # le temps passe, la marge fond
    # deux réussites espacées de 7 jours : maîtrisé, il sort du reste à faire
    r = [res("2026-11-01", "v1"), res("2026-11-08", "v1")]
    b2 = P.plan_jour(ctx(exos, r, dispo=dispo), D(2026, 11, 10), seance=True)["bilan"]
    assert b2["total"] == b1["total"] - 30 and b2["marge"] == b1["marge"] + 30
    # un exercice seulement acquis reste à faire (calcul prudent)
    b3 = P.plan_jour(ctx(exos, [res("2026-11-08", "v1")], dispo=dispo), D(2026, 11, 10), seance=True)["bilan"]
    assert b3["total"] == b1["total"]


def test_marge_negative_annales_jamais_coupees_et_ouvertes_plus_tot():
    exos = [ex("v1", sc=sc("1.1"), t=100), ex("s1", sc=sc("1.1"), imp="secondaire", t=10),
            annale_sc("an", "2022-23", sc("1.3"), t=40), annale_sc("blanc", "2024-25", sc("1.3"), t=40)]
    court = {"fin": "2026-11-09", "examens": "2026-11-10"}             # 2 jours = 240 min pour 140 min : marge > 0
    p = P.plan_jour(ctx(exos, dispo=court), D(2026, 11, 8), seance=True)
    assert p["bilan"]["marge"] > 0 and genres_annale(p) == []         # annale de 1.3 pas encore éligible
    exos2 = exos + [ex("v2", sc=sc("1.1"), t=200)]                                   # +200 min : marge négative
    p2 = P.plan_jour(ctx(exos2, dispo=court), D(2026, 11, 8), seance=True)
    assert p2["bilan"]["marge"] < 0 and genres_annale(p2) == ["an"]    # l'annale s'ouvre plus tôt
    # le reste à faire ne contient que annales, vital et important : secondaire et exotique sont hors périmètre
    assert set(p2["bilan"]["par"]["topologie"]) == {"annales", "vital", "important"}
    assert p2["bilan"]["par"]["topologie"]["annales"] == 80                  # les deux annales, y compris l examen blanc


# ================================================= modèle de compréhension (comprehension.yaml)
def comp(**entrees):
    """comprehension.yaml minimal : nom -> niveau, ou dict d'entrée complet."""
    return {"notions": {k: ({"niveau": v, "maj": "2026-11-04"} if isinstance(v, str) else {"maj": "2026-11-04", **v})
                        for k, v in entrees.items()}, "style": []}


def ctx_comp(comprehension, **kw):
    """Topologie 1.1 / 1.2 / 1.3 (bloc : 1.3 après 1.1 et 1.2 acquis) + une notion par sous-chapitre."""
    exos = [ex("a1", sc=sc("1.1"), notions=["n-a"]), ex("b1", sc=sc("1.2"), notions=["n-b"]),
            ex("c1", sc=sc("1.3"), notions=["n-c"]), ex("d1", sc=sc("1.4"), notions=["n-d"])]
    notions = {k: notion(k, "Chapitre 1 - X", s) for k, s in
               (("n-a", "1.1"), ("n-b", "1.2"), ("n-c", "1.3"), ("n-d", "1.4"), ("n-c2", "1.3"))}
    for n in notions.values():
        n["titre"] = "Titre " + n["id"]
    return ctx(exos, [res("2026-11-04", "a1"), res("2026-11-04", "b1")], notions=notions,
               cartes=[carte("cA", "n-a"), carte("cC", "n-c")], comprehension=comprehension, **kw)


def now(c, d=D(2026, 11, 5)):
    p = P.plan_jour(c, d)
    return P.rediger(c, p, P.anki(c, p)), p


def section(L, titre="## À consolider"):
    """Lignes de la section `titre`, jusqu'au titre suivant (sans la ligne vide finale)."""
    i = L.index(titre) + 1      # le titre suivant est « ## Cours (30 min) » etc.
    j = next(k for k in range(i, len(L)) if L[k].startswith("## "))
    return L[i:j - 1]


# ---- (a) section « À consolider »
def test_a_consolider_absente_si_vide_et_comportement_inchange():
    L0, p0 = now(ctx_comp(None))
    assert p0["sous_chapitre"] == sc("1.3") and "## À consolider" not in L0
    for vide in ({"notions": {}, "style": []}, comp(**{"n-a": "tenue", "n-c": "reliee"})):
        L, _ = now(ctx_comp(vide))
        # seule différence : le niveau déjà mesuré sur la ligne de cours (11/11/2026)
        assert [x.split(" · déjà vu : ")[0] + (" · " + x.rsplit(" · ", 1)[1] if " · déjà vu : " in x else "")
                for x in L] == L0


def test_a_consolider_juste_avant_le_cours_et_filtre_par_sous_chapitre():
    c = ctx_comp(comp(**{"n-a": {"niveau": "fragile", "vision": "ses mots"}, "n-c": "recitee",
                         "n-d": "fragile",                        # 1.4 : après le bloc
                         "n-b": "tenue"}))                        # ni faible ni à consolider
    L, _ = now(c)
    cours = next(i for i, x in enumerate(L) if x.startswith("## Cours"))
    assert L.index("## À consolider") + len(section(L)) + 2 == cours                 # juste avant le cours
    bloc = "\n".join(section(L))
    assert "`n-a`" in bloc and "`n-c`" in bloc and "n-d" not in bloc and "n-b" not in bloc
    assert "· fragile · ses mots ·" in bloc and "f.pdf p.1" in bloc


def test_a_consolider_ordre_plafond_et_vision_ou_confusion():
    ouverte = [{"date": "2026-11-01", "texte": "vieille", "statut": "ouverte"},
               {"date": "2026-11-03", "texte": "récente", "statut": "ouverte"}]
    extra = {f"x{i}": {**notion(f"x{i}", "Chapitre 1 - X", "1.1"), "titre": f"x{i}"} for i in range(5)}
    c = ctx_comp(comp(**{"n-a": {"niveau": "fragile", "vision": "ses mots"},
                         "n-b": {"niveau": "tenue", "confusions": ouverte, "vision": "ignorée"},   # confusion ouverte : en tête
                         "n-c": "recitee"}, **{k: "fragile" for k in extra}))
    c["notions"].update(extra)
    bloc = section(now(c)[0])
    assert len(bloc) == 6 and bloc[0].startswith("- `n-b`") and "récente" in bloc[0]
    assert "vieille" not in bloc[0] and "ignorée" not in bloc[0]
    assert bloc[1].startswith("- `n-c`")                         # recitee avant fragile
    assert bloc[-1] == "- + 3 autres"                           # 8 notions à consolider, 5 lignes
    c["notions"]["n-b"]["titre"] = "T" * 300
    assert all(len(x) <= 162 for x in section(now(c)[0]))        # "- " + 160


def test_a_consolider_prerequis_inconnu_rattache_d_une_autre_matiere():
    c = ctx_comp(comp(**{"m-p": "inconnue", "m-p2": "fragile"}))
    for k in ("m-p", "m-p2"):         # prérequis de mesure, requis par une notion du 1.3 de topologie
        c["notions"][k] = {**notion(k, "Chapitre 5 - Y", "5.1", "mesure"), "type": "prerequis", "requis_par": ["n-c"]}
    bloc = "\n".join(section(now(c)[0]))
    assert "`m-p`" in bloc and "m-p2" not in bloc                # seul l'inconnue est rattaché hors matière


# ---- (b) cartes
def test_b_cartes_des_notions_faibles_reviennent_une_fois():
    c = ctx_comp(comp(**{"n-a": "fragile", "n-b": "tenue", "n-c": "inconnue"}))
    c["cartes"] += [carte("cB", "n-b")]
    c["couverture"] = {"n-a": {"statut": "couverte", "notes": [42]}}
    faits = P.jours_travailles(c)

    def rech(d, faits=faits):
        return P.recherche_a_revoir(c["a_revoir"] + P.entrees_faibles(c), d, faits)
    assert rech("2026-11-04") == ""                              # maj < d exigé
    assert rech("2026-11-05") == '(nid:42 or "Id:cA")'          # faible : oui ; tenue, inconnue : non
    c["a_revoir"] = [{"pour": "2026-11-05", "id": "cB", "nid": 42}]
    assert rech("2026-11-05") == '(nid:42 or "Id:cB" or "Id:cA")'   # fusion sans doublon
    c["a_revoir"] = []
    assert rech("2026-11-09", {"2026-11-05"}) == ""              # un jour travaillé entre maj et d consomme l'entrée
    assert rech("2026-11-05", {"2026-11-05"}) != ""              # le jour travaillé n'est pas avant d
    def revoir(L):
        return "\n".join(section(L, "## Anki — à réviser"))
    assert '"Id:cA"' in revoir(now(c)[0])
    c["resultats"].append(res("2026-11-05", "zz", "aide"))
    assert '"Id:cA"' not in revoir(now(c, D(2026, 11, 6))[0])
    # une notion faible non retravaillée ne repasse qu'une fois mais reste listée dans « À consolider »
    assert "`n-a`" in "\n".join(section(now(c, D(2026, 11, 6))[0]))
    # une confusion ouverte rend faible une notion tenue
    c["comprehension"]["notions"]["n-b"]["confusions"] = [{"date": "2026-11-04", "texte": "t", "statut": "ouverte"}]
    assert any(e.get("id") == "cB" for e in P.entrees_faibles(c))


def test_b_cartes_nouvelles_d_un_prerequis_inconnu_apres_les_prioritaires_avant_les_dues():
    c = ctx_cartes(dispo={"cartes_par_jour": 100})
    for k in ("m-p", "m-q"):
        c["notions"][k] = {**notion(k, "Chapitre 9 - Y", "9.1", "mesure"), "type": "prerequis", "requis_par": ["n-d"]}
    c["cartes"] += [carte("pM", "m-p"), carte("pQ", "m-q")]
    c["comprehension"] = comp(**{"m-p": "inconnue", "m-q": "fragile"})
    p = P.plan_jour(c, D(2026, 11, 4))
    sortie = anki_ids(c, p)
    assert sortie[:4] == ["eT", "eM", "pM", "rev"]               # erreurs, prérequis inconnue, puis a_revoir
    assert "pQ" not in sortie[:5]                                # fragile : pas de priorité
    c["dispo"]["cartes_par_jour"] = 3
    assert anki_ids(c, p) == ["eT", "eM", "pM"]                  # plafond inchangé


# ---- (c) exercices
def test_c_exercices_sur_notion_faible_prioritaires_dans_reprises_et_bloc():
    exos = [ex("e1", sc=sc("1.1"), notions=["n-a"]), ex("e2", sc=sc("1.1"), notions=["n-b"]),
            ex("e3", sc=sc("1.1"), imp="important", notions=["n-c"]),
            ex("e4", sc=sc("1.2"), notions=["n-a"]), ex("e5", sc=sc("1.2"), notions=[])]
    dispo = {"minutes_exercices_jour": 100}
    assert ids(P.plan_jour(ctx(exos, dispo=dispo), D(2026, 11, 4))) == ["e1", "e2", "e3", "e4", "e5"]
    for niveau in ("recitee", "fragile"):         # recitee compte comme faible aussi pour les exercices
        c = ctx(exos, dispo=dispo, comprehension=comp(**{"n-b": niveau}))
        assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["e2", "e1", "e3", "e4", "e5"]   # dans le sous-chapitre seulement
    c = ctx(exos, dispo=dispo, comprehension=comp(**{"n-b": "tenue", "n-a": "inconnue"}))
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["e1", "e2", "e3", "e4", "e5"]
    # catégorie : la prioritaire important passe avant les non prioritaires vitales du même sous-chapitre
    # (confusion ouverte sur une notion tenue = faible)
    ouv = {"niveau": "tenue", "confusions": [{"date": "2026-11-01", "texte": "t", "statut": "ouverte"}]}
    c = ctx(exos, dispo=dispo, comprehension=comp(**{"n-c": ouv}))
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["e3", "e1", "e2", "e4", "e5"]
    # reprises : à revoir d'abord, puis prioritaires, puis la plus en retard ; plafond inchangé
    r = [res("2026-11-01", "e1", "aide"), res("2026-11-02", "e2", "aide"), res("2026-11-03", "e4", "aide")]
    c = ctx(exos, r, dispo={**dispo, "minutes_reprises_max": 20}, comprehension=comp(**{"n-a": "fragile"}))
    reprises = lambda c: [e["id"] for e, g in P.plan_jour(c, D(2026, 11, 20))["items"] if g == "reprise"]  # noqa: E731
    assert reprises(c) == ["e1", "e4"]                           # e4 prioritaire passe avant e2, plus en retard
    c["comprehension"] = None
    assert reprises(c) == ["e1", "e2"]


def test_c_annale_jamais_deplacee_par_la_priorite():
    def plan(comprehension):
        exos = [ex("e1", sc=sc("1.1"), notions=["n-a"]), annale_sc("an24", "2024", sc("1.1")),
                annale_sc("an23", "2023", sc("1.1"))]
        for e in exos[1:]:
            e["notions"] = ["n-a"]
        c = ctx(exos, comprehension=comprehension, dispo={"annales_libres_des": "2026-11-01"})
        return [(e["id"], g.split()[0]) for e, g in P.plan_jour(c, D(2026, 11, 4))["items"]]
    assert plan(None) == [("an23", "annale"), ("e1", "bloc")]
    assert plan(comp(**{"n-a": "fragile"})) == plan(None)       # annale ni retirée ni déplacée


# ---- (d) prérequis multi-matières
def ctx_multi(**kw):
    exos = [ex("t1", sc=sc("2.3", 2), notions=["t-n"]),
            ex("m1", "mesure", sc=sc("1.2"), notions=["m-n1"]), ex("m2", "mesure", sc=sc("1.3"), notions=["m-n2"]),
            ex("m3", "mesure", sc=sc("1.4"), notions=["m-n3"])]
    pre = {**notion("topo-p", "Chapitre 2 - X", "2.3"), "type": "prerequis", "requis_par": ["m-n2", "m3", "m-n3"]}
    notions = {"t-n": notion("t-n", "Chapitre 2 - X", "2.3"), "topo-p": pre,
               "m-n1": notion("m-n1", "Chapitre 1 - X", "1.2", "mesure"),
               "m-n2": notion("m-n2", "Chapitre 1 - X", "1.3", "mesure"),
               "m-n3": notion("m-n3", "Chapitre 1 - X", "1.4", "mesure")}
    cartes = [carte("cm1", "m-n1"), carte("cm2", "m-n2"), carte("cm3", "m-n3"), carte("ct", "t-n"), carte("cp", "topo-p")]
    return ctx(exos, notions=notions, cartes=cartes, dispo={"cartes_par_jour": 100}, **kw)


def test_d_prerequis_servi_aussi_au_premier_sous_chapitre_de_chaque_matiere_qui_l_exige():
    c = ctx_multi()
    # m-n2 (1.3) avant m3 et m-n3 (1.4) : un seul rattachement dans mesure
    assert P.prerequis_par_sc(c, "mesure") == {sc("1.3"): ["topo-p"]}
    assert P.prerequis_par_sc(c, "topologie") == {sc("2.3", 2): ["topo-p"]}
    assert P.prerequis_par_sc(c, "proba") == {}
    # notions_sc : avant les notions du poly, dans la matière qui l'exige
    assert P.notions_sc(c, c["exercices"], "mesure", sc("1.3")) == ["topo-p", "m-n2"]
    assert P.notions_sc(c, c["exercices"], "mesure", sc("1.4")) == ["m-n3"]
    assert P.notions_sc(c, c["exercices"], "topologie", sc("2.3", 2)) == ["topo-p", "t-n"]
    # ordre_cartes : en bloc mesure, la carte du prérequis sort avant celles du poly du 1.3, mais après le 1.2
    c["exercices"] = [e for e in c["exercices"] if e["matiere"] == "mesure"]
    p = P.plan_jour(c, D(2026, 11, 4))
    assert p["matiere"] == "mesure" and p["sous_chapitre"] == sc("1.2")
    assert anki_ids(c, p) == ["cm1", "cp", "cm2", "cm3"]         # pas de doublon, pas en tête de matière
    # anciennes notes
    c["couverture"] = {"topo-p": {"statut": "couverte", "notes": [7]}, "m-n2": {"statut": "couverte", "notes": [8]},
                       "m-n1": {"statut": "couverte", "notes": [6]}}
    assert P.anciennes_notes(c, {**p, "sous_chapitre": sc("1.3")}) == [7, 8]
    # notions_des_exercices : une notion du cours du jour requise (même sans exercice du jour qui la cite)
    p13 = {**p, "sous_chapitre": sc("1.3"), "items": [], "info": {"minutes_cours": 30}}
    assert P.notions_des_exercices(c, p13) == {"topo-p"}
    assert P.notions_des_exercices(c, {**p13, "sous_chapitre": sc("1.2")}) == set()
    # ... ou une notion des exercices du jour
    assert P.notions_des_exercices(c, {"items": [(c["exercices"][1], "bloc")]}) == {"m-n2", "topo-p"}


# ---- (e) check.py
def depot_comp(tmp_path, comprehension):
    import yaml
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True, exist_ok=True)
    (tmp_path / "state").mkdir(exist_ok=True)

    def ecrire(chemin, d):
        (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    e = {**ex("topologie-1", sc=sc("1.1")), "sources": [{}]}
    e.pop("matiere")
    ecrire("state/dispo.yaml", ctx([])["dispo"])
    ecrire("state/resultats.yaml", [])
    ecrire("matieres/topologie/exercices.yaml", [e])
    ecrire("matieres/topologie/notions.yaml", [{"id": f"topo-n-000{i}", "type": "definition", "titre": "t", "enonce": "e",
                                                "chapitre": "Chapitre 1 - X", "sous_chapitre": "1.1"} for i in (1, 2)])
    if comprehension is not None:
        ecrire("state/comprehension.yaml", comprehension)
    elif (tmp_path / "state" / "comprehension.yaml").exists():
        (tmp_path / "state" / "comprehension.yaml").unlink()


def comp_valide():
    return {"notions": {"topo-n-0001": {
        "niveau": "reliee", "vision": "v", "maj": "2026-11-08",
        "liens": [{"vers": "topo-n-0002", "texte": "t"}], "liens_manquants": [{"vers": "topo-n-0002", "texte": "t"}],
        "confusions": [{"date": "2026-11-08", "texte": "t", "statut": "reparee"}],
        "preuves": [{"date": "2026-11-08", "source": "exercice", "exercice": "topologie-1", "extrait": "x",
                     "verdict": "juste"}]}},
        "style": ["a"]}


def test_e_check_comprehension(tmp_path):
    import copy
    import check as C
    depot_comp(tmp_path, None)
    assert C.verifier(tmp_path) == []                            # fichier absent
    depot_comp(tmp_path, {"notions": {}, "style": []})
    assert C.verifier(tmp_path) == []
    depot_comp(tmp_path, comp_valide())
    assert C.verifier(tmp_path) == []

    def modif(f):
        d = copy.deepcopy(comp_valide())
        f(d, d["notions"]["topo-n-0001"])
        return d
    cas = [(lambda d, n: d.pop("style"), "racine"),
           (lambda d, n: d.update(autre=1), "racine"),
           (lambda d, n: d.update(notions=[]), "dictionnaire"),
           (lambda d, n: d.update(style=["x"] * 7), "style"),
           (lambda d, n: d.update(style=[1]), "style"),
           (lambda d, n: d["notions"].update({"inconnue-id": dict(n)}), "notion inconnue"),
           (lambda d, n: n["liens"].append({"vers": "nope"}), "notion inconnue (nope)"),
           (lambda d, n: n["liens_manquants"].append({"vers": "topo-n-0001"}), "elle-même"),
           (lambda d, n: n.update(niveau="parfait"), "niveau invalide"),
           (lambda d, n: n["confusions"][0].update(statut="fermee"), "statut invalide"),
           (lambda d, n: n["preuves"][0].update(source="reve"), "source invalide"),
           (lambda d, n: n["preuves"][0].update(verdict="bof"), "verdict invalide"),
           (lambda d, n: n["preuves"][0].update(exercice="zzz"), "exercice inconnu"),
           (lambda d, n: n.update(maj="08/11/2026"), "date invalide"),
           (lambda d, n: n.update(maj="2026-13-45"), "date invalide"),
           (lambda d, n: n["confusions"][0].update(date="hier"), "date invalide"),
           (lambda d, n: n["preuves"][0].update(date="2026-11-8"), "date invalide"),
           (lambda d, n: n.update(maj="2999-01-01"), "futur"),
           (lambda d, n: n["preuves"][0].update(date="2999-01-01"), "futur"),
           (lambda d, n: n.update(preuves=n["preuves"] * 7), "plus de 6 preuves"),
           (lambda d, n: n.update(confusions=n["confusions"] * 9), "plus de 8 confusions"),
           (lambda d, n: n["preuves"][0].update(extrait="x" * 161), "160"),
           (lambda d, n: n["confusions"][0].update(statut="ouverte"), "confusion ouverte"),
           (lambda d, n: (n.update(niveau="tenue"), n["confusions"][0].update(statut="ouverte")), "confusion ouverte"),
           (lambda d, n: n.update(liens=[]), "sans `liens`")]
    for f, attendu in cas:
        depot_comp(tmp_path, modif(f))
        assert any(attendu in x for x in C.verifier(tmp_path)), attendu
    # limites acceptées : 6 preuves, 8 confusions, extrait de 160 caractères, tenue sans liens
    depot_comp(tmp_path, modif(lambda d, n: (
        n.update(preuves=n["preuves"] * 6, confusions=n["confusions"] * 8, niveau="tenue", liens=[]),
        n["preuves"][0].update(extrait="x" * 160))))
    assert C.verifier(tmp_path) == []
    # fragile avec confusion ouverte : valide
    depot_comp(tmp_path, modif(lambda d, n: (n.update(niveau="fragile"), n["confusions"][0].update(statut="ouverte"))))
    assert C.verifier(tmp_path) == []


def test_cartes_d_exercices_a_part_avec_leur_plafond():
    c = ctx_cartes(dispo={"cartes_par_jour": 3, "exercices_par_jour": 2})
    c["cartes"] += [carte("x1", "n-a", ["exercice"]), carte("x2", "n-c", ["exercice"]), carte("x3", "n-b", ["exercice"])]
    p = P.plan_jour(c, D(2026, 11, 4), seance=True)
    a = P.anki(c, p)
    assert a["nouvelles"] == ["eT", "eM", "rev"]                  # le cours garde tout son plafond
    assert len(a["exercices"]) == 2 and set(a["exercices"]) <= {"x1", "x2", "x3"}
    texte = "\n".join(P.rediger(c, p, a))
    assert "## Anki — exercices à revoir (2 nouvelles)" in texte
    cours = texte.split("## Anki — cours, à apprendre")[1].split("## Anki — exercices")[0]
    assert "x1" not in cours and "x2" not in cours and "x3" not in cours
    # « tout le sujet du jour » : le cours seul
    assert "x1" not in P.recherche_sujet({"n-a"}, None, c["cartes"])
    # avec Anki : une carte d'exercice déjà apprise laisse la place à la suivante
    vu = FauxAnki(TOUTES | {"x2", "x3"})                          # x1 déjà apprise
    assert set(P.anki(c, p, vu)["exercices"]) == {"x2", "x3"}


def test_ranger_cours_dans_sous_paquet():
    import anki_connect as AC
    ch = "tg::Maths::L3 Paris Cité::Topologie::Chapitre 1 - Espace métrique"
    cartes = [(1, ch), (2, ch + "::Exercices"), (3, ch + "::Cours"), (4, "Filtré 1"),
              (5, "tg::Maths::L3 Paris Cité::Topologie"), (6, ch + "::Exercices::Vieux")]
    deplacements, filtrees = AC.plan_rangement(cartes)
    assert deplacements == [(1, ch, ch + "::Cours")]       # seule la carte posée dans le chapitre bouge
    assert filtrees == 1


# ------------------------------------------------ suivi par sous-question (09/11/2026)
def resq(d, id, **qs):
    return {"date": D.fromisoformat(d), "exercice": id, "resultat": E.pire(qs.values()), "questions": qs}


def test_reprise_seulement_des_questions_manquees():
    exos = [ex("e1", t=40)]
    r = [resq("2026-11-04", "e1", Q1="reussi", Q2="aide", Q3="reussi", Q4="reussi")]
    p = P.plan_jour(ctx(exos, r), D(2026, 11, 9))
    (e, genre), = [it for it in p["items"] if it[1] == "reprise"]
    assert e["a_refaire"] == ["Q2"] and e["questions_justes"] == ["Q1", "Q3", "Q4"]
    assert e["temps_min"] == 10                       # 40 × 1/4, 10 min au moins
    assert exos[0]["temps_min"] == 40                 # l'exercice lui-même n'est pas modifié


def test_reprise_partielle_reussie_rend_l_exercice_acquis_seulement_si_tout_est_juste():
    r = [resq("2026-11-04", "e1", Q1="reussi", Q2="presque", Q3="non_fait"),
         resq("2026-11-06", "e1", Q2="reussi")]
    h = E.historique(r)["e1"]
    assert [x[1] for x in h] == ["non_fait", "non_fait"]      # Q3 manque encore
    assert E.questions(r, D(2026, 11, 6))["e1"] == {"Q1": "reussi", "Q2": "reussi", "Q3": "non_fait"}
    r.append(resq("2026-11-08", "e1", Q3="reussi"))
    assert E.etat_exercice(E.historique(r)["e1"], D(2026, 11, 8))["etat"] == "acquis"
    # la reprise d'entretien (acquis) porte sur l'exercice entier
    p = P.plan_jour(ctx([ex("e1", t=40)], r), D(2026, 11, 15))
    (e,) = p["anki_seul"]
    assert "a_refaire" not in e and e["temps_min"] == 40


def test_tentative_entiere_et_decoupage_d_une_question():
    r = [resq("2026-11-04", "e1", Q1="presque", Q2="reussi"),
         {"date": D(2026, 11, 6), "exercice": "e1", "resultat": "aide"}]       # exercice entier refait
    assert E.questions(r, D(2026, 11, 6))["e1"] == {"Q1": "aide", "Q2": "aide"}
    r = [resq("2026-11-04", "e1", Q1="presque", Q2="reussi"),
         resq("2026-11-06", "e1", **{"Q1-directe": "reussi", "Q1-reciproque": "presque"})]
    assert E.questions(r, D(2026, 11, 6))["e1"] == {"Q2": "reussi", "Q1-directe": "reussi", "Q1-reciproque": "presque"}
    # sans détail des questions : comportement d'avant, exercice entier
    assert P.reprise_partielle(ex("e2", t=30), None)["temps_min"] == 30


def test_resultat_ajouter_questions():
    import resultat as R
    assert R.lire_questions("Q1=reussi, Q2 = presque") == {"Q1": "reussi", "Q2": "presque"}
    with pytest.raises(ValueError):
        R.lire_questions("Q1=bof")


def test_now_affiche_seulement_les_questions_a_refaire():
    exos = [ex("e1", t=40)]
    c = ctx(exos, [resq("2026-11-04", "e1", Q1="reussi", Q2="aide")])
    p = P.plan_jour(c, D(2026, 11, 9))
    texte = "\n".join(P.rediger(c, p, P.anki(c, p)))
    assert "`e1` e1 · 20 min" in texte and "**seulement Q2** (Q1 déjà juste)" in texte


# ------------------------------------------------ garde-fous de la review du 10/11/2026
def test_reprise_detaillee_apres_un_resultat_global_ne_rend_pas_acquis():
    r = [res("2026-11-04", "e1", "presque"), resq("2026-11-12", "e1", Q3="reussi")]
    assert [x[1] for x in E.historique(r)["e1"]] == ["presque", "presque"]        # le reste garde son niveau
    assert E.questions(r, D(2026, 11, 12))["e1"] == {"reste": "presque", "Q3": "reussi"}
    assert E.etat_exercice(E.historique(r)["e1"], D(2026, 11, 12))["etat"] == "a_revoir"
    # la liste couvre tout l'exercice (`complet`) : le reste disparaît
    r[1] = dict(resq("2026-11-12", "e1", Q1="reussi", Q2="reussi", Q3="reussi"), complet=True)
    assert E.etat_exercice(E.historique(r)["e1"], D(2026, 11, 12))["etat"] == "acquis"
    # exercice entier refait ensuite : tout prend son résultat
    r.append(res("2026-11-20", "e1", "aide"))
    assert set(E.questions(r, D(2026, 11, 20))["e1"].values()) == {"aide"}


def test_simulation_d_un_jour_n_ecrit_rien(tmp_path):
    import yaml
    (tmp_path / "state").mkdir()
    (tmp_path / "matieres").mkdir()
    (tmp_path / "state" / "dispo.yaml").write_text(yaml.safe_dump(ctx([])["dispo"]), encoding="utf-8")
    avant = sorted(p.name for p in tmp_path.rglob("*"))
    assert P.jour(D(2026, 11, 10), tmp_path, ecrire=False)
    assert sorted(p.name for p in tmp_path.rglob("*")) == avant


def test_rythme_objectif_et_projection():
    exos = [ex("v1", t=30), ex("v2", t=20), ex("i1", imp="important", t=10), ex("s1", imp="secondaire", t=50)]
    c = ctx(exos, [res("2026-11-05", "v1"), res("2026-11-05", "v2", "presque")])
    d = D(2026, 11, 10)
    r = P.rythme(c, d, exos, P._etats(exos, c["resultats"], d))
    assert (r["objectif"], r["acquis"], r["reste"]) == (3, 1, 2)       # le secondaire n'est pas dans l'objectif
    assert r["charge"] == 30                                            # v2 (20) + i1 (10) ; v1 est acquis
    assert r["observe"] == 1 and r["tentatives"] == 2 and r["seuls"] == 1
    assert r["fin_projetee"] == D(2026, 11, 24)                         # 2 restants à 1 par semaine
    texte = "\n".join(P.lignes_rythme(r, 1000))
    assert "1/3 exercices" in texte and "ALERTE" not in texte
    assert "ALERTE" in "\n".join(P.lignes_rythme(r, 10))
    c0 = ctx([ex("v1")])
    r0 = P.rythme(c0, d, c0["exercices"], P._etats(c0["exercices"], [], d))
    assert r0["fin_projetee"] is None and "aucun exercice réussi seul" in "\n".join(P.lignes_rythme(r0, 1000))


def test_points_de_blocage_affiches_a_la_reprise():
    exos = [ex("e1", t=30)]
    r = [dict(resq("2026-11-04", "e1", Q1="reussi", Q2="aide", Q3="non_fait"), resultat="aide",
              points={"Q2": "cas k=0 oublié", "Q3": "pas faite"})]
    c = ctx(exos, r)
    assert [x[1] for x in E.historique(r)["e1"]] == ["aide"]          # le jugement global reste le niveau
    p = P.plan_jour(c, D(2026, 11, 9))
    texte = "\n".join(P.rediger(c, p, P.anki(c, p)))
    assert "**seulement Q2 (cas k=0 oublié) ; Q3 (pas faite)** (Q1 déjà juste)" in texte
    # Q2 réussie ensuite : son point disparaît, l'exercice reste à revoir pour Q3
    r.append(resq("2026-11-06", "e1", Q2="reussi"))
    assert E.points(r, D(2026, 11, 6))["e1"] == {"Q3": "pas faite"}
    assert E.historique(r)["e1"][-1][1] == "non_fait"
    # rien de juste : exercice entier, mais le blocage est affiché
    r2 = [dict(resq("2026-11-04", "e1", Q1="non_fait"), points={"Q1": "synthèse"})]
    c2 = ctx([ex("e1", t=30)], r2)
    p2 = P.plan_jour(c2, D(2026, 11, 6))
    assert "· 30 min ·" in "\n".join(P.rediger(c2, p2, P.anki(c2, p2))) and "**à refaire : Q1 (synthèse)**" in "\n".join(P.rediger(c2, p2, P.anki(c2, p2)))


# ----------------------------------------------------------- notions jumelles (meme_que)
def test_notions_jumelles_partagent_la_comprehension():
    notions = {"m-5": {"id": "m-5", "titre": "limsup", "matiere": "mesure", "meme_que": ["p-1"]},
               "p-1": {"id": "p-1", "titre": "limsup", "matiere": "proba", "type": "prerequis", "meme_que": ["m-5"]},
               "x": {"id": "x", "titre": "x", "matiere": "proba"}}
    comp = {"notions": {"m-5": {"niveau": "fragile", "maj": "2026-11-09"}}}
    c = ctx([], notions=notions, comprehension=comp)
    r = P._comp(c)
    assert r["p-1"] == {"niveau": "fragile", "maj": "2026-11-09", "via": "m-5"}    # vue en mesure hier
    assert "x" not in r and "via" not in r["m-5"]
    comp["notions"]["p-1"] = {"niveau": "tenue", "maj": "2026-11-10"}             # retravaillée en proba
    r = P._comp(c)
    assert r["p-1"]["niveau"] == "tenue" and "via" not in r["p-1"]
    assert r["m-5"] == {"niveau": "tenue", "maj": "2026-11-10", "via": "p-1"}     # la plus récente gagne
    comp["notions"]["p-1"]["maj"] = "2026-11-09"
    assert P._comp(c)["m-5"]["niveau"] == "fragile"                               # à égalité, la sienne
    assert P._ref(notions["p-1"]) == "prérequis L1-L2"
    assert P._ref({"source": {"fichier": "a.pdf", "page": 6}}) == "a.pdf p.6"
    assert P._ref({"source": {"fichier": "a.pdf"}}) == "a.pdf"


def test_check_meme_que(tmp_path):
    import yaml
    import check as C
    (tmp_path / "state").mkdir()
    for m in E.MATIERES:
        (tmp_path / "matieres" / m).mkdir(parents=True)
    ecrire = lambda chemin, d: (tmp_path / chemin).write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")  # noqa: E731
    ecrire("state/dispo.yaml", ctx([])["dispo"])
    ecrire("state/resultats.yaml", [])
    a = {"id": "topo-n-0001", "type": "definition", "titre": "t", "chapitre": "Chapitre 1 - X",
         "sous_chapitre": "1.1", "enonce": "e", "meme_que": ["mesure-n-0001"]}
    b = {**a, "id": "mesure-n-0001", "meme_que": ["topo-n-0001"]}
    ecrire("matieres/topologie/notions.yaml", [a])
    ecrire("matieres/mesure/notions.yaml", [b])
    assert not [x for x in C.verifier(tmp_path) if "meme_que" in x]
    for b2, attendu in [({**b, "meme_que": []}, "sans le lien inverse"),
                        ({**b, "meme_que": ["topo-n-0001", "mesure-n-0009"]}, "meme_que inconnu"),
                        ({**b, "meme_que": "topo-n-0001"}, "doit être une liste")]:
        ecrire("matieres/mesure/notions.yaml", [b2])
        assert any(attendu in x for x in C.verifier(tmp_path)), attendu


# ----------------------------------------------------------- --toutes-reprises (11/11/2026)
def test_toutes_reprises_ajoute_les_a_revoir_hors_budget():
    exos = [ex("v1"), ex("v2"), ex("v3"), ex("v4")]
    res = [{**resq("2026-11-04", "v1", Q1="reussi", Q2="aide"), "points": {"Q2": "cas 0"}},
           {"exercice": "v2", "date": D(2026, 11, 4), "resultat": "aide", "palier_aide": 0},
           {"exercice": "v4", "date": D(2026, 11, 4), "resultat": "aide", "palier_aide": 0}]
    c = ctx(exos, res, cartes=[{**carte("ex-v2", None, ["exercice"]), "exercice": "v2"}],
            dispo={"minutes_reprises_max": 10})
    p = P.plan_jour(c, D(2026, 11, 7), seance=True)
    deja = {e["id"] for e, g in p["items"] if g == "reprise"}
    plus = P.reprises_en_plus(c, p)
    assert len(deja) == 1 and {e["id"] for e in plus} == {"v1", "v2", "v4"} - deja      # v3 jamais tenté : non
    p["en_plus"] = plus
    L = P.rediger(c, p, P.anki(c, p))
    assert any(x.startswith("### Reprises en plus") for x in L)
    assert any("cartes de toutes les reprises" in x for x in L) and any('"Id:ex-v2"' in x for x in L)
    if "v1" in {e["id"] for e in plus}:
        assert any("`v1`" in x and "seulement Q2 (cas 0)" in x for x in L)


# ----------------------------------------------------------- notions requises par les exercices (11/11/2026)
def ctx_requis(**kw):
    ch = "Chapitre 1 - X"
    exos = [ex("a1", sc=f"{ch} > 1.1 A", notions=["n-a"]), ex("b1", sc=f"{ch} > 1.3 C", notions=["n-c"])]
    notions = {"n-a": notion("n-a", ch, "1.1 A"), "n-b": notion("n-b", ch, "1.2 B"),       # 1.2 : aucun exercice
               "n-c": notion("n-c", ch, "1.3 C"), "n-d": notion("n-d", ch, "1.4 D")}
    cartes = [carte("cA", "n-a"), carte("cB1", "n-b"), carte("cB2", "n-b"), carte("cC", "n-c"), carte("cD", "n-d")]
    return ctx(exos, notions=notions, cartes=cartes, **kw)


def test_notions_requises_et_sous_chapitre_sans_exercice():
    c = ctx_requis(dispo={"cartes_par_jour": 1})
    p = P.plan_jour(c, D(2026, 11, 4))
    assert ids(p) == ["a1", "b1"] and p["sous_chapitre"].endswith("1.1 A")
    assert P.notions_requises(c, p) == {"n-a", "n-b", "n-c"}                 # pas n-d (1.4, après le 1.3)
    assert [n["id"] for n in P.notions_sans_exercice(c, p)] == ["n-b"]
    k = P.anki(c, p)
    assert k["nouvelles"] == ["cA"] and k["requises"] == ["cB1", "cB2", "cC"]    # plafond 1, + 3 requises (pas cD)
    L = P.rediger(c, p, k)
    assert any("sous-chapitre sans exercice" in x and "`n-b`" in x for x in L)
    assert any("dont 3 en plus du plafond" in x for x in L)
    c["comprehension"] = {"notions": {"n-b": {"niveau": "tenue", "maj": "2026-11-03"}}}
    assert P.notions_sans_exercice(c, p) == []                                # déjà tenue : omise


# ----------------------------------------------------------- reprises seul dans Anki (12/11/2026)
def test_reussi_ou_presque_reprise_seul_dans_anki_aide_avec_claude():
    exos = [ex("r1"), ex("p1"), ex("a1")]
    rs = [res("2026-11-01", "r1"), res("2026-11-04", "p1", "presque"),
          {"exercice": "a1", "date": D(2026, 11, 4), "resultat": "aide", "palier_aide": 4}]
    c = ctx(exos, rs, cartes=[{**carte("ex-p1", None, ["exercice"]), "exercice": "p1"}])
    p = P.plan_jour(c, D(2026, 11, 9))
    assert [e["id"] for e, g in p["items"] if g == "reprise"] == ["a1"]          # bloqué : avec Claude, en séance
    assert {e["id"] for e in p["anki_seul"]} == {"r1", "p1"}                     # hors séance, hors budget
    L = P.rediger(c, p, P.anki(c, p))
    assert any(x.startswith("### Reprises seul dans Anki") for x in L) and any('"Id:ex-p1"' in x for x in L)
