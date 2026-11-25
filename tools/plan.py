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
import math
import datetime as dt
import sys
from pathlib import Path

import yaml

import etat as E

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MAX_LIGNES = 60
MIN_PAR_NOTION = 10         # durée estimée d'une notion de cours
RESTE_LISIBLE = {E.RESTE: "tout sauf les questions déjà justes"}
SEUL = ("reussi", "presque")  # dernier résultat -> reprise seul dans Anki, hors séance (12/11/2026)
REPRISE_MIN = 10            # minutes au moins pour une reprise partielle (seulement les questions manquées)
REPRISES_MAX_DEFAUT = 30    # minutes de reprises par jour au plus (dispo.yaml : minutes_reprises_max)
CARTES_DEFAUT = 20          # ancien plafond en cartes (remplacé le 23/11/2026 par NOTIONS_DEFAUT)
NOTIONS_DEFAUT = 8          # notions nouvelles par jour au moins (dispo.yaml : notions_par_jour) ; plus si l'échéance l'exige
JOURS_REVISION_CARTES = 7   # toutes les cartes apprises une semaine avant la fin (dispo.yaml : fin_cartes)
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
    """notion -> entrée de comprehension.yaml ({} si le fichier est absent ou vide).
    Notions jumelles (`meme_que` de notions.yaml : la même notion dans deux matières) : chaque notion prend
    l'entrée la plus récente (`maj`) entre la sienne et celles de ses jumelles ; la sienne à égalité. Une entrée
    venue d'une jumelle porte `via: <id>`."""
    brut = ((ctx.get("comprehension") or {}).get("notions")) or {}
    res = dict(brut)
    for i, n in (ctx.get("notions") or {}).items():
        cand = ([(i, brut[i])] if i in brut else []) + [(j, brut[j]) for j in n.get("meme_que") or [] if j in brut]
        if cand:
            j, c = max(cand, key=lambda t: str(t[1].get("maj") or ""))     # max garde le premier à égalité
            if j != i:
                res[i] = {**c, "via": j}
    return res


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


def reprise_partielle(e, etat_q, pts=None) -> dict:
    """Reprise d'un exercice à revoir dont des questions sont déjà justes : seulement les autres
    (09/11/2026). Copie de l'exercice avec `a_refaire` et un temps au prorata, 10 min au moins."""
    if not etat_q:
        return e
    refaire = [q for q, v in etat_q.items() if v != "reussi"]
    if not refaire:
        return e
    if len(refaire) == len(etat_q):            # rien de juste : exercice entier, mais on dit où ça a bloqué
        return {**e, "a_refaire": refaire, "points": pts or {}, "questions_justes": []} if pts else e
    temps = min(e["temps_min"], max(REPRISE_MIN, math.ceil(e["temps_min"] * len(refaire) / len(etat_q))))
    return {**e, "temps_min": temps, "a_refaire": refaire, "points": pts or {},
            "questions_justes": [q for q in etat_q if q not in refaire]}


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
    qmap, pmap = E.questions(resultats, d), E.points(resultats, d)
    plan["anki_seul"] = []
    for e in dus:
        dern = etats[e["id"]]["dernier"]
        if dern and dern[1] in SEUL:        # 12/11/2026 : réussi ou presque -> reprise seul dans Anki, hors séance
            if etats[e["id"]]["etat"] == "a_revoir":
                e = reprise_partielle(e, qmap.get(e["id"]), pmap.get(e["id"]))
            plan["anki_seul"].append(e)
            continue
        if etats[e["id"]]["etat"] == "a_revoir":
            e = reprise_partielle(e, qmap.get(e["id"]), pmap.get(e["id"]))
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


def prerequis_atteint(plan, n) -> bool:
    """Le sous-chapitre du prérequis `n` est atteint dans sa matière (sous-chapitre courant du plan) ; sans
    sous-chapitre courant connu pour la matière, on le considère atteint."""
    courant = (plan.get("courants") or {}).get(n.get("matiere"))
    return courant is None or E.cle_sc(_sc_notion(n)) <= E.cle_sc(courant)


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
    n_max = ctx["dispo"].get("notions_cours_jour") or plan["info"]["minutes_cours"] // MIN_PAR_NOTION
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


def sc_max_du_jour(plan):
    """Le sous-chapitre le plus avancé des exercices du bloc et de l'annale du jour, dans la matière du bloc."""
    scs = [e.get("sous_chapitre") for e, g in plan["items"]
           if g.split(" ")[0] in ("bloc", "annale") and e["matiere"] == plan["matiere"] and e.get("sous_chapitre")]
    return max(scs + [plan["sous_chapitre"]], key=E.cle_sc) if plan.get("sous_chapitre") else None


