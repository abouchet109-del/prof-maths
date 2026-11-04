"""Tests des règles d'état et de planification, sur de petites données fictives."""
import datetime as dt
import sys
from pathlib import Path

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


def ctx(exos, resultats=(), dispo=None):
    for i, e in enumerate(exos):
        e["ordre"] = i
    base = {"debut": "2026-11-03", "fin": "2027-01-10", "examens": "2027-01-11",
            "minutes_exercices_jour": 120, "minutes_cours_jour": 30, "cartes_par_jour": 12,
            "exceptions": [{"type": "off", "du": "2026-11-07", "au": "2026-11-08"},
                           {"type": "quota", "du": "2026-12-21", "au": "2027-01-03", "minutes_exercices_jour": 240}]}
    base.update(dispo or {})
    return {"exercices": exos, "resultats": list(resultats), "dispo": base,
            "notions": {}, "cartes": [], "anki_plan": {}}


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


def test_plan_ne_propose_pas_important_tant_que_vital_ouvert():
    c = ctx([ex("v1"), ex("i1", imp="important")], dispo={"minutes_exercices_jour": 100})
    assert ids(P.plan_jour(c, D(2026, 11, 4))) == ["v1"]


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


def test_alternance_des_matieres():
    exos = [ex("t1", "topologie", sc="A"), ex("t2", "topologie", sc="A"), ex("t3", "topologie", sc="A"),
            ex("p1", "proba", sc="B", t=10), ex("p2", "proba", sc="B", t=10)]
    p = P.plan_jour(ctx(exos, dispo={"minutes_exercices_jour": 50}), D(2026, 11, 4))
    m = [e["matiere"] for e, _ in p["items"]]
    assert m == ["topologie", "proba", "topologie", "proba", "topologie"]


def test_sous_chapitre_au_score_le_plus_faible():
    exos = [ex("a1", sc="A"), ex("a2", sc="A"), ex("b1", sc="B"), ex("b2", sc="B")]
    c = ctx(exos, [res("2026-11-03", "a1", "non_fait"), res("2026-11-03", "b1")])
    p = P.plan_jour(c, D(2026, 11, 4))
    nouveaux = [e["id"] for e, g in p["items"] if g == "nouveau"]
    assert nouveaux[0] == "a2"                # A (score 0) avant B (score 1)


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
