"""POC: independent verification oracle via render->OCR (different code path).
Demonstrates catching a homoglyph-evaded sensitive value that a naive byte
substring scan misses."""
from PIL import Image, ImageDraw, ImageFont
import pytesseract, unicodedata

SENSITIVE = "Ada Lovelace"

# Simulated "anonymized" output that still leaks the name via a Cyrillic 'а'
# homoglyph (U+0430) instead of ASCII 'a' (U+0061).
leaked = "Contact: Ad\u0430 Lovelace <redacted@example.invalid>"

# --- Primary textual scan (naive byte substring), the kind an author might write ---
naive_hit = SENSITIVE in leaked
print(f"[naive byte scan]      sensitive present? {naive_hit}")

# --- Normalized textual scan (the correct deterministic cross-check) ---
def fold(s):  # NFKC + strip common Cyrillic->Latin homoglyphs
    hp = {"\u0430":"a","\u0435":"e","\u043e":"o","\u0440":"p","\u0441":"c"}
    return unicodedata.normalize("NFKC", "".join(hp.get(c,c) for c in s))
norm_hit = fold(SENSITIVE) in fold(leaked)
print(f"[normalized scan]      sensitive present? {norm_hit}")

# --- Independent OCR oracle (pixels, totally different code path) ---
img = Image.new("RGB", (700, 60), "white")
d = ImageDraw.Draw(img)
d.text((8, 18), leaked, fill="black")
img.save("oracle_poc.png")
ocr = pytesseract.image_to_string(Image.open("oracle_poc.png")).strip()
ocr_hit = SENSITIVE.lower() in ocr.lower()
print(f"[OCR pixel oracle]     OCR read: {ocr!r}")
print(f"[OCR pixel oracle]     sensitive present? {ocr_hit}")
