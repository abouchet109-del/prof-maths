"""Rend une page de PDF en PNG, à ouvrir ensuite avec l'outil Read.

Usage : python -I tools/rendre_page.py FICHIER_PDF PAGE SORTIE.png
"""
import sys

import pymupdf

doc = pymupdf.open(sys.argv[1])
doc[int(sys.argv[2]) - 1].get_pixmap(dpi=100).save(sys.argv[3])
print(sys.argv[3])
