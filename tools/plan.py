"""Planificateur.

    plan.py seance [--sans-anki]      NOW.md pour maintenant, d'après ce qui a réellement été fait
    plan.py bilan [--date AAAA-MM-JJ]  bilan réel de la séance (à recopier dans le journal)
    plan.py jour --date AAAA-MM-JJ    simulation pour une date du calendrier (hors workflow)

Le plan est organisé en blocs de sous-chapitre : une matière par séance (rotation), les reprises dues
toutes matières confondues (plafonnées), au plus une annale prioritaire, puis le bloc. NOW.md fait 60
lignes au plus. `seance` ignore les jours `off` de dispo.yaml (ils ne servent qu'au calcul de la capacité).

Cartes : si AnkiConnect répond, une carte du système est « vue » si et seulement si elle n'est plus
`is:new` dans Anki (lecture seule) ; sinon on estime d'après state/anki_plan.yaml (journal des cartes
proposées) et les jours travaillés.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import yaml

import etat as E

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MAX_LIGNES = 60
MIN_PAR_NOTION = 10         # durée estimée d'une notion de cours
REPRISES_MAX_DEFAUT = 30    # minutes de reprises par jour au plus (dispo.yaml : minutes_reprises_max)
CARTES_DEFAUT = 20          # cartes nouvelles par jour au plus (dispo.yaml : cartes_par_jour)
EXERCICES_DEFAUT = 10       # cartes d'exercices nouvelles par jour au plus, à part des cartes de cours (dispo.yaml : exercices_par_jour)
ANCIENNES_MAX = 10          # anciennes notes (couverture.yaml) ajoutées par jour aux « à apprendre », hors plafond
LOT_ANKI = 40               # cartes interrogées à la fois dans Anki
TAGS_PRIORITAIRES = {"erreur", "exercice"}   # cartes d'erreurs et d'exercices : toujours en tête de leur liste « à apprendre »
NOMS = {"topologie": "Topologie", "mesure": "Mesure", "proba": "Probabilités", "modelisation": "Modélisation"}
PART_CAPACITE = 1.25 / len(E.MATIERES)   # part de la capacité restante au-delà de laquelle on alerte


def contexte(racine=E.RACINE) -> dict:
    """Charge toutes les données nécessaires au plan."""
    racine = Path(racine)
    return {
        "exercices": E.charger_exercices(racine),
        "resultats": E.charger_resultats(racine),
        "dispo": E.charger_yaml(racine / "state" / "dispo.yaml", {}),
        "notions": E.charger_notions(racine),
        "cartes": E.charger_cartes(racine),
        "anki_plan": E.charger_yaml(racine / "state" / "anki_plan.yaml", {}),
        "a_revoir": E.charger_yaml(racine / "state" / "a_revoir.yaml", []),
        "couverture": charger_couverture(racine),
        "anciennes_donnees": E.charger_yaml(racine / "state" / "anki_anciennes.yaml", {}),
        "blocs": E.charger_yaml(racine / "state" / "blocs.yaml", {}),
        "avancement": E.charger_yaml(racine / "state" / "avancement_cours.yaml", {}),
        "seances": E.charger_yaml(racine / "state" / "seance.yaml", {}),
        "exportees": charger_exportees(racine),
        "comprehension": E.charger_yaml(racine / "state" / "comprehension.yaml", {}),
    }


def charger_exportees(racine=E.RACINE):
    """Ids des cartes déjà exportées vers Anki (anki/registre.csv) ; None si le registre n'existe pas."""
    f = Path(racine) / "anki" / "registre.csv"
    if not f.exists():
        return None
    return {l.split(";")[0] for l in f.read_text(encoding="utf-8").splitlines()[1:] if l.strip()}


def charger_couverture(racine=E.RACINE) -> dict:
    """notion -> {statut, notes} fusionné sur toutes les matières (matieres/<m>/couverture.yaml)."""
    res = {}
    for m in E.MATIERES:
        res.update(E.charger_yaml(Path(racine) / "matieres" / m / "couverture.yaml", {}) or {})
    return res


def _etats(exos, resultats, d):
    h = E.historique(resultats)
    return {e["id"]: E.etat_exercice(h.get(e["id"], []), d) for e in exos}


def _annee(e) -> str:
    return str(e["annale"]["annee"]) if e.get("annale") else ""


def _derniere_annee(exos) -> dict:
    """Année d'annale la plus récente de chaque matière (annales prioritaires) : examens blancs."""
    res = {}
    for e in exos:
        if e.get("annale_prioritaire") and e.get("annale"):
            res[e["matiere"]] = max(res.get(e["matiere"], ""), _annee(e))
    return res


# ------------------------------------------------------- modèle de compréhension (state/comprehension.yaml)
NIVEAUX = ["inconnue", "recitee", "fragile", "tenue", "reliee"]
A_CONSOLIDER_MAX = 5        # lignes de la section « À consolider » de NOW.md (puis « + k autres »)


def _comp(ctx) -> dict:
    """notion -> entrée de comprehension.yaml ({} si le fichier est absent ou vide)."""
    return ((ctx.get("comprehension") or {}).get("notions")) or {}


def _ouvertes(c) -> list[dict]:
    return [x for x in c.get("confusions") or [] if x.get("statut") == "ouverte"]


def est_faible(c) -> bool:
    """Niveau `recitee` ou `fragile`, ou une confusion ouverte."""
    return c.get("niveau") in ("recitee", "fragile") or bool(_ouvertes(c))


def est_a_consolider(c) -> bool:
    """Niveau `inconnue`, `recitee` ou `fragile`, ou une confusion ouverte."""
    return c.get("niveau") in ("inconnue", "recitee", "fragile") or bool(_ouvertes(c))


def notions_faibles(ctx) -> set[str]:
    return {i for i, c in _comp(ctx).items() if est_faible(c)}


def _sc_notion(n) -> str:
    return f"{n.get('chapitre')} > {n.get('sous_chapitre')}"


def _meme_sc(a, b) -> bool:
    """Deux sous-chapitres identiques (forme « chapitre > sous-chapitre », ou le sous-chapitre seul)."""
    return a == b or str(a).endswith(" > " + str(b)) or str(b).endswith(" > " + str(a))


