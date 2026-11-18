"""Pilote Anki par AnkiConnect (http://127.0.0.1:8765, version 6) ; bibliothèque standard seulement.

Usage (depuis la racine du projet, Anki ouvert avec AnkiConnect pour tout sauf --dry-run) :
    python tools/anki_connect.py importer PAQUET.apkg [PAQUET.apkg ...]
    python tools/anki_connect.py fusionner [--dry-run] [--prerequis]
    python tools/anki_connect.py ranger [--dry-run]
    python tools/anki_connect.py annuler anki/export/fusion-AAAA-MM-JJ.csv

`ranger` (09/11/2026) met les cartes posées directement dans un paquet de chapitre L3 dans son sous-paquet
`::Cours` (les exercices sont déjà dans `::Exercices`), pour réviser le cours seul. Le sous-paquet reprend
les options du chapitre. Les cartes dans un paquet filtré sont laissées (relancer après l'avoir vidé).
Même fichier d'annulation que `fusionner` (`anki/export/ranger-AAAA-MM-JJ.csv`), même commande `annuler`.

`fusionner` range les notes des paquets `tg::Maths::AoutLicenceMath::*` dans le paquet L3, selon les
chapitres de Paris Cité. Changer une carte de paquet garde son historique de révision. Aucun paquet n'est
supprimé, même vide. Avant toute modification, un fichier d'annulation (carte ; ancien paquet ; nouveau
paquet) est écrit dans `anki/export/` ; `annuler` remet chaque carte dans son ancien paquet.

Rattachement d'une note (fonction pure `cible`) :
  - ses notions sont celles de `matieres/*/couverture.yaml` qui la citent ; leur chapitre est celui de
    `notions.yaml`, donc le même que celui des cartes de cours ;
  - on garde les notions de la matière de l'ancien paquet (TH mesure -> mesure, Topologie -> topologie) ;
    plusieurs chapitres : le premier dans l'ordre du poly ;
  - une note d'un paquet TD rattachable va dans le sous-paquet `::Exercices` du chapitre ;
  - sinon, `inventaire/anki/rattachement_ancien.yaml` (rangement par lot des notes absentes de la couverture,
    d'après leur recto) : `nid: chapitre`, ou `nid: {chapitre: ..., exercices: true}` pour un paquet TD ;
  - sinon (valeur `null` : hors de tous les chapitres de la matière) :
    `tg::Maths::L3 Paris Cité::<Matière>::Autres (AoutLicenceMath)`.

`--prerequis` (fonction pure `cible_fusion`) : traite aussi les notes citées dans `couverture.yaml` par une
notion `type: prerequis`, quel que soit leur paquet source (Mathématiques DD centrale, AoutLicenceMath d'une
autre matière…) : elles vont dans le paquet du chapitre du prérequis, sauf si la couverture les rattache déjà
à un chapitre de la matière de leur ancien paquet AoutLicenceMath. Une note des paquets ECG
(`tg::Maths::1ere année`, `tg::Maths::2ere année ECG`) ne bouge jamais.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import anki as A  # noqa: E402
import etat as E  # noqa: E402

RACINE = E.RACINE
URL = "http://127.0.0.1:8765"
VERSION = 6
PREFIXE = "tg::Maths::AoutLicenceMath"
ETIQUETTE = "AoutLicenceMath"
AUTRES = "Autres (AoutLicenceMath)"
MATIERE_ANCIEN = {"TH mesure": "mesure", "Topologie": "topologie"}   # 2e segment après le préfixe
# Référentiel de l'utilisateur : jamais déplacé. Le paquet de 2e année s'appelle « 2ere année ECG » dans Anki
# (vérifié le 18/11/2026) ; l'ancien nom documenté est gardé par prudence.
ECG = ("tg::Maths::1ere année", "tg::Maths::2ere année ECG", "tg::Maths::Cours deuxième année")
EN_TETE = ["carte", "ancien", "nouveau"]
RATTACHEMENT = Path("inventaire") / "anki" / "rattachement_ancien.yaml"


# ------------------------------------------------------------------ AnkiConnect
# 12/11/2026 : une carte vue une fois puis « À revoir » reste en apprentissage (is:learn) : pas encore apprise.
PAS_APPRISE = "(is:new or (is:learn -is:review)) -is:suspended"   # suspendue : écartée (tri du 17/11/2026)


class ErreurAnki(Exception):
    """AnkiConnect injoignable ou en erreur (la ligne de commande la transforme en message d'arrêt)."""


def appel(action: str, *, delai: float = 60, **params):
    requete = json.dumps({"action": action, "version": VERSION, "params": params}).encode("utf-8")
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, requete), timeout=delai) as r:
            reponse = json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError) as ex:
        raise ErreurAnki(f"AnkiConnect injoignable sur {URL} (Anki ouvert ? extension installée ?) : {ex}")
    if reponse.get("error"):
        raise ErreurAnki(f"AnkiConnect, {action} : {reponse['error']}")
    return reponse["result"]


