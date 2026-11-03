"""Prépare le classement des exercices, puis le fusionne dans les fichiers d'exercices.

  python -I tools/classement.py preparer MATIERE
      Écrit inventaire/classement-MATIERE.md : sous-chapitres et notions du cours, énoncés de
      Paris Cité (annales prioritaires signalées), puis les entrées UVSQ en une ligne chacune.
  python -I tools/classement.py fusionner MATIERE
      Reporte matieres/MATIERE/classement.yaml dans exercices.yaml et exercices_uvsq.yaml.
"""
import sys
from pathlib import Path

import yaml

from post_exercices import ecrire

RACINE = Path(__file__).resolve().parents[1]
CHAMPS = ("sous_chapitre", "methodes", "notions", "importance", "justification", "difficulte", "temps_min")


def fichiers(m: str) -> list[Path]:
    return [p for p in (RACINE / "matieres" / m / "exercices.yaml", RACINE / "matieres" / m / "exercices_uvsq.yaml")
            if p.exists()]


def preparer(m: str) -> int:
    notions = yaml.safe_load((RACINE / "matieres" / m / "notions.yaml").read_text(encoding="utf-8"))
    lignes = ["# Sous-chapitres du cours (taxonomie à utiliser)"]
    vus = []
    for n in notions:
        cle = f"{n['chapitre']} > {n['sous_chapitre']}"
        if cle not in vus:
            vus.append(cle)
            lignes.append(f"- {cle}")
    lignes.append("\n# Notions (id | type | titre)")
    lignes += [f"- {n['id']} | {n['type']} | {n['titre']}" for n in notions]
    pc, uvsq = [], []
    for p in fichiers(m):
        for e in yaml.safe_load(p.read_text(encoding="utf-8")):
            if any(s["etab"] == "paris-cite" for s in e["sources"]):
                drapeau = " [ANNALE PRIORITAIRE]" if e.get("annale_prioritaire") else ""
                pc.append(f"\n## {e['id']}{drapeau} ({e['type_source']})\n{e['enonce']}")
            else:
                ind = e.get("indice_tableur") or {}
                extrait = " ".join((e.get("enonce") or "").split())[:160]
                uvsq.append(f"- {e['id']} | {e['type_source']} | {e['titre']} | tableur : "
                            f"{ind.get('importance', '-')} {ind.get('difficulte', '')} | {extrait}")
    lignes.append(f"\n# Exercices de Paris Cité ({len(pc)})")
    lignes += pc
    lignes.append(f"\n# Exercices UVSQ ({len(uvsq)}) : id | type | titre | indice du tableur | début d'énoncé")
    lignes += uvsq
    chemin = RACINE / "inventaire" / f"classement-{m}.md"
    texte = "\n".join(lignes)
    chemin.write_text(texte, encoding="utf-8")
    print(f"{m} : {len(pc)} Paris Cité, {len(uvsq)} UVSQ, ~{len(texte) // 3} tokens")
    return 0


def fusionner(m: str) -> int:
    classement = yaml.safe_load((RACINE / "matieres" / m / "classement.yaml").read_text(encoding="utf-8"))
    restants = set(classement)
    for p in fichiers(m):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        for e in data:
            c = classement.get(e["id"])
            if c:
                restants.discard(e["id"])
                for k in CHAMPS:
                    if k in c:
                        e[k] = c[k]
                if c.get("doublon_de"):
                    e["doublon_de"] = c["doublon_de"]
        ecrire(p, data)
    total = sum(len(yaml.safe_load(p.read_text(encoding="utf-8"))) for p in fichiers(m))
    print(f"{m} : {len(classement) - len(restants)} classés sur {total} ; ids inconnus : {sorted(restants) or 'aucun'}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(preparer(sys.argv[2]) if sys.argv[1] == "preparer" else fusionner(sys.argv[2]))