def prerequis_par_sc(ctx, m) -> dict[str, list[str]]:
    """Règle (d) : sous-chapitre de la matière `m` -> prérequis L1-L2 qui y sont servis. Un prérequis P est
    rattaché à son propre sous-chapitre et, pour chaque matière où figure un élément (exercice ou notion)
    de son `requis_par`, au premier sous-chapitre (ordre du poly) qui contient l'un de ces éléments."""
    elements = {}
    for e in ctx["exercices"]:
        if e.get("sous_chapitre"):
            elements[e["id"]] = (e["matiere"], e["sous_chapitre"])
    for n in ctx["notions"].values():
        if n.get("chapitre") and n.get("sous_chapitre"):
            elements.setdefault(n["id"], (n["matiere"], _sc_notion(n)))
    res: dict[str, list[str]] = {}
    for n in ctx["notions"].values():
        if not est_prerequis(n):
            continue
        rattaches: dict[str, list[str]] = {}      # matière -> sous-chapitres
        if n.get("sous_chapitre"):
            rattaches.setdefault(n["matiere"], []).append(_sc_notion(n))
        premiers: dict[str, str] = {}
        for x in n.get("requis_par") or []:
            mat, sc = elements.get(x) or (None, None)
            if mat and (mat not in premiers or E.cle_sc(sc) < E.cle_sc(premiers[mat])):
                premiers[mat] = sc
        for mat, sc in premiers.items():
            rattaches.setdefault(mat, []).append(sc)
        for sc in dict.fromkeys(rattaches.get(m, [])):
            res.setdefault(sc, []).append(n["id"])
    return res


def prerequis_de(rattaches, sc) -> list[str]:
    """Prérequis servis au sous-chapitre `sc` (voir prerequis_par_sc)."""
    return list(dict.fromkeys(i for k, ids in rattaches.items() if _meme_sc(k, sc) for i in ids))


# ------------------------------------------------------- sous-chapitres et ligne principale
def exercices_par_sc(exos, m) -> dict:
    """sous-chapitre -> exercices de la matière (hors annales prioritaires), dans l'ordre du poly."""
    res: dict = {}
    for e in exos:
        if e["matiere"] == m and not e.get("annale_prioritaire"):
            res.setdefault(e.get("sous_chapitre"), []).append(e)
    return dict(sorted(res.items(), key=lambda kv: E.cle_sc(kv[0])))


def ligne_principale(es, etats) -> list[dict]:
    """Ligne principale d'un sous-chapitre : les vitaux pas encore acquis, puis les importants jamais tentés."""
    vit = [e for e in es if E.categorie(e) == "vital" and etats[e["id"]]["etat"] not in E.ACQUIS]
    imp = [e for e in es if E.categorie(e) == "important" and etats[e["id"]]["etat"] == "jamais"]
    return vit + imp


def _dans_limite(sc, limite) -> bool:
    """Avancement du cours : jamais de sous-chapitre au-delà du dernier vu en CM (None : pas de limite)."""
    return limite is None or E.cle_sc(sc) <= E.cle_sc(limite)


def sous_chapitre_courant(par_sc, etats, limite=None):
    """Premier sous-chapitre (ordre du poly) qui a encore une ligne principale à faire, sinon None."""
    for sc, es in par_sc.items():
        if _dans_limite(sc, limite) and ligne_principale(es, etats):
            return sc
    return None


def candidats_bloc(par_sc, etats, limite=None, prioritaires=frozenset()) -> list[dict]:
    """Exercices à faire pour le bloc d'une matière, dans l'ordre : à partir du sous-chapitre courant,
    sa ligne principale (jamais tentés ; les « à revoir » reviennent par les reprises), puis celle du
    suivant, etc. Une fois toute la ligne principale épuisée : secondaire et exotique, avec le
    passage de catégorie par sous-chapitre. Dans un sous-chapitre, les exercices `prioritaires` (une notion
    faible) passent d'abord : clé (non prioritaire, catégorie, ordre)."""
    def cle(e):
        return (e["id"] not in prioritaires, E.CATEGORIES.index(E.categorie(e)), e["ordre"])


    if sous_chapitre_courant(par_sc, etats, limite) is not None:
        res = []
        for sc, es in par_sc.items():
            if _dans_limite(sc, limite):
                res += sorted((e for e in ligne_principale(es, etats) if etats[e["id"]]["etat"] == "jamais"),
                              key=cle)
        return res
    res = []
    for sc, es in par_sc.items():
        if not _dans_limite(sc, limite):
            continue
        cat = E.categorie_ouverte(es, etats)
        if cat in ("secondaire", "exotique"):
            res += sorted((e for e in es if E.categorie(e) == cat and etats[e["id"]]["etat"] == "jamais"), key=cle)
    return res


def vitaux_acquis(es, etats) -> tuple[int, int]:
    vit = [e for e in es if E.categorie(e) == "vital"]
    return sum(etats[e["id"]]["etat"] in E.ACQUIS for e in vit), len(vit)


def matiere_du_jour(blocs, resultats, d: dt.date, a_planifier) -> str | None:
    """Rotation : matière suivante dans E.CYCLE après celle du dernier bloc effectivement travaillé
    (date antérieure à `d` avec au moins un résultat). On saute une matière sans rien à planifier."""
    travaillees = {E.en_date(r["date"]) for r in resultats}
    anterieurs = [(E.en_date(k), v) for k, v in (blocs or {}).items()
                  if E.en_date(k) < d and E.en_date(k) in travaillees]
    debut = 0
    if anterieurs:
        m = max(anterieurs, key=lambda t: t[0])[1].get("matiere")
        if m in E.CYCLE:
            debut = (E.CYCLE.index(m) + 1) % len(E.CYCLE)
    for k in range(len(E.CYCLE)):
        m = E.CYCLE[(debut + k) % len(E.CYCLE)]
        if a_planifier.get(m):
            return m
    return None


# ------------------------------------------------------------------ échéance (calcul)
def bilan(ctx, d: dt.date, exos, etats, info=None) -> dict:
    """Minutes restantes (annales + vital + important non maîtrisés), par matière, contre la capacité.

    Recalculé à chaque plan d'après les résultats et la date. Secondaire et exotique n'y comptent jamais :
    c'est ce qu'on coupe en premier si la marge est négative (les annales, elles, ne sont jamais coupées).
    `info` : budget réel du jour `d` si on y travaille alors que le calendrier le dit off (séance)."""
    par = {m: {"annales": 0, "vital": 0, "important": 0} for m in E.MATIERES}
    for e in exos:
        if etats[e["id"]]["etat"] == "maitrise":
            continue
        if e.get("annale_prioritaire"):
            par[e["matiere"]]["annales"] += e["temps_min"]
        elif E.categorie(e) in ("vital", "important"):
            par[e["matiere"]][E.categorie(e)] += e["temps_min"]
    dispo = ctx["dispo"]
    fin = E.en_date(dispo["fin"]) if dispo.get("fin") else E.en_date(dispo["examens"]) - dt.timedelta(1)
    capacite = sum(E.jour_info(dispo, j)["minutes_exercices"] for j in E.jours(d, fin))
    if info is not None:
        capacite += info["minutes_exercices"] - E.jour_info(dispo, d)["minutes_exercices"]
    total = sum(sum(v.values()) for v in par.values())
    return {"par": par, "total": total, "capacite": capacite, "marge": capacite - total, "fin": fin}


