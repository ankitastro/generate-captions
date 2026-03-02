# In varga_engine.py

"""
Varga Engine - Divisional Charts Calculator
Implementation of all major Varga charts according to Brihat Parashara Hora Shastra (BPHS)
"""

from typing import Dict, List

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

VARGA_NAMES = {
    1: "Rashi (D1)",
    2: "Hora (D2)",
    3: "Drekkana (D3)",
    4: "Chaturthamsa (D4)",
    7: "Saptamsa (D7)",
    9: "Navamsa (D9)",
    10: "Dasamsa (D10)",
    12: "Dwadasamsa (D12)",
    16: "Shodasamsa (D16)",
    20: "Vimsamsa (D20)",
    24: "Chaturvimsamsa (D24)",
    27: "Saptavimsamsa (D27)",
    30: "Trimsamsa (D30)",
    40: "Khavedamsa (D40)",
    45: "Akshavedamsa (D45)",
    60: "Shastyamsa (D60)"
}


def get_sign_name(index: int) -> str:
    return SIGN_NAMES[index % 12]

def get_sign_type(sign_index: int) -> str:
    """Returns 'Movable', 'Fixed', or 'Dual'."""
    if sign_index in [0, 3, 6, 9]: return "Movable"
    if sign_index in [1, 4, 7, 10]: return "Fixed"
    return "Dual"



def get_varga_sign(planet_deg: float, varga: int) -> str:
    planet_deg %= 360
    base_sign_index = int(planet_deg / 30)
    degree_in_sign = planet_deg % 30
    sign_type = get_sign_type(base_sign_index)
    is_odd_sign = base_sign_index % 2 == 0

    division_size = 30 / varga
    division = int(degree_in_sign / division_size)

    # General rule for many vargas
    forward_count = base_sign_index + division

    # Specific Parashari Rules
    if varga == 9: # D9 - Navamsa
        if sign_type == "Movable": start_index = base_sign_index
        elif sign_type == "Fixed": start_index = base_sign_index + 8
        else: start_index = base_sign_index + 4
        return get_sign_name(start_index + division)

    if varga == 2: # D2 - Hora
        return "Leo" if (is_odd_sign and degree_in_sign < 15) or (not is_odd_sign and degree_in_sign >= 15) else "Cancer"

    if varga == 3: # D3 - Drekkana
        return get_sign_name(base_sign_index + (division * 4))

    if varga == 4: # D4 - Chaturthamsa
        return get_sign_name(base_sign_index + (division * 3))

    if varga == 7: # D7 - Saptamsa
        start_index = base_sign_index if is_odd_sign else base_sign_index + 6
        return get_sign_name(start_index + division)

    if varga == 10: # D10 - Dasamsa
        start_index = base_sign_index if is_odd_sign else base_sign_index + 8
        return get_sign_name(start_index + division)

    if varga == 12: # D12 - Dwadasamsa
        return get_sign_name(forward_count)

    if varga == 16: # D16 - Shodasamsa
        if sign_type == "Movable": start_index = 0  # Aries
        elif sign_type == "Fixed": start_index = 4  # Leo
        else: start_index = 8  # Sagittarius
        return get_sign_name(start_index + division)

    if varga == 20: # D20 - Vimsamsa
        if sign_type == "Movable": start_index = 0 # Aries
        elif sign_type == "Fixed": start_index = 8 # Sagittarius
        else: start_index = 4 # Leo
        return get_sign_name(start_index + division)
        
    if varga == 24: # D24 - Chaturvimsamsa
        start_index = 4 if is_odd_sign else 3 # Leo or Cancer
        return get_sign_name(start_index + division)

    # For other vargas or as a default
    return get_sign_name(forward_count)


def get_varga_chart(planet_positions: Dict[str, float], varga: int) -> Dict[str, List[str]]:
    chart = {sign: [] for sign in SIGN_NAMES}
    for planet_name, planet_deg in planet_positions.items():
        try:
            divisional_sign = get_varga_sign(planet_deg, varga)
            chart[divisional_sign].append(planet_name)
        except Exception:
            continue
    return chart

def get_all_varga_charts(planet_positions: Dict[str, float], vargas: List[int] = None) -> Dict[int, Dict[str, List[str]]]:
    if vargas is None:
        vargas = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

    all_charts = {}
    for varga in vargas:
        all_charts[varga] = get_varga_chart(planet_positions, varga)
    return all_charts


def deg_to_dms_str(deg: float) -> str:
    """Convert decimal degrees to DMS string format"""
    d = int(deg)
    m_float = abs(deg - d) * 60.0
    m = int(m_float)
    s = round((m_float - m) * 60.0)
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return f"{d}°{m:02d}′{s:02d}″"


def get_varga_chart_detailed(planet_positions: Dict[str, float], varga: int) -> Dict[str, List[Dict]]:
    """
    Returns detailed varga chart with planet positions including sign, degree, and house.

    Note: The 'degree' shown is the D1 (Rasi) degree for reference, as per Vedic tradition.
    The varga sign is calculated based on divisional rules.

    Returns:
        Dict mapping signs to list of planet details:
        {
            "Aries": [
                {
                    "planet": "Sun",
                    "sign": "Aries",  # Varga sign
                    "degree": 12.45,  # D1 degree for reference
                    "degree_dms": "12°27′00″",
                    "house": 1  # House in this varga chart
                }
            ]
        }
    """
    chart = {sign: [] for sign in SIGN_NAMES}

    # Find Lagna sign in this varga to calculate houses
    lagna_sign = None
    if 'Lagna' in planet_positions:
        lagna_sign = get_varga_sign(planet_positions['Lagna'], varga)

    lagna_sign_index = SIGN_NAMES.index(lagna_sign) if lagna_sign else 0

    for planet_name, planet_deg in planet_positions.items():
        try:
            # Get the varga sign for this planet
            divisional_sign = get_varga_sign(planet_deg, varga)

            # Use D1 degree (within birth sign) for reference - standard Vedic practice
            # This matches what the SVG displays
            d1_degree_in_sign = planet_deg % 30

            # Calculate house number based on varga lagna
            sign_index = SIGN_NAMES.index(divisional_sign)
            house_num = ((sign_index - lagna_sign_index) % 12) + 1

            planet_detail = {
                "planet": planet_name,
                "sign": divisional_sign,  # Sign in this varga chart
                "degree": round(d1_degree_in_sign, 2),  # D1 degree (for reference)
                "degree_dms": deg_to_dms_str(d1_degree_in_sign),
                "house": house_num  # House in this varga chart
            }

            chart[divisional_sign].append(planet_detail)
        except Exception:
            continue

    return chart


def get_all_varga_charts_detailed(planet_positions: Dict[str, float], vargas: List[int] = None) -> Dict[int, Dict[str, List[Dict]]]:
    """
    Returns all varga charts with detailed planet information.

    Returns:
        Dict mapping varga numbers to detailed charts:
        {
            2: {"Aries": [{"planet": "Sun", "sign": "Aries", "degree": 12.45, "degree_dms": "12°27′00″", "house": 1}]},
            3: {...},
            ...
        }
    """
    if vargas is None:
        vargas = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

    all_charts_detailed = {}
    for varga in vargas:
        all_charts_detailed[varga] = get_varga_chart_detailed(planet_positions, varga)

    return all_charts_detailed