class ClientAnki:
    """Lecture seule dans Anki, pour le plan : quelles cartes sont encore « nouvelles » (`is:new`).

    Même interface que le faux client des tests : disponible(), ids_nouveaux(ids), nids_nouveaux(nids),
    nids_a_apprendre(nids, donnees).
    Ne modifie jamais Anki."""
    LOT = 40

    def disponible(self) -> bool:
        try:
            appel("version", delai=1.5)
            return True
        except ErreurAnki:
            return False

    def ids_nouveaux(self, ids) -> set[str]:
        """Parmi les ids de cartes du système, ceux dont la carte est encore nouvelle dans Anki."""
        res: set[str] = set()
        ids = list(ids)
        for k in range(0, len(ids), self.LOT):
            requete = " or ".join(f'"Id:{i}"' for i in ids[k:k + self.LOT])
            notes = appel("findNotes", query=f"({requete}) {PAS_APPRISE}", delai=20)
            if notes:
                res |= {n["fields"]["Id"]["value"] for n in appel("notesInfo", notes=notes, delai=20)}
        return res

    def nids_nouveaux(self, nids) -> set[int]:
        """Parmi ces notes (anciennes cartes), celles qui ont encore une carte nouvelle."""
        res: set[int] = set()
        nids = list(nids)
        for k in range(0, len(nids), 200):
            res |= set(appel("findNotes", query=f"nid:{','.join(map(str, nids[k:k + 200]))} {PAS_APPRISE}", delai=20))
        return res

    def nids_a_apprendre(self, nids, donnees=None) -> set[int]:
        """Anciennes notes encore à apprendre (règle du 18/11/2026 : seul ECG dit ce que l'utilisateur sait).

        Une note ECG suit Anki (`nids_nouveaux`). Une note hors ECG (AoutLicenceMath, Centrale, …) déjà apprise
        dans Anki compte comme jamais faite tant qu'elle n'a pas été revue (journal de révision d'Anki) le jour
        où le plan l'a donnée ou après : `donnees` = {nid: premier jour donné, AAAA-MM-JJ}. Suspendue : écartée."""
        nids = [int(n) for n in nids]
        res = self.nids_nouveaux(nids)
        reste = [n for n in nids if n not in res]
        if not reste:
            return res
        sauf_ecg = " ".join(f'-"deck:{p}"' for p in ECG)          # deck: inclut les sous-paquets
        hors: set[int] = set()
        for k in range(0, len(reste), 200):
            hors |= set(appel("findNotes", query=f"nid:{','.join(map(str, reste[k:k + 200]))} -is:suspended {sauf_ecg}",
                              delai=20))
        return res | (hors - self.nids_revus_depuis(hors, donnees or {}))

    def nids_revus_depuis(self, nids, donnees) -> set[int]:
        """Notes dont une carte a une révision dans Anki le jour `donnees[nid]` ou après (lecture seule)."""
        nids = [n for n in nids if n in donnees]
        if not nids:
            return set()
        cartes = []
        for k in range(0, len(nids), 200):
            cartes += appel("findCards", query=f"nid:{','.join(map(str, nids[k:k + 200]))}", delai=20)
        note = {c["cardId"]: c["note"] for c in appel("cardsInfo", cards=cartes, delai=60)}
        revus: set[int] = set()
        for k in range(0, len(cartes), 200):
            journal = appel("getReviewsOfCards", cards=[str(c) for c in cartes[k:k + 200]], delai=60)
            for cid, revs in journal.items():
                n = note.get(int(cid))
                debut = dt.datetime.combine(dt.date.fromisoformat(str(donnees[n])), dt.time()).timestamp() * 1000
                if any(r["id"] >= debut for r in revs):
                    revus.add(n)
        return revus