# ------------------------------------------------------------------ plan du jour
def annale_eligible(e, d: dt.date, dispo, courants, limites, marge: int) -> bool:
    """Une annale n'est éligible que si son sous-chapitre est déjà passé dans sa matière (avant le
    sous-chapitre courant), sauf à partir de `annales_libres_des` ou si la marge est négative."""
    libres = dispo.get("annales_libres_des")
    if marge < 0 or (libres and d >= E.en_date(libres)):
        return True
    m, sc = e["matiere"], e.get("sous_chapitre")
    courant = courants.get(m)
    if courant is None:        # ligne principale épuisée dans la limite du cours
        return _dans_limite(sc, limites.get(m))
    return E.cle_sc(sc) < E.cle_sc(courant)


def info_seance(dispo, d: dt.date) -> dict:
    """Budget d'une séance lancée le jour `d` : un jour `off` ou hors période ne bloque rien, la séance
    a le budget normal (les jours de quota gardent le leur)."""
    info = E.jour_info(dispo, d)
    if info["off"]:
        info.update(off=False, raison="séance hors calendrier (" + info["raison"] + ")",
                    minutes_exercices=dispo["minutes_exercices_jour"], minutes_cours=dispo["minutes_cours_jour"])
    return info


def plan_jour(ctx, d: dt.date, resultats=None, seance=False) -> dict:
    """Plan : reprises, au plus une annale prioritaire, puis le bloc de la matière du jour.
    `seance=True` : plan complet même un jour off du calendrier."""
    resultats = ctx["resultats"] if resultats is None else resultats
    info = info_seance(ctx["dispo"], d) if seance else E.jour_info(ctx["dispo"], d)
    exos = [e for e in ctx["exercices"] if E.planifiable(e)]
    etats = _etats(exos, resultats, d)
    plan = {"date": d, "info": info, "items": [], "minutes": 0, "etats": etats, "exos": exos,
            "matiere": None, "sous_chapitre": None, "vitaux": None, "courants": {},
            "bilan": bilan(ctx, d, exos, etats, info if seance else None), "seance": seance,
            "dernier_jour": max((E.en_date(r["date"]) for r in resultats if E.en_date(r["date"]) < d), default=None)}
    if info["off"]:
        return plan
    restant = info["minutes_exercices"]
    ids = set()

    def ajouter(e, genre) -> bool:
        nonlocal restant
        if e["id"] in ids or e["temps_min"] > restant:      # ne tient pas : sauté
            return False
        ids.add(e["id"])
        restant -= e["temps_min"]
        plan["items"].append((e, genre))
        plan["minutes"] += e["temps_min"]
        return True

    limites = ctx.get("avancement") or {}
    par_sc = {m: exercices_par_sc(exos, m) for m in E.MATIERES}
    courants = {m: sous_chapitre_courant(par_sc[m], etats, limites.get(m)) for m in E.MATIERES}
    faibles = notions_faibles(ctx)
    prio = {e["id"] for e in exos if faibles & set(e.get("notions") or [])}     # règle (c)
    cands = {m: candidats_bloc(par_sc[m], etats, limites.get(m), prio) for m in E.MATIERES}
    plan["courants"] = courants

    # (a) reprises dues, toutes matières : à revoir d'abord, puis les plus en retard ; plafonnées.
    # La plus urgente passe même si elle dépasse seule le plafond (sinon elle ne serait jamais reprise).
    plafond = ctx["dispo"].get("minutes_reprises_max", REPRISES_MAX_DEFAUT)
    dus = [e for e in exos if etats[e["id"]]["est_du"]]
    dus.sort(key=lambda e: (etats[e["id"]]["etat"] != "a_revoir", e["id"] not in prio, etats[e["id"]]["du"], e["ordre"]))
    reprises = 0
    for e in dus:
        if reprises and reprises + e["temps_min"] > plafond:
            continue
        if ajouter(e, "reprise"):
            reprises += e["temps_min"]

    # (b) au plus une annale prioritaire jamais tentée, si son sous-chapitre est passé ;
    # la dernière année de chaque matière = examen blanc, réservé à la période quota.
    derniere = _derniere_annee(exos)

    def blanc(e):
        return bool(e.get("annale")) and _annee(e) == derniere.get(e["matiere"])

    marge = plan["bilan"]["marge"]
    annales = [e for e in exos if e.get("annale_prioritaire") and etats[e["id"]]["etat"] == "jamais"
               and annale_eligible(e, d, ctx["dispo"], courants, limites, marge)]
    if not info["quota"]:
        annales = [e for e in annales if not blanc(e)]
    # examens blancs en dernier, puis les années les plus récentes d'abord
    annales.sort(key=lambda e: (blanc(e), -int(_annee(e)[:4] or 0), e["ordre"]))
    for e in annales:
        if ajouter(e, "annale " + _annee(e)) and not info["quota"]:
            break   # hors période quota : une annale par jour au plus

    # (c) le bloc : ligne principale du sous-chapitre courant de la matière du jour, puis des suivants
    m = matiere_du_jour(ctx.get("blocs"), resultats, d, cands)
    if m:
        # un exercice qui ne tient pas est sauté, mais le bloc ne saute pas à un sous-chapitre plus loin
        butee = None
        for e in cands[m]:
            if butee is not None and E.cle_sc(e.get("sous_chapitre")) > E.cle_sc(butee):
                break
            if not ajouter(e, "bloc") and butee is None and e["id"] not in ids:
                butee = e.get("sous_chapitre")
        bloc = [e for e, g in plan["items"] if g == "bloc"]
        sc = bloc[0].get("sous_chapitre") if bloc else courants[m]
        plan["matiere"], plan["sous_chapitre"] = m, sc
        plan["vitaux"] = vitaux_acquis(par_sc[m].get(sc, []), etats)
    return plan


# ------------------------------------------------------------------ cours
def est_prerequis(n) -> bool:
    """Notion `type: prerequis` (L1-L2) : servie avant les notions du poly de son sous-chapitre."""
    return (n or {}).get("type") == "prerequis"


def _dans_sc(n, sc) -> bool:
    return sc in (n.get("sous_chapitre"), f"{n.get('chapitre')} > {n.get('sous_chapitre')}")


