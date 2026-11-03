"""Vérification des énoncés contre les PDF, en deux temps.

  python -I tools/verification.py preparer DOSSIER MATIERE [MATIERE...]
      Pour les annales de Paris Cité et les énoncés a_verifier : rend les pages en PNG et écrit
      DOSSIER/lots.md (par PDF : pages à ouvrir, puis énoncés à comparer).
  python -I tools/verification.py appliquer MATIERE CORRECTIONS.yaml
      Applique {id: {enonce?, page?, qualite_extraction?}} à matieres/MATIERE/exercices.yaml.
"""
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pymupdf
import yaml

from post_exercices import ecrire

RACINE = Path(__file__).resolve().parents[1]


def source_de(ex: dict) -> dict:
    for s in ex["sources"]:
        if s.get("etab") == "paris-cite" and "/annales/" in str(s.get("fichier")):
            return s
    return ex["sources"][0]


def trouver_pdf(fichier: str) -> Path:
    """Chemin sous bibliotheque/, quelle que soit la forme Unicode des noms décompressés."""
    cible = RACINE / "bibliotheque" / fichier
    if cible.exists():
        return cible
    voulu = unicodedata.normalize("NFC", fichier)
    for p in (RACINE / "bibliotheque").rglob("*.pdf"):
        rel = p.relative_to(RACINE / "bibliotheque").as_posix()
        if unicodedata.normalize("NFC", rel) == voulu:
            return p
    raise SystemExit(f"PDF introuvable : {fichier}")


def preparer(dossier: Path, matieres: list[str]) -> int:
    dossier.mkdir(parents=True, exist_ok=True)
    lots = defaultdict(list)
    for m in matieres:
        for ex in yaml.safe_load((RACINE / "matieres" / m / "exercices.yaml").read_text(encoding="utf-8")):
            if ex.get("annale_prioritaire") or ex.get("qualite_extraction") == "a_verifier":
                lots[source_de(ex)["fichier"]].append((m, ex))
    lignes, n_pages = [], 0
    for fichier in sorted(lots):
        doc = pymupdf.open(trouver_pdf(fichier))
        annale = "/annales/" in fichier
        pages = range(len(doc)) if annale else sorted(
            {p for _, e in lots[fichier] for p in (int(source_de(e)["page"]) - 1, int(source_de(e)["page"]))
             if p < len(doc)})
        lignes.append(f"\n# {fichier}\nPages à ouvrir :")
        for p in pages:
            png = dossier / f"{fichier.replace('/', '_').removesuffix('.pdf')}-p{p + 1}.png"
            doc[p].get_pixmap(dpi=100).save(png)
            lignes.append(f"- {png}")
            n_pages += 1
        for m, e in lots[fichier]:
            s = source_de(e)
            lignes.append(f"\n## {e['id']} | matière {m} | {s['numero']} p.{s['page']} | {e['qualite_extraction']}\n{e['enonce']}")
    (dossier / "lots.md").write_text("\n".join(lignes), encoding="utf-8")
    total = sum(len(v) for v in lots.values())
    print(f"{total} énoncés, {len(lots)} PDF, {n_pages} pages rendues -> {dossier / 'lots.md'}")
    return 0


def appliquer(matiere: str, corrections: Path) -> int:
    chemin = RACINE / "matieres" / matiere / "exercices.yaml"
    data = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    corr = yaml.safe_load(corrections.read_text(encoding="utf-8")) or {}
    par_id = {e["id"]: e for e in data}
    inconnus = [i for i in corr if i not in par_id]
    if inconnus:
        raise SystemExit(f"id inconnus : {inconnus}")
    for i, c in corr.items():
        ex = par_id[i]
        if "enonce" in c:
            ex["enonce"] = c["enonce"]
        if "qualite_extraction" in c:
            ex["qualite_extraction"] = c["qualite_extraction"]
        if "page" in c:
            source_de(ex)["page"] = c["page"]
    ecrire(chemin, data)
    print(f"{matiere} : {len(corr)} corrections appliquées")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "preparer":
        return preparer(Path(sys.argv[2]), sys.argv[3:])
    return appliquer(sys.argv[2], Path(sys.argv[3]))


if __name__ == "__main__":
    sys.exit(main())
