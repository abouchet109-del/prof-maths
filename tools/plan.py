"""Planificateur : `plan.py jour [--date AAAA-MM-JJ] [--racine CHEMIN]` écrit NOW.md (60 lignes au plus).

Le jour est organisé en blocs de sous-chapitre : une matière par jour (rotation), les reprises dues
toutes matières confondues (plafonnées), au plus une annale prioritaire, puis le bloc.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import yaml

import etat as E

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MAX_LIGNES = 60
MIN_PAR_NOTION = 10         # durée estimée d'une notion de cours
REPRISES_MAX_DEFAUT = 30    # minutes de reprises par jour au plus (dispo.yaml : minutes_reprises_max)
CARTES_DEFAUT = 20          # cartes nouvelles par jour au plus (dispo.yaml : cartes_par_jour)
NOMS = {"topologie": "Topologie", "mesure": "Mesure", "proba": "Probabilités", "modelisation": "Modélisation"}
PART_CAPACITE = 1.25 / len(E.MATIERES)   # part de la capacité restante au-delà de laquelle on alerte


def contexte(racine=E.RACINE) -> dict:
    """Charge toutes les données nécessaires au plan."""
    racine = Path(racine)
    return {
        "exercices": E.charger_exercices(racine),
        "resultats": E.charger_resultats(racine),
        "dispo": E.charger_yaml(racine / "state" / "dispo.yaml", {}),
        "notions": E.charger_notions(racine),
        "cartes": E.charger_cartes(racine),
        "anki_plan": E.charger_yaml(racine / "state" / "anki_plan.yaml", {}),
        "a_revoir": E.charger_yaml(racine / "state" / "a_revoir.yaml", []),
        "couverture": charger_couverture(racine),
        "blocs": E.charger_yaml(racine / "state" / "blocs.yaml", {}),
        "avancement": E.charger_yaml(racine / "state" / "avancement_cours.yaml", {}),
    }


def charger_couverture(racine=E.RACINE) -> dict:
    """notion -> {statut, notes} fusionné sur toutes les matières (matieres/<m>/couverture.yaml)."""
    res = {}
    for m in E.MATIERES:
        res.update(E.charger_yaml(Path(racine) / "matieres" / m / "couverture.yaml", {}) or {})
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


# ------------------------------------------------------- sous-chapitres et ligne principale
def exercices_par_sc(exos, m) -> dict:
    """sous-chapitre -> exercices de la matière (hors annales prioritaires), dans l'ordre du poly."""
    res: dict = {}
    for e in exos:
        if e["matiere"] == m and not e.get("annale_prioritaire"):
            res.setdefault(e.get("sous_chapitre"), []).append(e)
    return dict(sorted(res.items(), key=lambda kv: E.cle_sc(kv[0])))


def ligne_principale(es, etats) -> list[dict]:
    """Ligne principale d'un sous-chapitre : les vitaux pas encore acquis, puis les importants jamais tentés."""
    vit = [e for e in es if E.categorie(e) == "vital" and etats[e["id"]]["etat"] not in E.ACQUIS]
    imp = [e for e in es if E.categorie(e) == "important" and etats[e["id"]]["etat"] == "jamais"]
    return vit + imp


def _dans_limite(sc, limite) -> bool:
    """Avancement du cours : jamais de sous-chapitre au-delà du dernier vu en CM (None : pas de limite)."""
    return limite is None or E.cle_sc(sc) <= E.cle_sc(limite)


def sous_chapitre_courant(par_sc, etats, limite=None):
    """Premier sous-chapitre (ordre du poly) qui a encore une ligne principale à faire, sinon None."""
    for sc, es in par_sc.items():
        if _dans_limite(sc, limite) and ligne_principale(es, etats):
            return sc
    return None