def notions_sc(ctx, exos, m, sc, prioritaires=()) -> list[str]:
    """Notions d'un sous-chapitre : les prérequis L1-L2 d'abord, puis celles de ses exercices (les
    `prioritaires` d'abord, puis vital, important…), puis celles de notions.yaml rattachées au sous-chapitre."""
    es = [e for e in exos if e["matiere"] == m and e.get("sous_chapitre") == sc and not e.get("annale_prioritaire")]
    es.sort(key=lambda e: (e["id"] not in prioritaires, E.CATEGORIES.index(E.categorie(e)), e["ordre"]))
    vues = []
    for e in es:
        for n in e.get("notions") or []:
            if n not in vues:
                vues.append(n)
    for n in ctx["notions"].values():
        if n.get("matiere") != m or n["id"] in vues:
            continue
        if _dans_sc(n, sc):
            vues.append(n["id"])
    for i in prerequis_de(prerequis_par_sc(ctx, m), sc):      # règle (d) : prérequis d'une autre matière aussi
        if i not in vues:
            vues.append(i)
    return sorted(vues, key=lambda i: not est_prerequis(ctx["notions"].get(i)))   # tri stable : prérequis en tête


def notions_des_exercices(ctx, plan) -> set[str]:
    """Notions des exercices du jour, plus les prérequis L1-L2 qu'ils utilisent (`requis_par` : un exercice du
    jour, une notion des exercices du jour ou une notion du cours du jour)."""
    ids = {e["id"] for e, _ in plan["items"]}
    res = {n for e, _ in plan["items"] for n in e.get("notions") or []}
    utiles = ids | res
    if plan.get("sous_chapitre") and plan.get("exos") is not None:
        utiles |= {n["id"] for n in cours_du_jour(ctx, plan)}
    return res | {n["id"] for n in ctx["notions"].values() if est_prerequis(n) and utiles & set(n.get("requis_par") or [])}


def cours_du_jour(ctx, plan) -> list[dict]:
    """Notions à lire : celles du sous-chapitre du bloc, dans la limite du temps de cours."""
    if not plan["sous_chapitre"]:
        return []
    n_max = plan["info"]["minutes_cours"] // MIN_PAR_NOTION
    bloc = {e["id"] for e, g in plan["items"] if g == "bloc"}
    vues = notions_sc(ctx, plan["exos"], plan["matiere"], plan["sous_chapitre"], bloc)
    return [ctx["notions"][n] for n in vues if n in ctx["notions"]][:n_max]


# ------------------------------------------------------------------ Anki
def _requete(ids) -> str:
    return " or ".join(f'"Id:{i}"' for i in ids)


def recherche_sujet(notions, couverture, cartes) -> str:
    """Recherche Anki unique : anciennes notes (nid:...) + cartes de cours (\"Id:...\") des notions, sans les
    cartes d'exercices (réviser le cours seul)."""
    notions = set(notions)
    nids = sorted({int(n) for k in notions for n in ((couverture or {}).get(k) or {}).get("notes") or []})
    parts = ([f"nid:{','.join(map(str, nids))}"] if nids else [])
    parts += [f'"Id:{c["id"]}"' for c in cartes if c.get("notion") in notions and not est_carte_exercice(c)]
    return f"({' or '.join(parts)})" if parts else ""


def a_revoir_dus(entrees, d, faits=()) -> list[dict]:
    """Entrées de state/a_revoir.yaml à montrer au plan de `d` : `pour` échu, et pas encore consommées par
    une séance travaillée (un résultat enregistré un jour entre `pour` et `d`)."""
    faits = {str(f) for f in faits}
    return [e for e in entrees or [] if str(e.get("pour")) <= str(d)
            and not any(str(e.get("pour")) <= f < str(d) for f in faits)]


def recherche_a_revoir(entrees, d, faits=()) -> str:
    """Cartes existantes que le debrief a demandé de revoir (state/a_revoir.yaml, champ `pour`)."""
    du_jour = a_revoir_dus(entrees, d, faits)
    nids = sorted({int(e["nid"]) for e in du_jour if e.get("nid")})
    parts = ([f"nid:{','.join(map(str, nids))}"] if nids else [])
    parts += [f'"Id:{i}"' for i in dict.fromkeys(e["id"] for e in du_jour if e.get("id"))]
    return f"({' or '.join(parts)})" if parts else ""


def entrees_faibles(ctx) -> list[dict]:
    """Règle (b) : entrées du type `a_revoir` pour les cartes des notions faibles (`pour` = lendemain de `maj`) ;
    elles se consomment comme celles de a_revoir.yaml (a_revoir_dus)."""
    res = []
    cou = ctx.get("couverture") or {}
    for i, c in _comp(ctx).items():
        if not est_faible(c) or not c.get("maj"):
            continue
        pour = str(E.en_date(c["maj"]) + dt.timedelta(1))
        res += [{"pour": pour, "nid": int(n)} for n in (cou.get(i) or {}).get("notes") or []]
        res += [{"pour": pour, "id": k["id"]} for k in ctx["cartes"] if k.get("notion") == i]
    return res


def _sc_matiere(ctx, plan) -> list[str]:
    """Tous les sous-chapitres de la matière du bloc (exercices et notions), triés, dans la limite du cours."""
    m = plan["matiere"]
    tous = set(exercices_par_sc(plan["exos"], m))
    tous |= {f"{n.get('chapitre')} > {n['sous_chapitre']}" for n in ctx["notions"].values()
             if n.get("matiere") == m and n.get("sous_chapitre") and n.get("chapitre")}
    tous |= set(prerequis_par_sc(ctx, m))       # règle (d) : sous-chapitre d'un prérequis rattaché
    limite = (ctx.get("avancement") or {}).get(m)
    return sorted((s for s in tous if _dans_limite(s, limite)), key=E.cle_sc)


def sc_suivants(ctx, plan) -> list[str]:
    """Sous-chapitres de la matière du bloc après celui du bloc."""
    return [s for s in _sc_matiere(ctx, plan) if E.cle_sc(s) > E.cle_sc(plan["sous_chapitre"])]


def sc_precedents(ctx, plan) -> list[str]:
    """Sous-chapitres de la matière du bloc avant celui du bloc."""
    return [s for s in _sc_matiere(ctx, plan) if E.cle_sc(s) < E.cle_sc(plan["sous_chapitre"])]


def jours_travailles(ctx) -> set[str]:
    """Dates (AAAA-MM-JJ) où au moins un résultat d'exercice est enregistré."""
    return {str(E.en_date(r["date"])) for r in ctx.get("resultats") or []}


