"""Lit un paquet .apkg sans le modifier et en exporte la structure.

Usage : python -I tools/lire_anki.py PAQUET.apkg

Écrit dans inventaire/anki/ :
  - decks.csv : paquet, nombre de cartes et de notes, cartes déjà révisées ;
  - notes.jsonl : une note par ligne (paquet, modèle, champs en texte, tags, médias cités).
Seule la base est extraite : les médias restent dans l'archive.
"""
import csv
import json
import re
import sqlite3
import sys
import zipfile
from collections import Counter
from pathlib import Path

import zstandard

RACINE = Path(__file__).resolve().parents[1]
TRAVAIL = RACINE / "anki" / "export"
RE_MEDIA = re.compile(r'<img[^>]+src="([^"]+)"|\[sound:([^\]]+)\]')
RE_BALISE = re.compile(r"<[^>]+>")


def extraire_base(paquet: Path) -> tuple[Path, list[str], int]:
    TRAVAIL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(paquet) as z:
        noms = z.namelist()
        n_media = sum(1 for n in noms if n.isdigit())
        for nom in ("collection.anki21b", "collection.anki21", "collection.anki2"):
            if nom in noms:
                cible = TRAVAIL / "collection.sqlite"
                brut = z.read(nom)
                if nom.endswith("b"):
                    brut = zstandard.ZstdDecompressor().stream_reader(brut).read()
                cible.write_bytes(brut)
                return cible, [nom], n_media
    raise SystemExit("Aucune base trouvée dans le paquet")


def charger_decks_modeles(con: sqlite3.Connection) -> tuple[dict, dict]:
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    if "decks" in tables and "notetypes" in tables:
        decks = {i: n.replace("\x1f", "::") for i, n in con.execute("select id, name from decks")}
        modeles = dict(con.execute("select id, name from notetypes"))
    else:
        d, m = con.execute("select decks, models from col").fetchone()
        decks = {int(k): v["name"] for k, v in json.loads(d).items()}
        modeles = {int(k): v["name"] for k, v in json.loads(m).items()}
    return decks, modeles


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    paquet = Path(sys.argv[1])
    base, source, n_media = extraire_base(paquet)
    con = sqlite3.connect(f"file:{base.as_posix()}?mode=ro", uri=True)
    con.create_collation("unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
    decks, modeles = charger_decks_modeles(con)

    cartes = Counter()
    revisees = Counter()
    deck_note = {}
    for nid, did, reps in con.execute("select nid, did, reps from cards"):
        nom = decks.get(did, f"?{did}")
        cartes[nom] += 1
        revisees[nom] += reps > 0
        deck_note.setdefault(nid, nom)

    sortie = RACINE / "inventaire" / "anki"
    sortie.mkdir(parents=True, exist_ok=True)
    notes_par_deck = Counter()
    avec_image = 0
    with (sortie / "notes.jsonl").open("w", encoding="utf-8") as f:
        for nid, mid, tags, flds in con.execute("select id, mid, tags, flds from notes"):
            nom = deck_note.get(nid, "?")
            notes_par_deck[nom] += 1
            medias = [a or b for a, b in RE_MEDIA.findall(flds)]
            avec_image += bool(medias)
            champs = [" ".join(RE_BALISE.sub(" ", c).split()) for c in flds.split("\x1f")]
            f.write(json.dumps({"id": nid, "deck": nom, "modele": modeles.get(mid, str(mid)),
                                "tags": tags.split(), "champs": champs, "medias": medias},
                               ensure_ascii=False) + "\n")

    with (sortie / "decks.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["deck", "cartes", "notes", "cartes_revisees"])
        for nom in sorted(cartes):
            w.writerow([nom, cartes[nom], notes_par_deck[nom], revisees[nom]])

    n_rev = con.execute("select count(*) from revlog").fetchone()[0]
    print(f"Base : {source} ; médias : {n_media}")
    print(f"Paquets : {len(cartes)} ; cartes : {sum(cartes.values())} ; "
          f"notes : {sum(notes_par_deck.values())} ; notes avec média : {avec_image}")
    print(f"Lignes d'historique : {n_rev} ; cartes déjà révisées : {sum(revisees.values())}")
    print("Modèles :", dict(Counter(modeles.get(m, str(m)) for (m,) in con.execute("select mid from notes")).most_common(8)))

    arbre = Counter()
    for nom, n in cartes.items():
        parties = nom.split("::")
        for prof in range(1, min(len(parties), 3) + 1):
            arbre["::".join(parties[:prof])] += n
    print("\nArbre (3 niveaux) :")
    for nom in sorted(arbre)[:90]:
        print(f"{'  ' * nom.count('::')}{nom.split('::')[-1]} : {arbre[nom]}")
    if len(arbre) > 90:
        print(f"... +{len(arbre) - 90} branches (voir decks.csv)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
