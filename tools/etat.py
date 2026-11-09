"""Règles communes : chargement des données, état d'un exercice, scores, calendrier.

Utilisé par plan.py, resultat.py et check.py.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
MATIERES = ["topologie", "mesure", "modelisation", "proba"]
# Ordre de rotation des matières pour le bloc du jour.
CYCLE = ["topologie", "mesure", "proba", "modelisation"]
CATEGORIES = ["vital", "important", "secondaire", "exotique"]
RESULTATS = ["reussi", "aide", "presque", "non_fait"]
SCORE = {"reussi": 1.0, "aide": 0.6, "presque": 0.3, "non_fait": 0.0}
# Délai (jours) avant qu'un exercice non réussi redevienne dû.
DELAI_REVOIR = {"non_fait": 1, "presque": 2, "aide": 3}
DELAI_ACQUIS = 7        # reprise d'un exercice acquis
ECART_MAITRISE = 7      # écart minimal entre deux réussites pour être maîtrisé
DELAI_MAITRISE = 21     # reprise d'un exercice maîtrisé
ACQUIS = ("acquis", "maitrise")


# ---------------------------------------------------------------- chargement
def en_date(x) -> dt.date:
    """Convertit une date YAML, un datetime ou une chaîne ISO en date."""
    if isinstance(x, dt.datetime):
        return x.date()
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x))


def charger_yaml(chemin, defaut=None):
    chemin = Path(chemin)
    if not chemin.exists():
        return defaut
    with open(chemin, encoding="utf-8") as f:
        donnees = yaml.safe_load(f)
    return defaut if donnees is None else donnees


def charger_exercices(racine=RACINE) -> list[dict]:
    """Tous les exercices (exercices*.yaml), avec les clés ajoutées `matiere` et `ordre`."""
    exos = []
    for m in MATIERES:
        for f in sorted((Path(racine) / "matieres" / m).glob("exercices*.yaml")):
            for e in charger_yaml(f, []):
                e["matiere"] = m
                e["ordre"] = len(exos)
                exos.append(e)
    return exos


def charger_notions(racine=RACINE) -> dict[str, dict]:
    notions = {}
    for m in MATIERES:
        for n in charger_yaml(Path(racine) / "matieres" / m / "notions.yaml", []):
            n["matiere"] = m
            notions[n["id"]] = n
    return notions


def charger_cartes(racine=RACINE) -> list[dict]:
    """Cartes dans l'ordre des fichiers (matières dans l'ordre de MATIERES)."""
    cartes = []
    for m in MATIERES:
        for c in charger_yaml(Path(racine) / "matieres" / m / "cartes.yaml", []):
            c["matiere"] = m
            cartes.append(c)
    return cartes


def cle_sc(sc) -> list:
    """Clé de tri « naturel » d'un sous-chapitre : les nombres sont comparés comme des nombres
    (« 2.10 » après « 2.9 », « Chapitre 10 » après « Chapitre 2 »). None se classe en premier."""
    morceaux = re.split(r"(\d+)", str(sc or ""))
    return [int(m) if i % 2 else m for i, m in enumerate(morceaux)]


def charger_resultats(racine=RACINE) -> list[dict]:
    return charger_yaml(Path(racine) / "state" / "resultats.yaml", [])


def pire(resultats) -> str:
    """Le moins bon résultat (ordre de RESULTATS : reussi < aide < presque < non_fait)."""
    return max(resultats, key=RESULTATS.index)


RESTE = "reste"      # pseudo-question : la partie de l'exercice jamais détaillée par question


def maj_questions(etat_q: dict, r, precedent: str | None = None) -> dict:
    """État des questions après la tentative `r` (sans effet de bord sur `etat_q`).

    Sans `questions`, la tentative porte sur l'exercice entier : toutes les questions connues prennent son
    résultat. Avec `questions`, seules les questions citées changent ; « Q1-reciproque » découpe « Q1 »,
    qui disparaît (le debrief écrit alors toutes ses parties).
    `precedent` : résultat effectif de l'exercice avant `r`. Si aucune question n'était connue, le reste de
    l'exercice garde ce niveau (pseudo-question `reste`) : une reprise « Q3=reussi » après un `presque`
    global ne rend pas l'exercice acquis. `complet: true` dans `r` (la liste couvre tout l'exercice)
    retire ce reste."""
    qs = r.get("questions") or {}
    if not qs:
        return {q: r["resultat"] for q in etat_q}
    nouveau = {q: v for q, v in etat_q.items() if not any(str(k).startswith(f"{q}-") for k in qs)}
    if not etat_q and precedent is not None:
        nouveau[RESTE] = precedent
    nouveau.update({str(k): v for k, v in qs.items()})
    if r.get("complet"):
        nouveau.pop(RESTE, None)
    return nouveau


def _suivre(liste, aujourdhui=None):
    """Parcourt les tentatives triées d'un exercice : rend [(date, résultat effectif)] et l'état des questions."""
    etat_q, precedent, h = {}, None, []
    for r in liste:
        if aujourdhui is not None and en_date(r["date"]) > aujourdhui:
            continue
        etat_q = maj_questions(etat_q, r, precedent)
        manquent = [v for v in etat_q.values() if v != "reussi"]
        # Le jugement global de la tentative reste le niveau de l'exercice ; mais « reussi » exige que
        # toutes les questions connues le soient (reprise partielle réussie : le moins bon du reste).
        precedent = pire(manquent) if r["resultat"] == "reussi" and manquent else r["resultat"]
        h.append((en_date(r["date"]), precedent))
    return h, etat_q


def points(resultats, aujourdhui: dt.date) -> dict[str, dict[str, str]]:
    """id d'exercice -> {question: ce qui a bloqué}, d'après le dernier `points` de chaque question encore
    à refaire (une question réussie perd son point)."""
    res = {}
    for ex, liste in _par_exercice(resultats).items():
        pts: dict = {}
        for r in liste:
            if en_date(r["date"]) <= aujourdhui:
                pts.update({str(k): v for k, v in (r.get("points") or {}).items()})
        etat_q = _suivre(liste, aujourdhui)[1]
        pts = {q: t for q, t in pts.items() if etat_q.get(q) not in (None, "reussi")}
        if pts:
            res[ex] = pts
    return res


def _par_exercice(resultats) -> dict[str, list[dict]]:
    """id d'exercice -> tentatives brutes triées par date (ordre du fichier à égalité)."""
    h: dict[str, list] = {}
    for r in resultats:
        h.setdefault(r["exercice"], []).append(r)
    for liste in h.values():
        liste.sort(key=lambda r: en_date(r["date"]))
    return h