def notions_requises(ctx, plan) -> set[str]:
    """Notions qu'il faut avoir apprises avant les exercices du jour (demande du 11/11/2026 : jamais un exercice
    dont une notion préalable n'a pas été vue) : dans la matière du bloc, toutes les notions du poly et tous les
    prérequis rattachés (règle d) des sous-chapitres jusqu'au plus avancé des exercices du bloc ; plus les notions
    citées par les exercices du bloc et de l'annale, et leurs prérequis (`requis_par`)."""
    if not plan.get("sous_chapitre"):
        return set()
    m, fin = plan["matiere"], E.cle_sc(sc_max_du_jour(plan))
    scs = [s for s in _sc_matiere(ctx, plan) if E.cle_sc(s) <= fin]
    cles = {tuple(E.cle_sc(s)) for s in scs}
    res = {n["id"] for n in ctx["notions"].values()
           if n.get("matiere") == m and n.get("sous_chapitre") and tuple(E.cle_sc(_sc_notion(n))) in cles}
    rattaches = prerequis_par_sc(ctx, m)
    for s in scs:
        res |= set(prerequis_de(rattaches, s))
    items = [(e, g) for e, g in plan["items"] if g.split(" ")[0] in ("bloc", "annale")]
    cites = {n for e, _ in items for n in e.get("notions") or []}
    ids = {e["id"] for e, _ in items} | cites
    res |= cites | {n["id"] for n in ctx["notions"].values() if est_prerequis(n) and ids & set(n.get("requis_par") or [])}
    return res


def notions_sans_exercice(ctx, plan) -> list[dict]:
    """Notions du poly des sous-chapitres sans aucun exercice situés entre le sous-chapitre du bloc et le plus
    avancé des exercices du jour (ex. 1.3.1 « Présentation du modèle » avant les exercices du 1.3.2) : jamais au
    « Cours » sinon. Celles déjà `tenue` ou `reliee` sont omises."""
    if not plan.get("sous_chapitre"):
        return []
    m = plan["matiere"]
    debut, fin = E.cle_sc(plan["sous_chapitre"]), E.cle_sc(sc_max_du_jour(plan))
    avec = {tuple(E.cle_sc(e.get("sous_chapitre"))) for e in ctx["exercices"] if e.get("matiere") == m}
    comp = _comp(ctx)
    res = [n for n in ctx["notions"].values()
           if n.get("matiere") == m and n.get("sous_chapitre") and not est_prerequis(n)
           and debut < E.cle_sc(_sc_notion(n)) <= fin and tuple(E.cle_sc(_sc_notion(n))) not in avec
           and (comp.get(n["id"]) or {}).get("niveau") not in ("tenue", "reliee")]
    return sorted(res, key=lambda n: (E.cle_sc(_sc_notion(n)), n["id"]))


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
    # règle (b) : cartes nouvelles d'un prérequis L1-L2 `inconnue`, toutes matières, juste après les prioritaires,
    # s'il sert déjà : son sous-chapitre est atteint dans sa matière (18/11/2026 : un prérequis rattaché au
    # chapitre 5 attend le chapitre 5, il ne passe pas avant le chapitre 1 ; la règle (d) le sert à son tour).
    inconnus = {i for i, c in _comp(ctx).items() if c.get("niveau") == "inconnue"
                and est_prerequis(ctx["notions"].get(i)) and prerequis_atteint(plan, ctx["notions"][i])}
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


def premier_don(ctx, d) -> dict[int, str]:
    """Premier jour (AAAA-MM-JJ, au plus `d`) où le plan a donné chaque ancienne note dans « à apprendre » :
    state/anki_anciennes.yaml et le journal des séances (state/seance.yaml, qui réunit les séances d'un jour)."""
    res: dict[int, str] = {}
    sources = list((ctx.get("anciennes_donnees") or {}).items())
    sources += [(k, (v or {}).get("anciennes")) for k, v in (ctx.get("seances") or {}).items()]
    for k, ns in sources:
        if str(k) <= str(d):
            for n in ns or []:
                if int(n) not in res or str(k) < res[int(n)]:
                    res[int(n)] = str(k)
    return res