# ------------------------------------------------------------------ rattachement (pur)
def matiere_ancien(deck: str) -> str | None:
    """Matière d'un ancien paquet `tg::Maths::AoutLicenceMath::<TH mesure|Topologie>::...`."""
    morceaux = deck.split("::")
    return MATIERE_ANCIEN.get(morceaux[3]) if deck.startswith(PREFIXE + "::") and len(morceaux) > 3 else None


def est_td(deck: str) -> bool:
    return bool(re.fullmatch(r"TD\d+", deck.split("::")[-1]))


def cible(deck: str, rattaches, ancien=None) -> tuple[str | None, str]:
    """(paquet cible, motif) d'une note de l'ancien paquet `deck`.

    `rattaches` : [(matière, chapitre)] des notions qui citent la note (couverture.yaml).
    `ancien` : (matière, chapitre, exercices) lu dans rattachement_ancien.yaml, ou None ; utilisé seulement
    si la couverture ne donne aucun chapitre dans la matière de l'ancien paquet.
    Motifs : rattache, ambigu (plusieurs chapitres, on prend le premier du poly), classe (rattachement par
    lot), autre_matiere (seules des notions d'une autre matière : va dans « Autres »), sans_rattachement,
    matiere_inconnue (cible None : la note ne bouge pas)."""
    m = matiere_ancien(deck)
    if m is None:
        return None, "matiere_inconnue"
    memes = sorted({r for r in rattaches if r[0] == m}, key=lambda r: E.cle_sc(r[1]))
    if not memes and ancien and ancien[0] == m:
        return A.nom_paquet(m, ancien[1], exercice=est_td(deck) or bool(ancien[2])), "classe"
    autres = f"tg::Maths::L3 Paris Cité::{A.MATIERES[m]}::{AUTRES}"
    if not memes:
        return autres, ("autre_matiere" if rattaches else "sans_rattachement")
    paquet = A.nom_paquet(m, memes[0][1], exercice=est_td(deck))
    return paquet, ("ambigu" if len({r[1] for r in memes}) > 1 else "rattache")


def est_ecg(deck: str) -> bool:
    """Paquets ECG (1ère et 2e année) : ce que l'utilisateur sait ; aucune de leurs notes ne bouge."""
    return any(deck == p or deck.startswith(p + "::") for p in ECG)


def cible_prerequis(deck: str, prereq) -> tuple[str | None, str]:
    """(paquet cible, motif) d'une note citée par des notions prérequis, quel que soit son paquet source.
    `prereq` : [(matière, chapitre)] de ces notions ; plusieurs : la première matière puis l'ordre du poly.
    Motifs : ecg (jamais déplacée), sans_prerequis (cible None), prerequis."""
    if est_ecg(deck):
        return None, "ecg"
    if not prereq:
        return None, "sans_prerequis"
    m, chapitre = sorted(set(prereq), key=lambda r: (E.MATIERES.index(r[0]), E.cle_sc(r[1])))[0]
    return A.nom_paquet(m, chapitre), "prerequis"


