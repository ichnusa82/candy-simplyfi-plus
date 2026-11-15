"""Client per l'API locale Candy simply-Fi."""
from __future__ import annotations

import asyncio
import logging

import aiohttp

from .crypto import decrypt_hex, find_key, flatten_status, parse_json

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=10)

# Modalità di lettura
MODE_PLAIN = "plain"      # http-read.json?encrypted=0 -> JSON in chiaro
MODE_PLAIN1 = "plain1"    # http-read.json?encrypted=1 -> JSON in chiaro (cifratura "senza chiave")
MODE_XOR = "xor"          # http-read.json?encrypted=1 -> esadecimale cifrato con chiave


class CandyError(Exception):
    """Errore generico."""


class CandyConnectionError(CandyError):
    """La macchina non risponde (spenta o fuori rete)."""


class CandyKeyError(CandyError):
    """Dati cifrati e chiave non trovata / errata, o risposta non valida."""


def _is_status(data: dict | None) -> bool:
    """True se è un JSON di stato reale (non {"response": "BAD REQUEST"} e simili)."""
    if not data:
        return False
    if set(data) == {"response"}:
        return False
    return bool(flatten_status(data))


class CandyApi:
    """Lettura stato e invio comandi."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        key: str | None = None,
        mode: str | None = None,
    ) -> None:
        self._session = session
        self.host = host
        self.key = key or None
        self.mode = mode or (MODE_XOR if self.key else None)
        self.last_raw: str | None = None

    async def _get(self, path: str) -> str:
        url = f"http://{self.host}/{path}"
        try:
            async with self._session.get(url, timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                # La macchina risponde spesso con content-type errato
                return (await resp.read()).decode("latin-1")
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            raise CandyConnectionError(f"{url}: {err}") from err

    async def async_detect(self) -> tuple[str, str | None]:
        """Capisce come leggere la macchina. Ritorna (modalità, chiave)."""
        if self.key:
            self.mode = MODE_XOR
            await self.async_get_status()  # verifica la chiave data a mano
            return self.mode, self.key

        # 1) encrypted=1: può essere JSON in chiaro oppure esadecimale cifrato
        text = await self._get("http-read.json?encrypted=1")
        self.last_raw = text
        if _is_status(parse_json(text)):
            self.mode, self.key = MODE_PLAIN1, None
            return self.mode, None
        key = find_key(text)
        if key is not None:
            self.mode, self.key = MODE_XOR, key
            return self.mode, key

        # 2) encrypted=0: JSON in chiaro
        text0 = await self._get("http-read.json?encrypted=0")
        if _is_status(parse_json(text0)):
            self.mode, self.key = MODE_PLAIN, None
            return self.mode, None

        _LOGGER.warning(
            "Candy Simply-Fi Plus: risposta non riconosciuta. encrypted=1 -> %r | encrypted=0 -> %r",
            text[:300], text0[:300],
        )
        raise CandyKeyError("Impossibile capire il formato dei dati (serve la chiave?)")

    async def async_get_status(self) -> dict[str, str]:
        """Legge lo stato attuale come dizionario piatto."""
        if self.mode is None:
            await self.async_detect()

        if self.mode == MODE_PLAIN:
            text = await self._get("http-read.json?encrypted=0")
        else:
            text = await self._get("http-read.json?encrypted=1")
            if self.mode == MODE_XOR:
                try:
                    text = decrypt_hex(text, self.key or "")
                except ValueError as err:
                    raise CandyKeyError(f"Risposta non esadecimale: {text[:120]!r}") from err

        self.last_raw = text
        data = parse_json(text)
        if not _is_status(data):
            raise CandyKeyError(f"Risposta non valida: {text[:120]!r}")
        return flatten_status(data)
