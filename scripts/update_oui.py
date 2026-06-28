#!/usr/bin/env python3
"""Regenerate the OUI (MAC vendor) lookup table shipped with the integration.

The IEEE registry (https://standards-oui.ieee.org/oui/oui.txt) blocks automated
downloads, so we use the Wireshark `manuf` database, which aggregates the IEEE
MA-L (/24), MA-M (/28) and MA-S (/36) assignment blocks and is published for
unattended download.

The output `oui.json.gz` is a flat ``{hex_prefix: vendor}`` dict where keys are
colon-free, upper-case hex prefixes of varying length:

    * MA-L (/24) -> 6 hex chars  (e.g. "00000C")
    * MA-M (/28) -> 7 hex chars  (e.g. "0055DA0")
    * MA-S (/36) -> 9 hex chars  (e.g. "001BC5000")

This mixed-length layout lets ``lookup_mac_vendor`` do longest-prefix matching
so MA-M/MA-S assignments resolve to the correct vendor instead of colliding
with the surrounding /24 block.
"""

from __future__ import annotations

import gzip
import json
import re
import sys
import urllib.request
from pathlib import Path

MANUF_URL = "https://www.wireshark.org/download/automated/data/manuf"
OUTPUT = Path(__file__).resolve().parent.parent / "custom_components" / "livebox" / "oui.json.gz"

# /NN allocation size -> number of hex nibbles that identify the vendor.
PREFIX_NIBBLES = {24: 6, 28: 7, 36: 9}


def fetch_manuf() -> str:
    """Download the Wireshark manuf database."""
    req = urllib.request.Request(MANUF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 - trusted host
        return resp.read().decode("utf-8", errors="replace")


def parse_manuf(text: str) -> dict[str, str]:
    """Parse manuf text into a ``{hex_prefix: vendor}`` dict."""
    db: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        block = cols[0].strip()
        # Prefer the long vendor name (3rd column); fall back to the short name.
        vendor = ""
        if len(cols) >= 3 and cols[2].strip():
            vendor = cols[2].strip()
        elif len(cols) >= 2 and cols[1].strip():
            vendor = cols[1].strip()
        if not vendor:
            continue

        if "/" in block:
            addr, _, bits_s = block.partition("/")
            bits = int(bits_s)
        else:
            addr, bits = block, 24
        nibbles = PREFIX_NIBBLES.get(bits)
        if nibbles is None:
            continue
        hex_only = re.sub(r"[^0-9A-Fa-f]", "", addr).upper()
        if len(hex_only) < nibbles:
            continue
        db[hex_only[:nibbles]] = vendor
    return db


def main() -> int:
    print(f"Downloading {MANUF_URL} ...")
    text = fetch_manuf()
    db = parse_manuf(text)
    if len(db) < 30000:
        print(f"Refusing to write: only {len(db)} entries parsed (source malformed?)")
        return 1

    counts = {n: 0 for n in (6, 7, 9)}
    for k in db:
        counts[len(k)] = counts.get(len(k), 0) + 1
    print(
        f"Parsed {len(db)} entries "
        f"(/24={counts.get(6, 0)}, /28={counts.get(7, 0)}, /36={counts.get(9, 0)})"
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8") as f:
        json.dump(db, f, sort_keys=True, separators=(",", ":"))
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