def cible_fusion(deck: str, rattaches, ancien=None, prereq=None) -> tuple[str | None, str]:
    """`cible`, plus l'option --prerequis : une note ECG ne bouge jamais ; une note citée par un prérequis
    (`prereq` non vide) va dans le chapitre du prérequis, sauf si la couverture la rattache déjà à un chapitre
    de la matière de son ancien paquet AoutLicenceMath (motifs rattache, ambigu)."""
    if est_ecg(deck):
        return None, "ecg"
    paquet, motif = cible(deck, rattaches, ancien)
    if prereq and motif not in ("rattache", "ambigu"):
        return cible_prerequis(deck, prereq)
    return paquet, motif


def _cle_nom(chapitre: str) -> str:
    return re.sub(r"[\$\^\{}]", "", chapitre)


def noms_chapitres(racine=RACINE) -> dict[str, tuple[str, str]]:
    """nom normalisé -> (matière, nom de chapitre) ; les noms des cartes de cours priment sur ceux de
    notions.yaml (« Espaces Lp » et non « Espaces $L^p$ »), car c'est leur paquet qui existe."""
    racine = Path(racine)
    res: dict[str, tuple[str, str]] = {}
    for n in E.charger_notions(racine).values():
        if n.get("chapitre"):
            res[_cle_nom(n["chapitre"])] = (n["matiere"], n["chapitre"])
    for c in E.charger_cartes(racine):
        if c.get("chapitre"):
            res[_cle_nom(c["chapitre"])] = (c["matiere"], c["chapitre"])
    return res


def index_notes(racine=RACINE, prerequis_seuls: bool = False) -> dict[int, list[tuple[str, str]]]:
    """nid -> [(matière, chapitre)] : couverture.yaml (nid -> notion) puis notions.yaml (notion -> chapitre).
    `prerequis_seuls` : seulement les notions `type: prerequis`."""
    racine = Path(racine)
    notions = E.charger_notions(racine)
    noms = noms_chapitres(racine)
    res: dict[int, list] = defaultdict(list)
    for m in E.MATIERES:
        for k, v in (E.charger_yaml(racine / "matieres" / m / "couverture.yaml", {}) or {}).items():
            n = notions.get(k)
            if not n or not n.get("chapitre"):
                continue
            if prerequis_seuls and n.get("type") != "prerequis":
                continue
            chapitre = noms[_cle_nom(n["chapitre"])][1]
            for nid in (v or {}).get("notes") or []:
                res[int(nid)].append((n["matiere"], chapitre))
    return res


def charger_ancien(racine=RACINE) -> dict[int, tuple[str, str, bool]]:
    """nid -> (matière, chapitre, exercices) lu dans inventaire/anki/rattachement_ancien.yaml (absent : {}).
    Les valeurs null (hors poly) sont ignorées ; un chapitre inconnu des cours est une erreur."""
    donnees = E.charger_yaml(Path(racine) / RATTACHEMENT, {}) or {}
    noms = noms_chapitres(racine)
    res = {}
    for nid, v in donnees.items():
        if v is None:
            continue
        chapitre, exo = (v, False) if isinstance(v, str) else (v["chapitre"], bool(v.get("exercices")))
        if _cle_nom(chapitre) not in noms:
            raise SystemExit(f"{RATTACHEMENT} : chapitre inconnu pour {nid} ({chapitre})")
        matiere, nom = noms[_cle_nom(chapitre)]
        res[int(nid)] = (matiere, nom, exo)
    return res


# ------------------------------------------------------------------ fusion
def notes_hors_ligne(racine=RACINE, prereq=None) -> list[tuple[int, str, str]]:
    """(nid, ancien paquet, premier champ) lus dans l'instantané inventaire/anki/notes.jsonl : les notes
    AoutLicenceMath, plus (option --prerequis) celles citées par un prérequis (`prereq` : nid -> ...)."""
    res = []
    for ligne in (Path(racine) / "inventaire" / "anki" / "notes.jsonl").read_text(encoding="utf-8").splitlines():
        n = json.loads(ligne)
        if n["deck"].startswith(PREFIXE) or int(n["id"]) in (prereq or {}):
            res.append((int(n["id"]), n["deck"], (n.get("champs") or [""])[0]))
    return res