def anciennes_notes(ctx, plan, client=None) -> list[int]:
    """Anciennes notes de l'utilisateur (couverture.yaml) des notions du sous-chapitre du bloc, au plus
    ANCIENNES_MAX, hors plafond `cartes_par_jour`. Le paquet L3 n'a aucune nouvelle carte par jour : sans
    cela, une ancienne carte jamais apprise ne sortirait plus.

    Avec Anki (`client`) : celles qui sont encore `is:new` dans Anki. Sans Anki : celles qui n'ont pas déjà
    été proposées un jour travaillé (state/anki_anciennes.yaml)."""
    if not plan["sous_chapitre"]:
        return []
    d = str(plan["date"])
    faits = jours_travailles(ctx)
    avant = set() if client else {int(n) for k, ns in (ctx.get("anciennes_donnees") or {}).items()
                                  if str(k) < d and str(k) in faits for n in ns}
    bloc = {e["id"] for e, g in plan["items"] if g == "bloc"}
    cou = ctx.get("couverture") or {}
    cand: list[int] = []
    for n in notions_sc(ctx, plan["exos"], plan["matiere"], plan["sous_chapitre"], bloc):
        for nid in (cou.get(n) or {}).get("notes") or []:
            if int(nid) not in avant and int(nid) not in cand:
                cand.append(int(nid))
    if client:
        nouveaux = client.nids_nouveaux(cand)
        cand = [n for n in cand if n in nouveaux]
    return cand[:ANCIENNES_MAX]


def ordre_cartes(ctx, plan, libres) -> list[dict]:
    """Cartes candidates dans l'ordre : erreurs et exercices, `a_revoir` dues, puis les sous-chapitres de la
    matière du bloc (passés, bloc, suivants), chacun selon la notion de la carte, prérequis L1-L2 d'abord."""
    d = str(plan["date"])
    ordre = [c for c in libres if TAGS_PRIORITAIRES & set(c.get("tags") or [])]
    # règle (b) : cartes nouvelles d'un prérequis L1-L2 `inconnue`, toutes matières, juste après les prioritaires
    inconnus = {i for i, c in _comp(ctx).items() if c.get("niveau") == "inconnue" and est_prerequis(ctx["notions"].get(i))}
    ordre += [c for c in libres if c.get("notion") in inconnus]
    dues = {e["id"] for e in a_revoir_dus(ctx.get("a_revoir"), d, jours_travailles(ctx)) if e.get("id")}
    ordre += [c for c in libres if c["id"] in dues]
    if plan["sous_chapitre"]:
        # Progression linéaire : d'abord les cartes restantes des sous-chapitres déjà passés de la matière,
        # dans l'ordre du poly, puis le bloc, puis la suite.
        # Une carte suit le sous-chapitre de SA notion (notions.yaml), pas celui des exercices qui la citent :
        # sinon une notion du chapitre 2 citée par un exercice du 1.3 passerait avant le 1.4.
        m = plan["matiere"]
        rattaches = prerequis_par_sc(ctx, m)
        for sc in sc_precedents(ctx, plan) + [plan["sous_chapitre"]] + sc_suivants(ctx, plan):
            # Dans un sous-chapitre, les prérequis L1-L2 (règle (d) : y compris ceux d'une autre matière que
            # requiert un élément du sous-chapitre) passent avant le poly.
            prereq = set(prerequis_de(rattaches, sc))
            poly = {n["id"] for n in ctx["notions"].values()
                    if n.get("matiere") == m and _dans_sc(n, sc) and not est_prerequis(n)}
            ordre += [c for c in libres if c.get("notion") in prereq]
            ordre += [c for c in libres if c.get("notion") in poly]
    return list({c["id"]: c for c in ordre}.values())


def est_carte_exercice(c) -> bool:
    """Carte d'exercice (tag `exercice`) : donnée à part des cartes de cours."""
    return "exercice" in (c.get("tags") or [])


def premieres_nouvelles(client, ids, n) -> list[str]:
    """Les `n` premiers de `ids` (dans l'ordre) que le client Anki dit encore nouveaux ; lecture par lots."""
    res: list[str] = []
    for k in range(0, len(ids), LOT_ANKI):
        if len(res) >= n:
            break
        nouveaux = client.ids_nouveaux(ids[k:k + LOT_ANKI])
        res += [i for i in ids[k:k + LOT_ANKI] if i in nouveaux]
    return res[:n]


def anki(ctx, plan, client=None) -> dict:
    """Cartes à apprendre et cartes déjà vues à réviser.

    Avec `client` (Anki répond) : une carte est vue si et seulement si elle n'est plus `is:new` dans Anki ;
    à apprendre = les N premières non vues dans l'ordre de `ordre_cartes`, sans réservation à l'avance.
    Sans client : estimation d'après state/anki_plan.yaml (cartes proposées un jour passé travaillé).
    Cartes de cours (plafond `cartes_par_jour` ; les anciennes notes s'y ajoutent hors plafond) et cartes
    d'exercices (tag `exercice`) à part, avec leur propre plafond `exercices_par_jour` (demande du 09/11/2026 :
    deux paquets filtrés, le cours du jour d'un côté, les exercices à revoir de l'autre)."""
    d = str(plan["date"])
    # Seuls les jours passés comptent : une entrée d'un jour futur vient d'un plan régénéré depuis, elle est caduque.
    # … et seulement les jours travaillés (un résultat enregistré) : les cartes d'un jour sauté reviennent.
    faits = jours_travailles(ctx)
    avant = {i for k, ids in ctx["anki_plan"].items() if str(k) < d and str(k) in faits for i in ids}
    notions_jour = notions_des_exercices(ctx, plan)
    exportees = ctx.get("exportees")
    if client:
        # une carte jamais exportée ne peut pas être apprise : on la signale au lieu de la proposer
        libres = [c for c in ctx["cartes"] if exportees is None or c["id"] in exportees]
    else:
        libres = [c for c in ctx["cartes"] if c["id"] not in avant]
    ordre = ordre_cartes(ctx, plan, libres)
    off = plan["info"]["off"]
    limite = 0 if off else ctx["dispo"].get("cartes_par_jour", CARTES_DEFAUT)
    limite_exos = 0 if off else ctx["dispo"].get("exercices_par_jour", EXERCICES_DEFAUT)
    ids = [c["id"] for c in ordre if not est_carte_exercice(c)]
    ids_exos = [c["id"] for c in ordre if est_carte_exercice(c)]
    if client:
        nouvelles = premieres_nouvelles(client, ids, limite)
        exercices = premieres_nouvelles(client, ids_exos, limite_exos)
        liees = [c["id"] for c in libres if c.get("notion") in notions_jour]
        encore = client.ids_nouveaux(liees) if liees else set()
        revoir = [i for i in liees if i not in encore]
    else:
        nouvelles = ids[:limite]
        exercices = ids_exos[:limite_exos]
        revoir = [c["id"] for c in ctx["cartes"] if c["id"] in avant and c.get("notion") in notions_jour]
    return {
        "nouvelles": nouvelles,
        "exercices": exercices,
        "anciennes": [] if plan["info"]["off"] else anciennes_notes(ctx, plan, client),
        "revoir": revoir,
        "source": "anki" if client else "estimee",
        "non_exportees": 0 if exportees is None else sum(c["id"] not in exportees for c in ctx["cartes"]),
    }


