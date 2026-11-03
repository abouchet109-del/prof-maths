"""Prépare la relecture des cartes : échantillon par matière + cartes signalées, pages rendues.

Usage : python -I tools/echantillon_cartes.py DOSSIER N_PAR_MATIERE ID_OU_MOTIF [...]
Un argument contenant `*` est un motif cherché dans le recto ou le verso ; sinon c'est un id
de carte ou de notion. Écrit DOSSIER/relecture.md.
"""
import random
import sys
from pathlib import Path

import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verification import trouver_pdf  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
MATIERES = ["topologie", "mesure", "modelisation", "proba"]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dossier, n = Path(sys.argv[1]), int(sys.argv[2])
    signales = sys.argv[3:]
    dossier.mkdir(parents=True, exist_ok=True)
    random.seed(11)
    choix = []
    for m in MATIERES:
        cartes = yaml.safe_load((RACINE / "matieres" / m / "cartes.yaml").read_text(encoding="utf-8"))
        notions = {x["id"]: x for x in yaml.safe_load(
            (RACINE / "matieres" / m / "notions.yaml").read_text(encoding="utf-8"))}
        marquees = [c for c in cartes if any(
            (s.strip("*") in f"{c['recto']} {c['verso']}") if "*" in s else s in (c["id"], c.get("notion"))
            for s in signales)]
        reste = [c for c in cartes if c not in marquees and c.get("priorite") == 1]
        for c in marquees + random.sample(reste, min(n, len(reste))):
            choix.append((m, c, notions.get(c.get("notion"), {}).get("source") or {}, c in marquees))
    lignes, rendues = [], set()
    for m, c, src, marquee in choix:
        page = src.get("page")
        image = "pas de page connue : utiliser le champ source"
        if src.get("fichier") and page:
            png = dossier / f"{Path(src['fichier']).stem}-p{page}.png"
            if png not in rendues:
                pymupdf.open(trouver_pdf(src["fichier"]))[int(page) - 1].get_pixmap(dpi=100).save(png)
                rendues.add(png)
            image = str(png)
        lignes.append(f"\n## {c['id']} | {m} | {'SIGNALÉE' if marquee else 'échantillon'}\n"
                      f"- recto : {c['recto']}\n- verso : {c['verso']}\n- source : {c['source']}\n- page : {image}")
    (dossier / "relecture.md").write_text("\n".join(lignes), encoding="utf-8")
    print(f"{len(choix)} cartes ({sum(x[3] for x in choix)} signalées), {len(rendues)} pages -> {dossier / 'relecture.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
