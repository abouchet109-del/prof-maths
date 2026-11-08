"""Construit le paquet Anki des cartes jamais exportées (inspiré de l'archi ML, adapté ici).

Usage (depuis la racine du projet) :
    python -I tools/anki.py [--dry-run] [--priorite-max N] [--reexporter ID,ID]

Circuit à sens unique : les cartes sources sont dans `matieres/*/cartes.yaml`. Seules celles
absentes de `anki/registre.csv` sont exportées, dans `anki/paquets/prof-maths-AAAA-MM-JJ.apkg`
(non versionné). Le registre est ensuite complété. Une carte déjà importée n'est jamais
réécrasée : Anki est maître des cartes importées.

Règles figées (ne jamais les modifier, sinon Anki ignore les mises à jour) :
  - type de note `Prof-maths (v1)`, identifiant 1830000001, champs Id/Recto/Verso/Source ;
    distinct de celui de l'archi ML (1730000001) ;
  - GUID = genanki.guid_for("prof-maths", <id de la carte>) ;
  - paquet `tg::Maths::L3 Paris Cité::<Matière>::<chapitre>`, identifiant dérivé d'un hash du nom ;
    les cartes d'exercices (tag `exercice`) vont dans le sous-paquet `...::<chapitre>::Exercices` ;
  - étiquettes : prof-maths, matière, priorite-N, puis les tags de la carte.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

import genanki
import yaml

RACINE = Path(__file__).resolve().parents[1]
MODEL_ID = 1830000001
MODEL_NAME = "Prof-maths (v1)"
GUID_NAMESPACE = "prof-maths"
FIELDS = ["Id", "Recto", "Verso", "Source"]
QFMT = "{{Recto}}"
AFMT = "{{FrontSide}}<hr id=answer>{{Verso}}<div class=source>{{Source}}</div>"
CSS = """\
.card { font-family: Arial, Helvetica, sans-serif; font-size: 20px; line-height: 1.45;
        text-align: left; color: #1a1a1a; background-color: #ffffff; }
.source { font-size: 12px; color: #888888; margin-top: 1.2em; }
"""
MATIERES = {"topologie": "Topologie", "mesure": "Mesure et intégration",
            "modelisation": "Modélisation", "proba": "Probabilités 5"}
REGISTRE = RACINE / "anki" / "registre.csv"
PAQUETS = RACINE / "anki" / "paquets"


def modele() -> genanki.Model:
    return genanki.Model(MODEL_ID, MODEL_NAME, fields=[{"name": n} for n in FIELDS],
                         templates=[{"name": "Carte 1", "qfmt": QFMT, "afmt": AFMT}],
                         css=CSS, sort_field_index=1)


def nom_paquet(matiere: str, chapitre: str, exercice: bool = False) -> str:
    chapitre = re.sub(r"[:$]", "", chapitre or "Divers").strip()
    nom = f"tg::Maths::L3 Paris Cité::{MATIERES[matiere]}::{chapitre}"
    return nom + "::Exercices" if exercice else nom


def deck_id(nom: str) -> int:
    h = int(hashlib.sha256(nom.encode("utf-8")).hexdigest()[:8], 16)
    return (1 << 30) | (h & ((1 << 30) - 1))


BALISE = re.compile(r"<(?!/?(?:br|b|i|u|em|strong|code|pre|sup|sub|div|span|ul|ol|li|p|hr)\b)", re.I)


def html(texte: str) -> str:
    """Un « < » mathématique (u_n<1) serait lu comme une balise et masquerait la suite."""
    return BALISE.sub("&lt;", texte)


def etiquette(texte: str) -> str:
    return re.sub(r"[^\w.\-]", "_", str(texte).strip())


def charger() -> list[dict]:
    cartes, vus = [], set()
    for m in MATIERES:
        chemin = RACINE / "matieres" / m / "cartes.yaml"
        if not chemin.exists():
            continue
        for c in yaml.safe_load(chemin.read_text(encoding="utf-8")) or []:
            for cle in ("id", "recto", "verso", "source"):
                if not str(c.get(cle) or "").strip():
                    raise SystemExit(f"{m} : carte {c.get('id')} sans `{cle}`")
            if c["id"] in vus:
                raise SystemExit(f"identifiant en double : {c['id']}")
            vus.add(c["id"])
            cartes.append({**c, "matiere": m})
    return cartes


def exportees() -> set[str]:
    if not REGISTRE.exists():
        return set()
    lignes = REGISTRE.read_text(encoding="utf-8").splitlines()[1:]
    return {l.split(";")[0] for l in lignes if l.strip()}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--priorite-max", type=int, default=3)
    p.add_argument("--reexporter", default="")
    a = p.parse_args()

    deja = exportees()
    redemandees = {i for i in a.reexporter.split(",") if i}
    selection = [c for c in charger()
                 if (c["id"] not in deja and int(c.get("priorite") or 3) <= a.priorite_max)
                 or c["id"] in redemandees]
    if not selection:
        print("Aucune carte à exporter.")
        return 0

    decks: dict[str, genanki.Deck] = {}
    m = modele()
    for c in selection:
        nom = nom_paquet(c["matiere"], c.get("chapitre"), "exercice" in (c.get("tags") or []))
        decks.setdefault(nom, genanki.Deck(deck_id(nom), nom))
        tags = ["prof-maths", c["matiere"], f"priorite-{c.get('priorite') or 3}",
                *[etiquette(t) for t in c.get("tags") or []]]
        decks[nom].add_note(genanki.Note(model=m, fields=[c["id"], html(c["recto"]), html(c["verso"]), html(c["source"])],
                                         tags=tags, guid=genanki.guid_for(GUID_NAMESPACE, c["id"])))
    for nom, d in sorted(decks.items()):
        print(f"  {len(d.notes):4} {nom}")
    print(f"{len(selection)} cartes dans {len(decks)} sous-paquets")
    if a.dry_run:
        print("[dry-run] rien n'a été écrit")
        return 0

    jour = dt.date.today().isoformat()
    PAQUETS.mkdir(parents=True, exist_ok=True)
    nom, n = f"prof-maths-{jour}.apkg", 1
    while (PAQUETS / nom).exists():
        n += 1
        nom = f"prof-maths-{jour}-{n}.apkg"
    genanki.Package(list(decks.values())).write_to_file(str(PAQUETS / nom))
    neuf = not REGISTRE.exists()
    with REGISTRE.open("a", encoding="utf-8", newline="\n") as f:
        if neuf:
            f.write("id;date;paquet\n")
        f.writelines(f"{c['id']};{jour};{nom}\n" for c in selection)
    print(f"Paquet écrit : {(PAQUETS / nom).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
