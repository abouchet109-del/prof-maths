"""Planificateur : `plan.py jour [--date AAAA-MM-JJ]` écrit NOW.md (60 lignes au plus)."""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import yaml

import etat as E

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MAX_LIGNES = 60
MIN_PAR_NOTION = 10     # durée estimée d'une notion de cours
JOURS_RATES = 7         # un exercice raté depuis moins de 7 jours compte comme « récent »
JOURS_PROCHES = 3       # cartes préparées pour les exercices des 3 jours suivants


def contexte(racine=E.RACINE) -> dict:
    """Charge toutes les données nécessaires au plan."""
    return {
        "exercices": E.charger_exercices(racine),
        "resultats": E.charger_resultats(racine),
        "dispo": E.charger_yaml(racine / "state" / "dispo.yaml", {}),
        "notions": E.charger_notions(racine),
        "cartes": E.charger_cartes(racine),
        "anki_plan": E.charger_yaml(racine / "state" / "anki_plan.yaml", {}),
        "a_revoir": E.charger_yaml(racine / "state" / "a_revoir.yaml", []),
        "couverture": charger_couverture(racine),
    }


def charger_couverture(racine=E.RACINE) -> dict:
    """notion -> {statut, notes} fusionné sur toutes les matières (matieres/<m>/couverture.yaml)."""
    res = {}
    for m in E.MATIERES:
        res.update(E.charger_yaml(racine / "matieres" / m / "couverture.yaml", {}) or {})
    return res


def _etats(exos, resultats, d):
    h = E.historique(resultats)
    return {e["id"]: E.etat_exercice(h.get(e["id"], []), d) for e in exos}


def _annee(e) -> str:
    return str(e["annale"]["annee"]) if e.get("annale") else ""


def _derniere_annee(exos) -> dict:
    """Année d'annale la plus récente de chaque matière (annales prioritaires) : examens blancs."""
    res = {}
    for e in exos:
        if e.get("annale_prioritaire") and e.get("annale"):
            res[e["matiere"]] = max(res.get(e["matiere"], ""), _annee(e))
    return res


def _scores_sous_chapitres(exos, resultats, d) -> dict:
    """(matière, sous-chapitre) -> score moyen des exercices déjà tentés."""
    h = E.historique(resultats)
    acc: dict = {}
    for e in exos:
        s = E.score_exercice(h.get(e["id"], []), d)
        if s is not None:
            acc.setdefault((e["matiere"], e.get("sous_chapitre")), []).append(s)
    return {k: sum(v) / len(v) for k, v in acc.items()}


