"""Inventorie des PDF : empreinte, pages, densité de texte, début du texte.

Usage : python -I tools/inventaire.py DOSSIER_SOURCE SORTIE.json [--depuis AAAA-MM-JJ]

Ne lit que le dossier source, sans le modifier. Les doublons exacts partagent
la même empreinte SHA-256. Une densité faible signale un scan ou du manuscrit.
"""
import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from pypdf import PdfReader

EXCLUS = ("price_discrimination", "Monopoly", "Lecture1_Intro", "idterm")


def decrire(chemin: Path) -> dict:
    infos = {
        "fichier": chemin.name,
        "ko": round(chemin.stat().st_size / 1024),
        "sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
    }
    try:
        lecteur = PdfReader(str(chemin))
        textes = [(p.extract_text() or "") for p in lecteur.pages]
        total = sum(len(t) for t in textes)
        infos.update(
            pages=len(textes),
            car_par_page=round(total / max(len(textes), 1)),
            debut=" ".join(" ".join(textes[:2]).split())[:220],
        )
    except Exception as exc:  # un PDF illisible ne doit pas arrêter l'inventaire
        infos.update(pages=None, car_par_page=0, debut=f"ERREUR : {exc}")
    return infos


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("sortie", type=Path)
    p.add_argument("--depuis", type=dt.date.fromisoformat, required=True)
    args = p.parse_args()

    resultats = []
    for chemin in sorted(args.source.glob("*.pdf")):
        date = dt.date.fromtimestamp(chemin.stat().st_mtime)
        if date >= args.depuis and not any(x in chemin.name for x in EXCLUS):
            resultats.append(decrire(chemin))

    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    args.sortie.write_text(json.dumps(resultats, ensure_ascii=False, indent=1), encoding="utf-8")
    vus = set()
    for r in resultats:
        double = "=" if r["sha256"] in vus else " "
        vus.add(r["sha256"])
        print(f"{double} {r['pages']}p {r['car_par_page']}c/p | {r['fichier']} | {r['debut'][:130]}")
    print(f"{len(resultats)} fichiers, {len(vus)} uniques, "
          f"{sum(r['pages'] or 0 for r in resultats)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
