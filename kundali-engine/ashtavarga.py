from typing import Dict, List

# --- Ashtakavarga Rules based on Brihat Parashara Hora Shastra ---
ASHTAKAVARGA_RULES = {
    'Sun': {
        'Sun': [1, 2, 4, 7, 8, 9, 10, 11], 'Moon': [3, 6, 10, 11],
        'Mars': [1, 2, 4, 7, 8, 9, 10, 11], 'Mercury': [3, 5, 6, 9, 10, 11, 12],
        'Jupiter': [5, 6, 9, 11], 'Venus': [6, 7, 12],
        'Saturn': [1, 2, 4, 7, 8, 9, 10, 11], 'Lagna': [3, 4, 6, 10, 11, 12]
    },
    'Moon': {
        'Sun': [3, 6, 7, 8, 10, 11], 'Moon': [1, 3, 6, 7, 10, 11],
        'Mars': [2, 3, 5, 6, 9, 10, 11], 'Mercury': [1, 3, 4, 5, 7, 8, 10, 11],
        'Jupiter': [1, 4, 7, 8, 10, 11, 12], 'Venus': [3, 4, 5, 7, 9, 10, 11],
        'Saturn': [3, 5, 6, 11], 'Lagna': [3, 6, 10, 11]
    },
    'Mars': {
        'Sun': [3, 5, 6, 10, 11], 'Moon': [3, 6, 11],
        'Mars': [1, 2, 4, 7, 8, 10, 11], 'Mercury': [3, 5, 6, 11],
        'Jupiter': [6, 10, 11, 12], 'Venus': [6, 8, 11, 12],
        'Saturn': [1, 4, 7, 8, 9, 10, 11], 'Lagna': [1, 3, 6, 10, 11]
    },
    'Mercury': {
        'Sun': [5, 6, 9, 11, 12], 'Moon': [2, 4, 6, 8, 10, 11],
        'Mars': [1, 2, 4, 7, 8, 9, 10, 11], 'Mercury': [1, 3, 5, 6, 9, 10, 11, 12],
        'Jupiter': [6, 8, 11, 12], 'Venus': [1, 2, 3, 4, 5, 8, 9, 11],
        'Saturn': [1, 2, 4, 7, 8, 9, 10, 11], 'Lagna': [1, 2, 4, 6, 8, 10, 11]
    },
    'Jupiter': {
        'Sun': [1, 2, 3, 4, 7, 8, 9, 10, 11], 'Moon': [2, 5, 7, 9, 11],
        'Mars': [1, 2, 4, 7, 8, 10, 11], 'Mercury': [1, 2, 4, 5, 6, 9, 10, 11],
        'Jupiter': [1, 2, 3, 4, 7, 8, 10, 11], 'Venus': [2, 5, 6, 9, 10, 11],
        'Saturn': [3, 5, 6, 12], 'Lagna': [1, 2, 4, 5, 6, 7, 9, 10, 11]
    },
    'Venus': {
        'Sun': [8, 11, 12], 'Moon': [1, 2, 3, 4, 5, 8, 9, 11, 12],
        'Mars': [3, 5, 6, 9, 11, 12], 'Mercury': [3, 5, 6, 9, 11],
        'Jupiter': [5, 8, 9, 10, 11], 'Venus': [1, 2, 3, 4, 5, 8, 9, 10, 11],
        'Saturn': [3, 4, 5, 8, 9, 10, 11], 'Lagna': [1, 2, 3, 4, 5, 8, 9, 11] 
    },
    'Saturn': {
        'Sun': [1, 2, 4, 7, 8, 10, 11], 'Moon': [3, 6, 11],
        'Mars': [3, 5, 6, 10, 11, 12], 'Mercury': [6, 8, 9, 10, 11, 12],
        'Jupiter': [5, 6, 11, 12], 'Venus': [6, 11, 12],
        'Saturn': [3, 5, 6, 11], 'Lagna': [1, 3, 4, 6, 10, 11]
    }
}

ZODIAC_SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]

def calculate_bav(planet_to_calculate: str, planet_positions: Dict[str, int], lagna_pos: int) -> List[int]:
    """Calculates the Bhinna Ashtakavarga for a single planet."""
    bav_table = [0] * 12
    factors = {**planet_positions, 'Lagna': lagna_pos}
    rules = ASHTAKAVARGA_RULES[planet_to_calculate]

    for factor_name, factor_pos in factors.items():
        if factor_name not in rules: continue
        
        auspicious_houses = rules[factor_name]
        for house in auspicious_houses:
            # house-1 because rules are 1-based, index is 0-based
            target_sign_index = (factor_pos + house - 1) % 12
            bav_table[target_sign_index] += 1
            
    return bav_table

def calculate_ashtakavarga(planet_positions: Dict[str, str], lagna_sign: str) -> Dict:
    """Calculates all Bhinna Ashtakavarga tables and the Sarvashtakavarga."""
    
    # Convert sign names to indices (0-11)
    planet_indices = {p: ZODIAC_SIGNS.index(s) for p, s in planet_positions.items()}
    lagna_index = ZODIAC_SIGNS.index(lagna_sign)

    planets_for_bav = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    all_bavs = {}

    for planet in planets_for_bav:
        all_bavs[planet] = calculate_bav(planet, planet_indices, lagna_index)

    # Calculate Sarvashtakavarga (SAV)
    sav_table = [0] * 12
    for sign_index in range(12):
        total_bindus = 0
        for planet in planets_for_bav:
            total_bindus += all_bavs[planet][sign_index]
        sav_table[sign_index] = total_bindus
        
    return {
        "bhinna_ashtakavarga": all_bavs,
        "sarvashtakavarga": sav_table
    }