# ------------------------------------------------------------------ plan du jour
def plan_jour(ctx, d: dt.date, resultats=None) -> dict:
    """Choisit les exercices du jour : reprises, annales prioritaires, nouveaux exercices."""
    resultats = ctx["resultats"] if resultats is None else resultats
    info = E.jour_info(ctx["dispo"], d)
    exos = [e for e in ctx["exercices"] if E.planifiable(e)]
    etats = _etats(exos, resultats, d)
    plan = {"date": d, "info": info, "items": [], "minutes": 0, "etats": etats, "exos": exos}
    if info["off"]:
        return plan
    restant = info["minutes_exercices"]
    ids = set()

    def ajouter(e, genre) -> bool:
        nonlocal restant
        if e["id"] in ids or e["temps_min"] > restant:      # ne tient pas : sauté
            return False
        ids.add(e["id"])
        restant -= e["temps_min"]
        plan["items"].append((e, genre))
        plan["minutes"] += e["temps_min"]
        return True

    # (a) reprises dues : exercices à revoir d'abord, puis les plus en retard
    dus = [e for e in exos if etats[e["id"]]["est_du"]]
    dus.sort(key=lambda e: (etats[e["id"]]["etat"] != "a_revoir", etats[e["id"]]["du"], e["ordre"]))
    for e in dus:
        ajouter(e, "reprise")

    # (b) annales prioritaires jamais tentées ; la dernière année de chaque matière = examen blanc
    derniere = _derniere_annee(exos)

    def blanc(e):
        return bool(e.get("annale")) and _annee(e) == derniere.get(e["matiere"])

    annales = [e for e in exos if e.get("annale_prioritaire") and etats[e["id"]]["etat"] == "jamais"]
    if not info["quota"]:
        annales = [e for e in annales if not blanc(e)]
    # examens blancs en dernier, puis les années les plus récentes d'abord
    annales.sort(key=lambda e: (blanc(e), -int(_annee(e)[:4] or 0), e["ordre"]))
    for e in annales:
        if ajouter(e, "annale " + _annee(e)) and not info["quota"]:
            break   # hors période quota : une annale par jour au plus

    # (c) nouveaux exercices de la catégorie ouverte, en alternant les matières
    scores = _scores_sous_chapitres(exos, resultats, d)
    cand, vital = {}, {}
    for m in E.MATIERES:
        em = [e for e in exos if e["matiere"] == m and not e.get("annale_prioritaire")]
        vital[m] = sum(e["temps_min"] for e in em if E.categorie(e) == "vital"
                       and etats[e["id"]]["etat"] in ("jamais", "a_revoir"))
        par_sc: dict = {}
        for e in em:
            par_sc.setdefault(e.get("sous_chapitre"), []).append(e)
        liste = []
        for rang, (sc, es) in enumerate(par_sc.items()):
            cat = E.categorie_ouverte(es, etats)
            if cat is None:
                continue
            s = scores.get((m, sc))
            s = 0.5 if s is None else s     # sous-chapitre jamais tenté : score neutre
            # vital avant important, etc., puis sous-chapitre le plus faible, puis ordre du fichier
            liste += [((E.CATEGORIES.index(cat), s, rang, e["ordre"]), e) for e in es
                      if E.categorie(e) == cat and etats[e["id"]]["etat"] == "jamais"]
        cand[m] = [e for _, e in sorted(liste, key=lambda t: t[0])]
    precedente = None
    while True:
        possibles = {m: [e for e in cand[m] if e["id"] not in ids and e["temps_min"] <= restant] for m in cand}
        possibles = {m: v for m, v in possibles.items() if v}
        if not possibles:
            break
        pool = [m for m in possibles if m != precedente] or list(possibles)
        m = max(pool, key=lambda m: (vital[m], -E.MATIERES.index(m)))
        e = possibles[m][0]
        ajouter(e, "nouveau")
        if E.categorie(e) == "vital":
            vital[m] -= e["temps_min"]
        precedente = m
    return plan


def projeter(ctx, d: dt.date, plan, jours=JOURS_PROCHES) -> list[dict]:
    """Plans des jours suivants, en supposant réussis tous les exercices déjà planifiés."""
    res = list(ctx["resultats"])
    plan_j, out = plan, []
    for k in range(1, jours + 1):
        res += [{"date": plan_j["date"], "exercice": e["id"], "resultat": "reussi"} for e, _ in plan_j["items"]]
        plan_j = plan_jour(ctx, d + dt.timedelta(k), res)
        out.append(plan_j)
    return out


# ------------------------------------------------------------------ cours
def cours_du_jour(ctx, plan) -> list[dict]:
    """Notions à lire : celles des exercices ratés récemment, sinon celles des nouveaux exercices."""
    n_max = plan["info"]["minutes_cours"] // MIN_PAR_NOTION
    d, etats = plan["date"], plan["etats"]
    rates = [e for e in plan["exos"] if etats[e["id"]]["dernier"]
             and etats[e["id"]]["dernier"][1] != "reussi"
             and (d - etats[e["id"]]["dernier"][0]).days <= JOURS_RATES]
    rates.sort(key=lambda e: etats[e["id"]]["dernier"][0], reverse=True)
    sources = rates or [e for e, g in plan["items"] if g == "nouveau"] or [e for e, _ in plan["items"]]
    vues = []
    for e in sources:
        for n in e.get("notions") or []:
            if n in ctx["notions"] and n not in vues:
                vues.append(n)
    return [ctx["notions"][n] for n in vues[:n_max]]


# ------------------------------------------------------------------ Anki
def _requete(ids) -> str:
    return " or ".join(f'"Id:{i}"' for i in ids)


