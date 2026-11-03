"""Résultats d'exercices.

  resultat.py ajouter <id_exercice> <resultat> [--aide N] [--note "..."] [--date D]
  resultat.py profil [--matiere M]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import yaml

import etat as E

LIMITE_LISTE = 15   # nombre de méthodes / notions affichées (les plus faibles)


def ajouter(args) -> int:
    exos = {e["id"]: e for e in E.charger_exercices()}
    e = exos.get(args.exercice)
    if e is None:
        print(f"Exercice inconnu : {args.exercice}", file=sys.stderr)
        return 1
    if e.get("doublon_de"):
        print(f"{args.exercice} est un doublon de {e['doublon_de']} : enregistrer le résultat sur celui-ci.",
              file=sys.stderr)
        return 1
    chemin = E.RACINE / "state" / "resultats.yaml"
    resultats = E.charger_yaml(chemin, [])
    resultats.append({
        "date": E.en_date(args.date) if args.date else dt.date.today(),
        "exercice": args.exercice,
        "resultat": args.resultat,
        "palier_aide": args.aide,
        "note": args.note,
    })
    with open(chemin, "w", encoding="utf-8") as f:
        yaml.safe_dump(resultats, f, allow_unicode=True, sort_keys=False, width=200)
    print(f"Ajouté : {args.exercice} {args.resultat} ({resultats[-1]['date']}).")
    return 0


def _moyennes(groupes: dict) -> list[tuple]:
    """cle -> [scores] devient [(score moyen, nb d'exercices, cle)] du plus faible au plus fort."""
    return sorted(((sum(v) / len(v), len(v), k) for k, v in groupes.items()), key=lambda t: (t[0], str(t[2])))


def profil(args) -> int:
    aujourdhui = dt.date.today()
    exos = [e for e in E.charger_exercices() if E.planifiable(e) and args.matiere in (None, e["matiere"])]
    if args.matiere and args.matiere not in E.MATIERES:
        print(f"Matière inconnue : {args.matiere} ({', '.join(E.MATIERES)})", file=sys.stderr)
        return 1
    h = E.historique(E.charger_resultats())
    titres = {n["id"]: n["titre"] for n in E.charger_notions().values()}
    for m in E.MATIERES:
        for x in E.charger_yaml(E.RACINE / "matieres" / m / "methodes.yaml", []):
            titres[x["id"]] = x["titre"]
    par_sc, par_met, par_not, a_revoir = {}, {}, {}, []
    for e in exos:
        s = E.score_exercice(h.get(e["id"], []), aujourdhui)
        if s is None:
            continue
        par_sc.setdefault((e["matiere"], e.get("sous_chapitre")), []).append(s)
        for m in e.get("methodes") or []:
            par_met.setdefault(m, []).append(s)
        for n in e.get("notions") or []:
            par_not.setdefault(n, []).append(s)
        et = E.etat_exercice(h[e["id"]], aujourdhui)
        if et["etat"] == "a_revoir":
            a_revoir.append((et["du"], e, et))
    if not par_sc:
        print("Aucun résultat enregistré.")
        return 0

    def afficher(titre, lignes, nom):
        print(f"\n## {titre}")
        for s, n, k in lignes:
            print(f"- {s:.2f} ({n} ex.) {nom(k)}")

    afficher("Maîtrise par sous-chapitre", _moyennes(par_sc), lambda k: f"{k[0]} / {k[1]}")
    afficher(f"Méthodes (les {LIMITE_LISTE} plus faibles)", _moyennes(par_met)[:LIMITE_LISTE],
             lambda k: f"{k} {titres.get(k, '')[:70]}")
    afficher(f"Notions (les {LIMITE_LISTE} plus faibles)", _moyennes(par_not)[:LIMITE_LISTE],
             lambda k: f"{k} {titres.get(k, '')[:70]}")
    print("\n## Exercices à revoir")
    for du, e, et in sorted(a_revoir, key=lambda t: t[0]):
        retard = "dû" if et["est_du"] else f"dû le {du}"
        print(f"- {e['id']} {e['titre'][:50]} — dernier : {et['dernier'][1]} ({et['dernier'][0]}), {retard}")
    if not a_revoir:
        print("- aucun")
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("ajouter", help="enregistre un résultat")
    a.add_argument("exercice")
    a.add_argument("resultat", choices=E.RESULTATS)
    a.add_argument("--aide", type=int, default=0, choices=range(5), help="palier d'aide 0..4")
    a.add_argument("--note", default=None)
    a.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    pr = sp.add_parser("profil", help="maîtrise par sous-chapitre, méthode, notion")
    pr.add_argument("--matiere", default=None)
    args = p.parse_args()
    sys.exit(ajouter(args) if args.cmd == "ajouter" else profil(args))


if __name__ == "__main__":
    main()