def premieres_nouvelles(client, ids, n, donnees=None) -> list[str]:
    """Les `n` premiers de `ids` (dans l'ordre) que le client Anki dit encore à apprendre ; lecture par lots.
    Un id `nid:<n>` est une ancienne note (couverture.yaml), lue par `nids_a_apprendre` : hors ECG, déjà
    apprise dans Anki mais pas revue depuis que le plan l'a donnée, elle est encore à apprendre (18/11/2026).
    `donnees` : premier jour donné de chaque ancienne note (`premier_don`)."""
    res: list[str] = []
    for k in range(0, len(ids), LOT_ANKI):
        if len(res) >= n:
            break
        lot = ids[k:k + LOT_ANKI]
        cartes = [i for i in lot if not i.startswith("nid:")]
        nids = [int(i[4:]) for i in lot if i.startswith("nid:")]
        nouveaux = (client.ids_nouveaux(cartes) if cartes else set()) |                    ({f"nid:{x}" for x in client.nids_a_apprendre(nids, donnees)} if nids else set())
        res += [i for i in lot if i in nouveaux]
    return res[:n]


def cartes_anciennes(ctx, exclues=frozenset()) -> list[dict]:
    """Anciennes notes de couverture.yaml en pseudo-cartes `nid:<n>` rattachées à leur notion (17/11/2026) :
    elles suivent l'ordre du poly avec les cartes du système et comptent dans le même plafond, si bien qu'un
    chapitre est fini, anciennes notes comprises, avant le suivant."""
    res, vus = [], set(exclues)
    for n, e in (ctx.get("couverture") or {}).items():
        for nid in (e or {}).get("notes") or []:
            if int(nid) not in vus:
                vus.add(int(nid))
                res.append({"id": f"nid:{int(nid)}", "notion": n, "tags": []})
    return res


def fin_cartes(ctx) -> dt.date:
    """Date à laquelle toutes les cartes de cours doivent être apprises : `fin_cartes` de dispo.yaml, sinon une
    semaine avant la fin des révisions (la dernière semaine sert à réviser, pas à apprendre)."""
    dispo = ctx["dispo"]
    if dispo.get("fin_cartes"):
        return E.en_date(dispo["fin_cartes"])
    fin = E.en_date(dispo["fin"]) if dispo.get("fin") else E.en_date(dispo["examens"]) - dt.timedelta(1)
    return fin - dt.timedelta(JOURS_REVISION_CARTES)


def plafond_notions(ctx, d, restantes: int) -> dict:
    """Nombre de notions nouvelles du jour (règle du 23/11/2026 : on raisonne en notions, définitions et
    propriétés comprises, plus en cartes ; demande du 18/11/2026 : tout apprendre avant les examens) :
    `notions_par_jour` au moins, et assez pour finir les `restantes` notions d'ici `fin_cartes`, sur les jours
    de travail. Chaque notion choisie apporte TOUTES ses cartes encore à apprendre."""
    dispo = ctx["dispo"]
    base = dispo.get("notions_par_jour", NOTIONS_DEFAUT)
    fin = fin_cartes(ctx)
    jours = sum(1 for j in E.jours(E.en_date(d), fin) if E.jour_info(dispo, j)["minutes_exercices"] > 0)
    besoin = (math.ceil(restantes / jours) if jours else restantes) if restantes else 0
    return {"plafond": max(base, besoin), "restantes": restantes, "jours": jours, "fin": fin, "base": base}


def ids_a_apprendre(client, ids, donnees=None) -> set[str]:
    """Parmi ces cartes de cours (ids du système et `nid:` d'anciennes notes), celles encore à apprendre."""
    cartes = [i for i in ids if not i.startswith("nid:")]
    nids = [int(i[4:]) for i in ids if i.startswith("nid:")]
    return (client.ids_nouveaux(cartes) if cartes else set()) | \
        ({f"nid:{n}" for n in client.nids_a_apprendre(nids, donnees)} if nids else set())