def historique(resultats) -> dict[str, list[tuple[dt.date, str]]]:
    """id d'exercice -> tentatives [(date, résultat effectif)] triées par date (ordre du fichier à égalité).

    Résultat effectif : le résultat déclaré, sauf un `reussi` alors qu'une question connue ne l'est pas
    (reprise de Q2 seule, réussie) : c'est alors le moins bon des questions restantes. L'exercice n'est
    donc `reussi` que si toutes ses questions le sont (suivi par sous-question, 09/11/2026)."""
    return {ex: _suivre(liste)[0] for ex, liste in _par_exercice(resultats).items()}


def questions(resultats, aujourdhui: dt.date) -> dict[str, dict[str, str]]:
    """id d'exercice -> {question: dernier résultat} d'après les tentatives jusqu'à `aujourdhui`
    (absent si aucune tentative ne détaille ses questions)."""
    res = {}
    for ex, liste in _par_exercice(resultats).items():
        etat_q = _suivre(liste, aujourdhui)[1]
        if etat_q:
            res[ex] = etat_q
    return res


# ------------------------------------------------------------------ exercices
def planifiable(e) -> bool:
    """Les doublons et les exercices pas encore vus en cours ne sont jamais planifiés."""
    return not e.get("doublon_de") and e.get("disponible", True) is not False