def candidats_bloc(par_sc, etats, limite=None) -> list[dict]:
    """Exercices à faire pour le bloc d'une matière, dans l'ordre : à partir du sous-chapitre courant,
    sa ligne principale (jamais tentés ; les « à revoir » reviennent par les reprises), puis celle du
    suivant, etc. Une fois toute la ligne principale épuisée : secondaire et exotique, avec le
    passage de catégorie par sous-chapitre."""
    if sous_chapitre_courant(par_sc, etats, limite) is not None:
        res = []
        for sc, es in par_sc.items():
            if _dans_limite(sc, limite):
                res += sorted((e for e in ligne_principale(es, etats) if etats[e["id"]]["etat"] == "jamais"),
                              key=lambda e: (E.CATEGORIES.index(E.categorie(e)), e["ordre"]))
        return res
    res = []
    for sc, es in par_sc.items():
        if not _dans_limite(sc, limite):
            continue
        cat = E.categorie_ouverte(es, etats)
        if cat in ("secondaire", "exotique"):
            res += [e for e in es if E.categorie(e) == cat and etats[e["id"]]["etat"] == "jamais"]
    return res


def vitaux_acquis(es, etats) -> tuple[int, int]:
    vit = [e for e in es if E.categorie(e) == "vital"]
    return sum(etats[e["id"]]["etat"] in E.ACQUIS for e in vit), len(vit)


def matiere_du_jour(blocs, resultats, d: dt.date, a_planifier) -> str | None:
    """Rotation : matière suivante dans E.CYCLE après celle du dernier bloc effectivement travaillé
    (date antérieure à `d` avec au moins un résultat). On saute une matière sans rien à planifier."""
    travaillees = {E.en_date(r["date"]) for r in resultats}
    anterieurs = [(E.en_date(k), v) for k, v in (blocs or {}).items()
                  if E.en_date(k) < d and E.en_date(k) in travaillees]
    debut = 0
    if anterieurs:
        m = max(anterieurs, key=lambda t: t[0])[1].get("matiere")
        if m in E.CYCLE:
            debut = (E.CYCLE.index(m) + 1) % len(E.CYCLE)
    for k in range(len(E.CYCLE)):
        m = E.CYCLE[(debut + k) % len(E.CYCLE)]
        if a_planifier.get(m):
            return m
    return None


# ------------------------------------------------------------------ échéance (calcul)
def bilan(ctx, d: dt.date, exos, etats) -> dict:
    """Minutes restantes (annales + vital + important non maîtrisés), par matière, contre la capacité."""
    par = {m: {"annales": 0, "vital": 0, "important": 0} for m in E.MATIERES}
    for e in exos:
        if etats[e["id"]]["etat"] == "maitrise":
            continue
        if e.get("annale_prioritaire"):
            par[e["matiere"]]["annales"] += e["temps_min"]
        elif E.categorie(e) in ("vital", "important"):
            par[e["matiere"]][E.categorie(e)] += e["temps_min"]
    dispo = ctx["dispo"]
    fin = E.en_date(dispo["fin"]) if dispo.get("fin") else E.en_date(dispo["examens"]) - dt.timedelta(1)
    capacite = sum(E.jour_info(dispo, j)["minutes_exercices"] for j in E.jours(d, fin))
    total = sum(sum(v.values()) for v in par.values())
    return {"par": par, "total": total, "capacite": capacite, "marge": capacite - total, "fin": fin}


# ------------------------------------------------------------------ plan du jour
def annale_eligible(e, d: dt.date, dispo, courants, limites, marge: int) -> bool:
    """Une annale n'est éligible que si son sous-chapitre est déjà passé dans sa matière (avant le
    sous-chapitre courant), sauf à partir de `annales_libres_des` ou si la marge est négative."""
    libres = dispo.get("annales_libres_des")
    if marge < 0 or (libres and d >= E.en_date(libres)):
        return True
    m, sc = e["matiere"], e.get("sous_chapitre")
    courant = courants.get(m)
    if courant is None:        # ligne principale épuisée dans la limite du cours
        return _dans_limite(sc, limites.get(m))
    return E.cle_sc(sc) < E.cle_sc(courant)


