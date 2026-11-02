"""Compte exercices, importances et statuts des tableurs UVSQ (lecture seule)."""
import sys
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

UVSQ = Path(__file__).resolve().parents[1] / "bibliotheque" / "uvsq"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for x in sorted(UVSQ.rglob("*.xlsx")):
        print(f"\n=== {x.name}")
        total_i, total_s = Counter(), Counter()
        for ws in load_workbook(x, read_only=True, data_only=True).worksheets:
            imp, stat, avec_remarque = Counter(), Counter(), 0
            en_tete = False
            for ligne in ws.iter_rows(values_only=True):
                if ligne and ligne[0] == "N° Exo":
                    en_tete = True
                    continue
                if not en_tete or len(ligne) < 8 or not ligne[2]:
                    continue
                imp[str(ligne[2]).strip()] += 1
                stat[str(ligne[6]).strip() if ligne[6] else "?"] += 1
                avec_remarque += bool(ligne[7])
            print(f"{ws.title[:34]:34} {dict(imp)} | {dict(stat)} | remarques {avec_remarque}")
            total_i += imp
            total_s += stat
        print(f"TOTAL {sum(total_i.values())} : {dict(total_i)} | {dict(total_s)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
