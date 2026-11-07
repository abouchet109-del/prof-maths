"""Valide les YAML de state/ et matieres/ ; code de sortie 1 en cas d'erreur."""
from __future__ import annotations

import sys

import yaml

import etat as E

CHAMPS_EXERCICE = ["id", "titre", "sources", "annale_prioritaire", "temps_min", "importance", "sous_chapitre"]


def verifier(racine=E.RACINE) -> list[str]:
    erreurs = []
    # 1. chargement de tous les YAML
    charges = {}
    for f in sorted(list((racine / "state").glob("*.yaml")) + list((racine / "matieres").rglob("*.yaml"))):
        try:
            charges[f] = E.charger_yaml(f)
        except yaml.YAMLError as ex:
            erreurs.append(f"{f.relative_to(racine)} : YAML invalide ({str(ex).splitlines()[0]})")
    nom = lambda f: str(f.relative_to(racine))  # noqa: E731

    # 2. exercices : champs, ids uniques, doublon_de existant
    exos = {}
    for f, data in charges.items():
        if f.name.startswith("exercices") and f.parent.parent.name == "matieres":
            for e in data or []:
                if e.get("id") in exos:
                    erreurs.append(f"{nom(f)} : id en double {e['id']}")
                exos[e.get("id")] = e
                for c in CHAMPS_EXERCICE:
                    if c not in e:
                        erreurs.append(f"{nom(f)} : {e.get('id')} sans champ {c}")
                if e.get("importance") not in E.CATEGORIES:
                    erreurs.append(f"{nom(f)} : {e.get('id')} importance invalide ({e.get('importance')})")
    for e in exos.values():
        if e.get("doublon_de") and e["doublon_de"] not in exos:
            erreurs.append(f"{e['id']} : doublon_de inconnu ({e['doublon_de']})")

    # 3. dispo
    dispo = charges.get(racine / "state" / "dispo.yaml")
    if dispo is None:
        erreurs.append("state/dispo.yaml manquant ou vide")
    else:
        try:
            for c in ["debut", "examens", "minutes_exercices_jour", "minutes_cours_jour"]:
                assert c in dispo, f"champ {c} manquant"
            for c in ["debut", "fin", "examens", "annales_libres_des"]:
                if c in dispo:
                    E.en_date(dispo[c])
            for c in ["minutes_reprises_max", "cartes_par_jour"]:
                assert c not in dispo or (isinstance(dispo[c], int) and dispo[c] >= 0), f"{c} : entier positif attendu"
            for x in dispo.get("exceptions", []):
                assert E.type_exception(x) in ("off", "quota"), f"type d'exception inconnu ({x['type']})"
                assert E.en_date(x["du"]) <= E.en_date(x["au"]), f"période inversée ({x['du']}..{x['au']})"
        except (AssertionError, KeyError, ValueError, TypeError) as ex:
            erreurs.append(f"state/dispo.yaml : {ex}")

    # 4. résultats
    res = charges.get(racine / "state" / "resultats.yaml")
    if not isinstance(res, list):
        erreurs.append("state/resultats.yaml : liste attendue")
    else:
        for i, r in enumerate(res, 1):
            try:
                E.en_date(r["date"])
            except (KeyError, ValueError, TypeError):
                erreurs.append(f"resultats #{i} : date invalide")
            if r.get("exercice") not in exos:
                erreurs.append(f"resultats #{i} : exercice inconnu ({r.get('exercice')})")
            if r.get("resultat") not in E.RESULTATS:
                erreurs.append(f"resultats #{i} : résultat invalide ({r.get('resultat')})")
            if r.get("palier_aide") not in range(5):
                erreurs.append(f"resultats #{i} : palier_aide hors 0..4 ({r.get('palier_aide')})")

    # 5. anki_plan : cartes existantes et jamais données deux fois
    ap = charges.get(racine / "state" / "anki_plan.yaml")
    if ap:
        cartes = {c["id"] for f, d in charges.items() if f.name == "cartes.yaml" for c in d or []}
        vus = set()
        for jour, ids in ap.items():
            for i in ids:
                if i not in cartes:
                    erreurs.append(f"anki_plan {jour} : carte inconnue {i}")
                if i in vus:
                    erreurs.append(f"anki_plan {jour} : carte {i} donnée plusieurs fois")
                vus.add(i)

    # 6. blocs.yaml et avancement_cours.yaml
    blocs = charges.get(racine / "state" / "blocs.yaml")
    if blocs:
        for jour, b in blocs.items():
            try:
                E.en_date(jour)
            except (ValueError, TypeError):
                erreurs.append(f"blocs {jour} : date invalide")
            if not isinstance(b, dict) or b.get("matiere") not in E.MATIERES:
                erreurs.append(f"blocs {jour} : matière inconnue ({b})")
    av = charges.get(racine / "state" / "avancement_cours.yaml")
    if av:
        for m, sc in av.items():
            if m not in E.MATIERES:
                erreurs.append(f"avancement_cours : matière inconnue ({m})")
            elif sc is not None and not any(e.get("sous_chapitre") == sc for e in exos.values()):
                erreurs.append(f"avancement_cours : sous-chapitre inconnu pour {m} ({sc})")
    return erreurs


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    erreurs = verifier()
    for e in erreurs:
        print("ERREUR", e)
    print(f"{len(erreurs)} erreur(s)." if erreurs else "OK : aucun problème.")
    sys.exit(1 if erreurs else 0)


if __name__ == "__main__":
    main()
