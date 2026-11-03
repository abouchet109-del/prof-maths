"""Contrôle un exercices.yaml : comptes, annales de Paris Cité, échantillon et rendu de pages.

Usage : python -I tools/controle_exercices.py MATIERE [--echantillon N] [--images DOSSIER]
"""
import argparse
import random
import sys
from collections import Counter
from pathlib import Path

import fitz
import yaml

RACINE = Path(__file__).resolve().parents[1]


def est_annale_pc(ex: dict) -> bool:
    return any(s.get("etab") == "paris-cite" and "/annales/" in str(s.get("fichier"))
               for s in ex.get("sources") or [])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("matiere")
    p.add_argument("--echantillon", type=int, default=0)
    p.add_argument("--images", type=Path)
    a = p.parse_args()
    data = yaml.safe_load((RACINE / "matieres" / a.matiere / "exercices.yaml").read_text(encoding="utf-8"))
    print(f"{len(data)} entrées ; id uniques : {len({e['id'] for e in data}) == len(data)}")
    print("type_source :", dict(Counter(e.get("type_source") for e in data)))
    print("corrigé :", dict(Counter(e["corrige"]["statut"] for e in data)))
    print("qualité :", dict(Counter(e.get("qualite_extraction") for e in data)))
    print("champ annale_prioritaire présent :", sum("annale_prioritaire" in e for e in data))
    pc = [e for e in data if est_annale_pc(e)]
    print(f"annales Paris Cité : {len(pc)} entrées")
    print("  par fichier :", dict(Counter(s["fichier"].split("/")[-1] for e in pc for s in e["sources"]
                                          if s.get("etab") == "paris-cite" and "/annales/" in s["fichier"])))
    print("statut du tableur repris sur des entrées :", sum(bool(e.get("indice_tableur")) for e in data))

    random.seed(7)
    lot = random.sample(pc, min(a.echantillon, len(pc)))
    for e in lot:
        s = next(x for x in e["sources"] if "/annales/" in x["fichier"])
        print(f"\n--- {e['id']} | {s['fichier']} p.{s['page']} {s['numero']} | corrigé {e['corrige']['statut']}")
        print(e["enonce"].strip()[:700])
        if a.images:
            a.images.mkdir(parents=True, exist_ok=True)
            doc = fitz.open(RACINE / "bibliotheque" / s["fichier"])
            sortie = a.images / f"{e['id']}.png"
            doc[int(s["page"]) - 1].get_pixmap(dpi=90).save(sortie)
            print(f"[page rendue : {sortie}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