def plan_fusion(notes, index, ancien=None, prereq=None) -> dict[int, tuple[str | None, str]]:
    ancien, prereq = ancien or {}, prereq or {}
    return {nid: cible_fusion(deck, index.get(nid, []), ancien.get(nid), prereq.get(nid)) for nid, deck, _ in notes}


def bougent(plan) -> int:
    """Notes réellement déplacées par `fusionner` (les « hors poly » restent dans leur ancien paquet)."""
    return sum(1 for c, m in plan.values() if c and m != "sans_rattachement")


def resume(notes, plan, index) -> list[str]:
    L = []
    par_cible = Counter(c for c, _ in plan.values() if c)
    L.append(f"{len(notes)} notes examinées ({sum(d.startswith(PREFIXE) for _, d, _ in notes)} dans {PREFIXE})")
    L.append(f"Notes qui bougeraient : {bougent(plan)}, dont {sum(m == 'prerequis' for _, m in plan.values())} "
             f"par --prerequis ; notes ECG laissées en place : {sum(m == 'ecg' for _, m in plan.values())}")
    for paquet, n in sorted(par_cible.items()):
        L.append(f"  {n:4} {paquet}")
    motifs = Counter(m for _, m in plan.values())
    L.append("Motifs : " + ", ".join(f"{m} {n}" for m, n in sorted(motifs.items())))
    for motif, titre in (("ambigu", "Rattachements ambigus (plusieurs chapitres, le premier du poly est retenu)"),
                         ("autre_matiere", "Notions d'une autre matière seulement (rangées dans « Autres »)"),
                         ("matiere_inconnue", "Matière de l'ancien paquet inconnue (note non déplacée)"),
                         ("prerequis", "Notes citées par un prérequis (--prerequis)"),
                         ("ecg", "Notes des paquets ECG (jamais déplacées)")):
        lignes = [(nid, d, f) for nid, d, f in notes if plan[nid][1] == motif]
        if lignes:
            L.append(f"{titre} : {len(lignes)}")
            for nid, d, f in lignes:
                chap = sorted({c for _, c in index.get(nid, [])}, key=E.cle_sc)
                L.append(f"  {nid} [{d.split('::', 3)[-1]}] {_propre(f)} -> {', '.join(chap) or '-'}")
    sans = [(nid, d, f) for nid, d, f in notes if plan[nid][1] == "sans_rattachement"]
    par_ancien = Counter(d.split("::", 3)[-1] for _, d, _ in sans)
    L.append(f"Hors de tous les chapitres (rangées dans « Autres ») : {len(sans)}")
    for d, n in sorted(par_ancien.items()):
        L.append(f"  {n:4} {d}")
    return L


def _propre(texte: str, n: int = 70) -> str:
    texte = html.unescape(re.sub(r"<[^>]+>", " ", texte or ""))
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte if len(texte) <= n else texte[: n - 1] + "…"


def chemin_annulation(racine=RACINE, prefixe: str = "fusion") -> Path:
    dossier = Path(racine) / "anki" / "export"
    dossier.mkdir(parents=True, exist_ok=True)
    jour = dt.date.today().isoformat()
    p, k = dossier / f"{prefixe}-{jour}.csv", 1
    while p.exists():
        k += 1
        p = dossier / f"{prefixe}-{jour}-{k}.csv"
    return p


