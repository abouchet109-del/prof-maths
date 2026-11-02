"""Validation de tous les fichiers de données du repo.

Usage (depuis la racine du repo ; `--racine DOSSIER` pour les tests) :

    python tools/check.py

Fichiers vérifiés : `state/dispo.yaml`, `state/semaine.yaml`,
`state/competences.yaml`, `state/jalons.yaml`, `modules/*/` (fiche, questions,
cartes, exercices), `ressources/catalogue.yaml`, `anki/registre.csv`,
`anki/progression.yaml`, `journal/`, `NOW.md`.

Sortie : une ligne par problème, `ERREUR` ou `AVERTISSEMENT`, avec le fichier,
l'identifiant concerné et la raison, puis un résumé.

Codes de sortie : 1 s'il y a au moins une erreur, 0 sinon (les avertissements
ne bloquent pas). Un dossier `modules/` absent ou vide n'est pas une erreur ;
en revanche un fichier d'état manquant (`state/*.yaml`) est signalé comme
erreur.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import Any

import common
from common import ErreurDonnees, ErreurFormat
from cal import Dispo, calculer

STATUTS_SEANCE = ["prevue", "faite", "partielle", "sautee", "deplacee"]
STATUTS_SAUTES = {"sautee", "deplacee"}
TYPES_SEANCE = ["cours", "exercices", "projet", "article", "consolidation", "examen",
                "diagnostic", "installation", "rattrapage"]
TYPES_PREUVE = ["diagnostic", "debrief", "exercice", "retest", "examen", "projet"]
TYPES_QUESTION = ["cours", "pourquoi", "transfert", "code", "calcul"]
STATUTS_JALON = ["a_venir", "a_risque", "atteint", "rate", "abandonne"]
TYPES_JALON = ["dur", "souple"]
STATUTS_EXCEPTION = ["confirme", "provisoire"]
TAGS_CARTE = ["essentiel", "complement", "erreur"]
INTERVALLES = [1, 3, 8, 16]
SECTIONS_FICHE = ["Objectifs", "Compétences visées", "Prérequis", "Séances", "Livrable",
                  "Points clés", "Sources"]

RE_SEANCE_ID = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z]$")
RE_COMPETENCE = re.compile(r"^[a-z0-9]+(\.[a-z0-9\-]+)+$")
RE_JALON = re.compile(r"^j\d{2}-[a-z0-9\-]+$")
RE_ID_COMPETENCE_TEXTE = re.compile(
    r"\b(?:" + "|".join(common.DOMAINES) + r")(?:\.[a-z0-9\-]+)+(?:\.\*)?")


class Rapport:
    def __init__(self) -> None:
        self.erreurs: list[str] = []
        self.avertissements: list[str] = []

    def erreur(self, fichier: str, ident: Any, msg: str) -> None:
        self.erreurs.append(_ligne("ERREUR", fichier, ident, msg))

    def avertissement(self, fichier: str, ident: Any, msg: str) -> None:
        self.avertissements.append(_ligne("AVERTISSEMENT", fichier, ident, msg))


def _ligne(niveau: str, fichier: str, ident: Any, msg: str) -> str:
    lieu = f"{fichier} [{ident}]" if ident not in (None, "") else fichier
    return f"{niveau} {lieu} : {msg}"


class Verif:
    """Validations élémentaires pour un fichier donné."""

    def __init__(self, rapport: Rapport, fichier: str) -> None:
        self.r = rapport
        self.fichier = fichier

    def err(self, ident: Any, msg: str) -> None:
        self.r.erreur(self.fichier, ident, msg)

    def warn(self, ident: Any, msg: str) -> None:
        self.r.avertissement(self.fichier, ident, msg)

    def requis(self, d: dict, cles: list[str], ident: Any) -> bool:
        ok = True
        for c in cles:
            if c not in d or d[c] is None or (isinstance(d[c], str) and not d[c].strip()):
                self.err(ident, f"champ obligatoire manquant ou vide : `{c}`")
                ok = False
        return ok

    def date(self, d: dict, cle: str, ident: Any, obligatoire: bool = True) -> dt.date | None:
        if d.get(cle) is None:
            if obligatoire:
                self.err(ident, f"champ obligatoire manquant : `{cle}`")
            return None
        try:
            return common.parse_date(d[cle])
        except ErreurFormat as exc:
            self.err(ident, f"`{cle}` : {exc}")
            return None

    def creneau(self, d: dict, cle: str, ident: Any) -> tuple[int, int] | None:
        if d.get(cle) is None:
            self.err(ident, f"champ obligatoire manquant : `{cle}`")
            return None
        try:
            return common.parse_creneau(d[cle])
        except ErreurFormat as exc:
            self.err(ident, f"`{cle}` : {exc}")
            return None

    def enum(self, d: dict, cle: str, valeurs: list[str], ident: Any,
             obligatoire: bool = True) -> Any:
        v = d.get(cle)
        if v is None:
            if obligatoire:
                self.err(ident, f"champ obligatoire manquant : `{cle}`")
            return None
        if v not in valeurs:
            self.err(ident, f"`{cle}` = {v!r} invalide (attendu : {', '.join(valeurs)})")
            return None
        return v

    def entier(self, d: dict, cle: str, ident: Any, mini: int, maxi: int | None = None,
               nullable: bool = False) -> int | None:
        v = d.get(cle)
        if v is None:
            if not nullable:
                self.err(ident, f"champ obligatoire manquant : `{cle}`")
            return None
        if isinstance(v, bool) or not isinstance(v, int) or v < mini or (maxi is not None and v > maxi):
            borne = f"{mini}..{maxi}" if maxi is not None else f">= {mini}"
            self.err(ident, f"`{cle}` = {v!r} invalide (entier {borne}{' ou null' if nullable else ''} attendu)")
            return None
        return v

    def liste_ids(self, d: dict, cle: str, ident: Any) -> list[str]:
        v = d.get(cle)
        if not isinstance(v, list) or not v:
            self.err(ident, f"`{cle}` : liste non vide attendue")
            return []
        return [x for x in v if isinstance(x, str)]


# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------

def charger(rapport: Rapport, racine: Path, rel: str, obligatoire: bool) -> tuple[bool, Any]:
    """(présent, données). Signale l'absence (si obligatoire) et les YAML invalides."""
    chemin = racine / rel
    if not chemin.is_file():
        if obligatoire:
            rapport.erreur(rel, None, "fichier manquant")
        return False, None
    try:
        return True, common.charger_yaml(chemin)
    except ErreurDonnees as exc:
        msg = str(exc)
        prefixe = f"{chemin.as_posix()} : "
        rapport.erreur(rel, None, msg[len(prefixe):] if msg.startswith(prefixe) else msg)
        return True, None