def recherche_sujet(notions, couverture, cartes) -> str:
    """Recherche Anki unique : anciennes notes (nid:...) + nouvelles cartes (\"Id:...\") des notions."""
    notions = set(notions)
    nids = sorted({int(n) for k in notions for n in ((couverture or {}).get(k) or {}).get("notes") or []})
    parts = ([f"nid:{','.join(map(str, nids))}"] if nids else [])
    parts += [f'"Id:{c["id"]}"' for c in cartes if c.get("notion") in notions]
    return f"({' or '.join(parts)})" if parts else ""


def recherche_a_revoir(entrees, d) -> str:
    """Cartes existantes que le debrief a demandé de revoir ce jour (state/a_revoir.yaml, champ `pour`)."""
    du_jour = [e for e in entrees or [] if str(e.get("pour")) == str(d)]
    nids = sorted({int(e["nid"]) for e in du_jour if e.get("nid")})
    parts = ([f"nid:{','.join(map(str, nids))}"] if nids else [])
    parts += [f'"Id:{i}"' for i in dict.fromkeys(e["id"] for e in du_jour if e.get("id"))]
    return f"({' or '.join(parts)})" if parts else ""


def anki(ctx, plan) -> dict:
    """Cartes nouvelles du jour (sans jamais redonner une carte) et cartes déjà données à réviser."""
    d = str(plan["date"])
    avant = {i for k, ids in ctx["anki_plan"].items() if str(k) < d for i in ids}
    donnees = {i for k, ids in ctx["anki_plan"].items() if str(k) != d for i in ids}
    notions_jour = {n for e, _ in plan["items"] for n in e.get("notions") or []}
    notions_proches = {n for p in projeter(ctx, plan["date"], plan) for e, _ in p["items"]
                       for n in e.get("notions") or []}
    cartes = [c for c in ctx["cartes"] if c["id"] not in donnees]
    ordre = [c for c in cartes if c["notion"] in notions_jour]
    ordre += [c for c in cartes if c["notion"] in notions_proches and c["notion"] not in notions_jour]
    ids_ordre = {c["id"] for c in ordre}
    ordre += [c for c in cartes if c.get("priorite") == 1 and c["id"] not in ids_ordre]
    limite = 0 if plan["info"]["off"] else ctx["dispo"].get("cartes_par_jour", 12)
    return {
        "nouvelles": [c["id"] for c in ordre[:limite]],
        "revoir": [c["id"] for c in ctx["cartes"] if c["id"] in avant and c["notion"] in notions_jour],
    }