def premieres_notions(ids, a_apprendre, notion_de, n, seules=frozenset()) -> list[str]:
    """Les cartes à apprendre des `n` premières unités (ordre de `ids`) : une unité est une notion, qui vient
    entière (toutes ses cartes, système et anciennes notes), sauf une carte de `seules` (erreur, `a_revoir`
    due), qui compte seule et n'entraîne pas sa notion."""
    def unite(i):
        return ("carte", i) if i in seules else ("notion", notion_de.get(i))
    choisies: list = []
    for i in ids:
        if i in a_apprendre and unite(i) not in choisies and len(choisies) < n:
            choisies.append(unite(i))
    garde = set(choisies)
    return [i for i in ids if i in a_apprendre and unite(i) in garde]


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
        libres = [c for c in ctx["cartes"] if exportees is None or c["id"] in exportees] + cartes_anciennes(ctx)
    else:
        deja = {int(n) for k, ns in (ctx.get("anciennes_donnees") or {}).items()
                if str(k) < d and str(k) in faits for n in ns}
        libres = [c for c in ctx["cartes"] if c["id"] not in avant] + cartes_anciennes(ctx, deja)
    ordre = ordre_cartes(ctx, plan, libres)
    off = plan["info"]["off"]
    # Règle du 23/11/2026 : on compte en NOTIONS (toutes leurs cartes), assez pour que toutes les notions de
    # cours encore à apprendre (toutes matières) le soient avant `fin_cartes`.
    cours = [c["id"] for c in libres if not est_carte_exercice(c)]
    notion_de = {c["id"]: c.get("notion") for c in libres}
    a_apprendre = ids_a_apprendre(client, cours, premier_don(ctx, d)) if client else set(cours)
    # Tag `hors_quota` (25/11/2026 : tableau des lois, revu d'un coup) : ces cartes ne comptent pas comme notions
    # nouvelles ; tant qu'elles ne sont pas apprises, elles s'ajoutent toutes, hors quota, sans plafond.
    hors = {c["id"] for c in libres if "hors_quota" in (c.get("tags") or [])}
    plafond = plafond_notions(ctx, plan["date"], len({notion_de[i] for i in a_apprendre - hors}))
    limite = 0 if off else plafond["plafond"]
    limite_exos = 0 if off else ctx["dispo"].get("exercices_par_jour", EXERCICES_DEFAUT)
    ids_tous = [c["id"] for c in ordre if not est_carte_exercice(c)]
    ids = [i for i in ids_tous if i not in hors]
    ids_exos = [c["id"] for c in ordre if est_carte_exercice(c)]
    requis = set() if off else notions_requises(ctx, plan)
    seules = {c["id"] for c in libres if TAGS_PRIORITAIRES & set(c.get("tags") or [])} | \
        {e["id"] for e in a_revoir_dus(ctx.get("a_revoir"), d, faits) if e.get("id")}
    nouvelles = premieres_notions(ids, a_apprendre, notion_de, limite, seules)
    # Notions dont les exercices du jour ont besoin et pas encore apprises : toutes, sans plafond (23/11/2026).
    deja = set(nouvelles)
    requises = [i for i in ids + [i for i in cours if i not in set(ids) and i not in hors]
                if i in a_apprendre and i not in deja and notion_de.get(i) in requis]
    revues = [] if off else [i for i in ids_tous + [i for i in cours if i not in set(ids_tous)]
                             if i in hors and i in a_apprendre]
    if client:
        exercices = premieres_nouvelles(client, ids_exos, limite_exos)
        liees = [c["id"] for c in libres if c.get("notion") in notions_jour]
        encore = client.ids_nouveaux(liees) if liees else set()
        revoir = [i for i in liees if i not in encore]
    else:
        exercices = ids_exos[:limite_exos]
        revoir = [c["id"] for c in ctx["cartes"] if c["id"] in avant and c.get("notion") in notions_jour]
    choisis = nouvelles + requises
    plafond["notions_jour"] = len({notion_de.get(i) for i in nouvelles if i not in seules})
    plafond["notions_requises"] = len({notion_de.get(i) for i in requises})
    plafond["cartes_revues"] = len(revues)
    requises = requises + revues             # même traitement en aval (recherche Anki, anki_plan)
    anciennes = [int(i[4:]) for i in choisis if i.startswith("nid:")]
    nouvelles = [i for i in nouvelles if not i.startswith("nid:")]
    requises = [i for i in requises if not i.startswith("nid:")]
    return {
        "nouvelles": nouvelles,
        "requises": requises,          # hors quota, sans plafond : les exercices du jour en ont besoin (23/11/2026)
        "exercices": exercices,
        "anciennes": anciennes,       # anciennes notes choisies dans la même file, dans le plafond
        "revoir": revoir,
        "plafond": plafond,           # en notions : {plafond, restantes, jours, fin, base, notions_jour, notions_requises}
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
def dans_objectif(e) -> bool:
    """Objectif de l'échéance (choix du 10/11/2026) : annales de Paris Cité, vital et important.
    Secondaire et exotique passent après, s'il reste du temps."""
    return bool(e.get("annale_prioritaire")) or E.categorie(e) in ("vital", "important")


def rythme(ctx, d: dt.date, exos, etats, resultats=None) -> dict:
    """Où en est l'objectif « chaque exercice de l'objectif réussi seul une fois » (état acquis ou maîtrisé).

    - charge : minutes au moins pour y arriver, si chaque exercice passe à sa prochaine tentative
      (jamais tenté : `temps_min` ; à revoir : le temps de sa reprise, partielle si des questions sont justes) ;
    - requis : exercices à faire passer acquis par semaine, sur les jours de travail restants ;
    - observe : exercices passés acquis sur les 7 derniers jours ; tentatives et réussites seul sur 7 jours ;
    - fin_projetee : date à ce rythme (None si aucun acquis sur 7 jours) ;
    - minutes_jour : minutes d'exercices par jour de travail pour tenir la charge."""
    resultats = ctx["resultats"] if resultats is None else resultats
    objectif = [e for e in exos if dans_objectif(e)]
    reste = [e for e in objectif if etats[e["id"]]["etat"] not in E.ACQUIS]
    qmap = E.questions(resultats, d)
    charge = sum(reprise_partielle(e, qmap.get(e["id"]))["temps_min"] if etats[e["id"]]["etat"] == "a_revoir"
                 else e["temps_min"] for e in reste)
    dispo = ctx["dispo"]
    fin = E.en_date(dispo["fin"]) if dispo.get("fin") else E.en_date(dispo["examens"]) - dt.timedelta(1)
    jours = sum(1 for j in E.jours(d, fin) if E.jour_info(dispo, j)["minutes_exercices"] > 0)
    avant = _etats(objectif, resultats, d - dt.timedelta(8))
    hier = _etats(objectif, resultats, d - dt.timedelta(1))
    observe = sum(1 for e in objectif if hier[e["id"]]["etat"] in E.ACQUIS and avant[e["id"]]["etat"] not in E.ACQUIS)
    recents = [r for r in resultats if d - dt.timedelta(7) <= E.en_date(r["date"]) < d]
    projetee = d + dt.timedelta(math.ceil(len(reste) * 7 / observe)) if observe and reste else None
    return {"objectif": len(objectif), "acquis": len(objectif) - len(reste), "reste": len(reste), "charge": charge,
            "jours": jours, "fin": fin, "requis": math.ceil(len(reste) * 7 / jours) if jours else None,
            "observe": observe, "tentatives": len(recents),
            "seuls": sum(1 for r in recents if r["resultat"] == "reussi"),
            "fin_projetee": projetee, "minutes_jour": math.ceil(charge / jours) if jours else None}


def lignes_rythme(r, capacite: int) -> list[str]:
    L = [f"- Objectif (annales, vital, important réussis seul une fois) : {r['acquis']}/{r['objectif']} exercices ; "
         f"au moins {r['charge']} min pour {capacite} min de capacité."]
    if not r["reste"]:
        return L + ["- Rythme : objectif atteint."]
    if not r["jours"]:
        return L + ["- Rythme : **plus aucun jour de travail avant l'échéance**."]
    L.append(f"- Rythme : il faut {r['requis']} exercices réussis seul par semaine ({r['jours']} jours de travail "
             f"restants) ; 7 derniers jours : {r['observe']}, pour {r['tentatives']} tentatives dont {r['seuls']} "
             f"réussies seul.")
    if r["fin_projetee"] is None:
        L.append(f"- Projection : **aucun exercice réussi seul sur 7 jours : à ce rythme, pas fini le {r['fin']}**.")
    elif r["fin_projetee"] > r["fin"]:
        L.append(f"- Projection : **fin le {r['fin_projetee']}, après le {r['fin']}**.")
    else:
        L.append(f"- Projection : fin le {r['fin_projetee']} (échéance {r['fin']}).")
    if r["charge"] > capacite:
        L.append(f"- **ALERTE** : la charge dépasse la capacité. Il faudrait {r['minutes_jour']} min d'exercices "
                 "par jour, ou réduire l'objectif.")
    return L


def echeance(ctx, plan) -> list[str]:
    """Minutes restantes (annales + vital + important non maîtrisés), par matière, contre la capacité."""
    b = plan["bilan"]
    lignes = lignes_rythme(rythme(ctx, plan["date"], plan["exos"], plan["etats"]), b["capacite"])
    lignes += [f"- Jusqu'à la maîtrise (2 réussites espacées, chaque exercice compté une fois) : {b['total']} min ; "
               f"capacité jusqu'au {b['fin']} : {b['capacite']} min ; marge : {b['marge']} min."]
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


def _ref(n) -> str:
    """Où lire la notion : le PDF et la page, sinon « prérequis L1-L2 » (pas de poly)."""
    s = n.get("source") or {}
    if s.get("fichier"):
        return f"{s['fichier']} p.{s['page']}" if s.get("page") else s["fichier"]
    return "prérequis L1-L2" if est_prerequis(n) else "sans source"


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
        morceaux = [f"`{i}` {_court(n['titre'], 50)}", c.get("niveau") + (f" (via `{c['via']}`)" if c.get("via") else ""),
                    " ".join(str(dire).split()), _ref(n)]
        lignes.append(_court("- " + " · ".join(x for x in morceaux if x), 160))
    if len(choisies) > A_CONSOLIDER_MAX:
        lignes.append(f"- + {len(choisies) - A_CONSOLIDER_MAX} autres")
    return lignes


def reprises_en_plus(ctx, plan) -> list[dict]:
    """Option `--toutes-reprises` (demande du 11/11/2026) : tous les exercices `a_revoir` qui ne sont pas déjà dans
    le plan, dus ou non, hors budget, en reprise partielle (seulement les questions manquées). Ordre : date de
    reprise prévue, puis ordre du fichier."""
    d, etats = plan["date"], plan["etats"]
    deja = {e["id"] for e, _ in plan["items"]} | {e["id"] for e in plan.get("anki_seul") or []}
    qmap, pmap = E.questions(ctx["resultats"], d), E.points(ctx["resultats"], d)
    es = [e for e in plan["exos"] if etats[e["id"]]["etat"] == "a_revoir" and e["id"] not in deja]
    es.sort(key=lambda e: (str(etats[e["id"]]["du"]), e["ordre"]))
    return [reprise_partielle(e, qmap.get(e["id"]), pmap.get(e["id"])) for e in es]


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
        affiches = plan["items"] + [(e, "plus") for e in plan.get("en_plus") or []]
        for titre, genre in (("Annale", "annale"), ("Bloc", "bloc"), ("Reprises (en fin de séance)", "reprise"),
                             ("Reprises en plus : toutes les autres à revoir, hors budget, à la toute fin", "plus")):
            groupe = [(e, g) for e, g in affiches if g.split(" ")[0] == genre]
            if not groupe:
                continue
            L.append(f"### {titre} ({sum(e['temps_min'] for e, _ in groupe)} min)")
            for e, g in groupe:
                etiquette = g if genre == "annale" else ""
                ligne = f"- [ ] `{e['id']}` {etiquette + ' · ' if etiquette else ''}{_court(e['titre'])} · {e['temps_min']} min · {_source(e)}"
                if e.get("a_refaire"):
                    pts = e.get("points") or {}
                    reste = " ; ".join(RESTE_LISIBLE.get(q, q) + (f" ({pts[q]})" if pts.get(q) else "")
                                       for q in e["a_refaire"])
                    justes = e["questions_justes"]
                    ligne += (f" · **seulement {reste}**" if justes else f" · **à refaire : {reste}**")
                    if justes:
                        ligne += f" ({', '.join(justes)} déjà juste{'s' if len(justes) > 1 else ''})"
                if e.get("enonce") is None:
                    ligne += " · **énoncé à extraire**"
                L.append(ligne)
        if not plan["items"]:
            L.append("- (rien à planifier)")
        seul = plan.get("anki_seul") or []
        if seul:
            L.append(f"### Reprises seul dans Anki (hors séance, sans Claude : dis juste ce que tu as réussi ou raté)")
            for e in seul:
                ligne = f"- [ ] `{e['id']}` {_court(e['titre'])} · {_source(e)}"
                if e.get("a_refaire"):
                    ligne += " · seulement " + ", ".join(RESTE_LISIBLE.get(q, q) for q in e["a_refaire"])
                L.append(ligne)
        # 12/11/2026 : paquet filtré de TOUTES les cartes d'exercices réussis ou presque ; Anki décide quand les revoir
        ids_seul = {i for i, st in plan["etats"].items() if st.get("dernier") and st["dernier"][1] in SEUL}
        ce = [k["id"] for k in ctx["cartes"] if k.get("exercice") in ids_seul and "exercice" in (k.get("tags") or [])]
        if ce:
            L += [f"Paquet filtré « Exercices seul » ({len(ce)} cartes d'exercices réussis ou presque ; "
                  "“replanifier” **coché** : Anki décide quand les revoir) :", "```", f"({_requete(ce)}) (is:due or is:new)", "```"]
        consolider = a_consolider(ctx, plan)
        if consolider:
            L += ["", "## À consolider"] + consolider
        notions = cours_du_jour(ctx, plan)
        sans_exo = notions_sans_exercice(ctx, plan)
        sujet = {n["id"] for n in notions} | notions_des_exercices(ctx, plan) | {n["id"] for n in sans_exo}
        L += ["", f"## Cours ({info['minutes_cours']} min)"]
        comp = _comp(ctx)
        for n in notions:
            c = comp.get(n["id"]) or {}
            deja = (f" · déjà vu : {c.get('niveau')}" + (f" (via `{c['via']}`)" if c.get("via") else "")) if c else ""
            L.append(f"- `{n['id']}` {_court(n['titre'], 50)}{deja} · {_ref(n)}")
        if not notions:
            L.append("- (aucune notion liée)")
        if sans_exo:
            L.append(_court("- Avant les exercices qui suivent, à voir aussi (sous-chapitre sans exercice) : "
                            + " ; ".join(f"`{n['id']}` {_court(n['titre'], 35)}" for n in sans_exo[:4])
                            + (f" ; + {len(sans_exo) - 4}" if len(sans_exo) > 4 else ""), 300))
        rech = recherche_sujet(sujet, ctx.get("couverture"), ctx["cartes"])
        L += ["", "## Anki — tout le sujet du jour"]
        L += ["```", rech, "```"] if rech else ["- (aucune carte pour ces notions)"]
        L.append("Outils → Créer un paquet filtré, coller, décocher “replanifier les cartes selon mes réponses” "
                 "pour réviser sans perturber le planning Anki.")
    anciennes = cartes.get("anciennes") or []
    req = cartes.get("requises") or []
    apprendre = cartes["nouvelles"] + req
    nrev = (cartes.get("plafond") or {}).get("cartes_revues", 0)
    L += ["", f"## Anki — cours, à apprendre ({len(apprendre)} nouvelles"
              + (f", dont {len(req) - nrev} en plus du quota : les exercices du jour en ont besoin" if len(req) > nrev else "")
              + (f", dont {nrev} hors quota à revoir d'un coup (tag `hors_quota`)" if nrev else "")
              + (f" + {len(anciennes)} anciennes" if anciennes else "") + ")"]
    p = cartes.get("plafond")
    if p:
        L.append(f"Notions du jour : {p.get('notions_jour', 0)} sur un quota de {p['plafond']}"
                 + (f", plus {p['notions_requises']} dont les exercices du jour ont besoin"
                    if p.get("notions_requises") else "")
                 + f" (chaque notion avec toutes ses cartes). Il reste {p['restantes']} notions de cours à apprendre "
                 f"(toutes matières) d'ici le {p['fin']}, sur {p['jours']} jours de travail"
                 + (f" (minimum `notions_par_jour` : {p['base']})." if p["plafond"] == p["base"] else "."))
    # Cartes du système : jamais une carte déjà apprise (en apprentissage : pas encore apprise). Anciennes notes :
    # sans filtre d'état, car une note hors ECG déjà apprise dans Anki se réapprend (règle du 18/11/2026).
    requete = " or ".join(([f"(({_requete(apprendre)}) (is:new or (is:learn -is:review)))"] if apprendre else [])
                          + ([f"nid:{','.join(map(str, anciennes))}"] if anciennes else []))
    requete = f"({requete}) -is:suspended" if requete else ""
    L += ["```", requete, "```"] if requete else ["- (aucune)"]
    if anciennes:
        L.append("Paquet filtré “replanifier” **coché** : une ancienne carte déjà apprise ne compte réapprise "
                 "qu'une fois revue (journal d'Anki).")
    exos = cartes.get("exercices") or []
    L += ["", f"## Anki — exercices à revoir ({len(exos)} nouvelles)"]
    L += ["```", f"({_requete(exos)}) (is:new or (is:learn -is:review)) -is:suspended", "```",
          "Paquet filtré à part : cherche l'attaque avant de retourner la carte."] if exos else ["- (aucune)"]
    if plan.get("en_plus"):
        ar = {e["id"] for e, g in plan["items"] if g == "reprise"} | {e["id"] for e in plan["en_plus"]}
        ce = [k["id"] for k in ctx["cartes"] if k.get("exercice") in ar and "exercice" in (k.get("tags") or [])]
        L += ["", f"## Anki — cartes de toutes les reprises ({len(ce)}, apprises ou non)"]
        L += ["```", _requete(ce), "```", "À regarder après avoir refait l'exercice sur papier."] if ce else ["- (aucune)"]
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


def jour(date: dt.date, racine=E.RACINE, ecrire: bool = True) -> list[str]:
    """Calcule le plan du jour. `ecrire` : écrit NOW.md et mémorise les cartes Anki données et le bloc
    (la ligne de commande ne le fait qu'avec --ecrire : une simulation ne touche à rien)."""
    racine = Path(racine)
    ctx = contexte(racine)
    plan = plan_jour(ctx, date)
    cartes = anki(ctx, plan)
    cartes["source"] = "simulation"
    lignes = rediger(ctx, plan, cartes)
    if not ecrire:
        return lignes
    enregistrer_anki(racine, ctx, date, cartes["nouvelles"] + (cartes.get("requises") or []) + cartes["exercices"])
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
        "cartes": union(avant.get("cartes"), cartes["nouvelles"] + (cartes.get("requises") or []) + (cartes.get("exercices") or [])),
        "anciennes": union(avant.get("anciennes"), cartes["anciennes"]),
        "anki": bool(cartes["source"] == "anki" or avant.get("anki")),
        "marge_debut": avant.get("marge_debut", b["marge"]),
        "restant_debut": avant.get("restant_debut", b["total"]),
    }
    _ecrire(Path(racine) / "state" / "seance.yaml", dict(sorted(donnees.items())),
            "# Journal des séances lancées par `plan.py seance` : ce qui a été proposé (lu par `plan.py bilan`).\n")