# ---------------------------------------------------------------------------
# state/dispo.yaml
# ---------------------------------------------------------------------------

def verifier_dispo(r: Rapport, data: Any) -> bool:
    """Retourne True si le fichier est exploitable pour les calculs de capacité."""
    f = "state/dispo.yaml"
    v = Verif(r, f)
    avant = len(r.erreurs)
    if not isinstance(data, dict):
        v.err(None, "un dictionnaire YAML est attendu")
        return False
    for cle in ("version", "fuseau", "heures_ml_semaine", "libres", "tampon"):
        if data.get(cle) is None:
            v.warn(None, f"clé absente : `{cle}`")
    v.date(data, "debut", None)
    if data.get("fuseau") not in (None, "Europe/Paris"):
        v.warn(None, f"fuseau {data.get('fuseau')!r} : Europe/Paris attendu")

    heures_ml = 0.0
    for section in ("creneaux_ml", "libres"):
        brut = data.get(section)
        if brut is None:
            if section == "creneaux_ml":
                v.err(None, "clé obligatoire manquante : `creneaux_ml`")
            continue
        if not isinstance(brut, dict):
            v.err(section, "dictionnaire jour -> liste de créneaux attendu")
            continue
        for jour, liste in brut.items():
            try:
                j = common.parse_jour(jour)
            except ErreurFormat as exc:
                v.err(section, str(exc))
                continue
            if not isinstance(liste, list):
                v.err(f"{section}.{j}", "liste de créneaux attendue")
                continue
            valides = []
            for c in liste:
                try:
                    valides.append((common.parse_creneau(c), c))
                except ErreurFormat as exc:
                    v.err(f"{section}.{j}", str(exc))
            valides.sort()
            for (a, ca), (b, cb) in zip(valides, valides[1:]):
                if common.creneaux_chevauchants(a, b):
                    msg = f"créneaux qui se chevauchent : {ca} et {cb}"
                    (v.err if section == "creneaux_ml" else v.warn)(f"{section}.{j}", msg)
            if section == "creneaux_ml":
                heures_ml += sum((b - a) / 60 for (a, b), _ in valides)
    hms = data.get("heures_ml_semaine")
    if isinstance(hms, (int, float)) and not isinstance(hms, bool):
        if abs(hms - heures_ml) > 1e-9:
            v.warn("heures_ml_semaine",
                   f"{hms} h déclarées mais les créneaux ML totalisent {common.fmt_h(heures_ml)}")
    elif hms is not None:
        v.err("heures_ml_semaine", "nombre attendu")

    tampon = data.get("tampon")
    if isinstance(tampon, dict):
        h = tampon.get("heures_semaine")
        if isinstance(h, bool) or not isinstance(h, (int, float)) or h < 0:
            v.err("tampon", "`heures_semaine` : nombre positif attendu")
    elif tampon is not None:
        v.err("tampon", "dictionnaire attendu")

    periodes: list[tuple[dt.date, dt.date, int]] = []
    exceptions = data.get("exceptions") or []
    if not isinstance(exceptions, list):
        v.err("exceptions", "liste attendue")
        exceptions = []
    for i, e in enumerate(exceptions):
        ident = f"exceptions[{i}]"
        if not isinstance(e, dict):
            v.err(ident, "dictionnaire attendu")
            continue
        du, au = v.date(e, "du", ident), v.date(e, "au", ident)
        if du and au:
            if au < du:
                v.err(ident, f"`au` ({au}) précède `du` ({du})")
            else:
                periodes.append((du, au, i))
        e_type = common.type_exception(e.get("type"))
        if e_type not in ("off", "quota"):
            v.err(ident, f"`type` = {e.get('type')!r} invalide (attendu : off, quota)")
        elif e_type == "quota":
            h = e.get("heures")
            if isinstance(h, bool) or not isinstance(h, (int, float)) or h <= 0:
                v.err(ident, "un quota exige `heures` (nombre > 0)")
        if e.get("statut") is None:
            v.warn(ident, "`statut` absent (confirme|provisoire)")
        elif e["statut"] not in STATUTS_EXCEPTION:
            v.err(ident, f"`statut` = {e['statut']!r} invalide (attendu : confirme, provisoire)")
    for k, (du1, au1, i1) in enumerate(periodes):
        for du2, au2, i2 in periodes[k + 1:]:
            if du1 <= au2 and du2 <= au1:
                v.warn(f"exceptions[{i1}]", f"chevauche exceptions[{i2}]")

    imprevus = data.get("imprevus") or []
    if not isinstance(imprevus, list):
        v.err("imprevus", "liste attendue")
        imprevus = []
    for i, e in enumerate(imprevus):
        ident = f"imprevus[{i}]"
        if not isinstance(e, dict):
            v.err(ident, "dictionnaire attendu")
            continue
        d = v.date(e, "date", ident)
        c = v.creneau(e, "creneau", ident)
        if d and c and isinstance(data.get("creneaux_ml"), dict):
            try:
                theo = [common.normaliser_creneau(x)
                        for x in data["creneaux_ml"].get(common.jour_abrege(d), [])]
                if common.formater_creneau(*c) not in theo:
                    v.warn(ident, f"le créneau {e.get('creneau')} ne correspond à aucun créneau ML du "
                                  f"{common.jour_abrege(d)} {d}")
            except ErreurFormat:
                pass
    return len(r.erreurs) == avant


