"""Finalise les fichiers d'exercices, sans tokens.

Usage :
  python -I tools/post_exercices.py normaliser MATIERE
      Calcule annale_prioritaire et retire les statuts et remarques du tableur d'un ami.
  python -I tools/post_exercices.py tableur MATIERE CSV
      Crée matieres/MATIERE/exercices_uvsq.yaml depuis un tableur UVSQ : une entrée par ligne,
      énoncé non extrait (qualite_extraction: a_extraire), à lire seulement si l'exercice est planifié.
"""
import csv
import re
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[1]
COURT = {"topologie": "topo", "mesure": "mes", "modelisation": "mod", "proba": "pro"}


class Dumper(yaml.SafeDumper):
    pass


def _texte(dumper, valeur):
    style = "|" if "\n" in valeur or "\\" in valeur else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", valeur, style=style)


Dumper.add_representer(str, _texte)


def ecrire(chemin: Path, data: list) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(yaml.dump(data, Dumper=Dumper, allow_unicode=True, sort_keys=False,
                                width=1000, default_flow_style=False), encoding="utf-8")


def est_annale_pc(ex: dict) -> bool:
    return any(s.get("etab") == "paris-cite" and "/annales/" in str(s.get("fichier"))
               for s in ex.get("sources") or [])


def normaliser(matiere: str) -> int:
    chemin = RACINE / "matieres" / matiere / "exercices.yaml"
    data = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    sortie = []
    for ex in data:
        nouveau = {}
        for cle, val in ex.items():
            if cle == "annale_prioritaire":
                continue
            nouveau[cle] = val
            if cle == "sources":
                nouveau["annale_prioritaire"] = est_annale_pc(ex)
        if nouveau.get("indice_tableur"):
            nouveau["indice_tableur"] = {k: v for k, v in nouveau["indice_tableur"].items()
                                         if k in ("importance", "difficulte")}
        sortie.append(nouveau)
    ecrire(chemin, sortie)
    print(f"{matiere} : {len(sortie)} entrées, "
          f"{sum(e['annale_prioritaire'] for e in sortie)} d'annales de Paris Cité")
    return 0


def tableur(matiere: str, csv_path: Path) -> int:
    entrees, vus = [], {}
    with csv_path.open(encoding="utf-8", newline="") as f:
        for ligne in csv.DictReader(f, delimiter=";"):
            base = re.sub(r"[^a-z0-9]+", "-", f"{ligne['feuille'][:7]}-{ligne['numero']}".lower()).strip("-")
            vus[base] = vus.get(base, 0) + 1
            suffixe = f"-{vus[base]}" if vus[base] > 1 else ""
            entrees.append({
                "id": f"{COURT[matiere]}-uvsq-{base}{suffixe}",
                "titre": ligne["intitule"],
                "enonce": None,
                "sources": [{"etab": "uvsq", "fichier": None, "page": None,
                             "numero": f"{ligne['feuille']} / {ligne['numero']}"}],
                "annale_prioritaire": False,
                "type_source": "annale" if re.search(r"CC|Exam|DS", ligne["numero"]) else "td",
                "annale": None, "disponible": True, "sous_chapitre": None, "methodes": [],
                "notions": [], "importance": None, "justification": None, "difficulte": None,
                "temps_min": None,
                "indice_tableur": {"importance": ligne["importance"], "difficulte": ligne["difficulte"],
                                   "mots_cles": ligne["mots_cles"]},
                "corrige": {"statut": "absent", "ref": None},
                "qualite_extraction": "a_extraire",
            })
    ecrire(RACINE / "matieres" / matiere / "exercices_uvsq.yaml", entrees)
    print(f"{matiere} : {len(entrees)} exercices UVSQ créés depuis le tableur")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "normaliser":
        return normaliser(sys.argv[2])
    return tableur(sys.argv[2], Path(sys.argv[3]))


if __name__ == "__main__":
    sys.exit(main())
