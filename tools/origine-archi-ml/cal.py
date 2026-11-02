"""Calendrier ML : créneaux, capacité, semaine ISO et prévision des jalons.

Usage (depuis la racine du repo ; `--racine DOSSIER` pour les tests) :

    python tools/cal.py creneaux --du AAAA-MM-JJ --au AAAA-MM-JJ
    python tools/cal.py capacite --du AAAA-MM-JJ --au AAAA-MM-JJ
    python tools/cal.py semaine AAAA-MM-JJ
    python tools/cal.py jalons [--date AAAA-MM-JJ]

Données lues : `state/dispo.yaml` (et `state/jalons.yaml` pour `jalons`).

Règles :
  - une exception `off` supprime les créneaux des jours concernés ;
  - une exception `quota` impose un nombre d'heures sur sa période ; si la
    plage demandée ne la couvre qu'en partie, les heures sont comptées au
    prorata des jours, et `creneaux` signale la période au lieu de générer
    les créneaux fixes ;
  - un `imprevu` retire un créneau précis ;
  - aucun créneau avant `debut` ;
  - `jalons` : capacité de la date (incluse) à la date du jalon (incluse) ;
    marge = capacité - heures_restantes_estimees ; statut suggéré `a_risque`
    si la marge est négative ou inférieure à 10 % de la capacité.

Codes de sortie : 0 si tout va bien, 2 en cas de fichier manquant ou invalide.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import common
from common import ErreurDonnees, ErreurFormat, fmt_h


# ---------------------------------------------------------------------------
# Modèle
# ---------------------------------------------------------------------------

@dataclass
class Periode:
    du: dt.date
    au: dt.date
    type: str                      # "off" | "quota"
    heures: float | None = None
    note: str = ""
    statut: str = ""

    def contient(self, d: dt.date) -> bool:
        return self.du <= d <= self.au

    @property
    def nb_jours(self) -> int:
        return (self.au - self.du).days + 1


@dataclass
class Imprevu:
    date: dt.date
    creneau: str                   # forme canonique
    note: str = ""


@dataclass
class Dispo:
    debut: dt.date
    creneaux_ml: dict[str, list[str]]
    libres: dict[str, list[str]]
    tampon_h: float
    heures_ml_semaine: float | None = None
    periodes: list[Periode] = field(default_factory=list)
    imprevus: list[Imprevu] = field(default_factory=list)

    # -- construction -------------------------------------------------------
    @classmethod
    def depuis_donnees(cls, data: Any, nom: str = "state/dispo.yaml") -> "Dispo":
        try:
            if not isinstance(data, dict):
                raise ErreurFormat("le fichier doit être un dictionnaire YAML")
            debut = common.parse_date(data.get("debut"))
            creneaux = _jours_creneaux(data.get("creneaux_ml"), "creneaux_ml")
            libres = _jours_creneaux(data.get("libres") or {}, "libres")
            tampon = data.get("tampon") or {}
            tampon_h = float(tampon.get("heures_semaine", 6)) if isinstance(tampon, dict) else 6.0
            hms = data.get("heures_ml_semaine")
            periodes = []
            for i, e in enumerate(data.get("exceptions") or []):
                if not isinstance(e, dict):
                    raise ErreurFormat(f"exceptions[{i}] : dictionnaire attendu")
                typ = common.type_exception(e.get("type"))
                if typ not in ("off", "quota"):
                    raise ErreurFormat(f"exceptions[{i}] : type {typ!r} invalide (off|quota)")
                du, au = common.parse_date(e.get("du")), common.parse_date(e.get("au"))
                if au < du:
                    raise ErreurFormat(f"exceptions[{i}] : `au` précède `du`")
                heures = None
                if typ == "quota":
                    if isinstance(e.get("heures"), bool) or not isinstance(e.get("heures"), (int, float)):
                        raise ErreurFormat(f"exceptions[{i}] : `heures` numérique requis pour un quota")
                    heures = float(e["heures"])
                periodes.append(Periode(du, au, typ, heures, str(e.get("note") or ""),
                                        str(e.get("statut") or "")))
            imprevus = []
            for i, e in enumerate(data.get("imprevus") or []):
                if not isinstance(e, dict):
                    raise ErreurFormat(f"imprevus[{i}] : dictionnaire attendu")
                imprevus.append(Imprevu(common.parse_date(e.get("date")),
                                        common.normaliser_creneau(e.get("creneau")),
                                        str(e.get("note") or "")))
        except (ErreurFormat, TypeError, ValueError) as exc:
            raise ErreurDonnees(f"{nom} : {exc}") from exc
        return cls(debut, creneaux, libres, tampon_h,
                   float(hms) if isinstance(hms, (int, float)) and not isinstance(hms, bool) else None,
                   periodes, imprevus)

    @classmethod
    def charger(cls, racine: Path) -> "Dispo":
        return cls.depuis_donnees(common.charger_yaml(racine / "state" / "dispo.yaml"))

    # -- requêtes -----------------------------------------------------------
    def periodes_du_type(self, typ: str) -> list[Periode]:
        return [p for p in self.periodes if p.type == typ]

    def off_du_jour(self, d: dt.date) -> Periode | None:
        return next((p for p in self.periodes_du_type("off") if p.contient(d)), None)

    def quota_du_jour(self, d: dt.date) -> Periode | None:
        return next((p for p in self.periodes_du_type("quota") if p.contient(d)), None)

    def creneaux_theoriques(self, d: dt.date) -> list[str]:
        """Créneaux ML fixes du jour de la semaine, sans exceptions."""
        return list(self.creneaux_ml.get(common.jour_abrege(d), []))

    def imprevus_du_jour(self, d: dt.date) -> list[Imprevu]:
        return [i for i in self.imprevus if i.date == d]

    def creneaux_fixes(self, d: dt.date) -> list[str]:
        """Créneaux ML effectifs : vide avant `debut`, en `off` ou en `quota`."""
        if d < self.debut or self.off_du_jour(d) or self.quota_du_jour(d):
            return []
        perdus = {i.creneau for i in self.imprevus_du_jour(d)}
        return [c for c in self.creneaux_theoriques(d) if c not in perdus]


def _jours_creneaux(brut: Any, nom: str) -> dict[str, list[str]]:
    if not isinstance(brut, dict):
        raise ErreurFormat(f"`{nom}` : dictionnaire jour -> créneaux attendu")
    sortie: dict[str, list[str]] = {}
    for jour, liste in brut.items():
        j = common.parse_jour(jour)
        if not isinstance(liste, list):
            raise ErreurFormat(f"`{nom}.{jour}` : liste attendue")
        sortie[j] = sorted((common.normaliser_creneau(c) for c in liste),
                           key=lambda c: common.parse_creneau(c))
    return sortie


# ---------------------------------------------------------------------------
# Calculs
# ---------------------------------------------------------------------------

@dataclass
class QuotaPartiel:
    periode: Periode
    jours_demandes: int
    heures: float


@dataclass
class Capacite:
    du: dt.date
    au: dt.date
    creneaux: list[tuple[dt.date, str]]
    quotas: list[QuotaPartiel]

    @property
    def heures_fixes(self) -> float:
        return sum(common.duree_creneau_h(c) for _, c in self.creneaux)

    @property
    def heures_quota(self) -> float:
        return sum(q.heures for q in self.quotas)

    @property
    def total(self) -> float:
        return self.heures_fixes + self.heures_quota


def calculer(dispo: Dispo, du: dt.date, au: dt.date) -> Capacite:
    """Créneaux fixes et quotas (au prorata des jours) de `du` à `au` inclus."""
    du_eff = max(du, dispo.debut)
    creneaux: list[tuple[dt.date, str]] = []
    quotas: list[QuotaPartiel] = []
    if au >= du_eff:
        for d in common.jours_de_a(du_eff, au):
            creneaux.extend((d, c) for c in dispo.creneaux_fixes(d))
        for p in dispo.periodes_du_type("quota"):
            debut, fin = max(p.du, du_eff), min(p.au, au)
            if fin >= debut:
                n = (fin - debut).days + 1
                quotas.append(QuotaPartiel(p, n, (p.heures or 0.0) * n / p.nb_jours))
    return Capacite(du, au, creneaux, quotas)


def capacite_h(dispo: Dispo, du: dt.date, au: dt.date) -> float:
    return calculer(dispo, du, au).total


def charger_jalons(racine: Path) -> list[dict[str, Any]]:
    data = common.charger_yaml(racine / "state" / "jalons.yaml")
    if not isinstance(data, dict) or not isinstance(data.get("jalons"), list):
        raise ErreurDonnees("state/jalons.yaml : clé `jalons` (liste) attendue")
    return data["jalons"]


def prevoir_jalons(dispo: Dispo, jalons: list[dict[str, Any]], ref: dt.date) -> list[dict[str, Any]]:
    """Pour chaque jalon `a_venir` ou `a_risque` : capacité, marge, statut suggéré.

    Les jalons sont triés par date puis identifiant.
    """
    sortie = []
    for j in jalons:
        if not isinstance(j, dict) or j.get("statut") not in ("a_venir", "a_risque"):
            continue
        ident = j.get("id", "?")
        try:
            date_j = common.parse_date(j.get("date"))
        except ErreurFormat as exc:
            raise ErreurDonnees(f"state/jalons.yaml : jalon {ident} : {exc}") from exc
        restantes = j.get("heures_restantes_estimees")
        if isinstance(restantes, bool) or not isinstance(restantes, (int, float)):
            restantes = None
        cap = capacite_h(dispo, ref, date_j)
        marge = None if restantes is None else cap - restantes
        if marge is None:
            suggere = j["statut"]
        elif marge < 0 or marge < 0.1 * cap:
            suggere = "a_risque"
        else:
            suggere = "a_venir"
        sortie.append({
            "id": ident, "nom": j.get("nom", ""), "date": date_j, "type": j.get("type", ""),
            "statut": j["statut"], "capacite": cap, "restantes": restantes,
            "marge": marge, "suggere": suggere, "echu": date_j < ref,
        })
    sortie.sort(key=lambda x: (x["date"], str(x["id"])))
    return sortie


# ---------------------------------------------------------------------------
# Affichage
# ---------------------------------------------------------------------------

def afficher_creneaux(dispo: Dispo, du: dt.date, au: dt.date, titre: str) -> Capacite:
    cap = calculer(dispo, du, au)
    print(titre)
    if au < du:
        print("(plage vide)")
        return cap
    du_eff = max(du, dispo.debut)
    if du_eff > du:
        print(f"Note : aucun créneau avant le début ({dispo.debut.isoformat()}).")
    quotas_annonces: set[int] = set()
    par_jour: dict[dt.date, list[str]] = {}
    for d, c in cap.creneaux:
        par_jour.setdefault(d, []).append(c)
    if au >= du_eff:
        for d in common.jours_de_a(du_eff, au):
            for q in cap.quotas:
                if id(q) not in quotas_annonces and q.periode.contient(d):
                    quotas_annonces.add(id(q))
                    p = q.periode
                    note = f" ({p.note})" if p.note else ""
                    statut = f" [{p.statut}]" if p.statut else ""
                    print(f"QUOTA  {p.du.isoformat()} -> {p.au.isoformat()} : "
                          f"{fmt_h(p.heures or 0)} imposées{note}{statut} ; "
                          f"plage demandée : {q.jours_demandes} j sur {p.nb_jours} = {fmt_h(q.heures)} ; "
                          f"créneaux fixes non générés")
            for c in par_jour.get(d, []):
                print(f"{d.isoformat()}  {common.jour_abrege(d)}  {c}  {fmt_h(common.duree_creneau_h(c))}")
    exceptions = _lignes_exceptions(dispo, du_eff, au)
    if exceptions:
        print("Exceptions appliquées :")
        for ligne in exceptions:
            print(f"  {ligne}")
    detail = f"{len(cap.creneaux)} créneaux fixes"
    if cap.quotas:
        detail += f" + {fmt_h(cap.heures_quota)} de quota"
    print(f"Total : {fmt_h(cap.total)} ({detail})")
    return cap


def _lignes_exceptions(dispo: Dispo, du: dt.date, au: dt.date) -> list[str]:
    lignes = []
    for p in dispo.periodes_du_type("off"):
        if p.au >= du and p.du <= au:
            note = f" : {p.note}" if p.note else ""
            statut = f" [{p.statut}]" if p.statut else ""
            lignes.append(f"off      {p.du.isoformat()} -> {p.au.isoformat()}{note}{statut}")
    for i in sorted(dispo.imprevus, key=lambda x: (x.date, x.creneau)):
        if du <= i.date <= au and i.creneau in dispo.creneaux_theoriques(i.date) \
                and not dispo.off_du_jour(i.date) and not dispo.quota_du_jour(i.date):
            note = f" : {i.note}" if i.note else ""
            lignes.append(f"imprévu  {i.date.isoformat()} {i.creneau}{note} (créneau retiré)")
    return lignes


def cmd_creneaux(racine: Path, args: argparse.Namespace) -> int:
    dispo = Dispo.charger(racine)
    afficher_creneaux(dispo, args.du, args.au,
                      f"Créneaux ML du {args.du.isoformat()} au {args.au.isoformat()}")
    return 0


def cmd_capacite(racine: Path, args: argparse.Namespace) -> int:
    dispo = Dispo.charger(racine)
    cap = calculer(dispo, args.du, args.au)
    print(f"Capacité ML du {args.du.isoformat()} au {args.au.isoformat()} : {fmt_h(cap.total)}")
    print(f"  créneaux fixes : {fmt_h(cap.heures_fixes)} ({len(cap.creneaux)} créneaux)")
    for q in cap.quotas:
        p = q.periode
        print(f"  quota {p.du.isoformat()} -> {p.au.isoformat()} : {fmt_h(q.heures)} "
              f"({q.jours_demandes} j sur {p.nb_jours}, {fmt_h(p.heures or 0)} imposées)")
    return 0


def cmd_semaine(racine: Path, args: argparse.Namespace) -> int:
    dispo = Dispo.charger(racine)
    lundi, dimanche = common.bornes_semaine(args.date)
    print(f"Semaine {common.etiquette_semaine(lundi)} : du {lundi.isoformat()} au {dimanche.isoformat()}")
    cap = afficher_creneaux(dispo, lundi, dimanche, "Créneaux ML :")
    print(f"Capacité ML : {fmt_h(cap.total)} ; tampon : {fmt_h(dispo.tampon_h)} "
          f"(capacité maximale planifiable : {fmt_h(cap.total + dispo.tampon_h)})")
    return 0


def cmd_jalons(racine: Path, args: argparse.Namespace) -> int:
    dispo = Dispo.charger(racine)
    jalons = charger_jalons(racine)
    ref = common.aujourdhui(args.date)
    resultats = prevoir_jalons(dispo, jalons, ref)
    print(f"Jalons au {ref.isoformat()} (capacité de cette date incluse à la date du jalon incluse)")
    if not resultats:
        print("Aucun jalon a_venir ou a_risque.")
    for r in resultats:
        restantes = "inconnu" if r["restantes"] is None else fmt_h(r["restantes"])
        marge = "inconnue" if r["marge"] is None else fmt_h(r["marge"])
        suggere = r["suggere"] if r["suggere"] == r["statut"] else f"{r['suggere']} (changement suggéré)"
        echu = " ; ECHEANCE DEPASSEE" if r["echu"] else ""
        print(f"{r['id']} | {r['date'].isoformat()} | {r['type'] or '?'} | "
              f"capacité {fmt_h(r['capacite'])} | restantes {restantes} | marge {marge} | "
              f"statut {r['statut']} -> suggéré {suggere}{echu}")
    return 0


# ---------------------------------------------------------------------------
# Ligne de commande
# ---------------------------------------------------------------------------

def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cal.py",
        description="Calendrier ML : créneaux, capacité, semaine ISO et prévision des jalons.",
    )
    common.ajouter_option_racine(p)
    sous = p.add_subparsers(dest="commande", required=True, metavar="COMMANDE")

    def plage(sp):
        sp.add_argument("--du", required=True, type=common.date_arg, metavar="AAAA-MM-JJ",
                        help="premier jour (inclus)")
        sp.add_argument("--au", required=True, type=common.date_arg, metavar="AAAA-MM-JJ",
                        help="dernier jour (inclus)")

    sp = sous.add_parser("creneaux", help="liste les créneaux ML datés d'une période")
    plage(sp)
    common.ajouter_option_racine(sp, True)
    sp.set_defaults(fonction=cmd_creneaux)

    sp = sous.add_parser("capacite", help="heures ML disponibles sur une période")
    plage(sp)
    common.ajouter_option_racine(sp, True)
    sp.set_defaults(fonction=cmd_capacite)

    sp = sous.add_parser("semaine", help="squelette de la semaine ISO qui contient la date")
    sp.add_argument("date", type=common.date_arg, metavar="AAAA-MM-JJ")
    common.ajouter_option_racine(sp, True)
    sp.set_defaults(fonction=cmd_semaine)

    sp = sous.add_parser("jalons", help="capacité, marge et statut suggéré de chaque jalon")
    sp.add_argument("--date", type=common.date_arg, metavar="AAAA-MM-JJ",
                    help="date de référence (défaut : aujourd'hui)")
    common.ajouter_option_racine(sp, True)
    sp.set_defaults(fonction=cmd_jalons)
    return p


def main(argv: list[str] | None = None) -> int:
    common.configurer_sortie()
    args = construire_parseur().parse_args(argv)
    try:
        racine = common.racine_depuis_arg(args.racine)
        return args.fonction(racine, args)
    except ErreurDonnees as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
