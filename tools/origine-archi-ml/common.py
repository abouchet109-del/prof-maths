"""Fonctions communes aux scripts de `tools/` (cal, check, now, anki).

Ce module ne se lance pas directement. Il fournit :
  - la résolution de la racine du repo (option `--racine`) ;
  - le chargement YAML / CSV en UTF-8, avec des erreurs claires ;
  - l'analyse des dates, des jours (`lun`..`dim`), des créneaux `"HH:MM-HH:MM"`
    (`24:00` accepté comme fin) et des semaines ISO (`AAAA-Www`).

Tout est portable (Windows et Linux) : `pathlib`, UTF-8 explicite, aucune
commande shell.
"""
from __future__ import annotations

import csv
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any

import yaml

JOURS = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
JOURS_LONGS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
DOMAINES = ["outils", "py", "math", "ml", "dl", "spe", "ing", "rech", "carriere"]

RE_ID = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")
RE_CRENEAU = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")
RE_SEMAINE = re.compile(r"^(\d{4})-W(\d{2})$")


class ErreurDonnees(Exception):
    """Fichier manquant, illisible ou mal formé (message destiné à l'utilisateur)."""


class ErreurFormat(ValueError):
    """Valeur mal formée (date, créneau, jour...)."""


# ---------------------------------------------------------------------------
# Console et racine
# ---------------------------------------------------------------------------

def configurer_sortie() -> None:
    """Force l'UTF-8 sur stdout/stderr (console Windows en cp1252 par défaut)."""
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def racine_depuis_arg(valeur: str | None) -> Path:
    """Racine du repo : `--racine` si fourni, sinon le dossier courant."""
    racine = Path(valeur).expanduser() if valeur else Path.cwd()
    racine = racine.resolve()
    if not racine.is_dir():
        raise ErreurDonnees(f"racine introuvable : {racine}")
    return racine


def chemin_relatif(racine: Path, chemin: Path) -> str:
    """Chemin relatif à la racine, avec des `/` (affichage identique partout)."""
    try:
        return chemin.resolve().relative_to(racine.resolve()).as_posix()
    except ValueError:
        return chemin.as_posix()


# ---------------------------------------------------------------------------
# Chargement des fichiers
# ---------------------------------------------------------------------------

def lire_texte(chemin: Path) -> str:
    if not chemin.is_file():
        raise ErreurDonnees(f"fichier manquant : {chemin.as_posix()}")
    try:
        return chemin.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ErreurDonnees(f"{chemin.as_posix()} : encodage UTF-8 invalide ({exc})") from exc


def charger_yaml(chemin: Path) -> Any:
    """Charge un fichier YAML (UTF-8). Lève ErreurDonnees si absent ou invalide."""
    texte = lire_texte(chemin)
    try:
        return yaml.safe_load(texte)
    except yaml.YAMLError as exc:
        marque = getattr(exc, "problem_mark", None)
        lieu = f" (ligne {marque.line + 1}, colonne {marque.column + 1})" if marque else ""
        probleme = getattr(exc, "problem", None) or str(exc)
        if "escape" in probleme:
            probleme += (" -- une chaîne entre guillemets doubles contient un antislash (MathJax ?) : "
                         "l'écrire entre apostrophes simples ou dans un bloc `|`")
        raise ErreurDonnees(f"{chemin.as_posix()} : YAML invalide{lieu} : {probleme}") from exc


def charger_csv_registre(chemin: Path) -> list[dict[str, str]]:
    """Lit `anki/registre.csv` (séparateur `;`, en-tête `id;date;paquet`).

    Un fichier absent donne un registre vide (premier export).
    """
    if not chemin.exists():
        return []
    texte = lire_texte(chemin)
    lecteur = csv.DictReader(texte.splitlines(), delimiter=";")
    champs = lecteur.fieldnames or []
    if [c.strip() for c in champs] != ["id", "date", "paquet"]:
        raise ErreurDonnees(
            f"{chemin.as_posix()} : en-tête attendu `id;date;paquet`, trouvé `{';'.join(champs)}`"
        )
    lignes = []
    for ligne in lecteur:
        if not any((v or "").strip() for v in ligne.values()):
            continue
        lignes.append({k.strip(): (v or "").strip() for k, v in ligne.items() if k})
    return lignes


def dossiers_modules(racine: Path) -> list[Path]:
    """Sous-dossiers de `modules/`, triés par nom (liste vide si `modules/` est absent)."""
    base = racine / "modules"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir()
                  if p.is_dir() and not p.name.startswith((".", "_")))


