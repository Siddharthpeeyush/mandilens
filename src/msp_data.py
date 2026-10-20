#!/usr/bin/env python3
"""Curated notified Minimum Support Prices (MSP) for Marketing Season 2026-27.

Values copied exactly from the Government of India's Press Information Bureau
releases (unit: Rs per quintal):
  - Kharif crops 2026-27: PIB PRID 2260617 (posted 13 May 2026)
  - Rabi crops   2026-27: PIB PRID 2177219
MSP is notified for these 20 mandated crops; commercial crops (Jute, Copra)
come from the Rabi release's commercial-crop listing (2025 values, as published).

Important scope fact verified 2026-10-20: vegetables (Onion, Potato, Tomato)
have NO notified MSP — MSP covers only the mandated crop list below. The
function msp_for() returns None for them, which the gap analysis reports
honestly as "gap undefined" rather than inventing a comparison.
"""
from typing import Dict, Optional

# (crop name, MSP Rs/qtl, marketing season)
_KHARIF_2026_27 = [
    ("Paddy (Common)", 2441, "Kharif 2026-27"),
    ("Paddy (Grade A)", 2461, "Kharif 2026-27"),
    ("Jowar (Hybrid)", 4023, "Kharif 2026-27"),
    ("Jowar (Maldandi)", 4073, "Kharif 2026-27"),
    ("Bajra", 2900, "Kharif 2026-27"),
    ("Ragi", 5205, "Kharif 2026-27"),
    ("Maize", 2410, "Kharif 2026-27"),
    ("Tur / Arhar", 8450, "Kharif 2026-27"),
    ("Moong", 8780, "Kharif 2026-27"),
    ("Urad", 8200, "Kharif 2026-27"),
    ("Groundnut", 7517, "Kharif 2026-27"),
    ("Sunflower Seed", 8343, "Kharif 2026-27"),
    ("Soybean (Yellow)", 5708, "Kharif 2026-27"),
    ("Sesamum", 10346, "Kharif 2026-27"),
    ("Nigerseed", 10052, "Kharif 2026-27"),
    ("Cotton (Medium Staple)", 8267, "Kharif 2026-27"),
]

_RABI_2026_27 = [
    ("Wheat", 2585, "Rabi 2026-27"),
    ("Barley", 2150, "Rabi 2026-27"),
    ("Gram", 5875, "Rabi 2026-27"),
    ("Lentil (Masur)", 7000, "Rabi 2026-27"),
    ("Rapeseed & Mustard", 6200, "Rabi 2026-27"),
    ("Safflower", 6540, "Rabi 2026-27"),
]

_COMMERCIAL = [
    ("Jute", 5650, "2025 (as published in PIB commercial-crop list)"),
    ("Copra (Milling)", 11582, "2025 (as published in PIB commercial-crop list)"),
]

MSP_TABLE = _KHARIF_2026_27 + _RABI_2026_27 + _COMMERCIAL

# Normalised alias lookup: lowercased, punctuation stripped.
_ALIASES: Dict[str, str] = {}
for name, value, season in MSP_TABLE:
    key = name.lower().replace("(", "").replace(")", "").strip()
    _ALIASES[key] = name
for alias, canonical in {
    "tur": "Tur / Arhar",
    "arhar": "Tur / Arhar",
    "pigeon pea": "Tur / Arhar",
    "masur": "Lentil (Masur)",
    "lentil": "Lentil (Masur)",
    "chana": "Gram",
    "mustard": "Rapeseed & Mustard",
    "rapeseed": "Rapeseed & Mustard",
    "soyabean": "Soybean (Yellow)",
    "soybean": "Soybean (Yellow)",
    "sesame": "Sesamum",
    "til": "Sesamum",
    "wheat": "Wheat",
    "barley": "Barley",
    "gram": "Gram",
    "maize": "Maize",
    "corn": "Maize",
    "bajra": "Bajra",
    "pearl millet": "Bajra",
    "jowar": "Jowar (Hybrid)",
    "sorghum": "Jowar (Hybrid)",
    "ragi": "Ragi",
    "finger millet": "Ragi",
    "moong": "Moong",
    "green gram": "Moong",
    "urad": "Urad",
    "black gram": "Urad",
    "groundnut": "Groundnut",
    "peanut": "Groundnut",
    "sunflower": "Sunflower Seed",
    "cotton": "Cotton (Medium Staple)",
    "jute": "Jute",
    "copra": "Copra (Milling)",
}.items():
    _ALIASES[alias] = canonical

_CANONICAL = {name: (value, season) for name, value, season in MSP_TABLE}


def msp_for(commodity: str) -> Optional[tuple]:
    """Return (canonical crop name, MSP Rs/qtl, season) or None if no
    notified MSP covers this commodity."""
    key = commodity.strip().lower().replace("(", "").replace(")", "")
    canonical = _ALIASES.get(key)
    if canonical is None:
        return None
    value, season = _CANONICAL[canonical]
    return canonical, value, season


def mandated_crops() -> list:
    return list(_CANONICAL.keys())
