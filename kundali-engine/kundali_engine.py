"""
Kundali Engine - Core astrology calculations for Vedic horoscopes
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union
import pytz
import swisseph as swe
import traceback
import math
import svg_chart_generator
import svgwrite
from kerykeion import AstrologicalSubject
from translation_manager import get_translation_manager



SIDEREAL_SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]

def _sign_from_lon(lon_sid: float) -> str:
    return SIDEREAL_SIGNS[int(lon_sid // 30)]

def _deg_in_sign(lon_sid: float) -> float:
    return lon_sid % 30.0

def _whole_sign_house_map(lagna_sign: str, planet_signs: Dict[str,str]) -> Dict[str,int]:
    """Map planet -> house# (1-12) using Vedic Whole Sign system."""
    lag_idx = SIDEREAL_SIGNS.index(lagna_sign)
    out = {}
    for p, s in planet_signs.items():
        s_idx = SIDEREAL_SIGNS.index(s)
        out[p] = ((s_idx - lag_idx) % 12) + 1
    return out

def _build_rasi_chart_from_house_map(house_map: Dict[str,int], include_lagna: bool=True) -> Dict[str,List[str]]:
    chart = {str(i): [] for i in range(1,13)}
    for planet, h in house_map.items():
        chart[str(h)].append(planet)
    if include_lagna:
        chart['1'].insert(0, 'Lagna')
    return chart


# Add the drik-panchanga directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'drik-panchanga'))

# Import drik-panchanga functions
from panchanga import (
    gregorian_to_jd, Date, Place, tithi, nakshatra, yoga, karana,
    vaara, masa, ritu, samvatsara, sunrise, sunset, day_duration,
    ahargana, elapsed_year, solar_longitude, lunar_longitude, lunar_phase
)

# Import our dasha calculator
from dasha import (
    VimshottariDasha, calculate_moon_nakshatra_info,
    get_nakshatra_lord, get_nakshatra_name
)

# Import new core modules
from core.panchanga import EnhancedPanchanga
from core.dasha import VimshottariDashaTree
from core.divisional import DivisionalCharts
from core.yogas import YogaDetector
from core.report_engine import ReportEngine


from core.varga_engine import get_varga_chart, get_all_varga_charts

from ashtavarga import calculate_ashtakavarga
from dosha_analyzer import calculate_mangal_dosha, calculate_kalasarpa_dosha


# Import models
from models import (
    PlanetPosition, NakshatraInfo, DashaInfo, PanchangaInfo,
    KundaliResponse, KundaliRequest, EnhancedPanchangaInfo,
    MahaDashaInfo, AntarDashaInfo, CurrentDashaInfo, NavamsaInfo,
    YogaInfo, YogaSummary, MangalDoshaResult,
    KalasarpaDoshaResult, LagnaInfo
)

from  svg_chart_generator import (
   PLANET_ABBREVIATIONS, PLANET_COLORS
)

# Add interpretation engine import
from core.interpretation_engine import InterpretationEngine

from core import varga_engine

# Patch the to_dms function to handle NaN and infinity values safely
def safe_to_dms(deg):
    """Safe version of to_dms that handles NaN and infinity values"""
    try:
        # Check for NaN or infinity
        if not isinstance(deg, (int, float)) or math.isnan(deg) or math.isinf(deg):
            return [0, 0, 0]

        d = int(deg)
        mins = (deg - d) * 60

        # Check if mins is valid
        if math.isnan(mins) or math.isinf(mins):
            return [d, 0, 0]

        m = int(mins)
        seconds = (mins - m) * 60

        # Check if seconds is valid
        if math.isnan(seconds) or math.isinf(seconds):
            return [d, m, 0]

        s = int(round(seconds))
        return [d, m, s]
    except (ValueError, OverflowError, TypeError):
        return [0, 0, 0]

# Patch the panchanga module's to_dms function
import panchanga
panchanga.to_dms = safe_to_dms

