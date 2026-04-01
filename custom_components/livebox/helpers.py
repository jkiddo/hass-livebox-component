"""Helpers functions."""

import gzip
import json
import logging
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)
_OUI_DB: dict[str, str] | None = None


def _load_oui_db() -> dict[str, str]:
    """Load the OUI database from disk (blocking, call from executor)."""
    oui_path = Path(__file__).parent / "oui.json.gz"
    if oui_path.exists():
        try:
            with gzip.open(oui_path, "rt") as f:
                return json.load(f)
        except Exception:
            _LOGGER.debug("Failed to load OUI database")
    return {}


def load_oui_db_sync() -> None:
    """Pre-load OUI database synchronously (call once at startup from executor)."""
    global _OUI_DB
    if _OUI_DB is None:
        _OUI_DB = _load_oui_db()


def lookup_mac_vendor(mac: str | None) -> str:
    """Look up the manufacturer for a MAC address using the OUI database."""
    global _OUI_DB
    if not mac:
        return ""
    if _OUI_DB is None:
        _OUI_DB = _load_oui_db()
    prefix = mac.upper().replace("-", ":")[0:8]
    return _OUI_DB.get(prefix, "")


def find_item(data: dict[str, Any], key_chain: str, default: Any = None) -> Any:
    """Get recursive key and return value.

    Parameters:
        data (dict[str, Any]) : dictionary to search
        key (str): searched string with dot for key delimited (ex: "key.key.key")
            It is possible to integrate an element of an array by indicating its index number
        default (Any): default value to return if key not found
    Returns:
        Any: value of the key or default if not found
    Example:
        >>> find_item({"a": {"b": [{"c": "value_a"},{"d": "value_b"}]}}, "a.b.0.c")
        "value_a"
        >>> find_item({"a": {"b": [{"c": "value"}]}}, "a.b.1.c", "default")
        "default"
    """
    if (keys := key_chain.split(".")) and isinstance(keys, list):
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            elif (
                isinstance(data, list)
                and len(data) > 0
                and key.isdigit()
                and int(key) < len(data)
            ):
                data = data[int(key)]
    return default if data is None and default is not None else data