def charger_cartes(racine: Path) -> list[dict[str, Any]]:
    """Cartes de `modules/*/cartes.yaml`, dans l'ordre (modules triés, ordre du fichier).

    Chaque carte reçoit la clé `module` (nom du dossier). Un fichier absent est ignoré ;
    un fichier mal formé lève ErreurDonnees.
    """
    cartes: list[dict[str, Any]] = []
    for dossier in dossiers_modules(racine):
        chemin = dossier / "cartes.yaml"
        if not chemin.is_file():
            continue
        rel = chemin_relatif(racine, chemin)
        data = charger_yaml(chemin)
        if data is None:
            continue
        if not isinstance(data, list):
            raise ErreurDonnees(f"{rel} : une liste YAML de cartes est attendue")
        for i, carte in enumerate(data, start=1):
            if not isinstance(carte, dict) or not isinstance(carte.get("id"), str) or not carte["id"].strip():
                raise ErreurDonnees(f"{rel} : carte n°{i} sans identifiant `id`")
            cartes.append({**carte, "module": dossier.name})
    return cartes


PROGRESSION = Path("anki") / "progression.yaml"


def valider_progression(data: Any) -> dict[str, int]:
    """Contrôle le contenu de `anki/progression.yaml` (module -> dernière séance faite)."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ErreurDonnees("anki/progression.yaml : un dictionnaire `module: séance` est attendu")
    for module, n in data.items():
        if not isinstance(module, str) or isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ErreurDonnees(
                f"anki/progression.yaml : `{module}: {n}` invalide (entier >= 0 attendu)")
    return dict(data)


def charger_progression(racine: Path) -> dict[str, int]:
    """Dernière séance faite par module ; un fichier absent équivaut à `{}`."""
    chemin = racine / PROGRESSION
    if not chemin.exists():
        return {}
    return valider_progression(charger_yaml(chemin))


def ecrire_progression(racine: Path, progression: dict[str, int]) -> None:
    chemin = racine / PROGRESSION
    chemin.parent.mkdir(parents=True, exist_ok=True)
    corps = yaml.safe_dump(dict(sorted(progression.items())), allow_unicode=True,
                           default_flow_style=False) if progression else "{}\n"
    chemin.write_text("# Dernière séance faite par module (écrit par tools/anki.py --avancer)\n" + corps,
                      encoding="utf-8", newline="\n")


def carte_exportable(carte: dict[str, Any], progression: dict[str, int]) -> bool:
    """Une carte sans `seance` est toujours exportable ; sinon, seulement si la séance est faite."""
    seance = carte.get("seance")
    if seance is None:
        return True
    if isinstance(seance, bool) or not isinstance(seance, int):
        return False
    return carte["module"] in progression and seance <= progression[carte["module"]]


# ---------------------------------------------------------------------------
# Dates, jours, semaines
# ---------------------------------------------------------------------------

def parse_date(valeur: Any) -> dt.date:
    """Accepte un objet date (YAML) ou une chaîne `AAAA-MM-JJ`."""
    if isinstance(valeur, dt.datetime):
        return valeur.date()
    if isinstance(valeur, dt.date):
        return valeur
    if isinstance(valeur, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", valeur.strip()):
        try:
            return dt.date.fromisoformat(valeur.strip())
        except ValueError:
            pass
    raise ErreurFormat(f"date invalide : {valeur!r} (attendu AAAA-MM-JJ)")


def date_arg(texte: str) -> dt.date:
    """Type argparse pour `--date`, `--du`, `--au`."""
    try:
        return parse_date(texte)
    except ErreurFormat as exc:
        import argparse
        raise argparse.ArgumentTypeError(str(exc)) from exc


def ajouter_option_racine(parser, sous_commande: bool = False) -> None:
    """Ajoute `--racine`. Sur une sous-commande, ne remplace pas la valeur du parseur principal."""
    import argparse
    parser.add_argument(
        "--racine",
        metavar="DOSSIER",
        default=argparse.SUPPRESS if sous_commande else None,
        help="racine du repo (défaut : dossier courant)",
    )


def aujourdhui(date_arg_valeur: dt.date | None) -> dt.date:
    return date_arg_valeur if date_arg_valeur is not None else dt.date.today()


def jour_abrege(d: dt.date) -> str:
    """`lun`..`dim`."""
    return JOURS[d.weekday()]


def jour_long(d: dt.date) -> str:
    return JOURS_LONGS[d.weekday()]


def parse_jour(valeur: Any) -> str:
    """Normalise un nom de jour (`lun`, `lundi`...) en forme abrégée."""
    if isinstance(valeur, str):
        v = valeur.strip().lower()
        if v in JOURS:
            return v
        if v in JOURS_LONGS:
            return JOURS[JOURS_LONGS.index(v)]
    raise ErreurFormat(f"jour invalide : {valeur!r} (attendu {' '.join(JOURS)})")


def jours_de_a(du: dt.date, au: dt.date):
    """Itère sur les dates de `du` à `au` inclus."""
    d = du
    while d <= au:
        yield d
        d += dt.timedelta(days=1)


def etiquette_semaine(d: dt.date) -> str:
    """Semaine ISO de `d`, au format `AAAA-Www`."""
    annee, semaine, _ = d.isocalendar()
    return f"{annee}-W{semaine:02d}"


def bornes_semaine(d: dt.date) -> tuple[dt.date, dt.date]:
    """(lundi, dimanche) de la semaine ISO qui contient `d`."""
    lundi = d - dt.timedelta(days=d.weekday())
    return lundi, lundi + dt.timedelta(days=6)


def parse_semaine(texte: str) -> tuple[dt.date, dt.date]:
    """`AAAA-Www` -> (lundi, dimanche)."""
    m = RE_SEMAINE.match(texte.strip()) if isinstance(texte, str) else None
    if not m:
        raise ErreurFormat(f"semaine invalide : {texte!r} (attendu AAAA-Www)")
    try:
        lundi = dt.date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
    except ValueError as exc:
        raise ErreurFormat(f"semaine invalide : {texte!r}") from exc
    return lundi, lundi + dt.timedelta(days=6)


# ---------------------------------------------------------------------------
# Créneaux
# ---------------------------------------------------------------------------

def parse_creneau(texte: Any) -> tuple[int, int]:
    """`"HH:MM-HH:MM"` -> (début, fin) en minutes depuis minuit.

    `24:00` est accepté comme fin (et seulement comme fin). Exige début < fin.
    """
    if not isinstance(texte, str):
        raise ErreurFormat(f"créneau invalide : {texte!r} (attendu \"HH:MM-HH:MM\")")
    m = RE_CRENEAU.match(texte.strip())
    if not m:
        raise ErreurFormat(f"créneau invalide : {texte!r} (attendu \"HH:MM-HH:MM\")")
    h1, m1, h2, m2 = (int(x) for x in m.groups())
    if m1 > 59 or m2 > 59:
        raise ErreurFormat(f"créneau invalide : {texte!r} (minutes > 59)")
    if h1 > 23:
        raise ErreurFormat(f"créneau invalide : {texte!r} (heure de début > 23)")
    if h2 > 24 or (h2 == 24 and m2 != 0):
        raise ErreurFormat(f"créneau invalide : {texte!r} (heure de fin > 24:00)")
    debut, fin = h1 * 60 + m1, h2 * 60 + m2
    if debut >= fin:
        raise ErreurFormat(f"créneau invalide : {texte!r} (le début doit précéder la fin)")
    return debut, fin


def formater_creneau(debut: int, fin: int) -> str:
    return f"{debut // 60:02d}:{debut % 60:02d}-{fin // 60:02d}:{fin % 60:02d}"


def normaliser_creneau(texte: Any) -> str:
    """Forme canonique `HH:MM-HH:MM` (pour comparer deux créneaux)."""
    return formater_creneau(*parse_creneau(texte))


def duree_creneau_h(texte: Any) -> float:
    debut, fin = parse_creneau(texte)
    return (fin - debut) / 60


def creneau_contenu(interne: tuple[int, int], externe: tuple[int, int]) -> bool:
    return externe[0] <= interne[0] and interne[1] <= externe[1]


def creneaux_chevauchants(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def type_exception(valeur: Any) -> Any:
    """Normalise le type d'une exception de `dispo.yaml`.

    PyYAML suit YAML 1.1 : `type: off` (sans guillemets) est lu comme le
    booléen `False`. On le ramène à la chaîne `"off"`.
    """
    if valeur is False:
        return "off"
    return valeur


# ---------------------------------------------------------------------------
# Affichage
# ---------------------------------------------------------------------------

def fmt_h(heures: float) -> str:
    """Heures au format français : `2`, `1,5`, `3,33` (max 2 décimales)."""
    arrondi = round(float(heures) + 0.0, 2)
    if arrondi == 0:
        arrondi = 0.0
    texte = f"{arrondi:.2f}".rstrip("0").rstrip(".")
    return texte.replace(".", ",") + " h"