def fusionner(dry_run: bool, racine=RACINE, prerequis: bool = False) -> int:
    index = index_notes(racine)
    ancien = charger_ancien(racine)
    prereq = index_notes(racine, prerequis_seuls=True) if prerequis else {}
    if dry_run:
        notes = notes_hors_ligne(racine, prereq)
        plan = plan_fusion(notes, index, ancien, prereq)
        print("\n".join(resume(notes, plan, index)))
        print("[dry-run] hors ligne depuis notes.jsonl, rien n'a été modifié")
        return 0

    nids = appel("findNotes", query=f'"deck:{PREFIXE}"')
    if prereq:
        nids = sorted(set(nids) | set(appel("findNotes", query="nid:" + ",".join(map(str, sorted(prereq))))))
    infos = appel("notesInfo", notes=nids)
    cartes = {c["cardId"]: c for c in appel("cardsInfo", cards=[c for i in infos for c in i["cards"]])}
    deplacements = []     # (carte, ancien, nouveau)
    notes_ciblees: dict[str, list[int]] = defaultdict(list)
    notes = []
    for i in infos:
        toutes = [cartes[c] for c in i["cards"]]
        if any(est_ecg(c["deckName"]) for c in toutes):
            continue                                  # une note ECG ne bouge jamais, même citée par un prérequis
        anciens = [c for c in toutes if c["deckName"].startswith(PREFIXE)]
        if not anciens and i["noteId"] in prereq:
            anciens = [c for c in toutes if not c["deckName"].startswith("tg::Maths::L3 Paris Cité")]
        if not anciens:
            continue
        deck = anciens[0]["deckName"]
        premier = next(iter(i["fields"].values()))["value"] if i.get("fields") else ""
        notes.append((i["noteId"], deck, premier))
        paquet, motif = cible_fusion(deck, index.get(i["noteId"], []), ancien.get(i["noteId"]), prereq.get(i["noteId"]))
        # Hors poly (chapitres pas encore vus) : l'utilisateur veut les laisser dans l'ancien paquet (08/11/2026).
        if paquet is None or motif == "sans_rattachement":
            continue
        if deck.startswith(PREFIXE):
            notes_ciblees[paquet].append(i["noteId"])     # étiquette AoutLicenceMath : seulement ses notes
        deplacements += [(c["cardId"], c["deckName"], paquet) for c in anciens]
    plan = plan_fusion(notes, index, ancien, prereq)
    print("\n".join(resume(notes, plan, index)))
    if not deplacements:
        print("Rien à déplacer.")
        return 0

    annulation = chemin_annulation(racine)
    with annulation.open("w", encoding="utf-8", newline="") as f:      # écrit AVANT toute modification
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(EN_TETE)
        w.writerows(deplacements)
    print(f"Fichier d'annulation : {annulation.as_posix()}")

    par_paquet: dict[str, list[int]] = defaultdict(list)
    for carte, _, nouveau in deplacements:
        par_paquet[nouveau].append(carte)
    for paquet, ids in sorted(par_paquet.items()):
        appel("createDeck", deck=paquet)
        appel("changeDeck", cards=ids, deck=paquet)
    if notes_ciblees:
        appel("addTags", notes=[n for ids in notes_ciblees.values() for n in ids], tags=ETIQUETTE)
    print(f"{len(deplacements)} cartes déplacées dans {len(par_paquet)} paquets, étiquette « {ETIQUETTE} » ajoutée. "
          f"Aucun paquet supprimé.")
    return 0


L3 = "tg::Maths::L3 Paris Cité"
SOUS_PAQUETS = ("Cours", "Exercices")


def plan_rangement(cartes) -> tuple[list[tuple[int, str, str]], int]:
    """([(carte, paquet du chapitre, sous-paquet ::Cours)], cartes dans un paquet filtré) pour les cartes
    `(id, paquet)` trouvées sous L3. Seules bougent celles posées directement dans un paquet de chapitre
    `L3::<Matière>::<Chapitre>` ; celles d'un sous-paquet (`::Cours`, `::Exercices`) ne bougent pas."""
    deplacements, filtrees = [], 0
    for carte, deck in cartes:
        if not deck.startswith(L3 + "::"):
            filtrees += 1                       # `deck:` trouve aussi une carte prêtée à un paquet filtré
            continue
        morceaux = deck.split("::")
        if len(morceaux) == len(L3.split("::")) + 2 and morceaux[-1] not in SOUS_PAQUETS:
            deplacements.append((carte, deck, deck + "::Cours"))
    return deplacements, filtrees


