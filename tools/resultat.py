"""Résultats d'exercices.

  resultat.py ajouter <id_exercice> <resultat> [--aide N] [--note "..."] [--date D]
  resultat.py ajouter <id_exercice> --questions "Q1=reussi,Q2=presque" [--aide N] [--note "..."] [--date D]
      (résultat global : celui donné, sinon le moins bon des questions ; `reussi` seulement si toutes le sont)
      --point "Q2=ce qui a bloqué" (répétable) : affiché à la reprise ; --complet : la liste couvre tout l'exercice
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
    try:
        questions = lire_questions(args.questions) if args.questions else None
    except ValueError as ex:
        print(f"--questions : {ex}", file=sys.stderr)
        return 1
    resultat = args.resultat or (E.pire(questions.values()) if questions else None)
    if resultat is None:
        print("Donner le résultat ou --questions.", file=sys.stderr)
        return 1
    if questions and (resultat == "reussi") != all(v == "reussi" for v in questions.values()):
        print(f"Résultat {resultat} contraire aux questions : `reussi` si et seulement si toutes le sont.",
              file=sys.stderr)
        return 1
    pts = {}
    for p in args.point or []:
        q, _, t = (x.strip() for x in p.partition("="))
        if not questions or q not in questions or not t or questions[q] == "reussi":
            print(f"--point « {p} » : attendu Question=texte, pour une question non réussie de --questions.",
                  file=sys.stderr)
            return 1
        pts[q] = t
    if args.complet and not questions:
        print("--complet va avec --questions.", file=sys.stderr)
        return 1
    if not questions and (resultat == "reussi") != (args.aide == 0) and resultat in ("reussi", "aide"):
        print(f"{resultat} avec un palier d'aide {args.aide} : `reussi` = palier 0, `aide` = palier 1 à 4.",
              file=sys.stderr)
        return 1
    chemin = E.RACINE / "state" / "resultats.yaml"
    resultats = E.charger_yaml(chemin, [])
    jour = E.en_date(args.date) if args.date else dt.date.today()
    if any(r["exercice"] == args.exercice and E.en_date(r["date"]) == jour for r in resultats):
        print(f"{args.exercice} a déjà un résultat le {jour} : une seule ligne par exercice et par jour.",
              file=sys.stderr)
        return 1
    entree = {
        "date": E.en_date(args.date) if args.date else dt.date.today(),
        "exercice": args.exercice,
        "resultat": resultat,
        "palier_aide": args.aide,
        "note": args.note,
    }
    if questions:
        entree["questions"] = questions
        if args.complet:
            entree["complet"] = True
        if pts:
            entree["points"] = pts
    resultats.append(entree)
    with open(chemin, "w", encoding="utf-8") as f:
        yaml.safe_dump(resultats, f, allow_unicode=True, sort_keys=False, width=200)
    print(f"Ajouté : {args.exercice} {resultat} ({resultats[-1]['date']}).")
    return 0


def lire_questions(texte: str) -> dict[str, str]:
    """« Q1=reussi,Q2=presque » -> {"Q1": "reussi", "Q2": "presque"}."""
    res = {}
    for morceau in filter(None, (m.strip() for m in texte.split(","))):
        q, _, r = (x.strip() for x in morceau.partition("="))
        if not q or r not in E.RESULTATS:
            raise ValueError(f"« {morceau} » : attendu Question=resultat, resultat parmi {', '.join(E.RESULTATS)}")
        res[q] = r
    if not res:
        raise ValueError("aucune question")
    return res


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
    a.add_argument("resultat", nargs="?", choices=E.RESULTATS)
    a.add_argument("--questions", default=None, help="résultat par sous-question : « Q1=reussi,Q2=presque »")
    a.add_argument("--complet", action="store_true",
                   help="avec --questions : la liste couvre tout l'exercice (retire le « reste » non détaillé)")
    a.add_argument("--point", action="append", metavar="Q=TEXTE",
                   help="ce qui a bloqué sur une question non réussie, en quelques mots (répétable)")
    a.add_argument("--aide", type=int, default=0, choices=range(5), help="palier d'aide 0..4")
    a.add_argument("--note", default=None)
    a.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    pr = sp.add_parser("profil", help="maîtrise par sous-chapitre, méthode, notion")
    pr.add_argument("--matiere", default=None)
    args = p.parse_args()
    sys.exit(ajouter(args) if args.cmd == "ajouter" else profil(args))


if __name__ == "__main__":
    main()
