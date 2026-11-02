"""Construit le paquet Anki « delta » des cartes jamais exportées.

Usage (depuis la racine du repo ; `--racine DOSSIER` pour les tests) :

    python tools/anki.py [--dry-run] [--date AAAA-MM-JJ] [--reexporter ID,ID]
                         [--avancer MODULE:N[,MODULE:N...]] [--sans-paquet]

Circuit à sens unique : les cartes sources sont dans `modules/*/cartes.yaml`.
Le script exporte seulement les cartes absentes de `anki/registre.csv` ET
exportables selon `anki/progression.yaml` (carte sans `seance`, ou module dont la
dernière séance faite est >= `seance` de la carte), plus celles de `--reexporter`
(sur demande explicite), dans le fichier
`anki/paquets/nouvelles-AAAA-MM-JJ.apkg` (non versionné), puis ajoute au
registre une ligne `id;date;paquet` par carte exportée.

Règles figées (voir docs/FORMATS.md) :
  - type de note `ML-Archi (v1)`, identifiant 1730000001, champs Id/Recto/Verso/Source ;
  - un paquet `ML-Archi::<module>` par module, avec un identifiant dérivé d'un hash du nom ;
  - GUID = genanki.guid_for("ml-archi", <id de la carte>) ;
  - étiquettes = tags de la carte + module + compétence (caractères interdits -> `_`).

`--avancer py-numpy:2` fixe progression[py-numpy] = max(valeur actuelle, 2) et écrit
`anki/progression.yaml` AVANT l'export. `--sans-paquet` ne met à jour que la
progression (ni .apkg, ni registre) : pour les sessions cloud. Les deux se combinent.

S'il n'y a rien à exporter, aucun fichier n'est créé. `--dry-run` n'écrit rien du tout (ni progression, ni paquet, ni registre).
Si le fichier du jour existe déjà, le nouveau paquet reçoit le suffixe `-2`, `-3`...
pour ne jamais écraser un paquet pas encore importé.

Codes de sortie : 0 si tout va bien, 2 en cas de fichier manquant ou invalide.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

import genanki

import common
from common import ErreurDonnees

MODEL_ID = 1730000001
MODEL_NAME = "ML-Archi (v1)"
GUID_NAMESPACE = "ml-archi"
FIELDS = ["Id", "Recto", "Verso", "Source"]
QFMT = "{{Recto}}"
AFMT = "{{FrontSide}}<hr id=answer>{{Verso}}<div class=source>{{Source}}</div>"
CSS = """\
.card {
  font-family: Arial, Helvetica, sans-serif;
  font-size: 18px;
  line-height: 1.4;
  text-align: left;
  color: #1a1a1a;
  background-color: #ffffff;
}
pre, code {
  font-family: Consolas, "DejaVu Sans Mono", Menlo, monospace;
  font-size: 0.95em;
}
pre {
  background-color: #f4f4f4;
  padding: 0.5em;
  overflow-x: auto;
}
.source {
  font-size: 12px;
  color: #888888;
  margin-top: 1.2em;
}
"""
DOSSIER_PAQUETS = Path("anki") / "paquets"
REGISTRE = Path("anki") / "registre.csv"


# ---------------------------------------------------------------------------
# Construction du paquet
# ---------------------------------------------------------------------------

def creer_modele() -> genanki.Model:
    """Type de note figé : ne jamais modifier (Anki ignorerait les mises à jour)."""
    return genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[{"name": nom} for nom in FIELDS],
        templates=[{"name": "Carte 1", "qfmt": QFMT, "afmt": AFMT}],
        css=CSS,
        sort_field_index=1,  # tri sur Recto ; le 1er champ (Id) reste celui des doublons
    )


# Paquets rangés par matière puis par chapitre (le module). Les numéros fixent l'ordre
# d'affichage dans Anki, qui trie les paquets par ordre alphabétique.
MATIERES = {
    "diag": "0 Diagnostic",
    "outils": "1 Outils",
    "py": "2 Python scientifique",
    "math": "3 Maths du ML",
    "ml": "4 ML classique",
    "dl": "5 Deep learning",
    "spe": "6 Spécialisation",
    "ing": "7 Ingénierie ML",
    "rech": "8 Recherche",
    "carriere": "9 Carrière",
}


def nom_paquet(module: str) -> str:
    """`ML-Archi::<matière>::<chapitre>`, par exemple `ML-Archi::2 Python scientifique::numpy`."""
    domaine, _, chapitre = module.partition("-")
    matiere = MATIERES.get(domaine, domaine)
    return f"ML-Archi::{matiere}::{chapitre or module}"


def deck_id_pour(nom: str) -> int:
    """Identifiant stable (entre 2^30 et 2^31) dérivé d'un hash SHA-256 du nom."""
    h = int(hashlib.sha256(nom.encode("utf-8")).hexdigest()[:8], 16)
    return (1 << 30) | (h & ((1 << 30) - 1))