# ---------------------------------------------------------------------------
# state/semaine.yaml
# ---------------------------------------------------------------------------

def verifier_semaine(r: Rapport, data: Any, dispo: Dispo | None, modules: set[str],
                     modules_verifiables: bool) -> dict[str, dict]:
    """Retourne les séances (id -> données) pour d'éventuelles références croisées."""
    f = "state/semaine.yaml"
    v = Verif(r, f)
    if not isinstance(data, dict):
        v.err(None, "un dictionnaire YAML est attendu")
        return {}
    v.requis(data, ["semaine", "du", "au"], None)
    du, au = v.date(data, "du", None), v.date(data, "au", None)
    if du and au:
        if du.weekday() != 0:
            v.err(None, f"`du` ({du}) est un {common.jour_long(du)}, pas un lundi")
        if au != du + dt.timedelta(days=6):
            v.err(None, f"`au` ({au}) devrait être le dimanche {du + dt.timedelta(days=6)}")
        etiquette = data.get("semaine")
        if isinstance(etiquette, str):
            try:
                debut_s, _ = common.parse_semaine(etiquette)
                if debut_s != du:
                    v.err(None, f"`semaine` {etiquette} ne correspond pas à `du` "
                                f"({du} est en {common.etiquette_semaine(du)})")
            except ErreurFormat as exc:
                v.err(None, str(exc))
    seances = data.get("seances")
    if not isinstance(seances, list):
        v.err(None, "`seances` : liste attendue")
        return {}

    par_id: dict[str, dict] = {}
    valides: list[dict[str, Any]] = []
    for i, s in enumerate(seances):
        ident = s.get("id") if isinstance(s, dict) and s.get("id") else f"seances[{i}]"
        if not isinstance(s, dict):
            v.err(ident, "dictionnaire attendu")
            continue
        if not v.requis(s, ["id", "date", "creneau", "type", "tache", "statut"], ident):
            pass
        if isinstance(s.get("id"), str):
            if s["id"] in par_id:
                v.err(ident, "identifiant de séance en double")
            else:
                par_id[s["id"]] = s
        d = v.date(s, "date", ident)
        cr = v.creneau(s, "creneau", ident)
        typ = v.enum(s, "type", TYPES_SEANCE, ident)
        statut = v.enum(s, "statut", STATUTS_SEANCE, ident)
        if isinstance(s.get("id"), str):
            m = RE_SEANCE_ID.match(s["id"])
            if not m:
                v.err(ident, "identifiant attendu au format <date>-<lettre> (ex. 2026-11-02-a)")
            elif d and m.group(1) != d.isoformat():
                v.err(ident, f"l'identifiant porte la date {m.group(1)} mais `date` vaut {d}")
        if d and du and au and not (du <= d <= au):
            v.err(ident, f"date {d} hors de la semaine {du} -> {au}")
        if d and s.get("jour") is not None:
            try:
                if common.parse_jour(s["jour"]) != common.jour_abrege(d):
                    v.err(ident, f"jour {s['jour']!r} incohérent avec la date {d} "
                                 f"({common.jour_long(d)})")
            except ErreurFormat as exc:
                v.err(ident, str(exc))
        hc = s.get("hors_creneau", False)
        if not isinstance(hc, bool):
            v.err(ident, f"`hors_creneau` doit être un booléen (trouvé {hc!r})")
            hc = False
        hr = s.get("heures_reelles")
        if hr is not None and (isinstance(hr, bool) or not isinstance(hr, (int, float)) or hr < 0):
            v.err(ident, f"`heures_reelles` = {hr!r} invalide (nombre >= 0 ou null)")
        elif hr is None and statut in ("faite", "partielle"):
            v.warn(ident, f"séance {statut} sans `heures_reelles`")
        mod = s.get("module")
        if mod is not None:
            if not isinstance(mod, str):
                v.err(ident, "`module` doit être une chaîne ou null")
            elif mod not in modules:
                msg = f"module `{mod}` introuvable (dossier modules/{mod}/ absent)"
                (v.err if modules_verifiables else v.warn)(ident, msg)
        rem = s.get("remplace")
        if typ == "rattrapage" and not rem:
            v.warn(ident, "rattrapage sans `remplace`")
        if typ != "rattrapage" and rem:
            v.warn(ident, "`remplace` n'a de sens que pour un rattrapage")
        if cr and d and typ and statut:
            valides.append({"id": ident, "date": d, "cr": cr, "creneau": s["creneau"], "type": typ,
                            "statut": statut, "hc": hc, "seance": s})

    for s in seances:  # références `remplace` (après avoir recensé les ids)
        if isinstance(s, dict) and s.get("remplace") and s["remplace"] not in par_id:
            v.warn(s.get("id"), f"`remplace` : séance {s['remplace']} absente de cette semaine")

    actives = [x for x in valides if x["statut"] not in STATUTS_SAUTES]

    # chevauchements entre séances actives du même jour
    for k, a in enumerate(actives):
        for b in actives[k + 1:]:
            if a["date"] == b["date"] and common.creneaux_chevauchants(a["cr"], b["cr"]):
                v.err(a["id"], f"chevauche la séance {b['id']} ({a['date']} {a['creneau']} / {b['creneau']})")

    if dispo is not None:
        for x in valides:
            _verifier_creneau_seance(v, dispo, x)
        for x in actives:
            off = dispo.off_du_jour(x["date"])
            if off and not x["hc"]:
                v.err(x["id"], f"séance le {x['date']} pendant une exception `off` "
                               f"({off.du} -> {off.au}) sans `hors_creneau: true`")
            if x["creneau"] and common.normaliser_creneau(x["creneau"]) in \
                    {i.creneau for i in dispo.imprevus_du_jour(x["date"])}:
                v.warn(x["id"], f"séance placée sur un créneau retiré par un imprévu "
                                f"({x['date']} {x['creneau']})")
        if du and au:
            planifie = sum((x["cr"][1] - x["cr"][0]) / 60 for x in actives)
            cap = calculer(dispo, du, au).total
            limite = cap + dispo.tampon_h
            if planifie > limite + 1e-9:
                v.err(None, f"{common.fmt_h(planifie)} planifiées sur la semaine, au-dessus de la "
                            f"capacité {common.fmt_h(cap)} + tampon {common.fmt_h(dispo.tampon_h)} "
                            f"= {common.fmt_h(limite)}")
    return par_id