def plan_jour(ctx, d: dt.date, resultats=None) -> dict:
    """Plan du jour : reprises, au plus une annale prioritaire, puis le bloc de la matière du jour."""
    resultats = ctx["resultats"] if resultats is None else resultats
    info = E.jour_info(ctx["dispo"], d)
    exos = [e for e in ctx["exercices"] if E.planifiable(e)]
    etats = _etats(exos, resultats, d)
    plan = {"date": d, "info": info, "items": [], "minutes": 0, "etats": etats, "exos": exos,
            "matiere": None, "sous_chapitre": None, "vitaux": None, "courants": {},
            "bilan": bilan(ctx, d, exos, etats)}
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

    limites = ctx.get("avancement") or {}
    par_sc = {m: exercices_par_sc(exos, m) for m in E.MATIERES}
    courants = {m: sous_chapitre_courant(par_sc[m], etats, limites.get(m)) for m in E.MATIERES}
    cands = {m: candidats_bloc(par_sc[m], etats, limites.get(m)) for m in E.MATIERES}
    plan["courants"] = courants

    # (a) reprises dues, toutes matières : à revoir d'abord, puis les plus en retard ; plafonnées.
    # La plus urgente passe même si elle dépasse seule le plafond (sinon elle ne serait jamais reprise).
    plafond = ctx["dispo"].get("minutes_reprises_max", REPRISES_MAX_DEFAUT)
    dus = [e for e in exos if etats[e["id"]]["est_du"]]
    dus.sort(key=lambda e: (etats[e["id"]]["etat"] != "a_revoir", etats[e["id"]]["du"], e["ordre"]))
    reprises = 0
    for e in dus:
        if reprises and reprises + e["temps_min"] > plafond:
            continue
        if ajouter(e, "reprise"):
            reprises += e["temps_min"]

    # (b) au plus une annale prioritaire jamais tentée, si son sous-chapitre est passé ;
    # la dernière année de chaque matière = examen blanc, réservé à la période quota.
    derniere = _derniere_annee(exos)

    def blanc(e):
        return bool(e.get("annale")) and _annee(e) == derniere.get(e["matiere"])

    marge = plan["bilan"]["marge"]
    annales = [e for e in exos if e.get("annale_prioritaire") and etats[e["id"]]["etat"] == "jamais"
               and annale_eligible(e, d, ctx["dispo"], courants, limites, marge)]
    if not info["quota"]:
        annales = [e for e in annales if not blanc(e)]
    # examens blancs en dernier, puis les années les plus récentes d'abord
    annales.sort(key=lambda e: (blanc(e), -int(_annee(e)[:4] or 0), e["ordre"]))
    for e in annales:
        if ajouter(e, "annale " + _annee(e)) and not info["quota"]:
            break   # hors période quota : une annale par jour au plus

    # (c) le bloc : ligne principale du sous-chapitre courant de la matière du jour, puis des suivants
    m = matiere_du_jour(ctx.get("blocs"), resultats, d, cands)
    if m:
        # un exercice qui ne tient pas est sauté, mais le bloc ne saute pas à un sous-chapitre plus loin
        butee = None
        for e in cands[m]:
            if butee is not None and E.cle_sc(e.get("sous_chapitre")) > E.cle_sc(butee):
                break
            if not ajouter(e, "bloc") and butee is None and e["id"] not in ids:
                butee = e.get("sous_chapitre")
        bloc = [e for e, g in plan["items"] if g == "bloc"]
        sc = bloc[0].get("sous_chapitre") if bloc else courants[m]
        plan["matiere"], plan["sous_chapitre"] = m, sc
        plan["vitaux"] = vitaux_acquis(par_sc[m].get(sc, []), etats)
    return plan


# ------------------------------------------------------------------ cours
def notions_sc(ctx, exos, m, sc, prioritaires=()) -> list[str]:
    """Notions d'un sous-chapitre : celles de ses exercices (les `prioritaires` d'abord, puis vital,
    important…), puis celles de notions.yaml rattachées à ce sous-chapitre."""
    es = [e for e in exos if e["matiere"] == m and e.get("sous_chapitre") == sc and not e.get("annale_prioritaire")]
    es.sort(key=lambda e: (e["id"] not in prioritaires, E.CATEGORIES.index(E.categorie(e)), e["ordre"]))
    vues = []
    for e in es:
        for n in e.get("notions") or []:
            if n not in vues:
                vues.append(n)
    for n in ctx["notions"].values():
        if n.get("matiere") != m or n["id"] in vues:
            continue
        if sc in (n.get("sous_chapitre"), f"{n.get('chapitre')} > {n.get('sous_chapitre')}"):
            vues.append(n["id"])
    return vues


