"""Convertit les tableurs UVSQ en CSV lisibles (inventaire/trackers/), sans les modifier."""
import csv
import sys
from pathlib import Path

from openpyxl import load_workbook

RACINE = Path(__file__).resolve().parents[1]
CHAMPS = ["feuille", "numero", "intitule", "importance", "difficulte", "mots_cles",
          "remarques", "statut", "mes_remarques"]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dossier = RACINE / "inventaire" / "trackers"
    dossier.mkdir(parents=True, exist_ok=True)
    for x in sorted((RACINE / "bibliotheque" / "uvsq").rglob("*.xlsx")):
        lignes = []
        for ws in load_workbook(x, read_only=True, data_only=True).worksheets:
            for ligne in ws.iter_rows(values_only=True):
                # Les intertitres n'ont pas d'importance valide : seules les vraies lignes passent.
                if len(ligne) >= 8 and ligne[2] in ("Vital", "Important", "Secondaire", "Exotique"):
                    lignes.append([ws.title, *[("" if v is None else str(v)) for v in ligne[:8]]])
        sortie = dossier / f"{x.stem}.csv"
        with sortie.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(CHAMPS)
            w.writerows(lignes)
        print(f"{sortie.name} : {len(lignes)} exercices")
    return 0


if __name__ == "__main__":
    sys.exit(main())