def ranger(dry_run: bool, racine=RACINE) -> int:
    ids = appel("findCards", query=f'"deck:{L3}"')
    infos = appel("cardsInfo", cards=ids) if ids else []
    deplacements, filtrees = plan_rangement((c["cardId"], c["deckName"]) for c in infos)
    par_chapitre = Counter(ancien for _, ancien, _ in deplacements)
    for deck, n in sorted(par_chapitre.items()):
        print(f"  {n:4} {deck[len(L3) + 2:]} -> ::Cours")
    print(f"{len(deplacements)} cartes de cours dans {len(par_chapitre)} chapitres"
          + (f" ; {filtrees} cartes dans un paquet filtré, laissées (relancer après l'avoir vidé)" if filtrees else ""))
    if dry_run or not deplacements:
        print("[dry-run] rien n'a été modifié" if dry_run else "Rien à déplacer.")
        return 0
    annulation = chemin_annulation(racine, "ranger")
    with annulation.open("w", encoding="utf-8", newline="") as f:      # écrit AVANT toute modification
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(EN_TETE)
        w.writerows(deplacements)
    print(f"Fichier d'annulation : {annulation.as_posix()}")
    for deck in sorted(par_chapitre):
        cours = deck + "::Cours"
        appel("createDeck", deck=cours)
        options = appel("getDeckConfig", deck=deck)
        if options and options.get("id") is not None:
            appel("setDeckConfigId", decks=[cours], configId=options["id"])     # mêmes options que le chapitre
        appel("changeDeck", cards=[c for c, ancien, _ in deplacements if ancien == deck], deck=cours)
    print(f"{len(deplacements)} cartes rangées dans {len(par_chapitre)} sous-paquets « Cours ». Aucun paquet supprimé.")
    return 0


def annuler(fichier: str) -> int:
    with open(fichier, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    par_ancien: dict[str, list[int]] = defaultdict(list)
    for r in lignes:
        par_ancien[r["ancien"]].append(int(r["carte"]))
    for paquet, ids in sorted(par_ancien.items()):
        appel("createDeck", deck=paquet)          # sans effet si le paquet existe
        appel("changeDeck", cards=ids, deck=paquet)
    print(f"{len(lignes)} cartes remises dans {len(par_ancien)} anciens paquets. "
          f"L'étiquette « {ETIQUETTE} » reste sur les notes (à retirer à la main si besoin).")
    return 0


def importer(paquets: list[str]) -> int:
    for p in paquets:
        chemin = Path(p).resolve()
        if not chemin.exists():
            raise SystemExit(f"Introuvable : {chemin}")
        ok = appel("importPackage", path=str(chemin))
        print(f"{'importé' if ok else 'ÉCHEC'} : {chemin.as_posix()}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("importer").add_argument("paquets", nargs="+")
    f = sp.add_parser("fusionner")
    f.add_argument("--dry-run", action="store_true")
    f.add_argument("--prerequis", action="store_true",
                   help="ranger aussi les notes citées par un prérequis L1-L2 (jamais une note ECG)")
    sp.add_parser("ranger").add_argument("--dry-run", action="store_true")
    sp.add_parser("annuler").add_argument("fichier")
    a = p.parse_args()
    try:
        if a.cmd == "importer":
            return importer(a.paquets)
        if a.cmd == "fusionner":
            return fusionner(a.dry_run, prerequis=a.prerequis)
        if a.cmd == "ranger":
            return ranger(a.dry_run)
        return annuler(a.fichier)
    except ErreurAnki as ex:
        raise SystemExit(str(ex))


if __name__ == "__main__":
    sys.exit(main())
