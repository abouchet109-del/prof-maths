"""Copie les PDF de cours vers bibliotheque/<matiere>/<type>/ et extrait leur texte.

Usage : python -I tools/trier_sources.py DOSSIER_SOURCE

Le dossier source n'est jamais modifié. Écrit :
  - bibliotheque/<matiere>/<type>/<nom>.pdf (non versionné) ;
  - bibliotheque/_texte/<matiere>/<type>/<nom>.txt (non versionné) ;
  - inventaire/sources.csv : matière, type, fichier, origine, pages, caractères, lecture.

`lecture` indique comment l'exploiter sans gaspiller de tokens :
  texte (extraction suffisante), image (manuscrit ou scan, à lire visuellement),
  verif (doublon de contenu d'un poly : ouvert seulement en cas de doute).
"""
import csv
import shutil
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader

RACINE = Path(__file__).resolve().parents[1]

# (matière, type, nom cible, nom d'origine, lecture)
TRI = [
    ("topologie", "cours", "chap1-espaces-metriques", "Chap1Topo.pdf", "texte"),
    ("topologie", "cours", "chap2-espaces-complets", "Chap2Topo.pdf", "texte"),
    ("topologie", "cours", "chap3-espaces-compacts", "Chap3Topo.pdf", "texte"),
    ("topologie", "slides", "chap2-slides", "SlidesChap2.pdf", "verif"),
    ("topologie", "slides", "chap3-slides", "SlidesChap3.pdf", "verif"),
    ("topologie", "td", "td1", "TD1.pdf", "texte"),
    ("topologie", "td", "td2", "TD2.pdf", "texte"),
    ("topologie", "td", "td3", "TD3.pdf", "texte"),
    ("topologie", "td", "td4", "TD4.pdf", "texte"),
    ("topologie", "annales", "exam-2020-21", "ExamTopo20.pdf", "texte"),
    ("topologie", "annales", "exam-2021-22", "ExamTopo21.pdf", "texte"),
    ("topologie", "annales", "exam-2022-23", "ExamTopo22-23.pdf", "texte"),
    ("topologie", "annales", "exam-2023-24", "ExamTopo23-24.pdf", "texte"),
    ("topologie", "annales", "partiel-2020-21-corrige", "CorCC-Topo20.pdf", "texte"),
    ("topologie", "annales", "partiel-2021-22", "CC-Topo21.pdf", "texte"),
    ("topologie", "annales", "partiel-2022-23", "CC-Topo22.pdf", "texte"),
    ("topologie", "annales", "partiel-2023-24", "CC-Topo23.pdf", "texte"),
    ("topologie", "dm", "dm-2020-21", "DM_2021.pdf", "texte"),
    ("topologie", "dm", "dm-2021-22", "DM_2122.pdf", "texte"),
    ("topologie", "dm", "dm-2022-23", "DM_2223.pdf", "texte"),
    ("topologie", "dm", "dm-2023-24", "DM_2324.pdf", "texte"),

    ("mesure", "cours", "poly-mesure-integration", "Mesure_Integration.pdf", "texte"),
    ("mesure", "notes", "cm-2026-10-13", "13-10-26.pdf", "image"),
    ("mesure", "notes", "cm-2026-10-20", "CM_20-10-26.pdf", "image"),
    ("mesure", "notes", "td3-2026-10-20", "TD3_20-10-26.pdf", "image"),
    ("mesure", "td", "td1-corrige", "TD1 TMI Correction.pdf", "texte"),
    ("mesure", "td", "td2-corrige", "TD2 TMI Correction.pdf", "texte"),
    ("mesure", "td", "td3", "TD3 TMI.pdf", "texte"),
    ("mesure", "td", "td4", "TD4 TMI.pdf", "texte"),
    ("mesure", "td", "td5", "TD5 TMI.pdf", "texte"),
    ("mesure", "td", "td6", "TD6 TMI.pdf", "texte"),
    ("mesure", "td", "td7", "TD7 TMI.pdf", "texte"),
    ("mesure", "dm", "dm-facultatif-lebesgue", "DM_facultatif_construction_mesure_Lebesgue.pdf", "texte"),

    ("modelisation", "cours", "chap1-galton-watson", "Chapitre 1.pdf", "texte"),
    ("modelisation", "cours", "chap2-markov", "Chapitre 2.pdf", "texte"),
    ("modelisation", "cours", "chap3-poisson", "Chapitre 3.pdf", "texte"),
    ("modelisation", "slides", "chap2-markov-slides-57p", "Chapitre2-Chaines-de-Markov-slides-annotées (3).pdf", "verif"),
    ("modelisation", "slides", "chap2-markov-slides-40p", "Chapitre2-Chaines-de-Markov-slides-annotées.pdf", "verif"),
    ("modelisation", "notes", "note-2026-10-21", "2026-10-21-Note-17-43_annoté.pdf", "image"),
    ("modelisation", "td", "td1-galton-watson", "TD1 (1).pdf", "texte"),
    ("modelisation", "td", "td2-markov", "TD2 (2).pdf", "texte"),
    ("modelisation", "annales", "partiel-2023-24", "Partiel-2324.pdf", "texte"),
    ("modelisation", "annales", "partiel-2023-24-corrige", "Partiel-2324-Cor.pdf", "texte"),
    ("modelisation", "annales", "partiel-2025-26", "Partiel-2025-2026.pdf", "texte"),
    ("modelisation", "annales", "partiel-2025-26-corrige", "Partiel-2025-2026-Cor.pdf", "texte"),
    ("modelisation", "annales", "exam-2023-24", "Examen-2324.pdf", "texte"),
    ("modelisation", "annales", "exam-2023-24-corrige", "Examen-2324-Cor.pdf", "texte"),
    ("modelisation", "annales", "exam-2025-26", "CT-2025-2026.pdf", "texte"),
    ("modelisation", "annales", "exam-2025-26-corrige", "CT-2025-2026_Cor.pdf", "texte"),

    ("proba", "cours", "poly-probabilites-5", "poly-L3.pdf", "texte"),
    ("proba", "slides", "chap1-slides", "Proba 5 - Chapitre 1 - slides.pdf", "verif"),
    ("proba", "slides", "chap2-slides", "Proba 5 - Chapitre 2 - slides.pdf", "verif"),
    ("proba", "slides", "chap3-slides-38p", "Proba 5 - Chapitre 3 - slides.pdf", "verif"),
    ("proba", "slides", "chap3-slides-2026-54p", "Proba 5 - Chapitre 3 - 2026.pdf", "verif"),
    ("proba", "slides", "chap4-slides", "Proba 5 - Chapitre 4 - slides.pdf", "verif"),
    ("proba", "slides", "chap5-slides", "Proba 5 - Chapitre 5 - slides.pdf", "verif"),
    ("proba", "td", "td1", "TD 1.pdf", "texte"),
    ("proba", "td", "td1-corrige", "TD 1 - Correction.pdf", "texte"),
    ("proba", "td", "td2", "TD2 (1).pdf", "texte"),
    ("proba", "td", "td2-corrige", "TD2 - Correction.pdf", "texte"),
    ("proba", "td", "td3", "TD3 (1).pdf", "texte"),
    ("proba", "td", "td3-corrige", "TD 3 - Correction.pdf", "texte"),
    ("proba", "td", "td4", "TD4 (1).pdf", "texte"),
    ("proba", "tp", "tp1", "TP1.pdf", "verif"),
    ("proba", "tp", "tp1-corrige", "TP1_corr.pdf", "verif"),
    ("proba", "tp", "tp2", "TP2.pdf", "verif"),
    ("proba", "tp", "tp2-corrige", "TP2_corr.pdf", "verif"),
    ("proba", "tp", "tp3", "TP3.pdf", "verif"),
    ("proba", "tp", "manuel-r-rstudio", "Manuel R et RStudio (L2).pdf", "verif"),
    ("proba", "annales", "partiel-2024-25", "CC_2425.pdf", "texte"),
    ("proba", "annales", "partiel-2024-25-corrige", "CC_2425-Cor.pdf", "texte"),
    ("proba", "annales", "partiel-2025-26", "CC_2526.pdf", "texte"),
    ("proba", "annales", "partiel-2025-26-corrige", "CC_2526-Cor.pdf", "texte"),
    ("proba", "annales", "exam-2024-25", "Examen-2024-2025.pdf", "texte"),
    ("proba", "annales", "exam-2024-25-corrige", "Examen-2024-2025-Cor.pdf", "texte"),
    ("proba", "annales", "exam-2025-26", "Examen-2025-2026.pdf", "texte"),
    ("proba", "annales", "exam-2025-26-corrige", "Examen-2025-2026-Cor.pdf", "texte"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    source = Path(sys.argv[1])
    biblio = RACINE / "bibliotheque"
    lignes, absents, totaux = [], [], {}
    # Certains noms téléchargés sont en Unicode décomposé (é = e + accent).
    fichiers = {unicodedata.normalize("NFC", p.name): p for p in source.glob("*.pdf")}
    for matiere, typ, nom, origine, lecture in TRI:
        src = fichiers.get(unicodedata.normalize("NFC", origine))
        if src is None:
            absents.append(origine)
            continue
        cible = biblio / matiere / typ / f"{nom}.pdf"
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, cible)
        lecteur = PdfReader(str(cible))
        pages = [p.extract_text() or "" for p in lecteur.pages]
        texte = cible.parent.relative_to(biblio)
        sortie = biblio / "_texte" / texte / f"{nom}.txt"
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(
            "".join(f"\n--- page {i} ---\n{t}" for i, t in enumerate(pages, 1)),
            encoding="utf-8")
        car = sum(len(t) for t in pages)
        lignes.append([matiere, typ, nom, origine, len(pages), car, lecture])
        cle = (matiere, lecture)
        p0, c0 = totaux.get(cle, (0, 0))
        totaux[cle] = (p0 + len(pages), c0 + car)

    csv_path = RACINE / "inventaire" / "sources.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["matiere", "type", "nom", "origine", "pages", "caracteres", "lecture"])
        w.writerows(lignes)

    print(f"{len(lignes)} fichiers rangés ; absents : {absents or 'aucun'}")
    for (matiere, lecture), (p, c) in sorted(totaux.items()):
        print(f"{matiere:13} {lecture:6} {p:4} p  {c:8} car  ~{c // 3:7} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