def _verifier_creneau_seance(v: Verif, dispo: Dispo, x: dict[str, Any]) -> None:
    d, cr, ident = x["date"], x["cr"], x["id"]
    libres = [common.parse_creneau(c) for c in dispo.libres.get(common.jour_abrege(d), [])]
    theo = [common.parse_creneau(c) for c in dispo.creneaux_theoriques(d)]
    if x["type"] == "rattrapage":
        if not x["hc"] and not any(common.creneau_contenu(cr, lib) for lib in libres):
            v.err(ident, f"rattrapage {d} {x['creneau']} hors de tout créneau libre déclaré "
                         f"et sans `hors_creneau: true`")
        return
    if x["hc"] or cr in theo:
        return
    if dispo.quota_du_jour(d) and any(common.creneau_contenu(cr, lib) for lib in libres):
        return
    v.err(ident, f"séance {d} {x['creneau']} hors créneau ML du {common.jour_abrege(d)} "
                 f"(attendu : {', '.join(common.formater_creneau(*t) for t in theo) or 'aucun'}) "
                 f"et sans `hors_creneau: true`")


# ---------------------------------------------------------------------------
# state/competences.yaml
# ---------------------------------------------------------------------------

def verifier_competences(r: Rapport, data: Any, modules: set[str],
                         modules_verifiables: bool) -> set[str]:
    f = "state/competences.yaml"
    v = Verif(r, f)
    ids: set[str] = set()
    if not isinstance(data, dict) or not isinstance(data.get("competences"), list):
        v.err(None, "clé `competences` (liste) attendue")
        return ids
    for i, c in enumerate(data["competences"]):
        ident = c.get("id") if isinstance(c, dict) and c.get("id") else f"competences[{i}]"
        if not isinstance(c, dict):
            v.err(ident, "dictionnaire attendu")
            continue
        v.requis(c, ["id", "nom", "domaine"], ident)
        cid = c.get("id")
        if isinstance(cid, str):
            if cid in ids:
                v.err(ident, "identifiant de compétence en double")
            ids.add(cid)
            if not RE_COMPETENCE.match(cid):
                v.err(ident, "identifiant attendu au format <domaine>.<sujet>[.<sous-sujet>] "
                             "(minuscules, ASCII)")
        dom = v.enum(c, "domaine", common.DOMAINES, ident)
        if dom == "carriere":
            v.warn(ident, "le domaine `carriere` n'a pas de compétences")
        if dom and isinstance(cid, str) and cid.split(".")[0] != dom:
            v.err(ident, f"l'identifiant ne commence pas par le domaine `{dom}.`")
        niveau = v.entier(c, "niveau", ident, 0, 4, nullable=True) if "niveau" in c else None
        v.entier(c, "cible", ident, 0, 4, nullable=True)
        mods = c.get("modules")
        if not isinstance(mods, list):
            v.err(ident, "`modules` : liste attendue")
        else:
            for m in mods:
                if not isinstance(m, str):
                    v.err(ident, f"module {m!r} : chaîne attendue")
                elif modules_verifiables and m not in modules:
                    v.warn(ident, f"module `{m}` sans dossier modules/{m}/ (pas encore créé ?)")
        derniere = None
        preuves = c.get("preuves") or []
        if not isinstance(preuves, list):
            v.err(ident, "`preuves` : liste attendue")
            preuves = []
        for k, p in enumerate(preuves):
            pid = f"{ident} preuve {k + 1}"
            if not isinstance(p, dict):
                v.err(pid, "dictionnaire attendu")
                continue
            d = v.date(p, "date", pid)
            v.enum(p, "type", TYPES_PREUVE, pid)
            if d:
                if derniere and d < derniere:
                    v.warn(pid, f"preuves non triées par date ({d} après {derniere})")
                derniere = d
            for cle, maxi in (("note", 2), ("aide", 4)):
                val = p.get(cle)
                if val is not None and (isinstance(val, bool) or not isinstance(val, (int, float))
                                        or not 0 <= val <= maxi):
                    v.err(pid, f"`{cle}` = {val!r} hors de 0..{maxi}")
        pv = v.date(c, "prochaine_verif", ident, obligatoire=False)
        if niveau is not None and niveau >= 2 and c.get("prochaine_verif") is None:
            v.warn(ident, f"niveau {niveau} sans `prochaine_verif`")
        if (niveau is None or niveau < 2) and pv is not None:
            v.warn(ident, "`prochaine_verif` renseignée alors que le niveau est inférieur à 2")
        if c.get("intervalle_sem") is not None and c["intervalle_sem"] not in INTERVALLES:
            v.err(ident, f"`intervalle_sem` = {c['intervalle_sem']!r} invalide "
                         f"(attendu : {', '.join(map(str, INTERVALLES))})")
        if c.get("echecs_consecutifs") is not None:
            v.entier(c, "echecs_consecutifs", ident, 0)
    return ids


