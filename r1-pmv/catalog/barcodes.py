"""Explicit barcode identity; numeric-looking internal codes remain literal."""
import re
import unicodedata

from django.core.exceptions import ValidationError


BARCODE_PATTERN = re.compile(r"[A-Za-z0-9 -]+")
FORMAT_MESSAGE = "El código de barras solo puede contener letras, números, espacios o guiones."
DUPLICATE_MESSAGE = "Ya existe un producto con este código de barras."
GTIN_MESSAGE = "Ingrese un GTIN de 12 o 13 dígitos, o su representación de 14 con cero inicial, con dígito de control válido."


def normalize_literal(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", value or "").split()).casefold()


def reading_keys(value: str, barcode_type: str) -> set[str]:
    """Return every accepted scanner spelling, without inferring a GTIN type.

    Fourteen digits are accepted here only as zero-padded retail GTIN-12/13.
    A packaging indicator is never discarded. UPC-E and EAN-8 are not expanded.
    """
    if barcode_type not in {"UNCLASSIFIED", "INTERNAL", "GTIN"}:
        raise ValidationError({"barcode_type": "Seleccione un tipo de código válido."})
    raw = (value or "").strip()
    if not raw or len(raw) > 64 or not re.fullmatch(r"[A-Za-z0-9\s\-]+", raw):
        raise ValidationError({"barcode": "Ingrese un código de hasta 64 caracteres con letras, números, espacios o guiones."})
    key = normalize_literal(raw)
    if barcode_type != "GTIN":
        return {key}
    if not re.fullmatch(r"[0-9]{12,14}", key) or (len(key) == 14 and not key.startswith("0")):
        raise ValidationError({"barcode": GTIN_MESSAGE})
    checksum = sum(int(digit) * (3 if index % 2 == 0 else 1)
                   for index, digit in enumerate(reversed(key[:-1])))
    if (10 - checksum % 10) % 10 != int(key[-1]):
        raise ValidationError({"barcode": GTIN_MESSAGE})
    canonical = key.zfill(14)
    keys = {canonical, canonical[1:]}
    if canonical.startswith("00"):
        keys.add(canonical[2:])
    return keys