def assainir_etiquette(texte: str) -> str:
    """Espaces et caractères interdits -> `_` (lettres, chiffres, `_`, `.`, `-` conservés)."""
    return re.sub(r"[^\w.\-]", "_", str(texte).strip())


def etiquettes(carte: dict[str, Any]) -> list[str]:
    brut = carte.get("tags") or []
    if isinstance(brut, str):
        brut = [brut]
    seance = carte.get("seance")
    candidates = list(brut) + [carte["module"], carte.get("competence"),
                               f"seance-{seance}" if seance else None]
    vus: list[str] = []
    for t in candidates:
        if t is None or not str(t).strip():
            continue
        t = assainir_etiquette(t)
        if t not in vus:
            vus.append(t)
    return vus


def guid_carte(identifiant: str) -> str:
    return genanki.guid_for(GUID_NAMESPACE, identifiant)


def creer_note(modele: genanki.Model, carte: dict[str, Any]) -> genanki.Note:
    return genanki.Note(
        model=modele,
        fields=[carte["id"], carte["recto"], carte["verso"], carte["source"]],
        tags=etiquettes(carte),
        guid=guid_carte(carte["id"]),
    )


def construire_package(cartes: list[dict[str, Any]]) -> genanki.Package:
    """Un paquet `ML-Archi::<module>` par module, dans l'ordre des modules."""
    modele = creer_modele()
    decks: dict[str, genanki.Deck] = {}
    for carte in cartes:
        nom = nom_paquet(carte["module"])
        if nom not in decks:
            decks[nom] = genanki.Deck(deck_id_pour(nom), nom)
        decks[nom].add_note(creer_note(modele, carte))
    return genanki.Package(list(decks.values()))


# ---------------------------------------------------------------------------
# Sélection des cartes
# ---------------------------------------------------------------------------

def valider_cartes(cartes: list[dict[str, Any]]) -> None:
    problemes: list[str] = []
    vus: dict[str, str] = {}
    for c in cartes:
        cid = c["id"]
        if cid in vus:
            problemes.append(f"{cid} : identifiant en double (modules {vus[cid]} et {c['module']})")
        vus[cid] = c["module"]
        for cle in ("recto", "verso", "source"):
            if not isinstance(c.get(cle), str) or not c[cle].strip():
                problemes.append(f"{cid} : champ `{cle}` manquant ou vide "
                                 f"(modules/{c['module']}/cartes.yaml)")
        sn = c.get("seance")
        if sn is not None and (isinstance(sn, bool) or not isinstance(sn, int) or sn < 1):
            problemes.append(f"{cid} : `seance` = {sn!r} invalide (entier >= 1 ou null)")
    if problemes:
        raise ErreurDonnees("cartes invalides :\n  " + "\n  ".join(problemes))


