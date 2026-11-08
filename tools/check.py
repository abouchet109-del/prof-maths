"""Valide les YAML de state/ et matieres/ ; code de sortie 1 en cas d'erreur."""
from __future__ import annotations

import re
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

    # 5. anki_plan et seance : simples journaux de ce qui a été proposé. Une carte proposée mais pas apprise
    # est proposée de nouveau (lecture d'Anki) : plus de contrôle de doublon, seulement des ids connus.
    cartes = {c["id"] for f, d in charges.items() if f.name == "cartes.yaml" for c in d or []}
    ap = charges.get(racine / "state" / "anki_plan.yaml")
    for jour, ids in (ap or {}).items():
        for i in ids:
            if i not in cartes:
                erreurs.append(f"anki_plan {jour} : carte inconnue {i}")
    seances = charges.get(racine / "state" / "seance.yaml")
    for jour, e in (seances or {}).items():
        try:
            E.en_date(jour)
        except (ValueError, TypeError):
            erreurs.append(f"seance {jour} : date invalide")
        for i in (e or {}).get("exercices") or []:
            if i not in exos:
                erreurs.append(f"seance {jour} : exercice inconnu {i}")
        for i in (e or {}).get("cartes") or []:
            if i not in cartes:
                erreurs.append(f"seance {jour} : carte inconnue {i}")

    # 5 bis. cartes d'exercices : tag `exercice` <=> champ `exercice` ; exercice connu, de la même matière,
    # une seule carte par exercice, notion renseignée (lue par plan.py)
    matiere_exo = {}
    for f, data in charges.items():
        if f.name.startswith("exercices") and f.parent.parent.name == "matieres":
            matiere_exo.update({e.get("id"): f.parent.name for e in data or []})
    cartes_exo = {}
    for f, data in charges.items():
        if f.name != "cartes.yaml":
            continue
        for c in data or []:
            marque = "exercice" in (c.get("tags") or [])
            if marque != bool(c.get("exercice")):
                erreurs.append(f"{nom(f)} : carte {c.get('id')} : tag `exercice` et champ `exercice` vont ensemble")
            if not c.get("exercice"):
                continue
            x = c["exercice"]
            if x not in exos:
                erreurs.append(f"{nom(f)} : carte {c.get('id')} : exercice inconnu ({x})")
            elif matiere_exo.get(x) != f.parent.name:
                erreurs.append(f"{nom(f)} : carte {c.get('id')} : l'exercice {x} est en {matiere_exo.get(x)}")
            if x in cartes_exo:
                erreurs.append(f"{nom(f)} : deux cartes pour l'exercice {x} ({cartes_exo[x]}, {c.get('id')})")
            cartes_exo[x] = c.get("id")
            if "notion" not in c:
                erreurs.append(f"{nom(f)} : carte {c.get('id')} sans champ notion")

    # une carte d'exercice va dans le sous-paquet `Exercices` d'un chapitre où les cartes de cours existent déjà
    for f, data in charges.items():
        if f.name == "cartes.yaml":
            cours = {c.get("chapitre") for c in data or [] if "exercice" not in (c.get("tags") or [])}
            for c in data or []:
                if c.get("exercice") and c.get("chapitre") not in cours:
                    erreurs.append(f"{nom(f)} : carte {c.get('id')} : chapitre inconnu des cartes de cours ({c.get('chapitre')})")

    # 5 ter. notions : ids uniques ; une notion `type: prerequis` (L1-L2) porte un sous-chapitre existant du poly
    # (d'une notion du poly ou d'un exercice de la même matière) et `requis_par` (exercices ou notions qui l'utilisent) ;
    # toute carte (hors erreur) a une notion connue, et celle d'un prérequis est du même chapitre que la carte
    notions = {}
    for f, data in charges.items():
        if f.name == "notions.yaml" and f.parent.parent.name == "matieres":
            for n in data or []:
                if n.get("id") in notions:
                    erreurs.append(f"{nom(f)} : id de notion en double {n['id']}")
                notions[n.get("id")] = {**n, "matiere": f.parent.name}
    sc_poly = {}
    for e in exos.values():
        sc_poly.setdefault(matiere_exo.get(e.get("id")), set()).add(e.get("sous_chapitre"))
    for n in notions.values():
        if n.get("type") != "prerequis":
            sc_poly.setdefault(n["matiere"], set()).add(f"{n.get('chapitre')} > {n.get('sous_chapitre')}")
    for n in notions.values():
        if n.get("type") != "prerequis":
            continue
        i = n.get("id")
        if not re.fullmatch(r"[a-z]+-p-\d{4}", str(i)):
            erreurs.append(f"notion prérequis {i} : id attendu `<préfixe>-p-NNNN`")
        for c in ("titre", "chapitre", "sous_chapitre", "enonce"):
            if not n.get(c):
                erreurs.append(f"notion prérequis {i} : champ {c} manquant")
        if f"{n.get('chapitre')} > {n.get('sous_chapitre')}" not in sc_poly.get(n["matiere"], set()):
            erreurs.append(f"notion prérequis {i} : sous-chapitre inconnu du poly ({n.get('chapitre')} > {n.get('sous_chapitre')})")
        if not n.get("requis_par"):
            erreurs.append(f"notion prérequis {i} : `requis_par` vide (exercices ou notions qui l'utilisent)")
        for x in n.get("requis_par") or []:
            if x not in exos and x not in notions:
                erreurs.append(f"notion prérequis {i} : requis_par inconnu ({x})")
    for f, data in charges.items():
        if f.name != "cartes.yaml":
            continue
        for c in data or []:
            k = c.get("notion")
            if not k and "erreur" not in (c.get("tags") or []) and not c.get("exercice"):
                erreurs.append(f"{nom(f)} : carte {c.get('id')} sans notion (un prérequis L1-L2 est une notion `type: prerequis`)")
            elif k and k not in notions:
                erreurs.append(f"{nom(f)} : carte {c.get('id')} : notion inconnue ({k})")
            elif k and notions[k].get("type") == "prerequis":
                neutre = lambda t: re.sub(r"[\$\^{}]", "", str(t))  # noqa: E731
                if neutre(notions[k].get("chapitre")) != neutre(c.get("chapitre")):
                    erreurs.append(f"{nom(f)} : carte {c.get('id')} : chapitre {c.get('chapitre')!r} différent de celui de la notion {k}")

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