def cours_du_jour(ctx, plan) -> list[dict]:
    """Notions à lire : celles du sous-chapitre du bloc, dans la limite du temps de cours."""
    if not plan["sous_chapitre"]:
        return []
    n_max = plan["info"]["minutes_cours"] // MIN_PAR_NOTION
    bloc = {e["id"] for e, g in plan["items"] if g == "bloc"}
    vues = notions_sc(ctx, plan["exos"], plan["matiere"], plan["sous_chapitre"], bloc)
    return [ctx["notions"][n] for n in vues if n in ctx["notions"]][:n_max]


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


def sc_suivants(ctx, plan) -> list[str]:
    """Sous-chapitres de la matière du bloc après celui du bloc (exercices et notions), dans la limite du cours."""
    m, sc = plan["matiere"], plan["sous_chapitre"]
    tous = set(exercices_par_sc(plan["exos"], m))
    tous |= {f"{n.get('chapitre')} > {n['sous_chapitre']}" for n in ctx["notions"].values()
             if n.get("matiere") == m and n.get("sous_chapitre") and n.get("chapitre")}
    limite = (ctx.get("avancement") or {}).get(m)
    return sorted((s for s in tous if E.cle_sc(s) > E.cle_sc(sc) and _dans_limite(s, limite)), key=E.cle_sc)


def anki(ctx, plan) -> dict:
    """Cartes nouvelles du jour (sans jamais redonner une carte) et cartes déjà données à réviser.

    Ordre : cartes d'erreurs, cartes `a_revoir` dues, cartes des notions du sous-chapitre du bloc,
    puis celles des sous-chapitres suivants de la même matière ; plafond `cartes_par_jour`."""
    d = str(plan["date"])
    avant = {i for k, ids in ctx["anki_plan"].items() if str(k) < d for i in ids}
    donnees = {i for k, ids in ctx["anki_plan"].items() if str(k) != d for i in ids}
    notions_jour = {n for e, _ in plan["items"] for n in e.get("notions") or []}
    libres = [c for c in ctx["cartes"] if c["id"] not in donnees]
    ordre = [c for c in libres if "erreur" in (c.get("tags") or [])]
    dues = {e["id"] for e in ctx.get("a_revoir") or [] if e.get("id") and str(e.get("pour")) <= d}
    ordre += [c for c in libres if c["id"] in dues]
    if plan["sous_chapitre"]:
        bloc = {e["id"] for e, g in plan["items"] if g == "bloc"}
        for sc in [plan["sous_chapitre"]] + sc_suivants(ctx, plan):
            notions = set(notions_sc(ctx, plan["exos"], plan["matiere"], sc, bloc))
            ordre += [c for c in libres if c.get("notion") in notions]
    ordre = list({c["id"]: c for c in ordre}.values())
    limite = 0 if plan["info"]["off"] else ctx["dispo"].get("cartes_par_jour", CARTES_DEFAUT)
    return {
        "nouvelles": [c["id"] for c in ordre[:limite]],
        "revoir": [c["id"] for c in ctx["cartes"] if c["id"] in avant and c["notion"] in notions_jour],
    }


def _ecrire(chemin, donnees, entete=""):
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(entete)
        yaml.safe_dump(donnees, f, allow_unicode=True, sort_keys=False, width=200)


def enregistrer_anki(racine, ctx, d, ids):
    """Mémorise les cartes données ce jour dans state/anki_plan.yaml (une carte n'est donnée qu'une fois)."""
    ap = {str(k): v for k, v in ctx["anki_plan"].items()}
    if ids:
        ap[str(d)] = ids
    else:
        ap.pop(str(d), None)
    _ecrire(Path(racine) / "state" / "anki_plan.yaml", dict(sorted(ap.items())))


