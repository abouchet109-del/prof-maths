"""Présélectionne, pour chaque notion, les cartes Anki les plus proches, sans tokens.

Usage : python -I tools/candidats_cartes.py [N_CANDIDATS]
Écrit inventaire/anki/candidats-<matiere>.md et affiche les comptes.
Les cartes sans texte exploitable (réponse et question en image) sont comptées par paquet.
"""
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import yaml
from sklearn.feature_extraction.text import TfidfVectorizer

RACINE = Path(__file__).resolve().parents[1]
MATIERES = ["topologie", "mesure", "modelisation", "proba"]


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    sortie = RACINE / "inventaire" / "anki"
    notes = [json.loads(l) for l in (sortie / "notes.jsonl").open(encoding="utf-8")]
    notes = [x for x in notes if x["deck"].startswith("tg::Maths") and "_Doublons" not in x["deck"]]
    avec_texte, sans_texte = [], Counter()
    for x in notes:
        texte = " ".join(c for c in x["champs"][:2] if c)
        if len(texte.strip()) >= 8:
            avec_texte.append((x, texte))
        else:
            sans_texte["::".join(x["deck"].split("::")[2:4])] += 1
    print(f"Cartes comparables : {len(avec_texte)} ; sans texte exploitable : {sum(sans_texte.values())}")
    for deck, c in sans_texte.most_common(10):
        print(f"  {c:4} {deck}")

    vect = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    matrice = vect.fit_transform(normaliser(t) for _, t in avec_texte)

    for m in MATIERES:
        notions = yaml.safe_load((RACINE / "matieres" / m / "notions.yaml").read_text(encoding="utf-8"))
        requetes = vect.transform(normaliser(f"{e['titre']} {e.get('enonce') or ''}") for e in notions)
        scores = (requetes @ matrice.T).toarray()
        lignes = []
        for e, s in zip(notions, scores):
            lignes.append(f"\n## {e['id']} [{e['type']}] {e['titre']}\n{(e.get('enonce') or '').strip()}")
            for i in s.argsort()[::-1][:n]:
                x, t = avec_texte[i]
                deck = "::".join(x["deck"].split("::")[2:])
                lignes.append(f"- {s[i]:.2f} | note {x['id']} | {deck} | {' '.join(t.split())[:110]}")
        chemin = sortie / f"candidats-{m}.md"
        chemin.write_text("\n".join(lignes), encoding="utf-8")
        print(f"{m} : {len(notions)} notions, ~{chemin.stat().st_size // 3} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
