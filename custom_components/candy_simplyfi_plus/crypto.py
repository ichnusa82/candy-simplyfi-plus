"""Cifratura XOR usata dai dispositivi Candy simply-Fi (nessuna dipendenza esterna)."""
from __future__ import annotations

import json
import string

KEY_LENGTH = 16

# Caratteri che possono comparire nel JSON restituito dalla macchina
_ALLOWED = set(
    (string.ascii_letters + string.digits + '{}[]":,._-+/ \t\r\n').encode()
)
# Le chiavi Candy sono alfanumeriche
_KEY_CHARS = (string.ascii_letters + string.digits).encode()
_STATUS_NAMES = ("statusDWash", "statusLavatrice", "statusForno", "statusTD", "statusAsciugatrice")


def xor(data: bytes, key: bytes) -> bytes:
    """XOR ciclico di data con key."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def decrypt_hex(hex_text: str, key: str) -> str:
    """Decifra la risposta esadecimale della macchina."""
    raw = bytes.fromhex(hex_text.strip())
    return xor(raw, key.encode()).decode("latin-1")


def encrypt_hex(plain: str, key: str) -> str:
    """Cifra una stringa e la restituisce in esadecimale (per http-write)."""
    return xor(plain.encode(), key.encode()).hex()


def parse_json(text: str) -> dict | None:
    """Prova a interpretare il testo come JSON, tollerando caratteri di controllo."""
    text = text.strip().rstrip("\x00")
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text, strict=False)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def find_key(hex_text: str, length: int = KEY_LENGTH) -> str | None:
    """Ricava la chiave XOR dalla risposta cifrata (analisi per colonna).

    Per ogni posizione della chiave sceglie il carattere che rende "JSON
    plausibile" il maggior numero di byte; poi verifica che il risultato
    sia JSON valido.
    """
    try:
        cipher = bytes.fromhex(hex_text.strip())
    except ValueError:
        return None
    if len(cipher) < length * 4:
        return None

    # 1) Testo iniziale noto: la risposta comincia sempre con {"statusXXX":{
    for name in _STATUS_NAMES:
        for prefix in (
            '{"%s":{"' % name,
            '{\n\t"%s":{\n\t\t"' % name,
            '{\n"%s":{\n"' % name,
            '{\r\n\t"%s":{\r\n\t\t"' % name,
            '{ "%s": { "' % name,
        ):
            known = prefix.encode()
            if len(known) < length:
                continue
            candidate_b = bytes(cipher[i] ^ known[i] for i in range(length))
            if not all(c in _KEY_CHARS for c in candidate_b):
                continue
            candidate = candidate_b.decode()
            if parse_json(decrypt_hex(hex_text, candidate)) is not None:
                return candidate

    # 2) Analisi statistica per colonna
    key = bytearray()
    for pos in range(length):
        column = cipher[pos::length]
        best = max(
            _KEY_CHARS, key=lambda k: sum((c ^ k) in _ALLOWED for c in column)
        )
        key.append(best)

    candidate = key.decode()
    if parse_json(decrypt_hex(hex_text, candidate)) is not None:
        return candidate
    return None


def flatten_status(data: dict) -> dict[str, str]:
    """{"statusDWash": {...}} -> {...}; valori convertiti in stringa."""
    if len(data) == 1:
        inner = next(iter(data.values()))
        if isinstance(inner, dict):
            data = inner
    return {str(k): str(v).strip() for k, v in data.items() if not isinstance(v, (dict, list))}
