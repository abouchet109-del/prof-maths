"""Mesure la part de texte et d'images dans les notes exportées (inventaire/anki/notes.jsonl)."""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    notes = [json.loads(l) for l in (RACINE / "inventaire/anki/notes.jsonl").open(encoding="utf-8")]
    par_deck = defaultdict(list)
    for n in notes:
        par_deck["::".join(n["deck"].split("::")[2:4])].append(n)
    print("sous-paquet | notes | recto en texte >=15 car | verso en texte >=15 car | médias par note")
    for deck in sorted(par_deck):
        lot = par_deck[deck]
        r = sum(len(n["champs"][0]) >= 15 for n in lot)
        v = sum(len(" ".join(n["champs"][1:])) >= 15 for n in lot)
        m = sum(len(n["medias"]) for n in lot) / len(lot)
        print(f"{deck[:60]:60} | {len(lot):4} | {r:4} | {v:4} | {m:.1f}")
    random.seed(1)
    print("\nÉchantillon :")
    for deck in sorted({d.split("::")[0] for d in par_deck}):
        lot = [n for d, l in par_deck.items() if d.split("::")[0] == deck for n in l]
        for n in random.sample(lot, min(3, len(lot))):
            print(f"[{deck[:25]}] {n['modele']} | tags={n['tags'][:4]} | "
                  f"{[c[:90] for c in n['champs'][:3]]} | médias={n['medias'][:2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
