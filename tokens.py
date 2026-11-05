# tokens.py
"""Estimación de tokens.

`estimate_tokens(text)` usa tiktoken (cl100k_base) si está instalado; si no,
el fallback simple len(text) / 4. El número SIEMPRE es un estimado: rotularlo
como "~tokens" en todas las salidas.
"""

from __future__ import annotations

_encoder = None
_tiktoken_failed = False


def _get_encoder():
    """Importa tiktoken una sola vez; None si no está disponible o falla."""
    global _encoder, _tiktoken_failed
    if _encoder is not None or _tiktoken_failed:
        return _encoder
    try:
        import tiktoken
        _encoder = tiktoken.get_encoding('cl100k_base')
    except Exception:
        _tiktoken_failed = True
        _encoder = None
    return _encoder


def estimate_tokens(text: str) -> int:
    """Estima el tamaño en tokens de un texto."""
    if not text:
        return 0
    enc = _get_encoder()
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    return len(text) // 4
