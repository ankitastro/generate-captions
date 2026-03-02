# ashtakoota_matcher.py

from typing import Dict, Any, Tuple

# --- Data Tables for Calculations ---

VARNA_MAP = {"Cancer": "Brahmin", "Scorpio": "Brahmin", "Pisces": "Brahmin", "Aries": "Kshatriya", "Leo": "Kshatriya", "Sagittarius": "Kshatriya", "Taurus": "Vaisya", "Virgo": "Vaisya", "Capricorn": "Vaisya", "Gemini": "Shudra", "Libra": "Shudra", "Aquarius": "Shudra"}
VASHYA_MAP = {"Aries": "Chatushpada", "Taurus": "Chatushpada", "Gemini": "Manava", "Cancer": "Jalachara", "Leo": "Chatushpada", "Virgo": "Manava", "Libra": "Manava", "Scorpio": "Keeta", "Sagittarius": "Chatushpada", "Capricorn": "Jalachara", "Aquarius": "Manava", "Pisces": "Jalachara"}
VASHYA_SCORES = {
    ("Manava", "Manava"): 2, ("Manava", "Jalachara"): 1, ("Manava", "Chatushpada"): 0, ("Manava", "Keeta"): 0,
    ("Chatushpada", "Chatushpada"): 2, ("Chatushpada", "Manava"): 1, ("Chatushpada", "Jalachara"): 1, ("Chatushpada", "Keeta"): 1,
    ("Jalachara", "Jalachara"): 2, ("Jalachara", "Manava"): 0, ("Jalachara", "Chatushpada"): 1,
    ("Keeta", "Keeta"): 2, ("Keeta", "Manava"): 0, ("Keeta", "Chatushpada"): 1,
}
NAKSHATRA_DETAILS = {
    'Ashwini': {'yoni': 'Ashwa', 'gana': 'Deva', 'nadi': 'Adi'}, 'Bharani': {'yoni': 'Gaja', 'gana': 'Manushya', 'nadi': 'Madhya'},
    'Krittika': {'yoni': 'Mesha', 'gana': 'Rakshasa', 'nadi': 'Antya'}, 'Rohini': {'yoni': 'Sarpa', 'gana': 'Manushya', 'nadi': 'Antya'},
    'Mrigashira': {'yoni': 'Sarpa', 'gana': 'Deva', 'nadi': 'Madhya'}, 'Ardra': {'yoni': 'Shwana', 'gana': 'Manushya', 'nadi': 'Adi'},
    'Punarvasu': {'yoni': 'Marjara', 'gana': 'Deva', 'nadi': 'Adi'}, 'Pushya': {'yoni': 'Mesha', 'gana': 'Deva', 'nadi': 'Madhya'},
    'Ashlesha': {'yoni': 'Marjara', 'gana': 'Rakshasa', 'nadi': 'Antya'}, 'Magha': {'yoni': 'Mushaka', 'gana': 'Rakshasa', 'nadi': 'Antya'},
    'Purva Phalguni': {'yoni': 'Mushaka', 'gana': 'Manushya', 'nadi': 'Madhya'}, 'Uttara Phalguni': {'yoni': 'Gau', 'gana': 'Manushya', 'nadi': 'Adi'},
    'Hasta': {'yoni': 'Mahisha', 'gana': 'Deva', 'nadi': 'Adi'}, 'Chitra': {'yoni': 'Vyaghra', 'gana': 'Rakshasa', 'nadi': 'Madhya'},
    'Swati': {'yoni': 'Mahisha', 'gana': 'Deva', 'nadi': 'Antya'}, 'Vishakha': {'yoni': 'Vyaghra', 'gana': 'Rakshasa', 'nadi': 'Adi'},
    'Anuradha': {'yoni': 'Mriga', 'gana': 'Deva', 'nadi': 'Madhya'}, 'Jyeshtha': {'yoni': 'Mriga', 'gana': 'Rakshasa', 'nadi': 'Adi'},
    'Mula': {'yoni': 'Shwana', 'gana': 'Rakshasa', 'nadi': 'Adi'}, 'Purva Ashadha': {'yoni': 'Vanara', 'gana': 'Manushya', 'nadi': 'Madhya'},
    'Uttara Ashadha': {'yoni': 'Nakula', 'gana': 'Manushya', 'nadi': 'Antya'}, 'Shravana': {'yoni': 'Vanara', 'gana': 'Deva', 'nadi': 'Antya'},
    'Dhanishta': {'yoni': 'Simha', 'gana': 'Rakshasa', 'nadi': 'Madhya'}, 'Shatabhisha': {'yoni': 'Ashwa', 'gana': 'Rakshasa', 'nadi': 'Adi'},
    'Purva Bhadrapada': {'yoni': 'Simha', 'gana': 'Manushya', 'nadi': 'Adi'}, 'Uttara Bhadrapada': {'yoni': 'Gau', 'gana': 'Manushya', 'nadi': 'Madhya'},
    'Revati': {'yoni': 'Gaja', 'gana': 'Deva', 'nadi': 'Antya'}
}
NAKSHATRA_ORDER = list(NAKSHATRA_DETAILS.keys())
YONI_SCORES = {
    ('Ashwa', 'Ashwa'): 4, ('Ashwa', 'Mahisha'): 2, ('Ashwa', 'Vyaghra'): 1, ('Ashwa', 'Gaja'): 4, ('Ashwa', 'Mesha'): 3, ('Ashwa', 'Sarpa'): 2, ('Ashwa', 'Shwana'): 2, ('Ashwa', 'Marjara'): 2, ('Ashwa', 'Mushaka'): 2, ('Ashwa', 'Gau'): 2, ('Ashwa', 'Mriga'): 3, ('Ashwa', 'Vanara'): 3, ('Ashwa', 'Nakula'): 2, ('Ashwa', 'Simha'): 0,
    ('Mahisha', 'Vyaghra'): 0, ('Mahisha', 'Gaja'): 2, ('Mahisha', 'Mesha'): 3, ('Mahisha', 'Sarpa'): 2, ('Mahisha', 'Shwana'): 3, ('Mahisha', 'Marjara'): 2, ('Mahisha', 'Mushaka'): 3, ('Mahisha', 'Gau'): 4, ('Mahisha', 'Mriga'): 3, ('Mahisha', 'Vanara'): 3, ('Mahisha', 'Nakula'): 2, ('Mahisha', 'Simha'): 2, ('Mahisha', 'Mahisha'): 4,
    ('Vyaghra', 'Gaja'): 0, ('Vyaghra', 'Mesha'): 2, ('Vyaghra', 'Sarpa'): 1, ('Vyaghra', 'Shwana'): 2, ('Vyaghra', 'Marjara'): 1, ('Vyaghra', 'Mushaka'): 0, ('Vyaghra', 'Gau'): 0, ('Vyaghra', 'Mriga'): 3, ('Vyaghra', 'Vanara'): 2, ('Vyaghra', 'Nakula'): 2, ('Vyaghra', 'Simha'): 4, ('Vyaghra', 'Vyaghra'): 4,
    ('Gaja', 'Mesha'): 3, ('Gaja', 'Sarpa'): 2, ('Gaja', 'Shwana'): 2, ('Gaja', 'Marjara'): 2, ('Gaja', 'Mushaka'): 2, ('Gaja', 'Gau'): 2, ('Gaja', 'Mriga'): 3, ('Gaja', 'Vanara'): 3, ('Gaja', 'Nakula'): 2, ('Gaja', 'Simha'): 0, ('Gaja', 'Gaja'): 4,
    ('Mesha', 'Sarpa'): 2, ('Mesha', 'Shwana'): 3, ('Mesha', 'Marjara'): 2, ('Mesha', 'Mushaka'): 3, ('Mesha', 'Gau'): 3, ('Mesha', 'Mriga'): 4, ('Mesha', 'Vanara'): 3, ('Mesha', 'Nakula'): 2, ('Mesha', 'Simha'): 3, ('Mesha', 'Mesha'): 4,
    ('Sarpa', 'Shwana'): 2, ('Sarpa', 'Marjara'): 0, ('Sarpa', 'Mushaka'): 1, ('Sarpa', 'Gau'): 2, ('Sarpa', 'Mriga'): 3, ('Sarpa', 'Vanara'): 2, ('Sarpa', 'Nakula'): 0, ('Sarpa', 'Simha'): 2, ('Sarpa', 'Sarpa'): 4,
    ('Shwana', 'Marjara'): 0, ('Shwana', 'Mushaka'): 0, ('Shwana', 'Gau'): 3, ('Shwana', 'Mriga'): 2, ('Shwana', 'Vanara'): 2, ('Shwana', 'Nakula'): 3, ('Shwana', 'Simha'): 2, ('Shwana', 'Shwana'): 4,
    ('Marjara', 'Mushaka'): 0, ('Marjara', 'Gau'): 2, ('Marjara', 'Mriga'): 2, ('Marjara', 'Vanara'): 1, ('Marjara', 'Nakula'): 3, ('Marjara', 'Simha'): 2, ('Marjara', 'Marjara'): 4,
    ('Mushaka', 'Gau'): 3, ('Mushaka', 'Mriga'): 2, ('Mushaka', 'Vanara'): 3, ('Mushaka', 'Nakula'): 0, ('Mushaka', 'Simha'): 2, ('Mushaka', 'Mushaka'): 4,
    ('Gau', 'Mriga'): 3, ('Gau', 'Vanara'): 3, ('Gau', 'Nakula'): 2, ('Gau', 'Simha'): 2, ('Gau', 'Gau'): 4,
    ('Mriga', 'Vanara'): 3, ('Mriga', 'Nakula'): 2, ('Mriga', 'Simha'): 3, ('Mriga', 'Mriga'): 4,
    ('Vanara', 'Nakula'): 2, ('Vanara', 'Simha'): 2, ('Vanara', 'Vanara'): 4,
    ('Nakula', 'Simha'): 2, ('Nakula', 'Nakula'): 4,
    ('Simha', 'Simha'): 4
}
GRAHA_RELATIONSHIPS = {
    'Sun': {'friends': ['Moon', 'Mars', 'Jupiter'], 'enemies': ['Saturn', 'Venus'], 'neutral': ['Mercury']},
    'Moon': {'friends': ['Sun', 'Mercury'], 'enemies': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
    'Mars': {'friends': ['Sun', 'Moon', 'Jupiter'], 'enemies': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
    'Mercury': {'friends': ['Sun', 'Venus'], 'enemies': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
    'Jupiter': {'friends': ['Sun', 'Moon', 'Mars'], 'enemies': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
    'Venus': {'friends': ['Mercury', 'Saturn'], 'enemies': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
    'Saturn': {'friends': ['Mercury', 'Venus'], 'enemies': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
}

# --- Helper Functions ---

def _get_yoni_score(yoni1: str, yoni2: str) -> int:
    """Helper to get score from symmetrical YONI_SCORES table."""
    return YONI_SCORES.get(tuple(sorted((yoni1, yoni2))), 0)

def _get_vashya_score(vashya1: str, vashya2: str) -> int:
    """Helper to get score from VASHYA_SCORES table."""
    return VASHYA_SCORES.get((vashya1, vashya2), 0)

# --- Koota Calculation Functions ---

def calculate_varna_koota(groom_rasi: str, bride_rasi: str) -> Tuple[int, str]:
    varna_order = {"Brahmin": 4, "Kshatriya": 3, "Vaisya": 2, "Shudra": 1}
    groom_varna = VARNA_MAP.get(groom_rasi, "Shudra")
    bride_varna = VARNA_MAP.get(bride_rasi, "Shudra")
    score = 1 if varna_order[groom_varna] >= varna_order[bride_varna] else 0
    description = f"Your Varna: {groom_varna}, Partner Varna: {bride_varna}. Compatibility is based on spiritual development."
    return score, description

def calculate_vashya_koota(groom_rasi: str, bride_rasi: str) -> Tuple[int, str]:
    groom_vashya = VASHYA_MAP.get(groom_rasi, "")
    bride_vashya = VASHYA_MAP.get(bride_rasi, "")
    score = _get_vashya_score(groom_vashya, bride_vashya)
    description = f"Your Vashya: {groom_vashya}, Partner Vashya: {bride_vashya}. Indicates mutual attraction and control."
    return score, description

def calculate_tara_koota(groom_nakshatra: str, bride_nakshatra: str) -> Tuple[int, str]:
    try:
        groom_idx = NAKSHATRA_ORDER.index(groom_nakshatra)
        bride_idx = NAKSHATRA_ORDER.index(bride_nakshatra)

        groom_to_bride = (bride_idx - groom_idx + 27) % 27 + 1
        bride_to_groom = (groom_idx - bride_idx + 27) % 27 + 1

        score = 0
        if (groom_to_bride % 9) not in (3, 5, 7) and (bride_to_groom % 9) not in (3, 5, 7):
            score = 3
        elif (groom_to_bride % 9) not in (3, 5, 7) or (bride_to_groom % 9) not in (3, 5, 7):
            score = 1.5

        description = f"Tara check between '{groom_nakshatra}' and '{bride_nakshatra}'. Assesses health and well-being."
        return score, description
    except ValueError:
        return 0, "One of the nakshatras was not found."

def calculate_yoni_koota(groom_nakshatra: str, bride_nakshatra: str) -> Tuple[int, str]:
    groom_yoni = NAKSHATRA_DETAILS.get(groom_nakshatra, {}).get('yoni', '')
    bride_yoni = NAKSHATRA_DETAILS.get(bride_nakshatra, {}).get('yoni', '')
    score = _get_yoni_score(groom_yoni, bride_yoni)
    description = f"Your Yoni: {groom_yoni}, Partner Yoni: {bride_yoni}. Level of genuine understanding, vulnerability, and authentic bond between partners."
    return score, description

def calculate_graha_maitri_koota(groom_rasi_lord: str, bride_rasi_lord: str) -> Tuple[int, str]:
    if groom_rasi_lord == bride_rasi_lord:
        score = 5
    elif bride_rasi_lord in GRAHA_RELATIONSHIPS[groom_rasi_lord]['friends']:
        score = 5
    elif bride_rasi_lord in GRAHA_RELATIONSHIPS[groom_rasi_lord]['neutral']:
        score = 4
    elif bride_rasi_lord in GRAHA_RELATIONSHIPS[groom_rasi_lord]['enemies']:
        score = 1
    else: # one is enemy, one is neutral
        score = 3
    description = f"Your's Rasi Lord: {groom_rasi_lord}, Partner's Rasi Lord: {bride_rasi_lord}. Measures mental and intellectual compatibility."
    return score, description

def calculate_gana_koota(groom_nakshatra: str, bride_nakshatra: str) -> Tuple[int, str]:
    groom_gana = NAKSHATRA_DETAILS.get(groom_nakshatra, {}).get('gana', '')
    bride_gana = NAKSHATRA_DETAILS.get(bride_nakshatra, {}).get('gana', '')

    if groom_gana == bride_gana:
        score = 6
    elif (groom_gana, bride_gana) in [('Deva', 'Manushya'), ('Manushya', 'Deva')]:
        score = 6
    elif (groom_gana, bride_gana) in [('Deva', 'Rakshasa'), ('Rakshasa', 'Deva')]:
        score = 1
    elif (groom_gana, bride_gana) in [('Manushya', 'Rakshasa'), ('Rakshasa', 'Manushya')]:
        score = 0
    else:
        score = 0

    description = f"Your Gana: {groom_gana}, Partner Gana: {bride_gana}. Reflects temperament and core nature."
    return score, description

def calculate_bhakoot_koota(groom_rasi: str, bride_rasi: str) -> Tuple[int, str]:
    sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    try:
        groom_idx = sign_order.index(groom_rasi)
        bride_idx = sign_order.index(bride_rasi)
        distance = abs(groom_idx - bride_idx)

        if distance in (0, 6): # 1/7 or 7/7 position
            score = 7
        elif distance in (2, 4, 8, 10): # 3/11, 5/9 positions
            score = 7
        else: # 2/12, 6/8 positions
            score = 0

        description = f"Distance between Moon signs is {distance+1}/{13-distance-1}. Assesses overall emotional compatibility."
        return score, description
    except ValueError:
        return 0, "One of the rasi signs was not found."

def calculate_nadi_koota(groom_nakshatra: str, bride_nakshatra: str) -> Tuple[int, str]:
    groom_nadi = NAKSHATRA_DETAILS.get(groom_nakshatra, {}).get('nadi', '')
    bride_nadi = NAKSHATRA_DETAILS.get(bride_nakshatra, {}).get('nadi', '')
    score = 0 if groom_nadi == bride_nadi else 8
    description = f"Your Nadi: {groom_nadi}, Partner Nadi: {bride_nadi}. The partnership's potential for long-term stability, mutual growth, and lasting success."
    return score, description


class AshtakootaMatcher:
    def __init__(self, groom_kundali: Any, bride_kundali: Any):
        self.groom = groom_kundali
        self.bride = bride_kundali

        # Helper function to extract data from both dict and object
        def _get_value(obj, key, attr=None):
            """Handle both dict and object access"""
            if isinstance(obj, dict):
                return obj.get(key)
            else:
                return getattr(obj, attr or key)

        # Helper for nested access (e.g., moon_nakshatra.name)
        def _get_nested(obj, outer_key, inner_key, outer_attr=None, inner_attr=None):
            """Handle nested access like moon_nakshatra.name for both dict and object"""
            if isinstance(obj, dict):
                inner = obj.get(outer_key)
                if isinstance(inner, dict):
                    return inner.get(inner_key)
                return None
            else:
                outer = getattr(obj, outer_attr or outer_key)
                return getattr(outer, inner_attr or inner_key) if outer else None

        # --- Extract Key Data ---
        self.groom_moon_nakshatra = _get_nested(groom_kundali, 'moon_nakshatra', 'name')
        self.bride_moon_nakshatra = _get_nested(bride_kundali, 'moon_nakshatra', 'name')

        # Extract planets list
        groom_planets = _get_value(groom_kundali, 'planets')
        bride_planets = _get_value(bride_kundali, 'planets')

        # Find Moon planet data
        groom_moon_planet = None
        bride_moon_planet = None

        if groom_planets:
            for p in groom_planets:
                p_name = _get_value(p, 'planet', 'planet')
                if p_name == 'Moon':
                    groom_moon_planet = p
                    break

        if bride_planets:
            for p in bride_planets:
                p_name = _get_value(p, 'planet', 'planet')
                if p_name == 'Moon':
                    bride_moon_planet = p
                    break

        if not groom_moon_planet or not bride_moon_planet:
            raise ValueError("Moon position not found in one of the Kundali objects.")

        self.groom_moon_rasi = _get_value(groom_moon_planet, 'sign', 'sign')
        self.bride_moon_rasi = _get_value(bride_moon_planet, 'sign', 'sign')
        self.groom_moon_rasi_lord = _get_value(groom_moon_planet, 'sign_lord', 'sign_lord')
        self.bride_moon_rasi_lord = _get_value(bride_moon_planet, 'sign_lord', 'sign_lord')

        self.groom_mangal_dosha = _get_value(groom_kundali, 'mangal_dosha', 'mangal_dosha')
        self.bride_mangal_dosha = _get_value(bride_kundali, 'mangal_dosha', 'mangal_dosha')


    def calculate_all_kootas(self) -> Dict[str, Any]:
        """Calculates all 8 kootas and returns a detailed report."""

        kootas = {}
        total_points = 0

        # Varna Koota (1 Point)
        varna_score, varna_desc = calculate_varna_koota(self.groom_moon_rasi, self.bride_moon_rasi)
        kootas['varna'] = {'obtained_points': varna_score, 'max_points': 1, 'description': varna_desc}
        total_points += varna_score

        # Vashya Koota (2 Points)
        vashya_score, vashya_desc = calculate_vashya_koota(self.groom_moon_rasi, self.bride_moon_rasi)
        kootas['vashya'] = {'obtained_points': vashya_score, 'max_points': 2, 'description': vashya_desc}
        total_points += vashya_score

        # Tara Koota (3 Points)
        tara_score, tara_desc = calculate_tara_koota(self.groom_moon_nakshatra, self.bride_moon_nakshatra)
        kootas['tara'] = {'obtained_points': tara_score, 'max_points': 3, 'description': tara_desc}
        total_points += tara_score

        # Yoni Koota (4 Points)
        yoni_score, yoni_desc = calculate_yoni_koota(self.groom_moon_nakshatra, self.bride_moon_nakshatra)
        kootas['yoni'] = {'obtained_points': yoni_score, 'max_points': 4, 'description': yoni_desc}
        total_points += yoni_score

        # Graha Maitri Koota (5 Points)
        maitri_score, maitri_desc = calculate_graha_maitri_koota(self.groom_moon_rasi_lord, self.bride_moon_rasi_lord)
        kootas['graha_maitri'] = {'obtained_points': maitri_score, 'max_points': 5, 'description': maitri_desc}
        total_points += maitri_score

        # Gana Koota (6 Points)
        gana_score, gana_desc = calculate_gana_koota(self.groom_moon_nakshatra, self.bride_moon_nakshatra)
        kootas['gana'] = {'obtained_points': gana_score, 'max_points': 6, 'description': gana_desc}
        total_points += gana_score

        # Bhakoot Koota (7 Points)
        bhakoot_score, bhakoot_desc = calculate_bhakoot_koota(self.groom_moon_rasi, self.bride_moon_rasi)
        kootas['bhakoot'] = {'obtained_points': bhakoot_score, 'max_points': 7, 'description': bhakoot_desc}
        total_points += bhakoot_score

        # Nadi Koota (8 Points)
        nadi_score, nadi_desc = calculate_nadi_koota(self.groom_moon_nakshatra, self.bride_moon_nakshatra)
        kootas['nadi'] = {'obtained_points': nadi_score, 'max_points': 8, 'description': nadi_desc}
        total_points += nadi_score

        # --- Helper to extract mangal_dosha values ---
        def _get_dosha_value(dosha, key, attr=None):
            """Extract value from mangal_dosha dict or object"""
            if dosha is None:
                return None
            if isinstance(dosha, dict):
                return dosha.get(key)
            else:
                return getattr(dosha, attr or key)

        # --- Mangal Dosha Analysis ---
        groom_is_present = _get_dosha_value(self.groom_mangal_dosha, 'is_present', 'is_present') or False
        bride_is_present = _get_dosha_value(self.bride_mangal_dosha, 'is_present', 'is_present') or False
        groom_status = _get_dosha_value(self.groom_mangal_dosha, 'manglik_status', 'manglik_status') or "Not Manglik"
        bride_status = _get_dosha_value(self.bride_mangal_dosha, 'manglik_status', 'manglik_status') or "Not Manglik"

        mangal_dosha_compatible = True
        mangal_dosha_report = "Mangal Dosha compatibility is good."
        if groom_is_present != bride_is_present:
            mangal_dosha_compatible = False
            mangal_dosha_report = "Significant mismatch in Mangal Dosha. One partner is Manglik and the other is not. This requires careful consideration and potential remedies."
        elif groom_is_present and bride_is_present:
            mangal_dosha_report = "Both partners have Mangal Dosha, which is considered to nullify the negative effects. Compatibility is good."

        # --- Final Conclusion ---
        conclusion = ""
        if total_points < 18:
            conclusion = "The total score is below the recommended minimum of 18. This match is not advised without consulting an experienced astrologer for detailed analysis and potential remedies."
        elif 18 <= total_points < 25:
            conclusion = "The match is acceptable with a score between 18 and 25. The couple can lead a happy married life."
        elif 25 <= total_points < 32:
            conclusion = "This is a very good match. The couple will enjoy a successful and prosperous married life."
        else:
            conclusion = "This is an excellent and highly recommended match. The couple shares a deep and spiritual connection."

        if not mangal_dosha_compatible:
            conclusion += " CRITICAL: Mangal Dosha mismatch detected. This is a significant concern."

        return {
            "total_points_obtained": total_points,
            "maximum_points": 36,
            "conclusion": conclusion,
            "mangal_dosha_analysis": {
                "is_compatible": mangal_dosha_compatible,
                "report": mangal_dosha_report,
                "groom_status": groom_status,
                "bride_status": bride_status,
            },
            "koota_details": kootas
        }