def selectionner(cartes: list[dict[str, Any]], exportees: set[str], reexporter: list[str],
                 progression: dict[str, int]) -> list[dict[str, Any]]:
    connues = {c["id"] for c in cartes}
    inconnues = [i for i in reexporter if i not in connues]
    if inconnues:
        raise ErreurDonnees(f"--reexporter : carte(s) inconnue(s) : {', '.join(inconnues)}")
    demandees = set(reexporter)
    return [c for c in cartes
            if c["id"] in demandees
            or (c["id"] not in exportees and common.carte_exportable(c, progression))]


def appliquer_avancer(racine: Path, avancer: dict[str, int],
                      progression: dict[str, int]) -> dict[str, int]:
    """progression[module] = max(valeur actuelle, N). Vérifie que les modules existent."""
    nouvelle = dict(progression)
    for module, n in avancer.items():
        if not (racine / "modules" / module).is_dir():
            raise ErreurDonnees(f"--avancer : module inconnu `{module}` (dossier modules/{module}/ absent)")
        nouvelle[module] = max(nouvelle.get(module, 0), n)
    return nouvelle


def resume_progression(avant: dict[str, int], apres: dict[str, int]) -> list[str]:
    return [f"  {m} : {avant.get(m, 0)} -> {apres[m]}" for m in sorted(apres)
            if apres[m] != avant.get(m)]


def nom_fichier_libre(dossier: Path, date: dt.date) -> str:
    base = f"nouvelles-{date.isoformat()}"
    nom, n = f"{base}.apkg", 1
    while (dossier / nom).exists():
        n += 1
        nom = f"{base}-{n}.apkg"
    return nom


def ajouter_au_registre(chemin: Path, ids: list[str], date: dt.date, paquet: str) -> None:
    lignes = "".join(f"{i};{date.isoformat()};{paquet}\n" for i in ids)
    if not chemin.exists():
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text("id;date;paquet\n" + lignes, encoding="utf-8", newline="\n")
        return
    existant = chemin.read_bytes()
    prefixe = "" if (not existant or existant.endswith(b"\n")) else "\n"
    with chemin.open("a", encoding="utf-8", newline="\n") as f:
        f.write(prefixe + lignes)


def timestamp_du(date: dt.date) -> float:
    """Horodatage fixe (midi UTC) : même date -> même contenu de base."""
    return dt.datetime(date.year, date.month, date.day, 12, tzinfo=dt.timezone.utc).timestamp()


# ---------------------------------------------------------------------------
# Commande
# ---------------------------------------------------------------------------

