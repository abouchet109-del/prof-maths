"""Extrait le texte des PDF UVSQ et résume les classeurs Excel, sans rien modifier.

Usage : python -I tools/apercu_uvsq.py
Écrit bibliotheque/_texte/uvsq/... et inventaire/uvsq.csv ; affiche la structure des .xlsx.
"""
import csv
import sys
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

RACINE = Path(__file__).resolve().parents[1]
UVSQ = RACINE / "bibliotheque" / "uvsq"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    lignes, totaux = [], {}
    for pdf in sorted(p for p in UVSQ.rglob("*") if p.suffix.lower() == ".pdf"):
        rel = pdf.relative_to(UVSQ)
        try:
            pages = [p.extract_text() or "" for p in PdfReader(str(pdf)).pages]
        except Exception as exc:  # un PDF illisible ne doit pas arrêter l'aperçu
            print(f"ILLISIBLE {rel} : {exc}")
            continue
        car = sum(len(t) for t in pages)
        lecture = "texte" if car / max(len(pages), 1) >= 200 else "image"
        sortie = RACINE / "bibliotheque" / "_texte" / "uvsq" / rel.with_suffix(".txt")
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text("".join(f"\n--- page {i} ---\n{t}" for i, t in enumerate(pages, 1)),
                          encoding="utf-8")
        lignes.append([rel.as_posix(), len(pages), car, lecture])
        cle = (rel.parts[0], lecture)
        p0, c0 = totaux.get(cle, (0, 0))
        totaux[cle] = (p0 + len(pages), c0 + car)
    with (RACINE / "inventaire" / "uvsq.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["fichier", "pages", "caracteres", "lecture"])
        w.writerows(lignes)
    for (m, lecture), (p, c) in sorted(totaux.items()):
        print(f"{m:12} {lecture:6} {p:4} p {c:8} car ~{c // 3:7} tokens")
    print("Scans ou manuscrits :")
    for l in lignes:
        if l[3] == "image":
            print(f"  {l[1]:3} p  {l[0]}")

    for x in sorted(UVSQ.rglob("*.xlsx")):
        wb = load_workbook(x, read_only=True, data_only=True)
        print(f"\n=== {x.relative_to(UVSQ).as_posix()}")
        for ws in wb.worksheets:
            print(f"-- {ws.title} ({ws.max_row} lignes, {ws.max_column} colonnes)")
            for i, ligne in enumerate(ws.iter_rows(values_only=True)):
                if i >= 6:
                    break
                print("   ", [str(v)[:40] for v in ligne if v is not None])
    return 0


if __name__ == "__main__":
    sys.exit(main())
