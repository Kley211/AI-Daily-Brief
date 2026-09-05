"""TLS context construction with an optional certifi CA bundle."""

from __future__ import annotations

import ssl


def default_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())