def _ecrire(chemin, donnees, entete=""):
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(entete)
        yaml.safe_dump(donnees, f, allow_unicode=True, sort_keys=False, width=200)


def enregistrer_anki(racine, ctx, d, ids):
    """Mémorise les cartes données ce jour dans state/anki_plan.yaml (une carte n'est donnée qu'une fois)."""
    ap = {str(k): v for k, v in ctx["anki_plan"].items() if str(k) < str(d)}     # les jours futurs sont caducs
    if ids:
        ap[str(d)] = ids
    else:
        ap.pop(str(d), None)
    _ecrire(Path(racine) / "state" / "anki_plan.yaml", dict(sorted(ap.items())))


def enregistrer_anciennes(racine, ctx, d, nids):
    """Mémorise les anciennes notes données ce jour dans state/anki_anciennes.yaml."""
    ap = {str(k): v for k, v in (ctx.get("anciennes_donnees") or {}).items() if str(k) < str(d)}
    if nids:
        ap[str(d)] = nids
    else:
        ap.pop(str(d), None)
    _ecrire(Path(racine) / "state" / "anki_anciennes.yaml", dict(sorted(ap.items())),
            "# Anciennes notes (nid) données dans « à apprendre », par jour (lu par tools/plan.py).\n")


def enregistrer_bloc(racine, ctx, plan):
    """Mémorise le bloc planifié dans state/blocs.yaml ({date: {matiere, sous_chapitre}})."""
    blocs = {str(k): v for k, v in (ctx.get("blocs") or {}).items()}
    if plan["matiere"]:
        blocs[str(plan["date"])] = {"matiere": plan["matiere"], "sous_chapitre": plan["sous_chapitre"]}
    else:
        blocs.pop(str(plan["date"]), None)
    _ecrire(Path(racine) / "state" / "blocs.yaml", dict(sorted(blocs.items())),
            "# Blocs planifiés par tools/plan.py : {AAAA-MM-JJ: {matiere, sous_chapitre}}.\n"
            "# La rotation des matières part du dernier bloc effectivement travaillé (résultat ce jour-là).\n")


# ------------------------------------------------------------------ échéance
def echeance(ctx, plan) -> list[str]:
    """Minutes restantes (annales + vital + important non maîtrisés), par matière, contre la capacité."""
    b = plan["bilan"]
    lignes = [f"- Restant : {b['total']} min ; capacité jusqu'au {b['fin']} : {b['capacite']} min ; "
              f"marge : {b['marge']} min."]
    part = b["capacite"] * PART_CAPACITE
    for m in E.MATIERES:
        v = b["par"][m]
        tot = sum(v.values())
        ligne = f"- {m} : {tot} min (annales {v['annales']}, vital {v['vital']}, important {v['important']})"
        if tot > part:
            ligne += f" — **dépasse sa part ({round(part)} min)**"
        lignes.append(ligne)
    if b["marge"] < 0:
        lignes.append(f"- **ALERTE** : il manque {-b['marge']} min. Réduire le périmètre ou ajouter du temps.")
    if ctx["dispo"].get("examens_a_confirmer"):
        lignes.append(f"- Examens : semaine du {ctx['dispo']['examens']} (dates à confirmer).")
    return lignes


# ------------------------------------------------------------------ rendu
def _source(e) -> str:
    s = next((s for s in e.get("sources") or [] if s.get("fichier")), None)
    if s:
        return f"{s['fichier']} p.{s.get('page')} ({s.get('numero')})"
    s = (e.get("sources") or [{}])[0]
    return f"{s.get('etab', '?')} : {s.get('numero', '?')}"


def _court(txt, n=60) -> str:
    return txt if len(txt) <= n else txt[: n - 1] + "…"


def a_consolider(ctx, plan) -> list[str]:
    """Règle (a) : lignes de la section « À consolider » (liste vide s'il n'y a rien)."""
    comp, m = _comp(ctx), plan.get("matiere")
    if not comp or not m or not plan.get("sous_chapitre"):
        return []
    cles = [E.cle_sc(s) for s in sc_precedents(ctx, plan) + [plan["sous_chapitre"]]]
    attaches = {i for k, ids in prerequis_par_sc(ctx, m).items() if E.cle_sc(k) in cles for i in ids}
    choisies = []
    for i, c in comp.items():
        n = ctx["notions"].get(i)
        if not n or not est_a_consolider(c):
            continue
        dans = n.get("matiere") == m and E.cle_sc(_sc_notion(n)) in cles
        inconnu_rattache = est_prerequis(n) and c.get("niveau") == "inconnue" and i in attaches
        if dans or inconnu_rattache:
            choisies.append((i, n, c))
    choisies.sort(key=lambda t: (not _ouvertes(t[2]), NIVEAUX.index(t[2]["niveau"]) if t[2].get("niveau") in NIVEAUX else 9,
                                 E.cle_sc(_sc_notion(t[1])), t[0]))
    lignes = []
    for i, n, c in choisies[:A_CONSOLIDER_MAX]:
        ouv = _ouvertes(c)
        dire = (max(ouv, key=lambda x: str(x.get("date")))["texte"] if ouv else c.get("vision")) or ""
        s = n.get("source") or {}
        morceaux = [f"`{i}` {_court(n['titre'], 50)}", c.get("niveau"), " ".join(str(dire).split())]
        if s.get("fichier"):
            morceaux.append(f"{s['fichier']} p.{s.get('page')}")
        lignes.append(_court("- " + " · ".join(x for x in morceaux if x), 160))
    if len(choisies) > A_CONSOLIDER_MAX:
        lignes.append(f"- + {len(choisies) - A_CONSOLIDER_MAX} autres")
    return lignes