def enregistrer_bloc(racine, ctx, plan):
    """Mémorise le bloc planifié dans state/blocs.yaml ({date: {matiere, sous_chapitre}})."""
    blocs = {str(k): v for k, v in (ctx.get("blocs") or {}).items()}
    if plan["matiere"]:
        blocs[str(plan["date"])] = {"matiere": plan["matiere"], "sous_chapitre": plan["sous_chapitre"]}
    else:
        blocs.pop(str(plan["date"]), None)
    _ecrire(Path(racine) / "state" / "blocs.yaml", dict(sorted(blocs.items())),
            "# Blocs planifiés par tools/plan.py : {AAAA-MM-JJ: {matiere, sous_chapitre}}.\n"
            "# La rotation des matières part du dernier bloc effectivement travaillé (résultat ce jour-là).\n")


# ------------------------------------------------------------------ échéance
def echeance(ctx, plan) -> list[str]:
    """Minutes restantes (annales + vital + important non maîtrisés), par matière, contre la capacité."""
    b = plan["bilan"]
    lignes = [f"- Restant : {b['total']} min ; capacité jusqu'au {b['fin']} : {b['capacite']} min ; "
              f"marge : {b['marge']} min."]
    part = b["capacite"] * PART_CAPACITE
    for m in E.MATIERES:
        v = b["par"][m]
        tot = sum(v.values())
        ligne = f"- {m} : {tot} min (annales {v['annales']}, vital {v['vital']}, important {v['important']})"
        if tot > part:
            ligne += f" — **dépasse sa part ({round(part)} min)**"
        lignes.append(ligne)
    if b["marge"] < 0:
        lignes.append(f"- **ALERTE** : il manque {-b['marge']} min. Réduire le périmètre ou ajouter du temps.")
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
        if plan["matiere"]:
            x, y = plan["vitaux"]
            L.append(f"Bloc du jour : {NOMS[plan['matiere']]} — {plan['sous_chapitre']} (vitaux acquis {x}/{y})")
        else:
            L.append("Bloc du jour : aucun (rien à planifier)")
        L += ["", f"## Exercices ({plan['minutes']}/{info['minutes_exercices']} min)"]
        for titre, genre in (("Reprises", "reprise"), ("Annale", "annale"), ("Bloc", "bloc")):
            groupe = [(e, g) for e, g in plan["items"] if g.split(" ")[0] == genre]
            if not groupe:
                continue
            L.append(f"### {titre} ({sum(e['temps_min'] for e, _ in groupe)} min)")
            for e, g in groupe:
                etiquette = g if genre == "annale" else ""
                ligne = f"- [ ] `{e['id']}` {etiquette + ' · ' if etiquette else ''}{_court(e['titre'])} · {e['temps_min']} min · {_source(e)}"
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
    """Calcule le plan du jour, écrit NOW.md et mémorise les cartes Anki données et le bloc."""
    racine = Path(racine)
    ctx = contexte(racine)
    plan = plan_jour(ctx, date)
    cartes = anki(ctx, plan)
    lignes = rediger(ctx, plan, cartes)
    enregistrer_anki(racine, ctx, date, cartes["nouvelles"])
    enregistrer_bloc(racine, ctx, plan)
    (racine / "NOW.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return lignes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    j = sp.add_parser("jour", help="écrit NOW.md pour une date")
    j.add_argument("--date", default=None, help="AAAA-MM-JJ (défaut : aujourd'hui)")
    j.add_argument("--racine", default=None, help="racine du dépôt (défaut : celui de l'outil)")
    a = p.parse_args()
    d = E.en_date(a.date) if a.date else dt.date.today()
    racine = Path(a.racine).resolve() if a.racine else E.RACINE
    lignes = jour(d, racine)
    print(f"NOW.md écrit pour le {d} ({len(lignes)} lignes).")
    if len(lignes) > MAX_LIGNES:
        print(f"ATTENTION : plus de {MAX_LIGNES} lignes.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