def enregistrer_anki(racine, ctx, d, ids):
    """Mémorise les cartes données ce jour dans state/anki_plan.yaml (une carte n'est donnée qu'une fois)."""
    ap = {str(k): v for k, v in ctx["anki_plan"].items()}
    if ids:
        ap[str(d)] = ids
    else:
        ap.pop(str(d), None)
    with open(racine / "state" / "anki_plan.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(dict(sorted(ap.items())), f, allow_unicode=True, sort_keys=False, width=200)


# ------------------------------------------------------------------ échéance
def echeance(ctx, plan) -> list[str]:
    """Minutes restantes (annales + vital + important non maîtrisés) contre la capacité jusqu'à la fin."""
    d = plan["date"]
    restant = {"annales": 0, "vital": 0, "important": 0}
    for e in plan["exos"]:
        if plan["etats"][e["id"]]["etat"] == "maitrise":
            continue
        if e.get("annale_prioritaire"):
            restant["annales"] += e["temps_min"]
        elif E.categorie(e) in ("vital", "important"):
            restant[E.categorie(e)] += e["temps_min"]
    fin = E.en_date(ctx["dispo"]["fin"])
    capacite = sum(E.jour_info(ctx["dispo"], j)["minutes_exercices"] for j in E.jours(d, fin))
    total = sum(restant.values())
    marge = capacite - total
    lignes = [f"- Restant : {total} min (annales {restant['annales']}, vital {restant['vital']}, "
              f"important {restant['important']}) ; capacité jusqu'au {fin} : {capacite} min ; marge : {marge} min."]
    if marge < 0:
        lignes.append(f"- **ALERTE** : il manque {-marge} min. Réduire le périmètre ou ajouter du temps.")
    if ctx["dispo"].get("examens_a_confirmer"):
        lignes.append(f"- Examens : semaine du {ctx['dispo']['examens']} (dates à confirmer).")
    return lignes


# ------------------------------------------------------------------ rendu
def _source(e) -> str:
    s = next((s for s in e.get("sources") or [] if s.get("fichier")), None)
    if s:
        return f"{s['fichier']} p.{s.get('page')} ({s.get('numero')})"
    s = (e.get("sources") or [{}])[0]
    return f"{s.get('etab', '?')} : {s.get('numero', '?')}"


def _court(txt, n=60) -> str:
    return txt if len(txt) <= n else txt[: n - 1] + "…"


def rediger(ctx, plan, cartes) -> list[str]:
    d, info = plan["date"], plan["info"]
    nature = info["raison"] if info["off"] else ("quota" if info["quota"] else "normal")
    L = [f"# NOW — {JOURS[d.weekday()]} {d} ({nature})", ""]
    if info["off"]:
        L.append("Aucun exercice aujourd'hui.")
    else:
        L.append(f"## Exercices ({plan['minutes']}/{info['minutes_exercices']} min)")
        for e, genre in plan["items"]:
            ligne = f"- [ ] `{e['id']}` {genre} · {_court(e['titre'])} · {e['temps_min']} min · {_source(e)}"
            if e.get("enonce") is None:
                ligne += " · **énoncé à extraire**"
            L.append(ligne)
        if not plan["items"]:
            L.append("- (rien à planifier)")
        notions = cours_du_jour(ctx, plan)
        sujet = {n["id"] for n in notions} | {n for e, _ in plan["items"] for n in e.get("notions") or []}
        L += ["", f"## Cours ({info['minutes_cours']} min)"]
        for n in notions:
            s = n.get("source") or {}
            L.append(f"- `{n['id']}` {_court(n['titre'], 50)} · {s.get('fichier')} p.{s.get('page')}")
        if not notions:
            L.append("- (aucune notion liée)")
        rech = recherche_sujet(sujet, ctx.get("couverture"), ctx["cartes"])
        L += ["", "## Anki — tout le sujet du jour"]
        L += ["```", rech, "```"] if rech else ["- (aucune carte pour ces notions)"]
        L.append("Outils → Créer un paquet filtré, coller, décocher “replanifier les cartes selon mes réponses” "
                 "pour réviser sans perturber le planning Anki.")
    L += ["", f"## Anki — à apprendre ({len(cartes['nouvelles'])} nouvelles)"]
    L += ["```", _requete(cartes["nouvelles"]), "```"] if cartes["nouvelles"] else ["- (aucune)"]
    L += ["", "## Anki — à réviser", "- Toutes les cartes dues : `is:due`"]
    if cartes["revoir"]:
        L.append(f"- Déjà données, liées aux exercices du jour ({len(cartes['revoir'])}) : `{_requete(cartes['revoir'])}`")
    rech = recherche_a_revoir(ctx.get("a_revoir"), plan["date"])
    if rech:
        L += ["- Cartes existantes à revoir, signalées au debrief (paquet filtré, “replanifier” **coché**) :",
              "```", rech, "```"]
    L += ["", "## Échéance"] + echeance(ctx, plan)
    return L


def jour(date: dt.date, racine=E.RACINE) -> list[str]:
    """Calcule le plan du jour, écrit NOW.md et mémorise les cartes Anki données."""
    ctx = contexte(racine)
    plan = plan_jour(ctx, date)
    cartes = anki(ctx, plan)
    lignes = rediger(ctx, plan, cartes)
    enregistrer_anki(racine, ctx, date, cartes["nouvelles"])
    (racine / "NOW.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return lignes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    j = sp.add_parser("jour", help="écrit NOW.md pour une date")
    j.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    a = p.parse_args()
    d = E.en_date(a.date) if a.date else dt.date.today()
    lignes = jour(d)
    print(f"NOW.md écrit pour le {d} ({len(lignes)} lignes).")
    if len(lignes) > MAX_LIGNES:
        print(f"ATTENTION : plus de {MAX_LIGNES} lignes.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
