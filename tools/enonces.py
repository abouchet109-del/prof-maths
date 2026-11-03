"""Écrit inventaire/enonces-<matiere>.md : les énoncés utiles à l'analyse des prérequis, sans le YAML.

Paris Cité partout, plus les annales de l'UVSQ en mesure, faute d'annales de Paris Cité.
"""
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[1]

sys.stdout.reconfigure(encoding="utf-8")
for m in ["topologie", "mesure", "modelisation", "proba"]:
    data = yaml.safe_load((RACINE / "matieres" / m / "exercices.yaml").read_text(encoding="utf-8"))
    garde = [e for e in data if m == "mesure" or any(s["etab"] == "paris-cite" for s in e["sources"])]
    texte = "\n".join(f"\n## {e['id']}{' [ANNALE PRIORITAIRE]' if e['annale_prioritaire'] else ''}\n{e['enonce']}"
                      for e in garde)
    chemin = RACINE / "inventaire" / f"enonces-{m}.md"
    chemin.write_text(texte, encoding="utf-8")
    print(f"{m} : {len(garde)} énoncés, ~{len(texte) // 3} tokens")