# ---------------------------------------------------------------------------
# state/jalons.yaml
# ---------------------------------------------------------------------------

def verifier_jalons(r: Rapport, data: Any) -> None:
    f = "state/jalons.yaml"
    v = Verif(r, f)
    if not isinstance(data, dict) or not isinstance(data.get("jalons"), list):
        v.err(None, "clé `jalons` (liste) attendue")
        return
    vus: set[str] = set()
    for i, j in enumerate(data["jalons"]):
        ident = j.get("id") if isinstance(j, dict) and j.get("id") else f"jalons[{i}]"
        if not isinstance(j, dict):
            v.err(ident, "dictionnaire attendu")
            continue
        v.requis(j, ["id", "nom", "critere"], ident)
        if isinstance(j.get("id"), str):
            if j["id"] in vus:
                v.err(ident, "identifiant de jalon en double")
            vus.add(j["id"])
            if not RE_JALON.match(j["id"]):
                v.warn(ident, "identifiant attendu au format jNN-slug")
        v.date(j, "date", ident)
        typ = v.enum(j, "type", TYPES_JALON, ident)
        v.enum(j, "statut", STATUTS_JALON, ident)
        h = j.get("heures_restantes_estimees")
        if h is None:
            v.warn(ident, "`heures_restantes_estimees` absent : marge incalculable")
        elif isinstance(h, bool) or not isinstance(h, (int, float)) or h < 0:
            v.err(ident, f"`heures_restantes_estimees` = {h!r} invalide (nombre >= 0)")
        if typ == "dur" and not j.get("source"):
            v.warn(ident, "jalon dur sans `source` (échéance externe à sourcer)")


# ---------------------------------------------------------------------------
# modules/
# ---------------------------------------------------------------------------

def verifier_modules(r: Rapport, racine: Path, competences: set[str] | None,
                     ressources: set[str] | None) -> set[str]:
    """Vérifie fiches, questions, cartes, exercices. Retourne les ids de cartes."""
    ids_globaux: dict[str, str] = {}
    cartes_ids: set[str] = set()
    for dossier in common.dossiers_modules(racine):
        mod = dossier.name
        rel = f"modules/{mod}"
        if not common.RE_ID.match(mod):
            r.erreur(rel, None, "nom de module invalide (ASCII, minuscules, `-` et `.` autorisés)")
        _verifier_fiche(r, racine, dossier, competences)
        for nom, kind in (("questions.yaml", "q"), ("cartes.yaml", "c")):
            rel_f = f"{rel}/{nom}"
            present, data = charger(r, racine, rel_f, obligatoire=False)
            if not present:
                r.avertissement(rel_f, None, "fichier absent")
                continue
            if data is None:
                continue
            if not isinstance(data, list):
                r.erreur(rel_f, None, "une liste YAML est attendue")
                continue
            v = Verif(r, rel_f)
            for i, entree in enumerate(data):
                if kind == "q":
                    _verifier_question(v, mod, i, entree, competences, ressources, ids_globaux)
                else:
                    cid = _verifier_carte(v, mod, i, entree, competences, ids_globaux)
                    if cid:
                        cartes_ids.add(cid)
        _verifier_exercices(r, racine, dossier)
    return cartes_ids


