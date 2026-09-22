"""
Replaces all non-ASCII characters in Python and SQL files with ASCII equivalents.
Run from project root: python scripts/ascii_clean.py
"""
import pathlib
import re

REPLACEMENTS = [
    # Arrows and ellipsis
    ("\u2192", "->"),        # →
    ("\u2026", "..."),       # …
    # Dashes
    ("\u2014", "--"),        # — em dash
    ("\u2013", "-"),         # – en dash
    ("\u2212", "-"),         # − minus sign
    # Math
    ("\u00D7", "*"),         # × multiplication
    ("\u00B1", "+/-"),       # ±
    ("\u2248", "~"),         # ≈
    # Box drawing (banner)
    ("\u2550", "="),         # ═
    ("\u2551", "|"),         # ║
    ("\u2554", "+"),         # ╔
    ("\u2557", "+"),         # ╗
    ("\u255A", "+"),         # ╚
    ("\u255D", "+"),         # ╝
    ("\u2500", "-"),         # ─ light horizontal
    # German umlauts
    ("\u00E4", "ae"),        # ä
    ("\u00F6", "oe"),        # ö
    ("\u00FC", "ue"),        # ü
    ("\u00C4", "Ae"),        # Ä
    ("\u00D6", "Oe"),        # Ö
    ("\u00DC", "Ue"),        # Ü
    ("\u00DF", "ss"),        # ß
]

files = (
    list(pathlib.Path("python").rglob("*.py"))
    + list(pathlib.Path("sql").rglob("*.sql"))
)

changed = 0
for f in sorted(files):
    text = f.read_text(encoding="utf-8")
    new_text = text
    for src, dst in REPLACEMENTS:
        new_text = new_text.replace(src, dst)
    if new_text != text:
        f.write_text(new_text, encoding="utf-8")
        print(f"  Cleaned: {f}")
        changed += 1

print(f"\nDone. {changed}/{len(files)} files modified.")
