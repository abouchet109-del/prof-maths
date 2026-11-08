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
    assert ids(P.plan_jour(c, D(2026, 11, 6))) == ["i1"]            # reprise due


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
    assert ids(P.plan_jour(c, D(2026, 11, 11))) == ["a1"]


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
    assert P.recherche_a_revoir(entrees, "2026-11-07") == ""
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


def test_cartes_jamais_donnees_deux_fois_et_replanification_stable():
    c = ctx_cartes(dispo={"cartes_par_jour": 4})
    p = P.plan_jour(c, D(2026, 11, 4))
    jour1 = anki_ids(c, p)
    assert jour1 == ["eT", "eM", "rev", "cA1"]
    c["anki_plan"] = {"2026-11-04": jour1}
    assert anki_ids(c, p) == jour1                                  # même date : identique
    jour2 = anki_ids(c, P.plan_jour(c, D(2026, 11, 5)))
    assert not set(jour1) & set(jour2) and jour2 == ["cA2", "cA3", "cB1", "cB2"]


def test_cartes_limitees_a_l_avancement_du_cours():
    c = ctx_cartes(dispo={"cartes_par_jour": 100}, avancement={"topologie": sc("1.2")})
    assert anki_ids(c, P.plan_jour(c, D(2026, 11, 4))) == ["eT", "eM", "rev", "cA1", "cA2", "cA3", "cB1", "cB2"]


def test_cartes_exercice_passent_avec_les_erreurs_avant_le_bloc():
    c = ctx_cartes(dispo={"cartes_par_jour": 100})
    c["cartes"].append({**carte("xT", "n-d", ["exercice"]), "exercice": "a1"})
    p = P.plan_jour(c, D(2026, 11, 4))
    assert anki_ids(c, p) == ["eT", "eM", "xT", "rev", "cA1", "cA2", "cA3", "cB1", "cB2", "cC1", "cD"]
    c["dispo"]["cartes_par_jour"] = 3
    assert anki_ids(c, p) == ["eT", "eM", "xT"]                     # plafond : le bloc passe après
    c["anki_plan"] = {"2026-11-04": ["eT", "eM", "xT"]}
    assert "xT" not in anki_ids(c, P.plan_jour(c, D(2026, 11, 5)))  # donnée une seule fois


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


def test_anciennes_notes_du_bloc_hors_plafond_et_sans_repetition():
    cou = {"n-a": {"statut": "couverte", "notes": list(range(100, 108))},
           "n-a2": {"statut": "partielle", "notes": [105, 200, 201, 202, 203]},
           "n-b": {"statut": "couverte", "notes": [300]}}
    c = ctx_cartes(dispo={"cartes_par_jour": 2}, couverture=cou)
    p = P.plan_jour(c, D(2026, 11, 4))
    a = P.anki(c, p)
    # plafond de 2 cartes du système respecté ; anciennes : celles du sous-chapitre du bloc (1.1), 10 au plus
    assert len(a["nouvelles"]) == 2
    assert a["anciennes"] == [100, 101, 102, 103, 104, 105, 106, 107, 200, 201]
    assert 300 not in a["anciennes"]
    lignes = P.rediger(c, p, a)
    requete = lignes[lignes.index("```", lignes.index(next(l for l in lignes if l.startswith("## Anki — à apprendre")))) + 1]
    assert requete.endswith("(nid:100,101,102,103,104,105,106,107,200,201 is:new)")
    assert requete.startswith('"Id:eT" or "Id:eM" or ')                  # cartes du système d'abord
    # le lendemain : les notes déjà données ne reviennent pas, les suivantes prennent leur place
    c["anciennes_donnees"] = {"2026-11-04": a["anciennes"]}
    assert P.anki(c, p)["anciennes"] == a["anciennes"]                       # même date : identique
    assert P.anki(c, P.plan_jour(c, D(2026, 11, 5)))["anciennes"] == [202, 203]
    # jour off ou sans couverture : rien
    assert P.anki(c, P.plan_jour(c, D(2026, 11, 7)))["anciennes"] == []
    c2 = ctx_cartes(dispo={"cartes_par_jour": 2})
    assert P.anki(c2, P.plan_jour(c2, D(2026, 11, 4)))["anciennes"] == []


def test_paquet_anki_des_cartes_d_exercices():
    import anki as A
    cours = A.nom_paquet("topologie", "Chapitre 1 - Espace métrique")
    assert cours == "tg::Maths::L3 Paris Cité::Topologie::Chapitre 1 - Espace métrique"
    assert A.nom_paquet("topologie", "Chapitre 1 - Espace métrique", exercice=True) == cours + "::Exercices"


# ------------------------------------------- fusion AoutLicenceMath (anki_connect, sans réseau)
def test_cible_fusion_aoutlicence():
    import anki_connect as AC
    ch1, ch2 = "Chapitre 1 - Espace métrique", "Chapitre 2 - Espace complet"
    base = "tg::Maths::L3 Paris Cité::Topologie::"
    cours = "tg::Maths::AoutLicenceMath::Topologie::Chapitre 3"
    td = "tg::Maths::AoutLicenceMath::Topologie::TD2"
    assert AC.cible(cours, [("topologie", ch1)]) == (base + ch1, "rattache")
    # plusieurs chapitres : le premier du poly (Chapitre 2 avant Chapitre 10)
    assert AC.cible(cours, [("topologie", "Chapitre 10 - Z"), ("topologie", ch2)]) == (base + ch2, "ambigu")
    assert AC.cible(cours, [("topologie", ch1), ("topologie", ch1)])[1] == "rattache"
    # paquet TD rattachable : sous-paquet Exercices
    assert AC.cible(td, [("topologie", ch2)]) == (base + ch2 + "::Exercices", "rattache")
    # sans rattachement, ou seulement une autre matière : « Autres » de la matière de l'ancien paquet
    autres = base + "Autres (AoutLicenceMath)"
    assert AC.cible(cours, []) == (autres, "sans_rattachement")
    assert AC.cible(td, []) == (autres, "sans_rattachement")
    assert AC.cible(cours, [("proba", "Chapitre 2 - V")]) == (autres, "autre_matiere")
    mesure = AC.cible("tg::Maths::AoutLicenceMath::TH mesure::Chapitre 1", [("mesure", "Chapitre 1 - T")])
    assert mesure[0] == "tg::Maths::L3 Paris Cité::Mesure et intégration::Chapitre 1 - T"
    # rattachement par lot (rattachement_ancien.yaml), seulement si la couverture ne donne rien dans la matière
    lot = ("topologie", ch2, False)
    assert AC.cible(cours, [], lot) == (base + ch2, "classe")
    assert AC.cible(cours, [("proba", "Chapitre 2 - V")], lot) == (base + ch2, "classe")
    assert AC.cible(cours, [("topologie", ch1)], lot) == (base + ch1, "rattache")     # la couverture prime
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
