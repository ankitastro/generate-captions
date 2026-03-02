"""
Utility functions for formatting and data transformation
"""

from typing import Any, Dict
from models import PlanetPosition, LagnaInfo


def deg_to_dms_str(deg: float) -> str:
    """
    Convert decimal degrees to DMS (degrees, minutes, seconds) format string

    Args:
        deg: Decimal degrees (can be negative)

    Returns:
        DMS format string like "15°30′45″"
    """
    d = int(deg)
    m_float = abs(deg - d) * 60.0
    m = int(m_float)
    s = round((m_float - m) * 60.0)

    # Handle rollover (59m 60s -> +1m etc.)
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        if deg >= 0:
            d += 1
        else:
            d -= 1

    sign_char = ""  # We report signed by numeric sign outside, not prefix
    return f"{sign_char}{d}°{m:02d}′{s:02d}″"


def _augment_planet_positions(planets):
    """
    Accepts list[PlanetPosition] or list[dict].
    Returns list of dicts with added 'degree_dms' & 'full_degree' (sign+deg).
    """
    out = []
    for p in planets:
        if isinstance(p, PlanetPosition):
            planet = p.planet
            sign = p.sign
            deg = p.degree
            retro = p.retrograde
            house = p.house
            sign_lord = p.sign_lord
            nakshatra_lord = p.nakshatra_lord
            nakshatra_name = p.nakshatra_name
            planet_awasta = p.planet_awasta
            status = p.status
        else:
            planet = p["planet"]
            sign = p["sign"]
            deg = p["degree"]
            retro = p["retrograde"]
            house = p["house"]
            sign_lord = p["sign_lord"]
            nakshatra_lord = p["nakshatra_lord"]
            nakshatra_name = p["nakshatra_name"]
            planet_awasta = p["planet_awasta"]
            status = p.get("status")

        dms = deg_to_dms_str(deg)
        full_deg = f"{dms} {sign}"
        out.append({
            "planet": planet,
            "sign": sign,
            "degree": deg,
            "degree_dms": dms,
            "full_degree": full_deg,
            "retrograde": retro,
            "house": house,
            "sign_lord": sign_lord,
            "nakshatra_lord": nakshatra_lord,
            "nakshatra_name": nakshatra_name,
            "planet_awasta": planet_awasta,
            "status": status,
        })
    return out


def _augment_lagna(sign: str, deg: float) -> Dict[str, Any]:
    """
    Augment Lagna data with DMS format

    Args:
        sign: Zodiac sign name
        deg: Degree within sign

    Returns:
        Dictionary with augmented lagna data
    """
    return {
        "sign": sign,
        "degree": deg,
        "degree_dms": deg_to_dms_str(deg),
        "full_degree": f"{deg_to_dms_str(deg)} {sign}",
    }