def seance(racine=E.RACINE, maintenant=None, client=None, toutes_reprises=False) -> list[str]:
    """Plan de la séance qui commence maintenant, d'après l'état réel : écrit NOW.md, mémorise le bloc, les
    cartes proposées (journal) et la séance. `client` : lecteur d'Anki (None : cartes estimées)."""
    racine = Path(racine)
    maintenant = maintenant or dt.datetime.now()
    d = maintenant.date()
    ctx = contexte(racine)
    plan = plan_jour(ctx, d, seance=True)
    plan["heure"] = maintenant.strftime("%H:%M")
    if toutes_reprises:
        plan["en_plus"] = reprises_en_plus(ctx, plan)
    cartes = anki(ctx, plan, client)
    lignes = rediger(ctx, plan, cartes)
    enregistrer_anki(racine, ctx, d, cartes["nouvelles"] + (cartes.get("requises") or []) + cartes["exercices"])
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
            encore_a = client.nids_a_apprendre(anciennes, premier_don(ctx, d)) if anciennes else set()
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
    L += lignes_rythme(rythme(ctx, demain, exos, _etats(exos, ctx["resultats"], demain)), b["capacite"])
    if b["marge"] < 0:
        L.append(f"  - **ALERTE** : il manque {-b['marge']} min (les annales s'ouvrent plus tôt ; on coupe d'abord "
                 "l'exotique, puis le secondaire, jamais une annale).")
    return L


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    j = sp.add_parser("jour", help="simule le plan d'une date (affiche, n'écrit rien sans --ecrire)")
    j.add_argument("--ecrire", action="store_true", help="écrit NOW.md et state/ (remplace le plan de la séance)")
    j.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    j.add_argument("--racine", default=None, help="racine du dépôt (défaut : celui de l'outil)")
    sc_ = sp.add_parser("seance", help="écrit NOW.md pour la séance qui commence maintenant")
    sc_.add_argument("--racine", default=None)
    sc_.add_argument("--sans-anki", action="store_true", help="ne pas lire Anki (cartes estimées)")
    sc_.add_argument("--toutes-reprises", action="store_true",
                     help="ajoute en fin de séance tous les autres exercices à revoir, hors budget")
    b = sp.add_parser("bilan", help="bilan réel de la séance du jour (à recopier dans le journal)")
    b.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    b.add_argument("--racine", default=None)
    b.add_argument("--sans-anki", action="store_true")
    a = p.parse_args()
    racine = Path(a.racine).resolve() if a.racine else E.RACINE
    if a.cmd == "seance":
        client = None if a.sans_anki else client_anki()
        lignes = seance(racine, client=client, toutes_reprises=a.toutes_reprises)
        print(f"NOW.md écrit pour la séance ({len(lignes)} lignes ; Anki {'lu' if client else 'fermé : cartes estimées'}).")
        if len(lignes) > MAX_LIGNES and not a.toutes_reprises:
            print(f"ATTENTION : plus de {MAX_LIGNES} lignes.", file=sys.stderr)
            sys.exit(1)
        return
    if a.cmd == "bilan":
        d = E.en_date(a.date) if a.date else dt.date.today()
        print("\n".join(bilan_seance(contexte(racine), d, None if a.sans_anki else client_anki())))
        return
    d = E.en_date(a.date) if a.date else dt.date.today()
    lignes = jour(d, racine, ecrire=a.ecrire)
    print(f"NOW.md écrit pour le {d} ({len(lignes)} lignes)." if a.ecrire
          else "\n".join(lignes) + "\n[simulation] rien n'a été écrit")
    if len(lignes) > MAX_LIGNES:
        print(f"ATTENTION : plus de {MAX_LIGNES} lignes.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