def rediger(ctx, plan, cartes) -> list[str]:
    d, info = plan["date"], plan["info"]
    nature = info["raison"] if info["off"] else ("quota" if info["quota"] else "normal")
    if plan.get("seance"):
        nature = info["raison"] or nature
        L = [f"# NOW — séance {JOURS[d.weekday()]} {d}{' ' + plan['heure'] if plan.get('heure') else ''} ({nature})", ""]
    else:
        L = [f"# NOW — {JOURS[d.weekday()]} {d} ({nature})", ""]
    if info["off"]:
        L.append("Aucun exercice aujourd'hui.")
    else:
        if plan["matiere"]:
            x, y = plan["vitaux"]
            L.append(f"Bloc du jour : {NOMS[plan['matiere']]} — {plan['sous_chapitre']} (vitaux acquis {x}/{y})")
        else:
            L.append("Bloc du jour : aucun (rien à planifier)")
        dj = plan.get("dernier_jour")
        L.append(f"Dernier jour travaillé : {dj} ({JOURS[dj.weekday()]})" if dj else "Dernier jour travaillé : aucun")
        L += ["", f"## Exercices ({plan['minutes']}/{info['minutes_exercices']} min)"]
        # Ordre de travail : annale, bloc, puis les reprises en fin de séance (seul, sur papier ; demande du 08/11/2026).
        # Le choix des exercices ne change pas : les reprises dues restent réservées en premier dans le temps.
        for titre, genre in (("Annale", "annale"), ("Bloc", "bloc"), ("Reprises (en fin de séance)", "reprise")):
            groupe = [(e, g) for e, g in plan["items"] if g.split(" ")[0] == genre]
            if not groupe:
                continue
            L.append(f"### {titre} ({sum(e['temps_min'] for e, _ in groupe)} min)")
            for e, g in groupe:
                etiquette = g if genre == "annale" else ""
                ligne = f"- [ ] `{e['id']}` {etiquette + ' · ' if etiquette else ''}{_court(e['titre'])} · {e['temps_min']} min · {_source(e)}"
                if e.get("enonce") is None:
                    ligne += " · **énoncé à extraire**"
                L.append(ligne)
        if not plan["items"]:
            L.append("- (rien à planifier)")
        consolider = a_consolider(ctx, plan)
        if consolider:
            L += ["", "## À consolider"] + consolider
        notions = cours_du_jour(ctx, plan)
        sujet = {n["id"] for n in notions} | notions_des_exercices(ctx, plan)
        L += ["", f"## Cours ({info['minutes_cours']} min)"]
        for n in notions:
            s = n.get("source") or {}
            L.append(f"- `{n['id']}` {_court(n['titre'], 50)} · {s.get('fichier')} p.{s.get('page')}")
        if not notions:
            L.append("- (aucune notion liée)")
        rech = recherche_sujet(sujet, ctx.get("couverture"), ctx["cartes"])
        L += ["", "## Anki — tout le sujet du jour"]
        L += ["```", rech, "```"] if rech else ["- (aucune carte pour ces notions)"]
        L.append("Outils → Créer un paquet filtré, coller, décocher “replanifier les cartes selon mes réponses” "
                 "pour réviser sans perturber le planning Anki.")
    anciennes = cartes.get("anciennes") or []
    L += ["", f"## Anki — cours, à apprendre ({len(cartes['nouvelles'])} nouvelles"
              + (f" + {len(anciennes)} anciennes" if anciennes else "") + ")"]
    requete = " or ".join(([_requete(cartes["nouvelles"])] if cartes["nouvelles"] else [])
                          + ([f"nid:{','.join(map(str, anciennes))}"] if anciennes else []))
    requete = f"({requete}) is:new" if requete else ""     # jamais une carte déjà apprise
    L += ["```", requete, "```"] if requete else ["- (aucune)"]
    exos = cartes.get("exercices") or []
    L += ["", f"## Anki — exercices à revoir ({len(exos)} nouvelles)"]
    L += ["```", f"({_requete(exos)}) is:new", "```",
          "Paquet filtré à part : cherche l'attaque avant de retourner la carte."] if exos else ["- (aucune)"]
    if cartes.get("source") == "estimee":
        L.append("Anki fermé : cartes estimées.")
    if cartes.get("non_exportees"):
        L.append(f"{cartes['non_exportees']} cartes pas encore exportées vers Anki (`python tools/anki.py`).")
    L += ["", "## Anki — à réviser", "- Toutes les cartes dues : `is:due`"]
    if cartes["revoir"]:
        L.append(f"- Déjà données, liées aux exercices du jour ({len(cartes['revoir'])}) : `{_requete(cartes['revoir'])}`")
    rech = recherche_a_revoir(list(ctx.get("a_revoir") or []) + entrees_faibles(ctx), plan["date"], jours_travailles(ctx))
    if rech:
        L += ["- Cartes existantes à revoir, signalées au debrief (paquet filtré, “replanifier” **coché**) :",
              "```", rech, "```"]
    L += ["", "## Échéance"] + echeance(ctx, plan)
    return L