def exporter(racine: Path, date: dt.date, dry_run: bool, reexporter: list[str],
             avancer: dict[str, int] | None = None, sans_paquet: bool = False) -> int:
    avancer = avancer or {}
    prefixe = "[dry-run] " if dry_run else ""
    if sans_paquet and reexporter:
        raise ErreurDonnees("--reexporter est incompatible avec --sans-paquet")
    if not (racine / "modules").is_dir():
        raise ErreurDonnees("dossier manquant : modules/")

    # 1. progression (écrite avant l'export)
    avant = common.charger_progression(racine)
    progression = appliquer_avancer(racine, avancer, avant)
    changements = resume_progression(avant, progression)
    if avancer:
        if changements:
            print(f"{prefixe}Progression mise à jour ({common.PROGRESSION.as_posix()}) :")
            print("\n".join(changements))
        else:
            print(f"{prefixe}Progression inchangée (valeurs déjà atteintes).")
        if changements and not dry_run:
            common.ecrire_progression(racine, progression)
    if sans_paquet:
        if not avancer:
            print("--sans-paquet sans --avancer : rien à faire.")
        else:
            print(f"{prefixe}--sans-paquet : aucun paquet, registre inchangé.")
        return 0

    # 2. sélection des cartes
    cartes = common.charger_cartes(racine)
    valider_cartes(cartes)
    registre = common.charger_csv_registre(racine / REGISTRE)
    exportees = {ligne["id"] for ligne in registre}
    selection = selectionner(cartes, exportees, reexporter, progression)
    retenues = sum(1 for c in cartes if c["id"] not in exportees
                   and not common.carte_exportable(c, progression))

    if not selection:
        print("Aucune carte en attente d'export : aucun paquet créé, registre inchangé.")
        if retenues:
            print(f"({retenues} carte(s) non exportable(s) : séance pas encore faite selon la progression.)")
        return 0

    par_module: dict[str, int] = {}
    for c in selection:
        par_module[c["module"]] = par_module.get(c["module"], 0) + 1
    relues = [c["id"] for c in selection if c["id"] in exportees]
    dossier = racine / DOSSIER_PAQUETS
    nom = nom_fichier_libre(dossier, date)
    chemin_rel = (DOSSIER_PAQUETS / nom).as_posix()

    reexp = f", dont {len(relues)} réexportée(s)" if relues else ""
    print(f"{prefixe}Paquet delta : {len(selection)} carte(s) en {len(par_module)} paquet(s){reexp}")
    for module, n in par_module.items():
        print(f"  {nom_paquet(module)} : {n}")
    if retenues:
        print(f"({retenues} carte(s) retenue(s) : séance pas encore faite selon la progression.)")
    if dry_run:
        print(f"[dry-run] Paquet qui serait écrit : {chemin_rel}")
        print(f"[dry-run] Lignes qui seraient ajoutées à {REGISTRE.as_posix()} : {len(selection)}")
        print("[dry-run] Rien n'a été écrit.")
        return 0

    dossier.mkdir(parents=True, exist_ok=True)
    construire_package(selection).write_to_file(str(dossier / nom), timestamp=timestamp_du(date))
    ajouter_au_registre(racine / REGISTRE, [c["id"] for c in selection], date, nom)
    print(f"Paquet écrit : {chemin_rel}")
    print(f"Registre mis à jour : +{len(selection)} ligne(s) dans {REGISTRE.as_posix()}")
    return 0


def liste_ids(texte: str) -> list[str]:
    return [t.strip() for t in texte.split(",") if t.strip()]


def liste_avancer(texte: str) -> dict[str, int]:
    resultat: dict[str, int] = {}
    for morceau in liste_ids(texte):
        module, sep, n = morceau.partition(":")
        if not sep or not module.strip() or not n.strip().isdigit():
            raise argparse.ArgumentTypeError(
                f"{morceau!r} invalide (attendu MODULE:N avec N entier >= 0, ex. py-numpy:2)")
        resultat[module.strip()] = max(resultat.get(module.strip(), 0), int(n))
    return resultat


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="anki.py",
        description="Construit le paquet Anki delta (cartes absentes de anki/registre.csv) "
                    "et complète le registre.",
    )
    p.add_argument("--dry-run", action="store_true",
                   help="affiche ce qui serait exporté, sans rien écrire")
    p.add_argument("--date", type=common.date_arg, metavar="AAAA-MM-JJ",
                   help="date à utiliser à la place d'aujourd'hui (nom du paquet, registre)")
    p.add_argument("--reexporter", type=liste_ids, default=[], metavar="ID,ID",
                   help="identifiants de cartes à réexporter même si elles sont au registre")
    p.add_argument("--avancer", type=liste_avancer, default={}, metavar="MODULE:N[,MODULE:N...]",
                   help="fixe la progression du module à max(valeur actuelle, N) dans "
                        "anki/progression.yaml, avant l'export")
    p.add_argument("--sans-paquet", action="store_true",
                   help="met seulement la progression à jour : ni .apkg, ni registre "
                        "(sessions cloud)")
    common.ajouter_option_racine(p)
    return p


def main(argv: list[str] | None = None) -> int:
    common.configurer_sortie()
    args = construire_parseur().parse_args(argv)
    try:
        racine = common.racine_depuis_arg(args.racine)
        return exporter(racine, common.aujourdhui(args.date), args.dry_run, args.reexporter,
                        args.avancer, args.sans_paquet)
    except ErreurDonnees as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