def categorie(e) -> str:
    return e.get("importance") if e.get("importance") in CATEGORIES else "secondaire"


def etat_exercice(tentatives, aujourdhui: dt.date) -> dict:
    """État d'un exercice à la date `aujourdhui`, d'après ses tentatives [(date, résultat)].

    Retourne {etat: jamais|a_revoir|acquis|maitrise, du: date de reprise ou None,
    est_du: bool, dernier: (date, résultat) ou None}. Les tentatives postérieures sont ignorées.
    """
    etat, ref, dernier = "jamais", None, None
    for d, r in sorted((t for t in tentatives if t[0] <= aujourdhui), key=lambda t: t[0]):
        dernier = (d, r)
        if r != "reussi":                      # tout échec (même en reprise) remet à revoir
            etat, ref = "a_revoir", d
        elif etat in ("jamais", "a_revoir"):   # réussite seule : acquis
            etat, ref = "acquis", d
        elif etat == "acquis":                 # 2e réussite assez espacée : maîtrisé
            if (d - ref).days >= ECART_MAITRISE:
                etat, ref = "maitrise", d
        else:                                  # maîtrisé : une nouvelle réussite repousse la reprise
            ref = d
    du = None
    if etat == "a_revoir":
        du = ref + dt.timedelta(DELAI_REVOIR[dernier[1]])
    elif etat == "acquis":
        du = ref + dt.timedelta(DELAI_ACQUIS)
    elif etat == "maitrise":
        du = ref + dt.timedelta(DELAI_MAITRISE)
    return {"etat": etat, "du": du, "est_du": du is not None and du <= aujourdhui, "dernier": dernier}


def categorie_ouverte(exos, etats) -> str | None:
    """Catégorie en cours d'un (matière, sous-chapitre) : la première dont un exercice
    n'est pas encore au moins `acquis`. `exos` : exercices planifiables ; `etats` : id -> état."""
    for cat in CATEGORIES:
        if any(etats[e["id"]]["etat"] not in ACQUIS for e in exos if categorie(e) == cat):
            return cat
    return None


def score_exercice(tentatives, aujourdhui: dt.date | None = None) -> float | None:
    """Score moyen des 2 dernières tentatives (None si jamais tenté)."""
    t = sorted((t for t in tentatives if aujourdhui is None or t[0] <= aujourdhui), key=lambda t: t[0])[-2:]
    return sum(SCORE[r] for _, r in t) / len(t) if t else None


# ------------------------------------------------------------------ calendrier
def type_exception(ex) -> str:
    """Type d'une exception de dispo.yaml ; YAML lit `off` non guillemeté comme False."""
    return "off" if ex["type"] is False else ex["type"]


def jour_info(dispo, d: dt.date) -> dict:
    """Budget d'un jour : off, quota, minutes d'exercices et de cours."""
    debut = en_date(dispo["debut"])
    fin = en_date(dispo["fin"]) if dispo.get("fin") else en_date(dispo["examens"]) - dt.timedelta(1)
    info = {"off": False, "quota": False, "raison": "",
            "minutes_exercices": dispo["minutes_exercices_jour"],
            "minutes_cours": dispo["minutes_cours_jour"]}
    if d < debut or d > fin:
        info.update(off=True, raison="hors période")
    for ex in dispo.get("exceptions", []):
        if en_date(ex["du"]) <= d <= en_date(ex["au"]):
            if type_exception(ex) == "off":
                info.update(off=True, raison="jour off")
            elif type_exception(ex) == "quota":
                info["quota"] = True
                info["minutes_exercices"] = ex.get("minutes_exercices_jour", info["minutes_exercices"])
                info["minutes_cours"] = ex.get("minutes_cours_jour", info["minutes_cours"])
    if info["off"]:
        info.update(minutes_exercices=0, minutes_cours=0)
    return info


def jours(debut: dt.date, fin: dt.date):
    d = debut
    while d <= fin:
        yield d
        d += dt.timedelta(1)