def jour(date: dt.date, racine=E.RACINE) -> list[str]:
    """Calcule le plan du jour, écrit NOW.md et mémorise les cartes Anki données et le bloc."""
    racine = Path(racine)
    ctx = contexte(racine)
    plan = plan_jour(ctx, date)
    cartes = anki(ctx, plan)
    cartes["source"] = "simulation"
    lignes = rediger(ctx, plan, cartes)
    enregistrer_anki(racine, ctx, date, cartes["nouvelles"] + cartes["exercices"])
    enregistrer_anciennes(racine, ctx, date, cartes["anciennes"])
    enregistrer_bloc(racine, ctx, plan)
    (racine / "NOW.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return lignes


def client_anki():
    """Client AnkiConnect (lecture seule) si Anki répond vite, sinon None. Aucun import ni appel en test."""
    try:
        import anki_connect as AC
    except ImportError:         # genanki absent : pas de lecture d'Anki
        return None
    c = AC.ClientAnki()
    return c if c.disponible() else None


def enregistrer_seance(racine, ctx, plan, cartes, maintenant):
    """Journal de la séance dans state/seance.yaml : ce qui a été proposé et la marge de départ.
    Une 2e séance le même jour complète la 1re (le bilan compare au total proposé)."""
    d = str(plan["date"])
    donnees = {str(k): v for k, v in (ctx.get("seances") or {}).items()}
    avant = donnees.get(d) or {}

    def union(a, b):
        return list(dict.fromkeys(list(a or []) + list(b or [])))

    b = plan["bilan"]
    donnees[d] = {
        "heure": avant.get("heure") or maintenant.strftime("%H:%M"),
        "exercices": union(avant.get("exercices"), [e["id"] for e, _ in plan["items"]]),
        "cartes": union(avant.get("cartes"), cartes["nouvelles"] + (cartes.get("exercices") or [])),
        "anciennes": union(avant.get("anciennes"), cartes["anciennes"]),
        "anki": bool(cartes["source"] == "anki" or avant.get("anki")),
        "marge_debut": avant.get("marge_debut", b["marge"]),
        "restant_debut": avant.get("restant_debut", b["total"]),
    }
    _ecrire(Path(racine) / "state" / "seance.yaml", dict(sorted(donnees.items())),
            "# Journal des séances lancées par `plan.py seance` : ce qui a été proposé (lu par `plan.py bilan`).\n")


def seance(racine=E.RACINE, maintenant=None, client=None) -> list[str]:
    """Plan de la séance qui commence maintenant, d'après l'état réel : écrit NOW.md, mémorise le bloc, les
    cartes proposées (journal) et la séance. `client` : lecteur d'Anki (None : cartes estimées)."""
    racine = Path(racine)
    maintenant = maintenant or dt.datetime.now()
    d = maintenant.date()
    ctx = contexte(racine)
    plan = plan_jour(ctx, d, seance=True)
    plan["heure"] = maintenant.strftime("%H:%M")
    cartes = anki(ctx, plan, client)
    lignes = rediger(ctx, plan, cartes)
    enregistrer_anki(racine, ctx, d, cartes["nouvelles"] + cartes["exercices"])
    enregistrer_anciennes(racine, ctx, d, cartes["anciennes"])
    enregistrer_bloc(racine, ctx, plan)
    enregistrer_seance(racine, ctx, plan, cartes, maintenant)
    (racine / "NOW.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return lignes


def bilan_seance(ctx, d: dt.date, client=None) -> list[str]:
    """Bilan réel de la séance du jour `d`, calculé d'après les résultats enregistrés, le journal de séance
    et (si Anki répond) l'état des cartes. À recopier tel quel dans journal/<date>.md."""
    entree = (ctx.get("seances") or {}).get(str(d)) or {}
    resultats = [r for r in ctx["resultats"] if E.en_date(r["date"]) == d]
    faits = {r["exercice"]: r for r in resultats}
    prevus = list(entree.get("exercices") or [])
    ok = [i for i in prevus if i in faits]
    non = [i for i in prevus if i not in faits]
    hors = [i for i in faits if i not in prevus]
    niveau = lambda i: f"{faits[i]['resultat']} (aide {faits[i].get('palier_aide', 0)})"  # noqa: E731
    L = ["## Bilan réel", ""]
    if not entree:
        L.append(f"- Aucune séance enregistrée le {d} par `plan.py seance` : exercices prévus inconnus.")
    L.append(f"- Exercices : {len(prevus)} prévus, {len(ok)} faits, {len(non)} non faits"
             + (f", {len(hors)} hors plan" if hors else "") + ".")
    for i in ok:
        L.append(f"  - fait : `{i}` · {niveau(i)}")
    for i in non:
        L.append(f"  - non fait : `{i}` · reporté automatiquement (il revient au prochain plan)")
    for i in hors:
        L.append(f"  - hors plan : `{i}` · {niveau(i)}")
    cartes, anciennes = list(entree.get("cartes") or []), list(entree.get("anciennes") or [])
    if not cartes and not anciennes:
        L.append("- Cartes : aucune proposée.")
    elif client:
        try:
            encore = client.ids_nouveaux(cartes) if cartes else set()
            encore_a = client.nids_nouveaux(anciennes) if anciennes else set()
            ap = [i for i in cartes if i not in encore]
            aa = [n for n in anciennes if n not in encore_a]
            L.append(f"- Cartes apprises dans la séance (lu dans Anki) : {len(ap)} sur {len(cartes)} proposées"
                     + (f", et {len(aa)} anciennes sur {len(anciennes)}" if anciennes else "") + ".")
            if encore:
                L.append(f"  - pas encore apprises : {', '.join(f'`{i}`' for i in cartes if i in encore)}"
                         " (elles reviennent au prochain plan)")
        except Exception as ex:          # Anki a cessé de répondre
            L.append(f"- Cartes : {len(cartes)} + {len(anciennes)} anciennes proposées ; Anki illisible ({ex}).")
    else:
        L.append(f"- Cartes : {len(cartes)} + {len(anciennes)} anciennes proposées ; Anki fermé, apprises non relevées.")
    exos = [e for e in ctx["exercices"] if E.planifiable(e)]
    demain = d + dt.timedelta(1)
    b = bilan(ctx, demain, exos, _etats(exos, ctx["resultats"], d))
    debut = entree.get("marge_debut")
    L.append(f"- Marge recalculée : {b['marge']} min (restant {b['total']} min, capacité {b['capacite']} min du {demain} "
             f"au {b['fin']})" + (f" ; au début de la séance : {debut} min." if debut is not None else "."))
    if b["marge"] < 0:
        L.append(f"  - **ALERTE** : il manque {-b['marge']} min (les annales s'ouvrent plus tôt ; on coupe d'abord "
                 "l'exotique, puis le secondaire, jamais une annale).")
    return L


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    j = sp.add_parser("jour", help="écrit NOW.md pour une date")
    j.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    j.add_argument("--racine", default=None, help="racine du dépôt (défaut : celui de l'outil)")
    sc_ = sp.add_parser("seance", help="écrit NOW.md pour la séance qui commence maintenant")
    sc_.add_argument("--racine", default=None)
    sc_.add_argument("--sans-anki", action="store_true", help="ne pas lire Anki (cartes estimées)")
    b = sp.add_parser("bilan", help="bilan réel de la séance du jour (à recopier dans le journal)")
    b.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    b.add_argument("--racine", default=None)
    b.add_argument("--sans-anki", action="store_true")
    a = p.parse_args()
    racine = Path(a.racine).resolve() if a.racine else E.RACINE
    if a.cmd == "seance":
        client = None if a.sans_anki else client_anki()
        lignes = seance(racine, client=client)
        print(f"NOW.md écrit pour la séance ({len(lignes)} lignes ; Anki {'lu' if client else 'fermé : cartes estimées'}).")
        if len(lignes) > MAX_LIGNES:
            print(f"ATTENTION : plus de {MAX_LIGNES} lignes.", file=sys.stderr)
            sys.exit(1)
        return
    if a.cmd == "bilan":
        d = E.en_date(a.date) if a.date else dt.date.today()
        print("\n".join(bilan_seance(contexte(racine), d, None if a.sans_anki else client_anki())))
        return
    d = E.en_date(a.date) if a.date else dt.date.today()
    lignes = jour(d, racine)
    print(f"NOW.md écrit pour le {d} ({len(lignes)} lignes).")
    if len(lignes) > MAX_LIGNES:
        print(f"ATTENTION : plus de {MAX_LIGNES} lignes.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