def _verifier_fiche(r: Rapport, racine: Path, dossier: Path, competences: set[str] | None) -> None:
    rel = f"modules/{dossier.name}/fiche.md"
    chemin = dossier / "fiche.md"
    if not chemin.is_file():
        r.avertissement(rel, None, "fichier absent")
        return
    try:
        texte = common.lire_texte(chemin)
    except ErreurDonnees as exc:
        r.erreur(rel, None, str(exc))
        return
    titres = {m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", texte, re.M)}
    for section in SECTIONS_FICHE:
        if section not in titres:
            r.avertissement(rel, None, f"section `## {section}` absente")
    if competences is not None:
        m = re.search(r"^##\s+Compétences visées\s*$(.*?)(?=^##\s|\Z)", texte, re.M | re.S)
        if m:
            for cid in sorted(set(RE_ID_COMPETENCE_TEXTE.findall(m.group(1)))):
                if cid.endswith(".*"):
                    prefixe = cid[:-1]
                    if not any(c.startswith(prefixe) for c in competences):
                        r.avertissement(rel, cid, "aucune compétence ne correspond à ce motif")
                elif cid not in competences:
                    r.avertissement(rel, cid, "compétence visée absente de state/competences.yaml")


def _enregistrer_id(v: Verif, ident: str, ids_globaux: dict[str, str]) -> None:
    if ident in ids_globaux:
        v.err(ident, f"identifiant en double (déjà défini dans {ids_globaux[ident]})")
    else:
        ids_globaux[ident] = v.fichier


def _verifier_question(v: Verif, mod: str, i: int, q: Any, competences: set[str] | None,
                       ressources: set[str] | None, ids_globaux: dict[str, str]) -> None:
    ident = q.get("id") if isinstance(q, dict) and q.get("id") else f"#{i + 1}"
    if not isinstance(q, dict):
        v.err(ident, "dictionnaire attendu")
        return
    v.requis(q, ["id", "competence", "type", "difficulte", "question"], ident)
    if isinstance(q.get("id"), str):
        _enregistrer_id(v, q["id"], ids_globaux)
        if not re.fullmatch(re.escape(mod) + r"-q\d{3,}", q["id"]):
            v.err(ident, f"identifiant attendu au format {mod}-qNNN")
    v.enum(q, "type", TYPES_QUESTION, ident)
    v.entier(q, "difficulte", ident, 1, 3)
    v.entier(q, "seance", ident, 1, nullable=True)
    _competence_existe(v, q, ident, competences)
    pa = q.get("points_attendus")
    if not isinstance(pa, list) or not pa or not all(isinstance(x, str) and x.strip() for x in pa):
        v.err(ident, "`points_attendus` : liste non vide de textes attendue")
    src = q.get("source")
    if not src:
        v.err(ident, "`source` manquante ou vide")
    elif not isinstance(src, dict):
        v.err(ident, "`source` : dictionnaire {ressource, ref, url} attendu")
    else:
        if not src.get("ressource") or not src.get("ref"):
            v.warn(ident, "`source` devrait contenir `ressource` et `ref`")
        elif ressources is not None and src["ressource"] not in ressources:
            v.warn(ident, f"ressource `{src['ressource']}` absente de ressources/catalogue.yaml")


def _verifier_carte(v: Verif, mod: str, i: int, c: Any, competences: set[str] | None,
                    ids_globaux: dict[str, str]) -> str | None:
    ident = c.get("id") if isinstance(c, dict) and c.get("id") else f"#{i + 1}"
    if not isinstance(c, dict):
        v.err(ident, "dictionnaire attendu")
        return None
    v.requis(c, ["id", "recto", "verso", "source", "competence"], ident)
    cid = c.get("id") if isinstance(c.get("id"), str) else None
    if cid:
        _enregistrer_id(v, cid, ids_globaux)
        if not re.fullmatch(re.escape(mod) + r"-[ce]\d{3,}", cid):
            v.err(ident, f"identifiant attendu au format {mod}-cNNN (ou {mod}-eNNN pour une erreur)")
    for cle in ("recto", "verso", "source"):
        if c.get(cle) is not None and not isinstance(c[cle], str):
            v.err(ident, f"`{cle}` : texte attendu")
    _competence_existe(v, c, ident, competences)
    v.entier(c, "seance", ident, 1, nullable=True)
    if cid and re.search(r"-e\d+$", cid) and c.get("seance") is not None:
        v.warn(ident, "une carte d'erreur ne devrait pas avoir de `seance`")
    tags = c.get("tags")
    if tags is not None and (not isinstance(tags, list) or not all(isinstance(t, str) for t in tags)):
        v.err(ident, "`tags` : liste de textes attendue")
    elif not any(t in TAGS_CARTE for t in (tags or [])):
        v.warn(ident, "aucune étiquette parmi essentiel|complement|erreur")
    return cid


def _competence_existe(v: Verif, d: dict, ident: Any, competences: set[str] | None) -> None:
    comp = d.get("competence")
    if isinstance(comp, str) and competences is not None and comp not in competences:
        v.err(ident, f"compétence `{comp}` absente de state/competences.yaml")


def _verifier_exercices(r: Rapport, racine: Path, dossier: Path) -> None:
    exo = dossier / "exercices"
    if not exo.is_dir():
        return
    for md in sorted(exo.glob("ex*.md")):
        m = re.match(r"^(ex\d{2})-", md.name)
        rel = f"modules/{dossier.name}/exercices/{md.name}"
        if not m:
            r.avertissement(rel, None, "nom attendu : exNN-<slug>.md")
            continue
        # Noms uniques dans tout le repo : test_<module_avec_underscores>_exNN.py (FORMATS).
        attendu = f"test_{dossier.name.replace('-', '_')}_{m.group(1)}.py"
        if not (exo / "tests" / attendu).is_file():
            r.avertissement(rel, None, f"tests/{attendu} absent")


# ---------------------------------------------------------------------------
# ressources, registre, journal, divers
# ---------------------------------------------------------------------------

def verifier_catalogue(r: Rapport, data: Any) -> set[str] | None:
    f = "ressources/catalogue.yaml"
    v = Verif(r, f)
    if not isinstance(data, list):
        v.err(None, "une liste YAML est attendue")
        return None
    ids: set[str] = set()
    for i, e in enumerate(data):
        ident = e.get("id") if isinstance(e, dict) and e.get("id") else f"#{i + 1}"
        if not isinstance(e, dict):
            v.err(ident, "dictionnaire attendu")
            continue
        v.requis(e, ["id", "titre"], ident)
        if isinstance(e.get("id"), str):
            if e["id"] in ids:
                v.err(ident, "identifiant de ressource en double")
            ids.add(e["id"])
            if not common.RE_ID.match(e["id"]):
                v.err(ident, "identifiant invalide (ASCII, minuscules, `-` et `.`)")
        if not e.get("url"):
            v.warn(ident, "`url` absente")
        v.enum(e, "acces", ["gratuit", "payant", "mixte"], ident, False)
        v.enum(e, "langue", ["en", "fr"], ident, False)
        v.enum(e, "format", ["html", "pdf", "video", "cours", "exercices", "livre"], ident, False)
        v.enum(e, "niveau", ["debutant", "intermediaire", "avance"], ident, False)
        v.enum(e, "role", ["principale", "secours", "complement"], ident, False)
        v.date(e, "verifie_le", ident, obligatoire=False)
        doms = e.get("domaines")
        if isinstance(doms, list):
            for dom in doms:
                if dom not in common.DOMAINES:
                    v.err(ident, f"domaine `{dom}` inconnu")
    return ids


def verifier_progression(r: Rapport, racine: Path, modules: set[str], modules_verifiables: bool) -> None:
    f = "anki/progression.yaml"
    present, data = charger(r, racine, f, obligatoire=False)
    if not present or data is None:
        return
    v = Verif(r, f)
    try:
        progression = common.valider_progression(data)
    except ErreurDonnees as exc:
        msg = str(exc)
        v.err(None, msg[len("anki/progression.yaml : "):] if msg.startswith("anki/progression.yaml : ") else msg)
        return
    for module in progression:
        if module not in modules:
            msg = f"module `{module}` introuvable (dossier modules/{module}/ absent)"
            (v.err if modules_verifiables else v.warn)(module, msg)


def verifier_registre(r: Rapport, racine: Path, cartes_ids: set[str]) -> None:
    f = "anki/registre.csv"
    chemin = racine / f
    if not chemin.exists():
        return
    v = Verif(r, f)
    try:
        lignes = common.charger_csv_registre(chemin)
    except ErreurDonnees as exc:
        msg = str(exc)
        prefixe = f"{chemin.as_posix()} : "
        v.err(None, msg[len(prefixe):] if msg.startswith(prefixe) else msg)
        return
    for n, ligne in enumerate(lignes, start=2):
        ident = ligne.get("id") or f"ligne {n}"
        if not ligne.get("id"):
            v.err(ident, "identifiant de carte vide")
        elif ligne["id"] not in cartes_ids:
            v.err(ident, "carte inconnue : absente de modules/*/cartes.yaml")
        try:
            common.parse_date(ligne.get("date"))
        except ErreurFormat as exc:
            v.err(ident, f"`date` : {exc}")
        if not ligne.get("paquet"):
            v.err(ident, "`paquet` vide")


RE_ENTETE_JOURNAL = re.compile(r"^#\s+(\d{4}-\d{2}-\d{2})\s*\(([^)]+)\)")


def verifier_journal(r: Rapport, racine: Path) -> None:
    dossier = racine / "journal"
    if not dossier.is_dir():
        return
    for chemin in sorted(dossier.glob("*.md")):
        rel = f"journal/{chemin.name}"
        nom = chemin.stem
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", nom):
            try:
                d = common.parse_date(nom)
            except ErreurFormat:
                r.erreur(rel, None, "date invalide dans le nom du fichier")
                continue
            try:
                lignes = common.lire_texte(chemin).splitlines()
            except ErreurDonnees as exc:
                r.erreur(rel, None, str(exc))
                continue
            m = RE_ENTETE_JOURNAL.match(lignes[0]) if lignes else None
            if not m:
                r.avertissement(rel, None, "titre attendu : `# AAAA-MM-JJ (jour)`")
                continue
            if m.group(1) != nom:
                r.erreur(rel, None, f"le titre porte la date {m.group(1)}, le fichier est du {nom}")
            jour = m.group(2).strip().lower()
            if jour not in (common.jour_long(d), common.jour_abrege(d)):
                r.erreur(rel, None, f"jour `{m.group(2).strip()}` incohérent avec la date {nom} "
                                    f"({common.jour_long(d)})")
        elif re.fullmatch(r"bilan-\d{4}-W\d{2}", nom):
            try:
                common.parse_semaine(nom[len("bilan-"):])
            except ErreurFormat:
                r.erreur(rel, None, "semaine ISO invalide dans le nom du fichier")
        elif re.fullmatch(r"resume-\d{4}-(0[1-9]|1[0-2])", nom):
            pass
        else:
            r.avertissement(rel, None, "nom inattendu (AAAA-MM-JJ.md, bilan-AAAA-Www.md, resume-AAAA-MM.md)")


def verifier_now(r: Rapport, racine: Path) -> None:
    chemin = racine / "NOW.md"
    if chemin.is_file():
        try:
            n = len(common.lire_texte(chemin).splitlines())
        except ErreurDonnees:
            return
        if n > 60:
            r.avertissement("NOW.md", None, f"{n} lignes (60 au plus) : relancer tools/now.py")


def verifier_doublons_tests(r: Rapport, racine: Path) -> None:
    """Deux fichiers `test_*.py` de même nom font échouer pytest (import mismatch)."""
    ignores = {".git", "fixtures", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache"}
    vus: dict[str, list[str]] = {}
    for base, dirs, fichiers in os.walk(racine):
        dirs[:] = sorted(d for d in dirs if d not in ignores)
        for nom in sorted(fichiers):
            if nom.startswith("test_") and nom.endswith(".py"):
                vus.setdefault(nom, []).append(common.chemin_relatif(racine, Path(base) / nom))
    for nom, chemins in sorted(vus.items()):
        if len(chemins) > 1:
            r.avertissement(chemins[0], None,
                            f"nom de test en double dans le repo ({', '.join(chemins)}) : "
                            f"pytest refusera de les collecter ensemble")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def verifier_repo(racine: Path) -> Rapport:
    r = Rapport()
    modules_dossiers = {p.name for p in common.dossiers_modules(racine)}
    modules_verifiables = bool(modules_dossiers)
    if not modules_verifiables:
        r.avertissement("modules/", None, "dossier absent ou vide : références aux modules et "
                                          "cartes non vérifiables")

    present, dispo_data = charger(r, racine, "state/dispo.yaml", True)
    dispo = None
    if present and dispo_data is not None:
        if verifier_dispo(r, dispo_data):
            try:
                dispo = Dispo.depuis_donnees(dispo_data)
            except ErreurDonnees as exc:
                r.erreur("state/dispo.yaml", None, str(exc))
        if dispo is None:
            r.avertissement("state/semaine.yaml", None,
                            "vérifications de créneaux et de capacité ignorées (dispo.yaml invalide)")

    present, comp_data = charger(r, racine, "state/competences.yaml", True)
    competences: set[str] | None = None
    if present and comp_data is not None:
        competences = verifier_competences(r, comp_data, modules_dossiers, modules_verifiables)

    present, sem_data = charger(r, racine, "state/semaine.yaml", True)
    if present and sem_data is not None:
        verifier_semaine(r, sem_data, dispo, modules_dossiers, modules_verifiables)

    present, jal_data = charger(r, racine, "state/jalons.yaml", True)
    if present and jal_data is not None:
        verifier_jalons(r, jal_data)

    present, cat_data = charger(r, racine, "ressources/catalogue.yaml", False)
    ressources = verifier_catalogue(r, cat_data) if present and cat_data is not None else None

    cartes_ids = verifier_modules(r, racine, competences, ressources)
    verifier_progression(r, racine, modules_dossiers, modules_verifiables)
    verifier_registre(r, racine, cartes_ids)
    verifier_journal(r, racine)
    verifier_now(r, racine)
    verifier_doublons_tests(r, racine)
    return r


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="check.py",
        description="Valide les fichiers d'état, les modules, le registre Anki et le journal. "
                    "Code de sortie 1 s'il y a des erreurs ; les avertissements ne bloquent pas.",
    )
    common.ajouter_option_racine(p)
    return p


def main(argv: list[str] | None = None) -> int:
    common.configurer_sortie()
    args = construire_parseur().parse_args(argv)
    try:
        racine = common.racine_depuis_arg(args.racine)
    except ErreurDonnees as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2
    rapport = verifier_repo(racine)
    for ligne in rapport.erreurs + rapport.avertissements:
        print(ligne)
    ne, na = len(rapport.erreurs), len(rapport.avertissements)
    if ne == 0 and na == 0:
        print("OK : aucune erreur, aucun avertissement.")
    else:
        print(f"Résumé : {ne} erreur(s), {na} avertissement(s).")
    return 1 if ne else 0


if __name__ == "__main__":
    sys.exit(main())
