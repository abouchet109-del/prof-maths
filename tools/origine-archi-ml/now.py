"""Génère `NOW.md` : le point d'entrée court (60 lignes au plus) de chaque session.

Usage (depuis la racine du repo ; `--racine DOSSIER` pour les tests) :

    python tools/now.py [--date AAAA-MM-JJ]

Sections, dans l'ordre : séance(s) du jour, séances restantes de la semaine,
séances à rattraper, vérifications de maintien dues (7 jours), jalons, Anki.

Entrées : `state/semaine.yaml`, `state/competences.yaml`, `state/jalons.yaml`,
`state/dispo.yaml`, `modules/*/cartes.yaml`, `anki/registre.csv`, `anki/progression.yaml`
(seules les cartes exportables selon la progression comptent comme en attente).
Les listes trop longues sont tronquées avec « … +N ». La sortie est
déterministe pour une `--date` donnée.

Codes de sortie : 0 si NOW.md est écrit, 2 si un fichier est manquant ou invalide.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

import common
from common import ErreurDonnees, ErreurFormat, fmt_h
from cal import Dispo, charger_jalons, prevoir_jalons

LIGNES_MAX = 60
FENETRE_MAINTIEN_J = 7
LARGEUR_MAX = 160


def court(texte: Any, largeur: int = LARGEUR_MAX) -> str:
    t = " ".join(str(texte).split())
    return t if len(t) <= largeur else t[: largeur - 1].rstrip() + "…"


def tronquer(lignes: list[str], limite: int) -> list[str]:
    if len(lignes) <= limite:
        return lignes
    return lignes[:limite] + [f"- … +{len(lignes) - limite}"]


# ---------------------------------------------------------------------------
# Collecte des données
# ---------------------------------------------------------------------------

def _date_ou_none(valeur: Any) -> dt.date | None:
    try:
        return common.parse_date(valeur)
    except ErreurFormat:
        return None


def charger_seances(racine: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = common.charger_yaml(racine / "state" / "semaine.yaml")
    if not isinstance(data, dict) or not isinstance(data.get("seances"), list):
        raise ErreurDonnees("state/semaine.yaml : clé `seances` (liste) attendue")
    seances = []
    for i, s in enumerate(data["seances"], start=1):
        if not isinstance(s, dict):
            raise ErreurDonnees(f"state/semaine.yaml : séance n°{i} mal formée")
        d = _date_ou_none(s.get("date"))
        if d is None or not isinstance(s.get("creneau"), str):
            raise ErreurDonnees(f"state/semaine.yaml : séance {s.get('id', i)} sans date ou créneau valide")
        seances.append({**s, "_date": d})
    seances.sort(key=lambda s: (s["_date"], s["creneau"], str(s.get("id", ""))))
    return data, seances


def charger_competences(racine: Path) -> list[dict[str, Any]]:
    data = common.charger_yaml(racine / "state" / "competences.yaml")
    if not isinstance(data, dict) or not isinstance(data.get("competences"), list):
        raise ErreurDonnees("state/competences.yaml : clé `competences` (liste) attendue")
    return [c for c in data["competences"] if isinstance(c, dict)]


def seances_a_rattraper(seances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    couvertes = {s.get("remplace") for s in seances if s.get("type") == "rattrapage" and s.get("remplace")}
    return [s for s in seances
            if s.get("statut") in ("sautee", "deplacee") and s.get("id") not in couvertes]


def maintien_du(competences: list[dict[str, Any]], aujourdhui: dt.date) -> list[dict[str, Any]]:
    limite = aujourdhui + dt.timedelta(days=FENETRE_MAINTIEN_J)
    dues = []
    for c in competences:
        d = _date_ou_none(c.get("prochaine_verif"))
        if d is not None and d <= limite:
            dues.append({"id": c.get("id", "?"), "niveau": c.get("niveau"), "date": d})
    dues.sort(key=lambda x: (x["date"], str(x["id"])))
    return dues


def etat_anki(racine: Path) -> tuple[int, str | None]:
    """(cartes en attente d'export selon la progression, date du dernier paquet ou None)."""
    cartes = common.charger_cartes(racine)
    progression = common.charger_progression(racine)
    registre = common.charger_csv_registre(racine / "anki" / "registre.csv")
    exportees = {ligne["id"] for ligne in registre}
    en_attente = len({c["id"] for c in cartes
                      if c["id"] not in exportees and common.carte_exportable(c, progression)})
    dates = [ligne["date"] for ligne in registre if _date_ou_none(ligne.get("date"))]
    return en_attente, (max(dates) if dates else None)


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------

def _libelle_seance(s: dict[str, Any]) -> str:
    mod = s.get("module") or "sans module"
    return f"{s['creneau']} · {s.get('type', '?')} · {mod}"


def construire(aujourdhui: dt.date, semaine: dict[str, Any], seances: list[dict[str, Any]],
               maintien: list[dict[str, Any]], jalons: list[dict[str, Any]],
               anki: tuple[int, str | None], lim: dict[str, int]) -> list[str]:
    out: list[str] = [f"# Aujourd'hui — {aujourdhui.isoformat()} ({common.jour_long(aujourdhui)})"]

    du_jour = [s for s in seances if s["_date"] == aujourdhui]
    if not du_jour:
        out.append("Pas de séance aujourd'hui.")
        du, au = _date_ou_none(semaine.get("du")), _date_ou_none(semaine.get("au"))
        if du and au and not (du <= aujourdhui <= au):
            out.append(f"Attention : state/semaine.yaml couvre {du.isoformat()} -> {au.isoformat()}, "
                       f"pas cette date (check-in à faire ?).")
    for s in du_jour[: lim["jour"]]:
        out.append(f"- {_libelle_seance(s)} · statut {s.get('statut', '?')}")
        if s.get("tache"):
            out.append(f"  Tâche : {court(s['tache'])}")
        ressources = s.get("ressources")
        if ressources:
            liste = ressources if isinstance(ressources, list) else [ressources]
            out.append(f"  Ressources : {court(' ; '.join(str(x) for x in liste))}")
        if s.get("livrable"):
            out.append(f"  Livrable : {court(s['livrable'])}")
    if len(du_jour) > lim["jour"]:
        out.append(f"- … +{len(du_jour) - lim['jour']}")

    out += ["", "## Cette semaine"]
    restantes = []
    for s in seances:
        if s["_date"] != aujourdhui and s.get("statut") in ("prevue", "partielle"):
            passee = " (passée, à débriefer)" if s["_date"] < aujourdhui else ""
            restantes.append(f"- {common.jour_abrege(s['_date'])} {s['_date'].isoformat()} "
                             f"{_libelle_seance(s)} · {s.get('statut')}{passee}")
    out += tronquer(restantes, lim["semaine"]) if restantes else ["- Aucune autre séance restante."]

    out += ["", "## À rattraper"]
    manquees = [f"- {s.get('id', '?')} · {s['_date'].isoformat()} {_libelle_seance(s)} · {s.get('statut')}"
                for s in seances_a_rattraper(seances)]
    out += tronquer(manquees, lim["rattraper"]) if manquees else ["- Rien à rattraper."]

    out += ["", "## Vérifications de maintien dues"]
    dues = []
    for m in maintien:
        niveau = "non évalué" if m["niveau"] is None else f"niveau {m['niveau']}"
        retard = (aujourdhui - m["date"]).days
        suffixe = f" (en retard de {retard} j)" if retard > 0 else ""
        dues.append(f"- {m['id']} · {niveau} · due le {m['date'].isoformat()}{suffixe}")
    out += tronquer(dues, lim["maintien"]) if dues else ["- Aucune d'ici 7 jours."]

    out += ["", "## Jalons"]
    lignes_j = []
    for j in jalons:
        marge = "marge inconnue" if j["marge"] is None else f"marge {fmt_h(j['marge'])}"
        statut = j["statut"] if j["suggere"] == j["statut"] else f"{j['statut']} (suggéré : {j['suggere']})"
        echu = " · ECHEANCE DEPASSEE" if j["echu"] else ""
        lignes_j.append(f"- {j['id']} · {j['date'].isoformat()} ({j['type'] or '?'}) · "
                        f"{marge} sur {fmt_h(j['capacite'])} · {statut}{echu}")
    out += tronquer(lignes_j, lim["jalons"]) if lignes_j else ["- Aucun jalon à venir."]

    out += ["", "## Anki"]
    n, dernier = anki
    out.append(f"- {n} carte(s) en attente d'export")
    out.append(f"- Dernier paquet : {dernier}" if dernier else "- Dernier paquet : aucun")

    out += ["", f"généré le {aujourdhui.isoformat()} par tools/now.py"]
    return out


def rendre(aujourdhui, semaine, seances, maintien, jalons, anki) -> list[str]:
    """Construit les lignes de NOW.md en réduisant les listes jusqu'à 60 lignes."""
    lim = {"jour": 3, "semaine": 8, "rattraper": 6, "maintien": 6, "jalons": 4}
    while True:
        lignes = construire(aujourdhui, semaine, seances, maintien, jalons, anki, lim)
        if len(lignes) <= LIGNES_MAX:
            return lignes
        cle = max(lim, key=lambda k: lim[k])
        if lim[cle] <= 1:
            return lignes[: LIGNES_MAX - 1] + [lignes[-1]]
        lim[cle] -= 1


def generer(racine: Path, aujourdhui: dt.date) -> list[str]:
    dispo = Dispo.charger(racine)
    semaine, seances = charger_seances(racine)
    competences = charger_competences(racine)
    jalons = prevoir_jalons(dispo, charger_jalons(racine), aujourdhui)
    return rendre(aujourdhui, semaine, seances, maintien_du(competences, aujourdhui), jalons,
                  etat_anki(racine))


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="now.py",
        description="Génère NOW.md (60 lignes au plus) : séance du jour, semaine, rattrapages, "
                    "maintien, jalons et Anki.",
    )
    p.add_argument("--date", type=common.date_arg, metavar="AAAA-MM-JJ",
                   help="date à utiliser à la place d'aujourd'hui (pour les tests)")
    common.ajouter_option_racine(p)
    return p


def main(argv: list[str] | None = None) -> int:
    common.configurer_sortie()
    args = construire_parseur().parse_args(argv)
    try:
        racine = common.racine_depuis_arg(args.racine)
        lignes = generer(racine, common.aujourdhui(args.date))
        (racine / "NOW.md").write_text("\n".join(lignes) + "\n", encoding="utf-8", newline="\n")
    except ErreurDonnees as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2
    print(f"NOW.md écrit ({len(lignes)} lignes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