class KundaliEngine:
    """
    Main engine for Kundali calculations
    Integrates drik-panchanga with additional planetary calculations
    """

    # Swiss Ephemeris planet constants
    PLANETS = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mars': swe.MARS,
        'Mercury': swe.MERCURY,
        'Jupiter': swe.JUPITER,
        'Venus': swe.VENUS,
        'Saturn': swe.SATURN,
        'Rahu': swe.MEAN_NODE,  # North Node
        'Ketu': -1  # Will be calculated as opposite of Rahu
    }
    SIGN_LORDS = {
        "Aries": "Mars",
        "Taurus": "Venus",
        "Gemini": "Mercury",
        "Cancer": "Moon",
        "Leo": "Sun",
        "Virgo": "Mercury",
        "Libra": "Venus",
        "Scorpio": "Mars",
        "Sagittarius": "Jupiter",
        "Capricorn": "Saturn",
        "Aquarius": "Saturn",
        "Pisces": "Jupiter"
    }

    # Zodiac signs
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    # Sanskrit names for reference
    SANSKRIT_NAMES = {
        'tithis': {
            '1': 'Pratipad', '2': 'Dwitiya', '3': 'Tritiya', '4': 'Chaturthi',
            '5': 'Panchami', '6': 'Shashthi', '7': 'Saptami', '8': 'Ashtami',
            '9': 'Navami', '10': 'Dashami', '11': 'Ekadashi', '12': 'Dwadashi',
            '13': 'Trayodashi', '14': 'Chaturdashi', '15': 'Purnima/Amavasya',
            '16': 'Pratipad', '17': 'Dwitiya', '18': 'Tritiya', '19': 'Chaturthi',
            '20': 'Panchami', '21': 'Shashthi', '22': 'Saptami', '23': 'Ashtami',
            '24': 'Navami', '25': 'Dashami', '26': 'Ekadashi', '27': 'Dwadashi',
            '28': 'Trayodashi', '29': 'Chaturdashi', '30': 'Amavasya'
        },
        'varas': {
            '0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday',
            '4': 'Thursday', '5': 'Friday', '6': 'Saturday'
        },
        'yogas': {
            '1': 'Vishkambha', '2': 'Priti', '3': 'Ayushman', '4': 'Saubhagya',
            '5': 'Shobhana', '6': 'Atiganda', '7': 'Sukarma', '8': 'Dhriti',
            '9': 'Shula', '10': 'Ganda', '11': 'Vriddhi', '12': 'Dhruva',
            '13': 'Vyaghata', '14': 'Harshana', '15': 'Vajra', '16': 'Siddhi',
            '17': 'Vyatipata', '18': 'Variyana', '19': 'Parigha', '20': 'Shiva',
            '21': 'Siddha', '22': 'Sadhya', '23': 'Shubha', '24': 'Shukla',
            '25': 'Brahma', '26': 'Indra', '27': 'Vaidhriti'
        },
        'karanas': {
            '1': 'Kimstughna', '2': 'Bava', '3': 'Balava', '4': 'Kaulava',
            '5': 'Taitila', '6': 'Gara', '7': 'Vanija', '8': 'Vishti',
            '9': 'Bava', '10': 'Balava', '11': 'Kaulava', '12': 'Taitila',
            '13': 'Gara', '14': 'Vanija', '15': 'Vishti', '16': 'Bava',
            '17': 'Balava', '18': 'Kaulava', '19': 'Taitila', '20': 'Gara',
            '21': 'Vanija', '22': 'Vishti', '23': 'Bava', '24': 'Balava',
            '25': 'Kaulava', '26': 'Taitila', '27': 'Gara', '28': 'Vanija',
            '29': 'Vishti', '30': 'Bava', '31': 'Balava', '32': 'Kaulava',
            '33': 'Taitila', '34': 'Gara', '35': 'Vanija', '36': 'Vishti',
            '37': 'Bava', '38': 'Balava', '39': 'Kaulava', '40': 'Taitila',
            '41': 'Gara', '42': 'Vanija', '43': 'Vishti', '44': 'Bava',
            '45': 'Balava', '46': 'Kaulava', '47': 'Taitila', '48': 'Gara',
            '49': 'Vanija', '50': 'Vishti', '51': 'Bava', '52': 'Balava',
            '53': 'Kaulava', '54': 'Taitila', '55': 'Gara', '56': 'Vanija',
            '57': 'Vishti', '58': 'Chatushpada', '59': 'Naga', '60': 'Kimstughna'
        },
        'masas': {
            '1': 'Chaitra', '2': 'Vaisakha', '3': 'Jyaistha', '4': 'Ashadha',
            '5': 'Shravana', '6': 'Bhadrapada', '7': 'Ashwin', '8': 'Kartik',
            '9': 'Margashirsha', '10': 'Pausha', '11': 'Magha', '12': 'Phalguna'
        },
        'ritus': {
            '0': 'Vasanta', '1': 'Grishma', '2': 'Varsha',
            '3': 'Sharad', '4': 'Hemanta', '5': 'Shishira'
        }
    }

    # Add missing constants
    NAKSHATRA_NAMES = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
        "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
        "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]

    NAKSHATRA_LORDS = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
        "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon",
        "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
        "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
        "Saturn", "Mercury"
    ]

    TITHI_NAMES = [
        "Pratipad", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti", "Saptami",
        "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
        "Purnima", "Pratipad", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti",
        "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi",
        "Chaturdashi", "Amavasya"
    ]

    YOGA_NAMES = [
        "Vishkambha", "Preeti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
        "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
        "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
        "Shukla", "Brahma", "Indra", "Vaidhriti"
    ]

    KARANA_NAMES = [
        "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Visti", "Shakuni",
        "Chatushpada", "Naga", "Kimstughna"
    ]

    VAARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    MASA_NAMES = [
        "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
        "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"
    ]

    RITU_NAMES = ["Vasanta", "Grishma", "Varsha", "Sharad", "Shishira", "Hemanta"]

    DASHA_YEARS = {
        "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18,
        "Jupiter": 16, "Saturn": 19, "Mercury": 17
    }
    NATURAL_RELATIONSHIPS = {
        'Sun':     {'friends': ['Moon', 'Mars', 'Jupiter'], 'enemies': ['Saturn', 'Venus'], 'neutral': ['Mercury']},
        'Moon':    {'friends': ['Sun', 'Mercury'], 'enemies': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
        'Mars':    {'friends': ['Sun', 'Moon', 'Jupiter'], 'enemies': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
        'Mercury': {'friends': ['Sun', 'Venus'], 'enemies': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
        'Jupiter': {'friends': ['Sun', 'Moon', 'Mars'], 'enemies': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
        'Venus':   {'friends': ['Mercury', 'Saturn'], 'enemies': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
        'Saturn':  {'friends': ['Mercury', 'Venus'], 'enemies': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
        'Rahu':    {'friends': ['Mercury', 'Venus', 'Saturn'], 'enemies': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
        'Ketu':    {'friends': ['Mercury', 'Venus', 'Saturn'], 'enemies': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
    }

    def __init__(self):
        """Initialize the Kundali Engine with all components"""
        self.panchanga = EnhancedPanchanga()
        self.dasha_calculator = VimshottariDashaTree()
        self.divisional_charts = DivisionalCharts()
        self.yoga_detector = YogaDetector()
        self.interpretation_engine = InterpretationEngine()  # Add interpretation engine

        # Set Swiss Ephemeris to use Lahiri ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # Initialize advanced modules
        self.enhanced_panchanga = EnhancedPanchanga()
        self.dasha_tree_calculator = VimshottariDashaTree()
        self.divisional_charts = DivisionalCharts()
        self.yoga_detector = YogaDetector()
        self.report_engine = ReportEngine()


    def _calculate_planet_status(self, planet: PlanetPosition, all_planets: list[PlanetPosition]) -> str:
        """Calculates the compound friendship status of a planet with its sign lord."""
        planet_name = planet.planet
        sign_lord_name = planet.sign_lord

        if planet_name == sign_lord_name:
            return "Own Sign"

        # 1. Find Natural Relationship
        natural_relation = "neutral"
        if sign_lord_name in self.NATURAL_RELATIONSHIPS[planet_name]['friends']:
            natural_relation = "friend"
        elif sign_lord_name in self.NATURAL_RELATIONSHIPS[planet_name]['enemies']:
            natural_relation = "enemy"

        # 2. Find Temporary Relationship
        lord_planet_obj = next((p for p in all_planets if p.planet == sign_lord_name), None)
        if not lord_planet_obj:
            return "Neutral" # Should not happen if all planets are present

        house_distance = abs(lord_planet_obj.house - planet.house)

        # Planets in houses 2, 3, 4, 10, 11, 12 from each other are temporary friends
        friendly_houses = {1, 2, 3, 9, 10, 11} # Corresponds to houses 2,3,4 and 10,11,12 away
        temporal_relation = "friend" if house_distance in friendly_houses else "enemy"

        # 3. Determine Compound Status (Panchadha Maitri)
        if natural_relation == "friend" and temporal_relation == "friend":
            return "Best Friend"
        if natural_relation == "friend" and temporal_relation == "enemy":
            return "Friend"
        if natural_relation == "neutral":
            return "Neutral" # Neutral status remains neutral regardless of temporary relation
        if natural_relation == "enemy" and temporal_relation == "friend":
            return "Neutral" # Enemy + Friend = Neutral
        if natural_relation == "enemy" and temporal_relation == "enemy":
            return "Bitter Enemy"

        return "Neutral"

    def _prepare_rasi_data_for_svg(self, updated_planets: List[PlanetPosition], lagna_info: LagnaInfo, lang: str = 'en') -> Dict:
        """Prepares Rasi chart data in the North Indian format for the SVG generator."""
        from svg_chart_generator import get_planet_abbreviation

        lagna_sign = lagna_info['sign']
        lagna_idx = self.ZODIAC_SIGNS.index(lagna_sign)

        # This structure maps HOUSE NUMBER -> {sign_num, planets}
        house_data = {str(h): {"sign_num": "", "planets": []} for h in range(1, 13)}

        # 1. Populate house numbers with correct sign numbers
        for house_num in range(1, 13):
            sign_index = (lagna_idx + house_num - 1) % 12
            house_data[str(house_num)]["sign_num"] = sign_index + 1

        # 2. Add Lagna to House 1 with language support
        lagna_abbr = get_planet_abbreviation("Lagna", lang)
        house_data['1']["planets"].append({
            "text": f"{lagna_abbr} {lagna_info['degree']:.2f}°",
            "color": PLANET_COLORS.get("Lagna", "#333")
        })

        # 3. Add all other planets to their respective houses with language support
        for planet in updated_planets:
            abbr = get_planet_abbreviation(planet.planet, lang)
            display_text = f"{abbr} {planet.degree:.2f}°"
            planet_info = {
                "text": display_text,
                "color": PLANET_COLORS.get(planet.planet, "#333")
            }
            house_data[str(planet.house)]["planets"].append(planet_info)

        return house_data

    def _prepare_navamsa_data_for_svg(self, navamsa_chart_layout: Dict, navamsa_lagna: Dict, degree_map: Dict, lang: str = 'en') -> Dict:
        """Prepares Navamsa chart data in the North Indian format for the SVG generator."""
        from svg_chart_generator import get_planet_abbreviation

        lagna_sign = navamsa_lagna['sign']
        lagna_idx = self.ZODIAC_SIGNS.index(lagna_sign)

        house_data = {str(h): {"sign_num": "", "planets": []} for h in range(1, 13)}

        for house_num in range(1, 13):
            sign_index = (lagna_idx + house_num - 1) % 12
            house_data[str(house_num)]["sign_num"] = sign_index + 1

        for house_num_str, planets_in_house in navamsa_chart_layout.items():
            for planet_name in planets_in_house:
                abbr = get_planet_abbreviation(planet_name, lang)
                degree = degree_map.get(planet_name, 0.0)
                display_text = f"{abbr} {degree:.2f}°"
                planet_info = {
                    "text": display_text,
                    "color": PLANET_COLORS.get(planet_name, "#333")
                }
                house_data[house_num_str]["planets"].append(planet_info)

        return house_data


    def generate_kundali(self, request: KundaliRequest, max_dasha_depth: int = 2) -> KundaliResponse:
        """
        Main method to generate complete Kundali

        Args:
            request: KundaliRequest with birth details
            max_dasha_depth: Maximum dasha depth (1=Maha only, 2=Maha+Antar, 3=+Pratyantar, 4=+Sukshma, 5=+Prana)
        """
        try:
            print(f"DEBUG: Starting Kundali generation for {request.name}, max_dasha_depth: {max_dasha_depth}")

            # Convert input datetime to Julian Day
            jd = self._datetime_to_jd(request.datetime, request.timezone)
            print(f"DEBUG: Julian Day calculated: {jd}")

            # Calculate planetary positions
            planets, lagna_info, person = self._calculate_positions_with_kerykeion(request)
            lagna_sign = lagna_info['sign']
            lagna_degree = lagna_info['degree']

            print(f"DEBUG: Planetary positions calculated: {len(planets)} planets")




            lagna_sign_index = self.ZODIAC_SIGNS.index(lagna_sign)
            lagna_full_long = lagna_sign_index * 30.0 + lagna_degree

            lagna_info = {
            'sign': lagna_sign,
            'degree': lagna_degree,
            'abs_longitude': lagna_full_long,  # <-- TRUE 0-360 value
            }

            # Generate Rasi chart
            rasi_chart = self._generate_rasi_chart(planets, lagna_sign)
            print("DEBUG: Rasi chart generated (Whole Sign).")

            # Update planetary positions with house information
            updated_planets = self._update_planetary_houses(planets, lagna_sign)
            print(f"DEBUG: Planetary houses updated")

            # Get Moon's nakshatra
            try:
                moon_nakshatra = self._get_moon_nakshatra(jd)
                print(f"DEBUG: Moon nakshatra: {moon_nakshatra.name}")
            except Exception as e:
                print(f"DEBUG: Error in _get_moon_nakshatra: {e}")
                raise

            # Calculate current dasha (basic)
            try:
                current_dasha = self._calculate_current_dasha(jd)
                print(f"DEBUG: Current dasha: {current_dasha.planet}")
            except Exception as e:
                print(f"DEBUG: Error in _calculate_current_dasha: {e}")
                raise

            # Get basic panchanga details (for backward compatibility)
            try:
                panchanga = self._get_panchanga_details(jd, request.latitude, request.longitude, request.timezone)
                print(f"DEBUG: Basic panchanga calculated")
            except Exception as e:
                print(f"DEBUG: Error in _get_panchanga_details: {e}")
                raise


            # 1. Enhanced Panchanga
            try:
                lang = getattr(request, 'language', 'en') or 'en'
                enhanced_panchanga = self.enhanced_panchanga.get_details(
                    jd, request.latitude, request.longitude, request.timezone, person, lang=lang
                )
            except Exception as e:
                print(f"DEBUG: Error in enhanced panchanga: {e}")
                enhanced_panchanga = self.enhanced_panchanga._get_fallback_panchanga()

            # 2. Full Vimshottari Dasha Tree
            try:
                vimshottari_dasha_tree = self.dasha_tree_calculator.get_full_dasha_tree(jd, request.datetime, max_depth=max_dasha_depth)
                current_dasha_detailed = self.dasha_tree_calculator.get_current_dasha(jd, request.datetime, max_depth=max_dasha_depth)
                print(f"DEBUG: Vimshottari dasha tree calculated (depth={max_dasha_depth}): {len(vimshottari_dasha_tree)} periods")
            except Exception as e:
                print(f"DEBUG: Error in dasha tree calculation: {e}")
                vimshottari_dasha_tree = []
                current_dasha_detailed = {
                    "maha_dasha": {"planet": "Mercury", "start_date": "1990-01-01", "end_date": "2007-01-01", "total_years": 17},
                    "antar_dasha": {"planet": "Mercury", "start_date": "1990-01-01", "end_date": "1992-01-01", "duration_years": 2.4}
                }

            # 3. Navamsa Chart
            try:
                navamsa_chart = self.divisional_charts.get_navamsa_chart(planets, lagna_info)
                print(f"DEBUG: Navamsa chart calculated")
            except Exception as e:
                print(f"DEBUG: Error in navamsa calculation: {e}")
                navamsa_chart = self.divisional_charts._get_fallback_navamsa_chart()

            # 4. Yoga Detection
            try:
                detected_yogas = self.yoga_detector.detect_all_yogas(updated_planets, rasi_chart, lagna_sign)
                yoga_summary = self.yoga_detector.get_yoga_summary(detected_yogas)
                print(f"DEBUG: Yoga detection completed: {len(detected_yogas)} yogas found")
            except Exception as e:
                print(f"DEBUG: Error in yoga detection: {e}")
                detected_yogas = []
                yoga_summary = {"total_yogas": 0, "strong_yogas": [], "moderate_yogas": [], "weak_yogas": [], "most_significant": None}

            # Convert detected yogas to the proper format
            yogas_info = []
            for yoga in detected_yogas:
                if hasattr(yoga, 'name'):  # YogaInfo dataclass
                    yogas_info.append(YogaInfo(
                        name=yoga.name,
                        description=yoga.description,
                        strength=yoga.strength,
                        planets_involved=yoga.planets_involved,
                        houses_involved=yoga.houses_involved,
                        significance=yoga.significance,
                        effects=yoga.effects
                    ))

            # Generate human-readable interpretation
            interpretation = self.interpretation_engine.generate_kundali_interpretation({
                'name': request.name,
                'lagna': lagna_sign,
                'planets': [planet.dict() for planet in updated_planets],  # Convert PlanetPosition objects to dicts
                'moon_nakshatra': moon_nakshatra.dict(),  # Convert NakshatraInfo to dict
                'detected_yogas': [yoga.dict() for yoga in yogas_info],  # Convert YogaInfo objects to dicts
                'rasi_chart': rasi_chart
            })
            # Pass language parameter for chart translation
            chart_lang = getattr(request, 'language', 'en') or 'en'
            translation_manager = get_translation_manager()

            # Translate chart titles
            rasi_chart_title = translation_manager.translate('charts.Rasi Chart', chart_lang, default="Rasi (D1)")
            rasi_svg_data = self._prepare_rasi_data_for_svg(updated_planets, lagna_info, lang=chart_lang)
            rasi_chart_svg_string = svg_chart_generator.create_single_chart_svg(rasi_chart_title, rasi_svg_data, lang=chart_lang)

            try:
                navamsa_degree_map = {p.planet: p.degree for p in updated_planets}
                navamsa_degree_map['Lagna'] = lagna_info['degree']
                for p_name, p_info in navamsa_chart['navamsa_positions'].items():
                    navamsa_degree_map[p_name] = p_info['degree']

                navamsa_svg_data = self._prepare_navamsa_data_for_svg(
                    navamsa_chart['navamsa_chart'],
                    navamsa_chart['navamsa_lagna'],
                    navamsa_degree_map,
                    lang=chart_lang
                )
                # Translate navamsa chart title
                navamsa_chart_title = translation_manager.translate('charts.Navamsa Chart', chart_lang, default="Navamsa (D9)")
                navamsa_chart_svg_string = svg_chart_generator.create_single_chart_svg(navamsa_chart_title, navamsa_svg_data, lang=chart_lang)
                print(f"DEBUG: Navamsa SVG Chart generated.")

            except Exception as e:
                print(f"DEBUG: Error in navamsa calculation or SVG generation: {e}")
                navamsa_chart = self.divisional_charts._get_fallback_navamsa_chart()
                navamsa_chart_svg_string = None # Set to None on error

            planet_signs = {p.planet: p.sign for p in updated_planets}
            planet_houses = {p.planet: p.house for p in updated_planets}
            planet_longitudes = {p.planet: getattr(p, "_abs_lon_sid", 0.0) for p in planets.values()}
            planet_longitudes['Lagna'] = lagna_info['abs_longitude']  # Add Lagna's absolute longitude
            planet_degrees = planet_longitudes


            ashtakavarga_data = None
            ashtakavarga_svg_string = None
            try:
                print("DEBUG: Preparing data for Ashtakavarga...")
                planet_signs = {p.planet: p.sign for p in updated_planets}
                print(f"DEBUG: Planet signs for Ashtakavarga: {planet_signs}")
                print(f"DEBUG: Lagna sign for Ashtakavarga: {lagna_sign}")

                print("DEBUG: Calculating Ashtakavarga data...")
                ashtakavarga_data = calculate_ashtakavarga(planet_signs, lagna_sign)
                print("DEBUG: Ashtakavarga data calculated successfully.")

                print("DEBUG: Generating Ashtakavarga SVG...")
                ashtakavarga_svg_string = svg_chart_generator.create_ashtakavarga_svg(ashtakavarga_data,lagna_sign)
                print("DEBUG: Ashtakavarga SVG generated successfully.")

            except Exception as e:
                import traceback
                print("\n" + "="*50)
                print(">>> FATAL ERROR DURING ASHTAKAVARGA GENERATION <<<")
                print(f"ERROR TYPE: {type(e).__name__}")
                print(f"ERROR DETAILS: {e}")
                print("--- TRACEBACK ---")
                traceback.print_exc()
                print("="*50 + "\n")
                # Set to None and continue to avoid a hard crash
                ashtakavarga_svg_string = None


            # Calculate Doshas
            mangal_dosha_data = calculate_mangal_dosha(planet_houses, planet_signs,planet_degrees)
            kalasarpa_dosha_data = calculate_kalasarpa_dosha(planet_longitudes,planet_houses)

            planet_degrees = {p.planet: (self.ZODIAC_SIGNS.index(p.sign) * 30 + p.degree) for p in planets.values()}
            planet_degrees['Lagna'] = lagna_info['abs_longitude']

            # 2. Define which vargas you want to calculate and generate
            vargas_to_generate = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24]
            all_varga_charts = varga_engine.get_all_varga_charts(planet_degrees, vargas_to_generate)

            # 3. Prepare a simple degree map for SVG display
            degree_map_for_svg = {p.planet: p.degree for p in planets.values()}
            degree_map_for_svg['Lagna'] = lagna_info['degree']
            interpretation_data = {
            'lagna': lagna_info,
            'planets': [p.dict() for p in updated_planets],
            }
            # Pass language parameter to report generation
            report_text = self.report_engine.generate_kundali_report(
                interpretation_data,
                language=request.language if hasattr(request, 'language') and request.language else 'en'
            )


            # Create response
            response = KundaliResponse(
                name=request.name,
                birth_info={
                    'date_of_birth': request.datetime.strftime('%Y-%m-%d'),
                    'time_of_birth': request.datetime.strftime('%H:%M:%S'),
                    'place_of_birth': request.place_of_birth,
                    'timezone': request.timezone,
                    'latitude': request.latitude,
                    'longitude': request.longitude
                },
                lagna=LagnaInfo(**lagna_info),
                lagna_degree=lagna_degree,
                planets=updated_planets,
                rasi_chart=rasi_chart,
                rasi_chart_svg=rasi_chart_svg_string,
                moon_nakshatra=moon_nakshatra,
                current_dasha=current_dasha,
                panchanga=panchanga,

                # Advanced features
                enhanced_panchanga=EnhancedPanchangaInfo(**enhanced_panchanga),
                vimshottari_dasha=[
                    MahaDashaInfo(
                        planet=dasha["planet"],
                        start_date=dasha["start_date"],
                        end_date=dasha["end_date"],
                        duration_years=dasha["duration_years"],
                        sub_periods=[
                            AntarDashaInfo(
                                planet=sub["planet"],
                                start_date=sub["start_date"],
                                end_date=sub["end_date"],
                                duration_years=sub["duration_years"]
                            ) for sub in dasha["sub_periods"]
                        ]
                    ) for dasha in vimshottari_dasha_tree
                ],
                current_dasha_detailed=CurrentDashaInfo(**current_dasha_detailed),
                navamsa_chart=NavamsaInfo(**navamsa_chart),
                navamsa_chart_svg=navamsa_chart_svg_string,
                detected_yogas=yogas_info,
                yoga_summary=YogaSummary(**yoga_summary),
                interpretation=interpretation,  # Add interpretation to response
                ashtakavarga=ashtakavarga_data,
                ashtavarga_svg=ashtakavarga_svg_string,
                mangal_dosha=MangalDoshaResult(**mangal_dosha_data), # <--- Ensure you're converting dict to Pydantic model here
                kalasarpa_dosha=KalasarpaDoshaResult(**kalasarpa_dosha_data),
                report=report_text,  # Add the generated report
                # major_varga_charts_svg=other_varga_charts_svg_string # ⭐ New field for other Varga charts grid SVG ⭐

            )

            print(f"DEBUG: Response created successfully with advanced features")
            return response

        except Exception as e:
            print(f"DEBUG: Exception in generate_kundali: {str(e)}")
            import traceback
            traceback.print_exc()

            raise Exception(f"Error generating Kundali: {str(e)}")

    # def _calculate_planetary_positions(self, jd: float) -> Dict[str, PlanetPosition]:
    #     """
    #     Return PlanetPosition objects AND attach a hidden attr ._abs_lon_sid on each
    #     so downstream funcs can compute houses cleanly.
    #     """

    #     from main import deg_to_dms_str

    #     planets = {}
    #     positions = {}
    #     ayan = swe.get_ayanamsa_ut(jd)
    #     if isinstance(ayan, tuple):
    #         ayan = ayan[0]

    #     for planet_name, planet_id in self.PLANETS.items():
    #         try:
    #             if planet_name == 'Ketu':
    #                 rahu_pos = swe.calc_ut(jd, swe.MEAN_NODE)
    #                 lon_trop = rahu_pos[0][0]
    #                 lon_trop = (lon_trop + 180.0) % 360.0
    #                 speed = -rahu_pos[0][3]
    #                 retrograde = True
    #             else:
    #                 planet_pos = swe.calc_ut(jd, planet_id)
    #                 lon_trop = planet_pos[0][0]
    #                 speed = planet_pos[0][3] if len(planet_pos[0]) > 3 else 0.0
    #                 retrograde = speed < 0

    #             lon_sid = (lon_trop - ayan) % 360.0
    #             sign = _sign_from_lon(lon_sid)
    #             deg = _deg_in_sign(lon_sid)
    #             nakshatra_index = int((lon_sid * 27) / 360)
    #             nakshatra_lord = self.NAKSHATRA_LORDS[nakshatra_index]
    #             nakshatra_name = self.NAKSHATRA_NAMES[nakshatra_index]
    #             sign_lord = self.SIGN_LORDS[sign]
    #             deg_in_sign = deg
    #             if deg_in_sign < 6: avastha = "Bala"
    #             elif deg_in_sign < 18: avastha = "Yuva"
    #             elif deg_in_sign < 24: avastha = "Vriddha"
    #             else: avastha = "Mrita"


    #             p = PlanetPosition(
    #                 planet=planet_name,
    #                 sign=sign,
    #                 degree=deg,
    #                 retrograde=retrograde,
    #                 house=1,
    #                 degree_dms=deg_to_dms_str(deg),
    #                 sign_lord=sign_lord,
    #                 nakshatra_lord=nakshatra_lord,
    #                 nakshatra_name=nakshatra_name,
    #                 planet_awasta=avastha
    #             )
    #             setattr(p, "_abs_lon_sid", lon_sid)
    #             positions[planet_name] = p

    #             print(f"DEBUG: {planet_name} sidereal {lon_sid:.2f}° -> {sign} {deg:.2f}°")

    #         except Exception as e:
    #             print(f"DEBUG: Error calculating {planet_name}: {e}")
    #             raise

    #     return positions
    # def _calculate_lagna_simplified(self, jd: float, latitude: float, longitude: float):
    #     """
    #     Return sidereal ascendant as (lagna_sign: str, lagna_degree: float, sidereal_abs: float).

    #     Uses Swiss Ephemeris for the tropical ascendant, then converts to sidereal (Lahiri).
    #     House cusps from swe.houses() are *not* used for whole-sign assignment, but you
    #     can call swe.houses() separately if you want to expose Placidus cusps to clients.
    #     """
    #     # Swiss Ephem ascendant: ascmc[0] in tropical degrees
    #     cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
    #     asc_tropical = ascmc[0]

    #     # Lahiri ayanamsa
    #     ayan = swe.get_ayanamsa_ut(jd)
    #     if isinstance(ayan, (tuple, list)):
    #         ayan = ayan[0]

    #     sidereal_asc = (asc_tropical - ayan) % 360
    #     sign_idx = int(sidereal_asc // 30)
    #     lagna_sign = self.ZODIAC_SIGNS[sign_idx]
    #     lagna_degree = sidereal_asc % 30

    #     return lagna_sign, lagna_degree, sidereal_asc, cusps  # keep cusps if needed

    def _calculate_positions_with_kerykeion(self, request: KundaliRequest) -> tuple[list[PlanetPosition], dict]:
        """
        Calculates all Vedic planetary and Lagna positions using the Kerykeion library.

        This is the definitive, corrected function for using Kerykeion v4+.
        """

        # Helper map to convert Kerykeion's 3-letter sign abbreviations to full names
        SIGN_MAP = {
            'Ari': 'Aries', 'Tau': 'Taurus', 'Gem': 'Gemini', 'Can': 'Cancer',
            'Leo': 'Leo', 'Vir': 'Virgo', 'Lib': 'Libra', 'Sco': 'Scorpio',
            'Sag': 'Sagittarius', 'Cap': 'Capricorn', 'Aqu': 'Aquarius', 'Pis': 'Pisces'
        }

        SIGN_ABBR_LIST = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']


        # 1. Instantiate AstrologicalSubject with explicit Vedic settings.
        person = AstrologicalSubject(
            name=request.name,
            year=request.datetime.year,
            month=request.datetime.month,
            day=request.datetime.day,
            hour=request.datetime.hour,
            minute=request.datetime.minute,
            nation="IN",
            city=request.place_of_birth,
            lng=request.longitude,
            lat=request.latitude,
            tz_str=request.timezone,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI"
        )

        all_planets = {}

        def _deg_to_dms_str(deg: float) -> str:
            d = int(deg)
            m_float = abs(deg - d) * 60.0
            m = int(m_float)
            s = round((m_float - m) * 60.0)
            if s == 60: s, m = 0, m + 1
            if m == 60: m, d = 0, d + 1
            return f"{d}°{m:02d}′{s:02d}″"

        planets_to_process = [
            "sun", "moon", "mercury", "venus", "mars",
            "jupiter", "saturn", "mean_node"
        ]

        for planet_key in planets_to_process:
            planet_obj = getattr(person, planet_key)

            planet_name = "Rahu" if planet_key == "mean_node" else planet_obj.name.capitalize()

            # --- FIX: Use the SIGN_MAP to get the full sign name ---
            sign_abbr = planet_obj.sign
            sign = SIGN_MAP[sign_abbr]
            # ---------------------------------------------------------

            degree_in_sign = planet_obj.position
            abs_longitude = planet_obj.abs_pos
            is_retrograde = planet_obj.retrograde

            sign_lord = self.SIGN_LORDS[sign]
            nakshatra_index = int(abs_longitude / (360.0 / 27))
            nakshatra_name = self.NAKSHATRA_NAMES[nakshatra_index]
            nakshatra_lord = self.NAKSHATRA_LORDS[nakshatra_index]

            if degree_in_sign < 6: avastha = "Bala"
            elif degree_in_sign < 18: avastha = "Yuva"
            elif degree_in_sign < 24: avastha = "Vriddha"
            else: avastha = "Mrita"

            planet_data = PlanetPosition(
                planet=planet_name,
                sign=sign,
                degree=degree_in_sign,
                retrograde=is_retrograde,
                house=1,
                degree_dms=_deg_to_dms_str(degree_in_sign),
                sign_lord=sign_lord,
                nakshatra_lord=nakshatra_lord,
                nakshatra_name=nakshatra_name,
                planet_awasta=avastha
            )
            all_planets[planet_name] = planet_data

        # Calculate Ketu
        rahu_obj = person.mean_node
        ketu_abs_pos = (rahu_obj.abs_pos + 180) % 360

        # --- FIX: Use the SIGN_MAP for Ketu's sign ---
        ketu_sign_num = int(ketu_abs_pos / 30)
        ketu_sign_abbr = SIGN_ABBR_LIST[ketu_sign_num]
        ketu_sign = SIGN_MAP[ketu_sign_abbr]

        # --------------------------------------------

        ketu_degree = ketu_abs_pos % 30
        ketu_nakshatra_index = int(ketu_abs_pos / (360.0 / 27))

        ketu_data = PlanetPosition(
            planet="Ketu",
            sign=ketu_sign,
            degree=ketu_degree,
            retrograde=True,
            house=1,
            degree_dms=_deg_to_dms_str(ketu_degree),
            sign_lord=self.SIGN_LORDS[ketu_sign],
            nakshatra_lord=self.NAKSHATRA_LORDS[ketu_nakshatra_index],
            nakshatra_name=self.NAKSHATRA_NAMES[ketu_nakshatra_index],
            planet_awasta="Yuva"
        )
        all_planets["Ketu"] = ketu_data

        # Get Lagna (Ascendant) information
        # --- FIX: Use the SIGN_MAP for the Lagna's sign ---
        lagna_sign_abbr = person.ascendant.sign
        lagna_sign = SIGN_MAP[lagna_sign_abbr]
        # -----------------------------------------------

        lagna_info = {
            'sign': lagna_sign,
            'degree': person.ascendant.position,
            'abs_longitude': person.ascendant.abs_pos
        }

        return all_planets, lagna_info,person

    def _generate_rasi_chart(self,
                         planets: Dict[str, PlanetPosition],
                         lagna_sign: str) -> Dict[str, List[str]]:
        """Return dict of house# -> [planets], whole-sign style."""
        lagna_sign_index = self.ZODIAC_SIGNS.index(lagna_sign)
        chart = {str(i): [] for i in range(1, 13)}
        chart["1"].append("Lagna")
        for p in planets.values():
            planet_sign_index = self.ZODIAC_SIGNS.index(p.sign)
            house_num = ((planet_sign_index - lagna_sign_index) % 12) + 1
            chart[str(house_num)].append(p.planet)
        return chart



    def _datetime_to_jd(self, dt: datetime, timezone_str: str) -> float:
        """
        Convert *local* birth datetime + timezone name to JD(UT) float.
        Always do full fractional day; required for degree accuracy.
        """
        tz = pytz.timezone(timezone_str)
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            local_dt = tz.localize(dt)
        else:
            # already aware; ensure in same zone for consistency
            local_dt = dt.astimezone(tz)

        utc_dt = local_dt.astimezone(pytz.UTC)

        frac_hours = (
            utc_dt.hour +
            utc_dt.minute / 60.0 +
            (utc_dt.second + utc_dt.microsecond / 1e6) / 3600.0
        )

        return swe.julday(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            frac_hours,
            swe.GREG_CAL
        )


    def _get_moon_nakshatra(self, jd: float) -> NakshatraInfo:
        """Get Moon's nakshatra information"""
        # Get Moon's position
        moon_pos = swe.calc_ut(jd, swe.MOON)
        moon_longitude = moon_pos[0][0]  # Extract longitude from nested tuple

        # Apply ayanamsa
        ayanamsa = swe.get_ayanamsa_ut(jd)
        # If ayanamsa is a tuple, extract the first element
        if isinstance(ayanamsa, tuple):
            ayanamsa = ayanamsa[0]

        sidereal_longitude = (moon_longitude - ayanamsa) % 360

        # Calculate nakshatra (1-27)
        nakshatra_num = int(sidereal_longitude * 27 / 360) + 1
        if nakshatra_num > 27:
            nakshatra_num = 27

        # Calculate pada (1-4)
        pada_num = int((sidereal_longitude % (360/27)) * 4 / (360/27)) + 1
        if pada_num > 4:
            pada_num = 4

        # Get nakshatra name and lord
        nakshatra_name = self.NAKSHATRA_NAMES[nakshatra_num - 1]
        nakshatra_lord = self.NAKSHATRA_LORDS[nakshatra_num - 1]

        return NakshatraInfo(
            name=nakshatra_name,
            pada=pada_num,
            lord=nakshatra_lord
        )

    def _calculate_current_dasha(self, jd: float) -> DashaInfo:
        """Calculate current Vimshottari Dasha"""
        from datetime import datetime, timedelta

        # Convert JD back to datetime for calculation
        greg_date = swe.revjul(jd)
        birth_date = datetime(int(greg_date[0]), int(greg_date[1]), int(greg_date[2]))

        # Use the proper dasha tree calculator to get current dasha
        try:
            current_dasha_detailed = self.dasha_tree_calculator.get_current_dasha(jd, birth_date)

            # Extract the maha dasha information
            maha_dasha = current_dasha_detailed["maha_dasha"]

            return DashaInfo(
                planet=maha_dasha["planet"],
                start_date=maha_dasha["start_date"],
                end_date=maha_dasha["end_date"],
                duration_years=maha_dasha["total_years"]
            )
        except Exception as e:
            print(f"DEBUG: Error in current dasha calculation: {e}")

            # Fallback to birth dasha lord calculation
            moon_nakshatra = self._get_moon_nakshatra(jd)
            nakshatra_num = self.NAKSHATRA_NAMES.index(moon_nakshatra.name) + 1
            dasha_lord = self.NAKSHATRA_LORDS[nakshatra_num - 1]
            dasha_years = self.DASHA_YEARS[dasha_lord]

            return DashaInfo(
                planet=dasha_lord,
                start_date=birth_date.strftime('%Y-%m-%d'),
                end_date=(birth_date + timedelta(days=dasha_years*365)).strftime('%Y-%m-%d'),
                duration_years=dasha_years
            )

    def _get_panchanga_details(self, jd: float, latitude: float, longitude: float, timezone_str: str) -> PanchangaInfo:
        """Get panchanga details using drik-panchanga"""
        try:
            print("DEBUG: Starting panchanga calculation")

            tz = pytz.timezone(timezone_str)


            # Convert JD to date
            greg_date = swe.revjul(jd)
            birth_date = Date(int(greg_date[0]), int(greg_date[1]), int(greg_date[2]))
            local_midnight = tz.localize(datetime(
                        birth_date.year, birth_date.month, birth_date.day, 0, 0, 0
                        ))
            # Get timezone offset
            offset = local_midnight.utcoffset().total_seconds() / 3600.0

            place = Place(latitude, longitude, offset)

            print("DEBUG: Basic panchanga calculated")

            # Calculate panchanga components with proper error handling
            def safe_format_time(time_data):
                """Safely format time data, handling various return formats"""
                try:
                    if isinstance(time_data, (list, tuple)) and len(time_data) >= 3:
                        # Convert to int to handle float values
                        hours = int(time_data[0]) if isinstance(time_data[0], (int, float)) else 0
                        minutes = int(time_data[1]) if isinstance(time_data[1], (int, float)) else 0
                        seconds = int(time_data[2]) if isinstance(time_data[2], (int, float)) else 0
                        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        return "00:00:00"
                except Exception as e:
                    print(f"Error formatting time: {e}")
                    return "00:00:00"

            try:
                # Calculate tithi
                tithi_info = tithi(jd, place)

                # Example tithi_info from drik-panchanga:
                # [22, [8, 13, 52], 23, [30, 33, 6]]
                # -> tithi number = 22, end time = [8, 13, 52]

                if isinstance(tithi_info, (list, tuple)) and len(tithi_info) >= 2:
                    tithi_num = int(tithi_info[0]) if isinstance(tithi_info[0], (int, float)) else 1
                    tithi_end_raw = tithi_info[1] if len(tithi_info) > 1 else [0, 0, 0]
                else:
                    tithi_num = 1
                    tithi_end_raw = [0, 0, 0]

                # Format tithi end time
                if isinstance(tithi_end_raw, (list, tuple)) and len(tithi_end_raw) >= 3:
                    tithi_end_time = f"{int(tithi_end_raw[0]):02d}:{int(tithi_end_raw[1]):02d}:{int(tithi_end_raw[2]):02d}"
                else:
                    tithi_end_time = "00:00:00"

                # Ensure valid tithi number (1-30)
                if tithi_num < 1 or tithi_num > 30:
                    tithi_num = 1

                # Determine Paksha
                paksha = "Shukla" if tithi_num <= 15 else "Krishna"

                tithi_name = self.TITHI_NAMES[tithi_num - 1]

            except Exception as e:
                print(f"Error calculating tithi: {e}")
                tithi_name = "Pratipad"
                tithi_end_time = "00:00:00"
                paksha = "Shukla"


            # Calculate nakshatra
            try:
                nakshatra_info = nakshatra(jd, place)
                if isinstance(nakshatra_info, (list, tuple)) and len(nakshatra_info) >= 2:
                    nakshatra_num = int(nakshatra_info[0]) if isinstance(nakshatra_info[0], (int, float)) else 1
                    nakshatra_time = nakshatra_info[1] if len(nakshatra_info) > 1 else [0, 0, 0]
                else:
                    nakshatra_num = int(nakshatra_info) if isinstance(nakshatra_info, (int, float)) else 1
                    nakshatra_time = [0, 0, 0]

                # Ensure nakshatra_num is in valid range
                if nakshatra_num < 1 or nakshatra_num > 27:
                    nakshatra_num = 1

                nakshatra_name = self.NAKSHATRA_NAMES[nakshatra_num - 1]
                nakshatra_end_time = safe_format_time(nakshatra_time)
            except Exception as e:
                print(f"Error calculating nakshatra: {e}")
                nakshatra_name = "Ashwini"
                nakshatra_end_time = "00:00:00"

            # Calculate yoga
            try:
                yoga_info = yoga(jd, place)
                if isinstance(yoga_info, (list, tuple)) and len(yoga_info) >= 2:
                    yoga_num = int(yoga_info[0]) if isinstance(yoga_info[0], (int, float)) else 1
                    yoga_time = yoga_info[1] if len(yoga_info) > 1 else [0, 0, 0]
                else:
                    yoga_num = int(yoga_info) if isinstance(yoga_info, (int, float)) else 1
                    yoga_time = [0, 0, 0]

                # Ensure yoga_num is in valid range
                if yoga_num < 1 or yoga_num > 27:
                    yoga_num = 1

                yoga_name = self.YOGA_NAMES[yoga_num - 1]
                yoga_end_time = safe_format_time(yoga_time)
            except Exception as e:
                print(f"Error calculating yoga: {e}")
                yoga_name = "Vishkambha"
                yoga_end_time = "00:00:00"

            # Calculate karana
            try:
                karana_info = karana(jd, place)
                if isinstance(karana_info, (list, tuple)):
                    karana_num = int(karana_info[0]) if len(karana_info) > 0 and isinstance(karana_info[0], (int, float)) else 1
                else:
                    karana_num = int(karana_info) if isinstance(karana_info, (int, float)) else 1

                # Adjust for karana names array
                if karana_num > len(self.KARANA_NAMES):
                    karana_num = ((karana_num - 1) % len(self.KARANA_NAMES)) + 1

                # Ensure karana_num is in valid range
                if karana_num < 1:
                    karana_num = 1

                karana_name = self.KARANA_NAMES[karana_num - 1]
            except Exception as e:
                print(f"Error calculating karana: {e}")
                karana_name = "Bava"

            # Calculate vaara
            try:
                vaara_info = vaara(jd)
                vaara_num = int(vaara_info) if isinstance(vaara_info, (int, float)) else 0

                # Ensure vaara_num is in valid range (0-6)
                if vaara_num < 0 or vaara_num > 6:
                    vaara_num = 0

                vaara_name = self.VAARA_NAMES[vaara_num]
            except Exception as e:
                print(f"Error calculating vaara: {e}")
                vaara_name = "Sunday"

            # Calculate masa
            try:
                masa_info = masa(jd, place)
                if isinstance(masa_info, (list, tuple)) and len(masa_info) >= 1:
                    masa_num = int(masa_info[0]) if isinstance(masa_info[0], (int, float)) else 1
                else:
                    masa_num = int(masa_info) if isinstance(masa_info, (int, float)) else 1

                # Ensure masa_num is in valid range
                if masa_num < 1 or masa_num > 12:
                    masa_num = 1

                masa_name = self.MASA_NAMES[masa_num - 1]
            except Exception as e:
                print(f"Error calculating masa: {e}")
                masa_name = "Chaitra"
                masa_num = 1

            # Calculate ritu
            try:
                ritu_num = int(ritu(masa_num)) if isinstance(ritu(masa_num), (int, float)) else 0

                # Ensure ritu_num is in valid range
                if ritu_num < 0 or ritu_num >= len(self.RITU_NAMES):
                    ritu_num = 0

                ritu_name = self.RITU_NAMES[ritu_num]
            except Exception as e:
                print(f"Error calculating ritu: {e}")
                ritu_name = "Vasanta"

            # Calculate samvatsara
            try:
                samvatsara_num = int(samvatsara(jd, masa_num)) if isinstance(samvatsara(jd, masa_num), (int, float)) else 0
                samvatsara_name = f"Samvatsara {samvatsara_num}"
            except Exception as e:
                print(f"Error calculating samvatsara: {e}")
                samvatsara_name = "Samvatsara 0"

            # Get sunrise/sunset
            try:
                sunrise_info = sunrise(jd, place)
                if isinstance(sunrise_info, (list, tuple)) and len(sunrise_info) >= 2:
                    sunrise_time = sunrise_info[1] if len(sunrise_info) > 1 else [6, 0, 0]
                else:
                    sunrise_time = [6, 0, 0]
                sunrise_formatted = safe_format_time(sunrise_time)
            except Exception as e:
                print(f"Error calculating sunrise: {e}")
                sunrise_formatted = "06:00:00"

            try:
                sunset_info = sunset(jd, place)
                if isinstance(sunset_info, (list, tuple)) and len(sunset_info) >= 2:
                    sunset_time = sunset_info[1] if len(sunset_info) > 1 else [18, 0, 0]
                else:
                    sunset_time = [18, 0, 0]
                sunset_formatted = safe_format_time(sunset_time)
            except Exception as e:
                print(f"Error calculating sunset: {e}")
                sunset_formatted = "18:00:00"

            print("DEBUG: Panchanga calculation completed successfully")

            return PanchangaInfo(
                tithi=tithi_name,
                tithi_end_time=tithi_end_time,
                nakshatra=nakshatra_name,
                nakshatra_end_time=nakshatra_end_time,
                yoga=yoga_name,
                yoga_end_time=yoga_end_time,
                karana=karana_name,
                vaara=vaara_name,
                masa=masa_name,
                ritu=ritu_name,
                samvatsara=samvatsara_name,
                sunrise=sunrise_formatted,
                sunset=sunset_formatted
            )

        except Exception as e:
            print(f"Error in panchanga calculation: {e}")
            import traceback
            traceback.print_exc()

            # Return basic panchanga if detailed calculation fails
            return PanchangaInfo(
                tithi="Pratipad",
                tithi_end_time="00:00:00",
                nakshatra="Ashwini",
                nakshatra_end_time="00:00:00",
                yoga="Vishkambha",
                yoga_end_time="00:00:00",
                karana="Bava",
                vaara="Sunday",
                masa="Chaitra",
                ritu="Vasanta",
                samvatsara="Samvatsara 0",
                sunrise="06:00:00",
                sunset="18:00:00"
            )

    def _update_planetary_houses(self, planets: Dict[str, PlanetPosition], lagna_sign: str) -> List[PlanetPosition]:
        """
        Update PlanetPosition.house using whole-sign houses (AstroTalk-style) and convert degree to DMS.
        """
        from api.utils.formatters import deg_to_dms_str
        lagna_sign_index = self.ZODIAC_SIGNS.index(lagna_sign)
        updated_planets = []

        for planet_pos in planets.values():
            planet_sign_index = self.ZODIAC_SIGNS.index(planet_pos.sign)
            house_num = ((planet_sign_index - lagna_sign_index) % 12) + 1

            updated_planets.append(PlanetPosition(
                planet=planet_pos.planet,
                sign=planet_pos.sign,
                degree=planet_pos.degree,
                retrograde=planet_pos.retrograde,
                house=house_num,
                degree_dms=deg_to_dms_str(planet_pos.degree),
                sign_lord=planet_pos.sign_lord,
                nakshatra_lord=planet_pos.nakshatra_lord,
                nakshatra_name=planet_pos.nakshatra_name,
                planet_awasta=planet_pos.planet_awasta
        ))
        for planet in updated_planets:
            planet.status = self._calculate_planet_status(planet, updated_planets)

        return updated_planets




    def get_varga_chart(self, planets: List[PlanetPosition], varga: int) -> Dict[str, List[str]]:
        """
        Generate a divisional chart using the comprehensive varga engine

        Args:
            planets: List of PlanetPosition objects
            varga: Divisional chart number (1-60)

        Returns:
            Dictionary mapping signs to planet lists
        """
        # Convert planet positions to degrees
        planet_degrees = {}
        for planet in planets:
            # Calculate sidereal longitude
            sign_index = self.ZODIAC_SIGNS.index(planet.sign)
            longitude = (sign_index * 30) + planet.degree
            planet_degrees[planet.planet] = longitude

        # Use the varga engine to generate the chart
        return get_varga_chart(planet_degrees, varga)

    def get_all_varga_charts(self, planets: List[PlanetPosition], vargas: List[int] = None) -> Dict[int, Dict[str, List[str]]]:
        """
        Generate multiple divisional charts at once

        Args:
            planets: List of PlanetPosition objects
            vargas: List of varga numbers (defaults to major vargas)

        Returns:
            Dictionary mapping varga numbers to their charts
        """
        # Convert planet positions to degrees
        planet_degrees = {}
        for planet in planets:
            sign_index = self.ZODIAC_SIGNS.index(planet.sign)
            longitude = (sign_index * 30) + planet.degree
            planet_degrees[planet.planet] = longitude

        # Use the varga engine to generate all charts
        return get_all_varga_charts(planet_degrees, vargas)

    def get_varga_analysis(self, planets: List[PlanetPosition], varga: int) -> Dict:
        """
        Get comprehensive analysis of a divisional chart

        Args:
            planets: List of PlanetPosition objects
            varga: Divisional chart number

        Returns:
            Dictionary containing chart analysis including strengths and summary
        """
        # Convert planet positions to degrees
        planet_degrees = {}
        for planet in planets:
            sign_index = self.ZODIAC_SIGNS.index(planet.sign)
            longitude = (sign_index * 30) + planet.degree
            planet_degrees[planet.planet] = longitude

        # Get comprehensive analysis
        summary = get_varga_summary(planet_degrees, varga)

        # Add varga name for reference
        summary['varga_name'] = get_varga_name(varga)

        return summary

    def get_major_varga_summary(self, planets: List[PlanetPosition]) -> Dict[str, Dict]:
        """
        Get analysis of all major divisional charts

        Args:
            planets: List of PlanetPosition objects


        Returns:
            Dictionary with analysis of major vargas
        """
        major_vargas = [1, 2, 3, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

        all_analysis = {}
        for varga in major_vargas:
            analysis = self.get_varga_analysis(planets, varga)
            all_analysis[get_varga_name(varga)] = analysis

        return all_analysis
