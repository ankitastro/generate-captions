"""
Planetary Horoscope Generation Engine

This module provides functionality to generate horoscopes based on actual planetary positions
for all 12 zodiac signs across 4 time scopes: daily, weekly, monthly, and yearly.
"""

import datetime
import sys
import os
from typing import Dict, List, Any, Tuple
from math import floor, degrees, radians, cos, sin

# Add the drik-panchanga directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'drik-panchanga'))

try:
    import swisseph as swe
    from panchanga import gregorian_to_jd, Place, Date, solar_longitude, lunar_longitude, nakshatra, tithi, sunrise, sunset
except ImportError as e:
    print(f"Error importing Swiss Ephemeris or panchanga: {e}")
    print("Please ensure swisseph is installed and panchanga.py is available")
    sys.exit(1)

# Valid zodiac signs
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Valid scopes
VALID_SCOPES = ["daily", "weekly", "monthly", "yearly"]

# Planetary constants
PLANETS = {
    # 'Ascendant': swe.ASC,
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
}

# Rashi (zodiac sign) mapping
RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Planetary aspects in degrees
ASPECTS = {
    'conjunction': 0,
    'sextile': 60,
    'square': 90,
    'trine': 120,
    'opposition': 180
}

class PlanetaryHoroscopeEngine:
    """Planetary horoscope generation engine using Swiss Ephemeris"""

    def __init__(self, latitude: float = 12.972, longitude: float = 77.594, timezone: float = 5.5):
        """
        Initialize the planetary horoscope engine

        Args:
            latitude: Latitude for calculations (default: Bangalore)
            longitude: Longitude for calculations (default: Bangalore)
            timezone: Timezone offset (default: IST +5.5)
        """
        self.place = Place(latitude, longitude, timezone)

        # Initialize Swiss Ephemeris
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # Lucky colors for each sign
        self.colors = {
            "Aries": ["Red", "Orange", "Golden Yellow"],
            "Taurus": ["Green", "Pink", "Blue"],
            "Gemini": ["Yellow", "Silver", "Grey"],
            "Cancer": ["White", "Silver", "Sea Green"],
            "Leo": ["Gold", "Orange", "Red"],
            "Virgo": ["Navy Blue", "Grey", "Brown"],
            "Libra": ["Blue", "Green", "White"],
            "Scorpio": ["Crimson Red", "Black", "Dark Red"],
            "Sagittarius": ["Purple", "Turquoise", "Orange"],
            "Capricorn": ["Black", "Brown", "Dark Green"],
            "Aquarius": ["Blue", "Violet", "Grey"],
            "Pisces": ["Sea Green", "Blue", "Purple"]
        }

        # Planetary significations
        self.planetary_significations = {
            'Sun': ['ego', 'vitality', 'authority', 'father', 'government', 'leadership', 'confidence'],
            'Moon': ['emotions', 'mind', 'mother', 'public', 'intuition', 'comfort', 'nurturing'],
            'Mercury': ['communication', 'intelligence', 'siblings', 'commerce', 'travel', 'writing', 'logic'],
            'Venus': ['love', 'beauty', 'relationships', 'art', 'luxury', 'harmony', 'marriage'],
            'Mars': ['energy', 'courage', 'conflicts', 'sports', 'accidents', 'brothers', 'passion'],
            'Jupiter': ['wisdom', 'expansion', 'teachers', 'philosophy', 'wealth', 'children', 'fortune'],
            'Saturn': ['discipline', 'delay', 'karma', 'hard work', 'limitations', 'elderly', 'perseverance'],
            'Uranus': ['innovation', 'sudden change', 'revolution', 'technology', 'freedom', 'uniqueness'],
            'Neptune': ['spirituality', 'illusion', 'creativity', 'dreams', 'compassion', 'mysticism'],
            'Pluto': ['transformation', 'power', 'regeneration', 'secrets', 'intensity', 'rebirth']
        }

    def get_planetary_positions(self, jd: float) -> Dict[str, Dict[str, Any]]:
        """
        Get positions of all planets for a given Julian Day

        Args:
            jd: Julian Day number

        Returns:
            Dictionary with planetary positions and their zodiac signs
        """
        positions = {}

        for planet_name, planet_id in PLANETS.items():
            try:
                # Get tropical longitude
                result = swe.calc_ut(jd, planet_id)
                longitude = result[0][0]  # result[0] is tuple of coordinates, [0] is longitude

                # Convert to sidereal (Lahiri ayanamsa)
                ayanamsa = swe.get_ayanamsa_ut(jd)
                sidereal_longitude = (longitude - ayanamsa) % 360

                # Determine zodiac sign
                rashi_num = int(sidereal_longitude / 30)
                rashi = RASHI_NAMES[rashi_num]

                # Degrees within sign
                degrees_in_sign = sidereal_longitude % 30

                positions[planet_name] = {
                    'longitude': sidereal_longitude,
                    'rashi': rashi,
                    'degrees_in_sign': degrees_in_sign,
                    'tropical_longitude': longitude
                }

            except Exception as e:
                print(f"Error calculating position for {planet_name}: {e}")
                positions[planet_name] = {
                    'longitude': 0,
                    'rashi': 'Aries',
                    'degrees_in_sign': 0,
                    'tropical_longitude': 0
                }

        return positions

    def get_planetary_aspects(self, positions: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate planetary aspects

        Args:
            positions: Planetary positions dictionary

        Returns:
            List of aspect dictionaries
        """
        aspects = []
        planet_names = list(positions.keys())

        for i, planet1 in enumerate(planet_names):
            for j, planet2 in enumerate(planet_names[i+1:], i+1):
                long1 = positions[planet1]['longitude']
                long2 = positions[planet2]['longitude']

                # Calculate angular distance
                angular_distance = abs(long1 - long2)
                if angular_distance > 180:
                    angular_distance = 360 - angular_distance

                # Check for aspects (with 8-degree orb)
                for aspect_name, aspect_angle in ASPECTS.items():
                    if abs(angular_distance - aspect_angle) <= 8:
                        aspects.append({
                            'planet1': planet1,
                            'planet2': planet2,
                            'aspect': aspect_name,
                            'angle': angular_distance,
                            'orb': abs(angular_distance - aspect_angle)
                        })

        return aspects

    def get_planetary_strength(self, positions: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        Determine planetary strength based on sign placement

        Args:
            positions: Planetary positions dictionary

        Returns:
            Dictionary of planetary strengths
        """
        strengths = {}

        # Planetary exaltation and debilitation signs
        exaltation_signs = {
            'Sun': 'Aries', 'Moon': 'Taurus', 'Mercury': 'Virgo', 'Venus': 'Pisces',
            'Mars': 'Capricorn', 'Jupiter': 'Cancer', 'Saturn': 'Libra'
        }

        debilitation_signs = {
            'Sun': 'Libra', 'Moon': 'Scorpio', 'Mercury': 'Pisces', 'Venus': 'Virgo',
            'Mars': 'Cancer', 'Jupiter': 'Capricorn', 'Saturn': 'Aries'
        }

        own_signs = {
            'Sun': ['Leo'], 'Moon': ['Cancer'], 'Mercury': ['Gemini', 'Virgo'],
            'Venus': ['Taurus', 'Libra'], 'Mars': ['Aries', 'Scorpio'],
            'Jupiter': ['Sagittarius', 'Pisces'], 'Saturn': ['Capricorn', 'Aquarius']
        }

        for planet, position in positions.items():
            rashi = position['rashi']

            if planet in exaltation_signs and rashi == exaltation_signs[planet]:
                strengths[planet] = 'Exalted'
            elif planet in debilitation_signs and rashi == debilitation_signs[planet]:
                strengths[planet] = 'Debilitated'
            elif planet in own_signs and rashi in own_signs[planet]:
                strengths[planet] = 'Own Sign'
            else:
                strengths[planet] = 'Neutral'

        return strengths

    def interpret_planetary_influence(self, positions: Dict[str, Dict[str, Any]],
                                    aspects: List[Dict[str, Any]],
                                    strengths: Dict[str, str],
                                    user_sign: str) -> Dict[str, str]:
        """
        Interpret planetary influences for horoscope generation

        Args:
            positions: Planetary positions
            aspects: Planetary aspects
            strengths: Planetary strengths
            user_sign: User's zodiac sign

        Returns:
            Dictionary with interpreted influences for different life areas
        """
        interpretations = {
            'love': '',
            'career': '',
            'money': '',
            'health': '',
            'travel': '',
            'luck': '',
            'general': ''
        }

        # Get planets in user's sign
        planets_in_sign = [planet for planet, pos in positions.items() if pos['rashi'] == user_sign]

        # Love and relationships (Venus influence)
        venus_rashi = positions['Venus']['rashi']
        venus_strength = strengths['Venus']

        if venus_strength == 'Exalted':
            interpretations['love'] = "Venus is exalted, bringing exceptional harmony and love into your relationships."
        elif venus_strength == 'Debilitated':
            interpretations['love'] = "Venus is debilitated, suggesting need for patience in romantic matters."
        elif venus_rashi == user_sign:
            interpretations['love'] = "Venus in your sign enhances your charm and attractiveness."
        else:
            interpretations['love'] = "Romantic energies are balanced, focus on communication and understanding."

        # Career (Sun and Jupiter influence)
        sun_strength = strengths['Sun']
        jupiter_strength = strengths['Jupiter']

        if sun_strength == 'Exalted' or jupiter_strength == 'Exalted':
            interpretations['career'] = "Strong planetary support for career advancement and recognition."
        elif positions['Sun']['rashi'] == user_sign:
            interpretations['career'] = "Sun's presence in your sign boosts leadership qualities and confidence."
        else:
            interpretations['career'] = "Steady progress in professional matters through consistent efforts."

        # Money and finances (Venus and Jupiter influence)
        if venus_strength == 'Exalted' or jupiter_strength == 'Exalted':
            interpretations['money'] = "Excellent time for financial growth and investment opportunities."
        elif positions['Saturn']['rashi'] == user_sign:
            interpretations['money'] = "Saturn's influence suggests careful financial planning and patience."
        else:
            interpretations['money'] = "Balanced approach to finances will yield positive results."

        # Health (Mars and Sun influence)
        mars_strength = strengths['Mars']
        if mars_strength == 'Exalted':
            interpretations['health'] = "Mars is exalted, boosting energy levels and physical vitality."
        elif positions['Mars']['rashi'] == user_sign:
            interpretations['health'] = "Mars in your sign increases energy but also suggests need for balance."
        else:
            interpretations['health'] = "Maintain regular health routines and listen to your body."

        # Travel (Mercury and Moon influence)
        mercury_rashi = positions['Mercury']['rashi']
        if mercury_rashi == user_sign:
            interpretations['travel'] = "Mercury's influence supports beneficial short journeys and communication."
        else:
            interpretations['travel'] = "Travel opportunities may arise, particularly for learning or business."

        # Luck (Jupiter influence)
        if jupiter_strength == 'Exalted':
            interpretations['luck'] = "Jupiter's exaltation brings exceptional fortune and opportunities."
        elif positions['Jupiter']['rashi'] == user_sign:
            interpretations['luck'] = "Jupiter in your sign enhances wisdom and good fortune."
        else:
            interpretations['luck'] = "Opportunities arise through patience and positive thinking."

        # General interpretation
        if planets_in_sign:
            planet_names = ", ".join(planets_in_sign)
            interpretations['general'] = f"Planetary presence ({planet_names}) in your sign enhances your natural abilities."
        else:
            interpretations['general'] = "Planetary energies support balanced growth and development."

        return interpretations

    def generate_daily_horoscope(self, sign: str, date: datetime.date = None, language: str = 'en') -> Dict[str, Any]:
        """
        Generate daily horoscope based on planetary positions

        Args:
            sign: Zodiac sign
            date: Date for horoscope (default: today)
            language: Language code - "en" (English) or "hi" (Hindi)

        Returns:
            Daily horoscope dictionary
        """
        if date is None:
            date = datetime.date.today()

        # Convert to Julian Day
        date_struct = Date(date.year, date.month, date.day)
        jd = gregorian_to_jd(date_struct)

        # Get planetary positions
        positions = self.get_planetary_positions(jd)
        aspects = self.get_planetary_aspects(positions)
        strengths = self.get_planetary_strength(positions)

        # Get panchanga details
        try:
            tithi_info = tithi(jd, self.place)
            nakshatra_info = nakshatra(jd, self.place)
            sunrise_time = sunrise(jd, self.place)
            sunset_time = sunset(jd, self.place)
        except Exception as e:
            print(f"Error calculating panchanga: {e}")
            tithi_info = [1, [6, 0, 0]]
            nakshatra_info = [1, [18, 0, 0]]
            sunrise_time = [jd, [6, 0, 0]]
            sunset_time = [jd, [18, 0, 0]]

        # Interpret planetary influences
        interpretations = self.interpret_planetary_influence(positions, aspects, strengths, sign)

        # Generate lucky elements based on planetary positions
        dominant_planet = self._get_dominant_planet(positions, sign)
        lucky_color = self._get_lucky_color(dominant_planet, sign)
        lucky_number = self._get_lucky_number(positions, sign)
        lucky_time = self._get_lucky_time(sunrise_time, sunset_time, dominant_planet)
        mood = self._get_mood(positions, sign)

        # Generate scores based on planetary strength
        love_score = self._calculate_score(positions, strengths, 'Venus')
        career_score = self._calculate_score(positions, strengths, 'Sun')
        money_score = self._calculate_score(positions, strengths, 'Jupiter')
        health_score = self._calculate_score(positions, strengths, 'Mars')
        travel_score = self._calculate_score(positions, strengths, 'Mercury')

        return {
            "date": date.strftime("%Y-%m-%d"),
            "sign": sign,
            "categories": {
                "lucky_color": lucky_color,
                "lucky_number": lucky_number,
                "lucky_time": lucky_time,
                "mood": mood,
                "love": {"score": love_score, "text": interpretations['love']},
                "career": {"score": career_score, "text": interpretations['career']},
                "money": {"score": money_score, "text": interpretations['money']},
                "health": {"score": health_score, "text": interpretations['health']},
                "travel": {"score": travel_score, "text": interpretations['travel']}
            },
            "planetary_data": {
                "positions": positions,
                "aspects": aspects,
                "strengths": strengths,
                "tithi": tithi_info[0],
                "nakshatra": nakshatra_info[0],
                "sunrise": f"{sunrise_time[1][0]:02d}:{sunrise_time[1][1]:02d}",
                "sunset": f"{sunset_time[1][0]:02d}:{sunset_time[1][1]:02d}"
            }
        }

    def _get_dominant_planet(self, positions: Dict[str, Dict[str, Any]], sign: str) -> str:
        """Get the most influential planet for the given sign"""
        # Check if any planet is in the user's sign
        for planet, pos in positions.items():
            if pos['rashi'] == sign:
                return planet

        # Default to ruling planet of the sign
        ruling_planets = {
            'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
            'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
            'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
        }
        return ruling_planets.get(sign, 'Sun')

    def _get_lucky_color(self, dominant_planet: str, sign: str) -> str:
        """Get lucky color based on dominant planet and sign"""
        planet_colors = {
            'Sun': 'Golden Yellow', 'Moon': 'Silver', 'Mercury': 'Green',
            'Venus': 'Pink', 'Mars': 'Red', 'Jupiter': 'Yellow',
            'Saturn': 'Blue', 'Uranus': 'Electric Blue', 'Neptune': 'Sea Green', 'Pluto': 'Maroon'
        }

        if dominant_planet in planet_colors:
            return planet_colors[dominant_planet]

        # Fallback to sign colors
        return self.colors[sign][0]

    def _get_lucky_number(self, positions: Dict[str, Dict[str, Any]], sign: str) -> int:
        """Calculate lucky number based on planetary positions"""
        # Sum of planetary degrees in sign
        total_degrees = sum(pos['degrees_in_sign'] for pos in positions.values())
        lucky_number = int(total_degrees) % 99 + 1
        return lucky_number

    def _get_lucky_time(self, sunrise_time: List, sunset_time: List, dominant_planet: str) -> str:
        """Calculate lucky time based on planetary hours"""
        # Planetary hours calculation (simplified)
        planetary_hours = {
            'Sun': 6, 'Moon': 7, 'Mercury': 8, 'Venus': 9, 'Mars': 10,
            'Jupiter': 11, 'Saturn': 12, 'Uranus': 13, 'Neptune': 14, 'Pluto': 15
        }

        base_hour = planetary_hours.get(dominant_planet, 12)
        start_hour = base_hour % 24
        end_hour = (base_hour + 2) % 24

        return f"{start_hour:02d}:00 {'AM' if start_hour < 12 else 'PM'} – {end_hour:02d}:00 {'AM' if end_hour < 12 else 'PM'}"

    def _get_mood(self, positions: Dict[str, Dict[str, Any]], sign: str) -> str:
        """Determine mood based on Moon's position"""
        moon_sign = positions['Moon']['rashi']

        moon_moods = {
            'Aries': 'Energetic', 'Taurus': 'Stable', 'Gemini': 'Curious',
            'Cancer': 'Nurturing', 'Leo': 'Confident', 'Virgo': 'Analytical',
            'Libra': 'Harmonious', 'Scorpio': 'Intense', 'Sagittarius': 'Optimistic',
            'Capricorn': 'Focused', 'Aquarius': 'Innovative', 'Pisces': 'Intuitive'
        }

        return moon_moods.get(moon_sign, 'Balanced')

    def _calculate_score(self, positions: Dict[str, Dict[str, Any]],
                        strengths: Dict[str, str], planet: str) -> int:
        """Calculate score based on planetary strength"""
        base_score = 60

        if planet in strengths:
            if strengths[planet] == 'Exalted':
                base_score += 20
            elif strengths[planet] == 'Own Sign':
                base_score += 10
            elif strengths[planet] == 'Debilitated':
                base_score -= 15

        # Add random variation
        import random
        variation = random.randint(-5, 5)
        return max(45, min(85, base_score + variation))


def generate_planetary_horoscope(sign: str, scope: str = "daily",
                               latitude: float = 12.972, longitude: float = 77.594,
                               timezone: float = 5.5, date: datetime.date = None, language: str = 'en') -> Dict[str, Any]:
    """
    Generate horoscope based on planetary positions

    Args:
        sign: Zodiac sign
        scope: Time scope (currently only "daily" is supported)
        latitude: Latitude for calculations
        longitude: Longitude for calculations
        timezone: Timezone offset
        date: Date for horoscope (default: today)
        language: Language code - "en" (English) or "hi" (Hindi)

    Returns:
        Dictionary containing horoscope data
    """
    if sign not in ZODIAC_SIGNS:
        raise ValueError(f"Invalid zodiac sign: {sign}. Must be one of: {', '.join(ZODIAC_SIGNS)}")

    if scope not in VALID_SCOPES:
        raise ValueError(f"Invalid scope: {scope}. Must be one of: {', '.join(VALID_SCOPES)}")

    if scope != "daily":
        raise NotImplementedError("Currently only daily horoscopes are supported")

    engine = PlanetaryHoroscopeEngine(latitude, longitude, timezone)

    if scope == "daily":
        return engine.generate_daily_horoscope(sign, date, language)


# Example usage
if __name__ == "__main__":
    # Test the planetary horoscope generation
    print("=== Planetary Daily Horoscope Example ===")

    try:
        # Generate horoscope for Scorpio
        horoscope = generate_planetary_horoscope("Scorpio", "daily")

        print(f"Sign: {horoscope['sign']}")
        print(f"Date: {horoscope['date']}")
        print(f"Lucky Color: {horoscope['categories']['lucky_color']}")
        print(f"Lucky Number: {horoscope['categories']['lucky_number']}")
        print(f"Mood: {horoscope['categories']['mood']}")
        print(f"Love Score: {horoscope['categories']['love']['score']}")
        print(f"Love Text: {horoscope['categories']['love']['text']}")

        print("\n=== Planetary Data ===")
        print(f"Tithi: {horoscope['planetary_data']['tithi']}")
        print(f"Nakshatra: {horoscope['planetary_data']['nakshatra']}")
        print(f"Sunrise: {horoscope['planetary_data']['sunrise']}")

        print("\n=== Planetary Positions ===")
        for planet, pos in horoscope['planetary_data']['positions'].items():
            print(f"{planet}: {pos['rashi']} ({pos['degrees_in_sign']:.1f}°)")

        print("\n=== Planetary Strengths ===")
        for planet, strength in horoscope['planetary_data']['strengths'].items():
            print(f"{planet}: {strength}")

    except Exception as e:
        print(f"Error generating horoscope: {e}")
        print("Make sure swisseph is installed: pip install pyswisseph")
