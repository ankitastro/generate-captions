"""
Gochar (Transit) Calculation Engine
Calculates planetary transits and their effects on birth chart
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import pytz
import swisseph as swe
import math

# Import parent Kundali engine for planet calculations
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from kundali_engine import KundaliEngine

# Import models
from models import (
    GocharAnalysis, GocharTransitInfo, BirthChartReference,
    OverallGocharScore, LifeAspectAnalysis, SpecialTransit,
    UpcomingTransit, GocharRecommendations, AstrologerNotes,
    KundaliRequest
)

# Import translation manager
from translation_manager import get_translation_manager

# Import Gochar effects
import sys
import os
sys.path.append(os.path.dirname(__file__))
from gochar_effects import (
    GOCHAR_TRANSIT_EFFECTS,
    GOCHAR_OVERALL_MESSAGES,
    GOCHAR_ASPECT_PREDICTIONS,
    GOCHAR_BEST_PRACTICES,
    GOCHAR_RECOMMENDATIONS
)


class GocharEngine:
    """
    Gochar (Transit) Calculation Engine
    Uses the same planet calculation methods as KundaliEngine
    """

    # Zodiac signs
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    # Good houses from Moon for each planet (classical Vedic astrology)
    GOOD_HOUSES_FROM_MOON = {
        'Sun': [3, 6, 10, 11],
        'Moon': [1, 3, 6, 7, 10, 11],
        'Mars': [3, 6, 11],
        'Mercury': [2, 4, 6, 8, 10, 11],
        'Jupiter': [2, 5, 7, 9, 11],
        'Venus': [2, 3, 4, 5, 8, 9, 11],
        'Saturn': [3, 6, 11],
        'Rahu': [3, 6, 11],
        'Ketu': [3, 6, 11]
    }

    # Challenging houses (generally bad)
    CHALLENGING_HOUSES = [1, 8, 12]

    # Planet weights for overall calculation (not all planets are equal!)
    PLANET_WEIGHTS = {
        'Jupiter': 3,   # Most important - luck, fortune, wisdom, expansion
        'Saturn': 3,    # Most important - karma, discipline, life lessons
        'Moon': 2,      # Very important - mind, emotions, mental peace
        'Sun': 1.5,     # Moderately important - soul, confidence, authority
        'Mars': 1.5,    # Moderately important - energy, courage, action
        'Venus': 1.5,   # Moderately important - relationships, comforts, prosperity
        'Rahu': 2,      # Important - desires, material world, shadow
        'Ketu': 2,      # Important - spirituality, detachment, shadow
        'Mercury': 1    # Less important - communication, intellect, skills
    }

    # Planet sign lords
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

    # Planets and their Swiss Ephemeris codes
    PLANETS = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mars': swe.MARS,
        'Mercury': swe.MERCURY,
        'Jupiter': swe.JUPITER,
        'Venus': swe.VENUS,
        'Saturn': swe.SATURN,
        'Rahu': swe.MEAN_NODE,
        'Ketu': swe.MEAN_NODE  # Will be calculated separately
    }

    def __init__(self):
        """Initialize Gochar Engine"""
        self.kundali_engine = KundaliEngine()
        self.translation_manager = get_translation_manager()

    def calculate_gochar(
        self,
        kundali_request: KundaliRequest,
        reference_date: Optional[datetime] = None,
        language: str = 'en'
    ) -> GocharAnalysis:
        """
        Calculate complete Gochar analysis

        Args:
            kundali_request: User's birth details
            reference_date: Date for transit analysis (default: today)
            language: Response language

        Returns:
            Complete Gochar analysis
        """
        if reference_date is None:
            reference_date = datetime.now(pytz.UTC)

        # Get birth chart data
        birth_chart = self.kundali_engine.generate_kundali(kundali_request)

        # Get birth chart reference points
        birth_moon_sign = self._get_moon_sign(birth_chart)
        birth_lagna_sign = birth_chart.lagna.sign

        # Get current planetary positions
        current_planets = self._get_current_planetary_positions(
            reference_date,
            kundali_request.latitude,
            kundali_request.longitude
        )

        # Calculate transit effects for each planet
        current_transits = {}
        for planet_name, planet_data in current_planets.items():
            transit_info = self._calculate_planet_transit(
                planet_name,
                planet_data,
                birth_moon_sign,
                birth_lagna_sign,
                language
            )
            current_transits[planet_name] = transit_info

        # Calculate overall score
        overall_score = self._calculate_overall_score(current_transits, language)

        # Analyze life aspects
        life_aspects = self._analyze_life_aspects(
            current_transits,
            birth_chart,
            language
        )

        # Check special transits
        special_transits = self._check_special_transits(
            current_transits,
            birth_moon_sign,
            birth_chart,
            reference_date,
            language
        )

        # Get upcoming transits
        upcoming_transits = self._get_upcoming_transits(
            reference_date,
            birth_moon_sign,
            kundali_request.latitude,
            kundali_request.longitude,
            language
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            current_transits,
            special_transits,
            overall_score,
            language
        )

        # Generate astrologer notes
        astrologer_notes = self._generate_astrologer_notes(
            current_transits,
            special_transits,
            overall_score,
            language
        )

        # Build birth chart reference
        birth_chart_reference = BirthChartReference(
            moon_sign=birth_moon_sign,
            moon_sign_hindi=self.translation_manager.translate(
                f'zodiac_signs_sanskrit.{birth_moon_sign}', language, default=birth_moon_sign
            ),
            moon_lord=self.SIGN_LORDS[birth_moon_sign],
            lagna_sign=birth_lagna_sign,
            lagna_sign_hindi=self.translation_manager.translate(
                f'zodiac_signs_sanskrit.{birth_lagna_sign}', language, default=birth_lagna_sign
            ),
            lagna_lord=self.SIGN_LORDS[birth_lagna_sign]
        )

        return GocharAnalysis(
            analysis_date=reference_date.strftime("%Y-%m-%d"),
            reference_type="moon_sign",
            birth_chart_reference=birth_chart_reference,
            current_transits=current_transits,
            overall_score=overall_score,
            life_aspects=life_aspects,
            special_transits=special_transits,
            upcoming_transits=upcoming_transits,
            recommendations=recommendations,
            astrologer_notes=astrologer_notes
        )

    def _get_moon_sign(self, birth_chart) -> str:
        """Extract Moon sign from birth chart"""
        for planet in birth_chart.planets:
            if planet.planet == 'Moon':
                return planet.sign
        return birth_chart.lagna.sign  # Fallback

    def _get_current_planetary_positions(
        self,
        target_date: datetime,
        latitude: float,
        longitude: float
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get current planetary positions using the same method as KundaliEngine
        """
        positions = {}

        # Convert to UTC
        if target_date.tzinfo is not None:
            target_date_utc = target_date.astimezone(pytz.UTC)
        else:
            target_date_utc = target_date.replace(tzinfo=pytz.UTC)

        # Calculate Julian Day
        jd = self._datetime_to_jd(target_date_utc)

        # Get each planet's position
        for planet_name, planet_code in self.PLANETS.items():
            if planet_name == 'Ketu':
                continue  # Will calculate from Rahu

            # Calculate position
            result = swe.calc_ut(jd, planet_code)
            longitude = result[0][0]

            # Apply ayanamsa (Lahiri)
            ayanamsa = swe.get_ayanamsa_ut(jd)
            sidereal_longitude = longitude - ayanamsa

            # Normalize to 0-360
            sidereal_longitude = sidereal_longitude % 360

            # Get sign and degree
            sign = self.ZODIAC_SIGNS[int(sidereal_longitude // 30)]
            degree = sidereal_longitude % 30

            positions[planet_name] = {
                'sign': sign,
                'degree': degree,
                'longitude': sidereal_longitude
            }

        # Calculate Ketu (opposite of Rahu)
        if 'Rahu' in positions:
            rahu_longitude = positions['Rahu']['longitude']
            ketu_longitude = (rahu_longitude + 180) % 360
            positions['Ketu'] = {
                'sign': self.ZODIAC_SIGNS[int(ketu_longitude // 30)],
                'degree': ketu_longitude % 30,
                'longitude': ketu_longitude
            }

        return positions

    def _datetime_to_jd(self, dt: datetime) -> float:
        """Convert datetime to Julian Day"""
        return swe.julday(
            dt.year, dt.month, dt.day,
            dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        )

    def _calculate_house_from_sign(self, transit_sign: str, birth_sign: str) -> int:
        """Calculate house number from birth sign"""
        transit_idx = self.ZODIAC_SIGNS.index(transit_sign)
        birth_idx = self.ZODIAC_SIGNS.index(birth_sign)
        return ((transit_idx - birth_idx) % 12) + 1

    def _calculate_planet_transit(
        self,
        planet_name: str,
        planet_data: Dict[str, Any],
        birth_moon_sign: str,
        birth_lagna_sign: str,
        language: str
    ) -> GocharTransitInfo:
        """Calculate transit effects for a single planet"""

        current_sign = planet_data['sign']
        current_degree = planet_data['degree']

        # Calculate houses
        house_from_moon = self._calculate_house_from_sign(current_sign, birth_moon_sign)
        house_from_lagna = self._calculate_house_from_sign(current_sign, birth_lagna_sign)

        # DEBUG LOGGING
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[GOCHAR] {planet_name}: current_sign={current_sign}, moon_sign={birth_moon_sign}, lagna_sign={birth_lagna_sign}")
        logger.info(f"[GOCHAR] {planet_name}: house_from_moon={house_from_moon}, house_from_lagna={house_from_lagna}")

        # Determine nature
        nature = self._get_transit_nature(planet_name, house_from_moon)

        # Get effects
        effect_summary = self._get_effect_summary(
            planet_name, house_from_moon, nature, language, 'summary'
        )
        detailed_effect = self._get_effect_summary(
            planet_name, house_from_moon, nature, language, 'detailed'
        )
        remedies = self._get_remedies(planet_name, house_from_moon, nature, language)

        # Translate planet name to Hindi if needed (but keep sign in English for calculations)
        translated_planet = self.translation_manager.translate(
            f'planets.{planet_name}', language, default=planet_name
        )
        # Keep sign in English - don't translate it as it's used for calculations

        return GocharTransitInfo(
            planet=translated_planet,
            current_sign=current_sign,  # Keep English sign for calculations
            current_degree=round(current_degree, 2),
            house_from_moon=house_from_moon,
            house_from_lagna=house_from_lagna,
            nature=nature,
            effect_summary=effect_summary,
            detailed_effect=detailed_effect,
            remedies=remedies
        )

    def _get_transit_nature(self, planet: str, house_from_moon: int) -> str:
        """Determine if transit is excellent, good, neutral, challenging, or bad"""
        good_houses = self.GOOD_HOUSES_FROM_MOON.get(planet, [])

        if house_from_moon == 11:
            # 11th house is universally excellent
            return 'excellent'
        elif house_from_moon in good_houses:
            if house_from_moon in [2, 5, 7, 9, 10]:
                return 'good'
            else:
                return 'good'
        elif house_from_moon in self.CHALLENGING_HOUSES:
            if house_from_moon == 8:
                return 'challenging'
            else:
                return 'bad'
        else:
            return 'neutral'

    def _get_effect_summary(
        self,
        planet: str,
        house: int,
        nature: str,
        language: str,
        summary_type: str
    ) -> str:
        """Get effect summary for planet transit"""
        # Import Hindi effects if needed
        if language == 'hi':
            try:
                from gochar_effects_hi import GOCHAR_TRANSIT_EFFECTS as effects
            except ImportError:
                effects = GOCHAR_TRANSIT_EFFECTS
        else:
            effects = GOCHAR_TRANSIT_EFFECTS

        # Get effect from dictionary
        effect = effects.get(planet, {}).get(house, {})

        if summary_type == 'summary':
            return effect.get('summary', f"{planet} in {house}th house from Moon")
        elif summary_type == 'detailed':
            return effect.get('detailed', self._get_generic_detailed_effect(planet, house, nature))

        return effect.get('summary', f"{planet} in {house}th house from Moon")

    def _get_default_effect(
        self,
        planet: str,
        house: int,
        nature: str,
        summary_type: str
    ) -> str:
        """Get default effect in English when translation not available"""

        effects = self._get_all_planet_effects()

        if summary_type == 'summary':
            return effects.get(planet, {}).get(house, {}).get('summary', f"{planet} in {house}th house from Moon")
        else:
            return effects.get(planet, {}).get(house, {}).get('detailed', self._get_generic_detailed_effect(planet, house, nature))

    def _get_generic_detailed_effect(self, planet: str, house: int, nature: str) -> str:
        """Generate a generic detailed effect when specific not available"""

        nature_text = {
            'excellent': 'This is an exceptionally favorable transit that brings significant positive outcomes.',
            'good': 'This is a beneficial transit that supports growth and positive developments.',
            'neutral': 'This transit produces mixed results and requires balanced approach.',
            'challenging': 'This transit presents challenges that require patience and careful handling.',
            'bad': 'This is a difficult transit that requires caution and remedial measures.'
        }

        base = f"{planet} is transiting the {house}th house from your Moon sign. {nature_text.get(nature, '')} "

        house_meanings = {
            1: "This house represents your personality, physical body, and overall approach to life. Current transits here directly influence your personal identity and how you present yourself to the world.",
            2: "This house governs finances, accumulated wealth, family life, and speech. You may experience significant changes in your financial situation and domestic environment during this transit.",
            3: "This house rules communication, courage, siblings, short journeys, and initiatives. You'll find opportunities to express yourself and may take on new projects or ventures.",
            4: "This house controls home, mother, property, vehicles, and emotional security. Matters related to your residence, land, and inner peace come into focus.",
            5: "This house signifies creativity, children, romance, speculation, and education. Your creative expression and relationships with children may be highlighted.",
            6: "This house represents enemies, diseases, debts, service, and competition. You may face obstacles that require strategy and patience to overcome.",
            7: "This house governs partnerships, marriage, business relationships, and public image. Your interpersonal connections and collaborative efforts are emphasized.",
            8: "This house rules transformation, longevity, inheritance, sudden events, and occult matters. Deep changes and unexpected developments may occur.",
            9: "This house represents luck, higher education, spirituality, teachers, and long journeys. You may feel drawn to philosophical pursuits and personal growth.",
            10: "This house governs career, fame, authority, and public status. Your professional life and public recognition come into sharp focus.",
            11: "This house represents gains, fulfillment of desires, social networks, and elder siblings. This is generally favorable for achieving your goals and expanding your circle.",
            12: "This house rules losses, expenses, foreign lands, isolation, and liberation. You may need to confront hidden matters and make sacrifices."
        }

        return base + " " + house_meanings.get(house, "")

    def _get_all_planet_effects(self) -> Dict[str, Dict[int, Dict[str, str]]]:
        """Get all planet effects dictionary"""
        return GOCHAR_TRANSIT_EFFECTS

    def _get_remedies(self, planet: str, house: int, nature: str, language: str) -> List[str]:
        """Get remedies for planet transit"""
        # Import Hindi effects if needed
        if language == 'hi':
            try:
                from gochar_effects_hi import GOCHAR_TRANSIT_EFFECTS as effects
            except ImportError:
                effects = GOCHAR_TRANSIT_EFFECTS
        else:
            effects = GOCHAR_TRANSIT_EFFECTS

        # Get remedies from dictionary
        effect = effects.get(planet, {}).get(house, {})
        remedies = effect.get('remedies', [])

        if remedies:
            return remedies

        # Fallback to default remedies
        return self._get_default_remedies(planet, house, nature)

    def _get_default_remedies(self, planet: str, house: int, nature: str) -> List[str]:
        """Get default remedies when translation not available"""

        # Planet-specific remedies
        planet_remedies = {
            'Sun': [
                "Offer water to Sun in copper vessel while chanting 'Om Ghrini Suryaya Namah'",
                "Recite Aditya Hridayam stotra on Sundays",
                "Wear red or orange colored clothes on Sundays",
                "Donate wheat, jaggery, or copper to needy on Sundays",
                "Respect and seek blessings from father and father figures"
            ],
            'Moon': [
                "Offer water to Moon on Mondays",
                "Recite 'Om Som Somaya Namah' mantra 108 times daily",
                "Wear white or cream colored clothes on Mondays",
                "Donate rice, sugar, or white clothes to needy on Mondays",
                "Respect and seek blessings from mother and mother figures"
            ],
            'Mars': [
                "Recite 'Om Ang Angarkaya Namah' mantra 108 times on Tuesdays",
                "Offer red flowers or sindoor to Hanuman temple",
                "Wear red colored clothes on Tuesdays",
                "Donate red lentils (masoor dal) or copper to needy on Tuesdays",
                "Serve younger brothers and help those in need of courage"
            ],
            'Mercury': [
                "Recite 'Om Budhaya Namah' mantra 108 times on Wednesdays",
                "Offer green grass or Durva to Lord Ganesha",
                "Wear green colored clothes on Wednesdays",
                "Donate moong dal, green vegetables, or books to students on Wednesdays",
                "Help sisters and cousins with education and communication"
            ],
            'Jupiter': [
                "Recite 'Om Brim Brihaspataye Namah' mantra 108 times on Thursdays",
                "Offer yellow flowers or turmeric to Lord Vishnu or Brihaspati",
                "Wear yellow or saffron colored clothes on Thursdays",
                "Donate yellow sweets, gram dal (chana), or gold to needy on Thursdays",
                "Seek blessings from guru and spiritual teachers"
            ],
            'Venus': [
                "Recite 'Om Shukraya Namah' mantra 108 times on Fridays",
                "Offer white flowers, sandalwood, or perfume to Goddess Lakshmi",
                "Wear white, pink, or light blue colored clothes on Fridays",
                "Donate rice, sugar, curd, or white clothes to needy women on Fridays",
                "Respect and help spouse and partners"
            ],
            'Saturn': [
                "Recite 'Om Sham Shanishcharaya Namah' mantra 108 times on Saturdays",
                "Offer mustard oil and black sesame seeds to Peepal tree or Shani temple",
                "Wear dark blue or black colored clothes on Saturdays",
                "Donate black sesame seeds, mustard oil, iron, or black clothes to needy on Saturdays",
                "Serve the poor, elderly, and disabled people"
            ],
            'Rahu': [
                "Recite 'Om Rahave Namah' mantra 108 times daily",
                "Offer blue flowers or coconut to Lord Shiva",
                "Wear dark blue or smoky grey colored clothes",
                "Donate sesame seeds, mustard oil, or blankets to needy on Saturdays or Wednesdays",
                "Help the poor and work selflessly for society"
            ],
            'Ketu': [
                "Recite 'Om Ketave Namah' mantra 108 times daily",
                "Offer multi-colored flowers or sesame seeds to Lord Ganesha",
                "Wear multi-colored or earthy tone colored clothes",
                "Donate sesame seeds, blankets, or food to dogs and poor people",
                "Practice spirituality and meditation for inner peace"
            ]
        }

        # House-specific additional remedies
        house_remedies = {
            1: "Focus on self-improvement and maintain positive attitude",
            2: "Be mindful of speech and maintain family harmony",
            3: "Practice courage but control anger",
            4: "Maintain peace at home and respect mother",
            5: "Be patient with children and creative pursuits",
            6: "Serve others and maintain good health habits",
            7: "Respect partners and avoid conflicts in relationships",
            8: "Be cautious and maintain ethical conduct",
            9: "Practice spirituality and seek blessings from elders",
            10: "Maintain professional ethics and respect authority",
            11: "Express gratitude and help others succeed",
            12: "Practice detachment and focus on spiritual growth"
        }

        base_remedies = planet_remedies.get(planet, [
            f"Recite {planet} mantra regularly",
            "Practice meditation and spiritual discipline",
            "Perform acts of charity",
            "Maintain positive attitude and patience"
        ])

        # Add house-specific remedy
        house_specific = house_remedies.get(house, "")
        if house_specific:
            return base_remedies + [house_specific]

        return base_remedies

    def _calculate_overall_score(
        self,
        transits: Dict[str, GocharTransitInfo],
        language: str
    ) -> OverallGocharScore:
        """Calculate overall Gochar score using weighted planet approach"""

        # Import Hindi overall messages if needed
        if language == 'hi':
            try:
                from gochar_effects_hi import GOCHAR_OVERALL_MESSAGES as overall_messages
            except ImportError:
                overall_messages = GOCHAR_OVERALL_MESSAGES
        else:
            overall_messages = GOCHAR_OVERALL_MESSAGES

        # Weighted calculation - important planets count more!
        total_score = 0
        max_possible_score = 0
        favorable_weighted = 0
        good_weighted = 0
        neutral_weighted = 0
        challenging_weighted = 0

        for planet_name, transit in transits.items():
            weight = self.PLANET_WEIGHTS.get(planet_name, 1)
            max_possible_score += weight * 2  # Maximum if excellent

            if transit.nature == 'excellent':
                total_score += weight * 2
                favorable_weighted += weight
            elif transit.nature == 'good':
                total_score += weight * 1
                good_weighted += weight
            elif transit.nature == 'neutral':
                total_score += weight * 0.5
                neutral_weighted += weight
            elif transit.nature in ['challenging', 'bad']:
                challenging_weighted += weight
                # No points for challenging/bad

        # Calculate percentage
        percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0

        # Determine verdict with more balanced thresholds
        if percentage >= 65:
            verdict = "EXCELLENT_PERIOD"
            summary = overall_messages.get('excellent_period',
                "This is an excellent period with multiple favorable planetary transits supporting your goals and aspirations.")
        elif percentage >= 50:
            verdict = "FAVORABLE_PERIOD"
            summary = overall_messages.get('favorable_period',
                "This is a favorable period with more beneficial transits than challenging ones. Make the most of positive influences.")
        elif percentage >= 35:
            verdict = "MODERATE_PERIOD"
            summary = overall_messages.get('moderate_period',
                "This is a moderate period with mixed influences. Exercise balanced approach and patience.")
        else:
            verdict = "CHALLENGING_PERIOD"
            summary = overall_messages.get('challenging_period',
                "This is a challenging period requiring caution, patience, and remedial measures to navigate obstacles.")

        # Count actual planets (not weighted)
        favorable = sum(1 for t in transits.values() if t.nature == 'excellent')
        good = sum(1 for t in transits.values() if t.nature == 'good')
        neutral = sum(1 for t in transits.values() if t.nature == 'neutral')
        challenging = sum(1 for t in transits.values() if t.nature in ['challenging', 'bad'])
        total = len(transits)

        return OverallGocharScore(
            favorable_planets=favorable,
            good_planets=good,
            neutral_planets=neutral,
            challenging_planets=challenging,
            total_planets=total,
            percentage=round(percentage, 1),
            verdict=verdict,
            summary=summary
        )

    def _analyze_life_aspects(
        self,
        transits: Dict[str, GocharTransitInfo],
        birth_chart,
        language: str
    ) -> Dict[str, LifeAspectAnalysis]:
        """Analyze different life aspects based on transits"""

        aspects = ['career', 'finance', 'relationships', 'health', 'education']

        aspect_analysis = {}

        for aspect in aspects:
            analysis = self._analyze_single_aspect(aspect, transits, birth_chart, language)
            aspect_analysis[aspect] = analysis

        return aspect_analysis

    def _analyze_single_aspect(
        self,
        aspect: str,
        transits: Dict[str, GocharTransitInfo],
        birth_chart,
        language: str
    ) -> LifeAspectAnalysis:
        """Analyze a single life aspect"""

        # Import Hindi data if needed
        if language == 'hi':
            try:
                from gochar_effects_hi import GOCHAR_ASPECT_PREDICTIONS as aspect_predictions
                from gochar_effects_hi import GOCHAR_BEST_PRACTICES as best_practices
            except ImportError:
                aspect_predictions = GOCHAR_ASPECT_PREDICTIONS
                best_practices = GOCHAR_BEST_PRACTICES
        else:
            aspect_predictions = GOCHAR_ASPECT_PREDICTIONS
            best_practices = GOCHAR_BEST_PRACTICES

        # Planets that influence each aspect
        aspect_planets = {
            'career': ['Sun', 'Mercury', 'Jupiter', 'Saturn'],
            'finance': ['Jupiter', 'Venus', 'Mercury', 'Moon'],
            'relationships': ['Venus', 'Moon', 'Mars', 'Jupiter'],
            'health': ['Sun', 'Moon', 'Mars', 'Saturn'],
            'education': ['Mercury', 'Jupiter', 'Moon']
        }

        # Get influencing planets for this aspect
        influencing_planets = [p for p in aspect_planets.get(aspect, []) if p in transits]

        # Calculate weighted score based on transits
        # Important planets have more influence on the aspect
        total_weight = 0
        weighted_score = 50  # Base score

        for planet in influencing_planets:
            transit = transits[planet]
            weight = self.PLANET_WEIGHTS.get(planet, 1)
            total_weight += weight

            # Weighted scoring
            if transit.nature == 'excellent':
                weighted_score += (10 * (weight / 2))  # Max 15 for Jupiter/Saturn
            elif transit.nature == 'good':
                weighted_score += (5 * (weight / 2))   # Max 7.5 for Jupiter/Saturn
            elif transit.nature == 'neutral':
                weighted_score += 0  # Neutral doesn't change score
            elif transit.nature == 'challenging':
                weighted_score -= (5 * (weight / 2))  # Max -7.5 for Jupiter/Saturn
            elif transit.nature == 'bad':
                weighted_score -= (10 * (weight / 2)) # Max -15 for Jupiter/Saturn

        # Normalize score if we had weighted planets
        score = int(round(max(0, min(100, weighted_score))))
        # Determine status
        if score >= 75:
            status = 'excellent'
        elif score >= 60:
            status = 'good'
        elif score >= 45:
            status = 'moderate'
        elif score >= 30:
            status = 'challenging'
        else:
            status = 'difficult'

        # Get predictions from gochar_effects files
        prediction = aspect_predictions.get(aspect, {}).get(
            status,
            f"The {aspect} aspect is showing {status} conditions based on current planetary transits."
        )
        detailed_prediction = aspect_predictions.get(aspect, {}).get(
            status,
            self._get_default_aspect_prediction(aspect, status)
        )

        # Get best_for and avoid from GOCHAR_BEST_PRACTICES
        aspect_best_practices = best_practices.get(aspect, {})

        # The structure is: {status: [best_for_list, avoid_list]}
        practice_data = aspect_best_practices.get(status, [])

        if practice_data and len(practice_data) >= 2:
            # First element is best_for, second is avoid
            best_for_raw = practice_data[0]
            avoid_raw = practice_data[1]

            # Split by comma if it's a string, otherwise use as-is
            if isinstance(best_for_raw, str):
                best_for = [item.strip() for item in best_for_raw.split(',')]
            else:
                best_for = best_for_raw

            if isinstance(avoid_raw, str):
                avoid = [item.strip() for item in avoid_raw.split(',')]
            else:
                avoid = avoid_raw
        else:
            best_for = []
            avoid = []

        # Get recommendations - use avoid list as recommendations for now
        recommendations_list = [
            f"Focus on: {', '.join(best_for[:3])}" if best_for else "Maintain balance in all matters",
            f"Avoid: {', '.join(avoid[:3])}" if avoid else "Practice caution"
        ]

        # Translate influencing planets to Hindi if needed
        translated_influencing_planets = [
            self.translation_manager.translate(f'planets.{planet}', language, default=planet)
            for planet in influencing_planets
        ]

        return LifeAspectAnalysis(
            score=score,
            status=status,
            influencing_planets=translated_influencing_planets,
            prediction=prediction,
            detailed_prediction=detailed_prediction,
            best_for=best_for,
            avoid=avoid,
            recommendations=recommendations_list
        )

    def _get_default_aspect_prediction(self, aspect: str, status: str) -> str:
        """Get default aspect prediction"""
        predictions = {
            'career': {
                'excellent': 'Outstanding period for career growth and professional success. Promotions, recognition, and new opportunities are highly likely. This is an ideal time to take initiative and pursue ambitious goals.',
                'good': 'Favorable period for career advancement. You may receive recognition for your work and find new opportunities opening up. Continue working hard and maintain professional relationships.',
                'moderate': 'Mixed period for career matters. Some opportunities may arise but also some challenges. Maintain patience and continue consistent effort. Avoid risky career moves.',
                'challenging': 'Challenging period for career matters. You may face obstacles, criticism, or delays. This is a time for patience, strategic planning, and avoiding conflicts at workplace.',
                'difficult': 'Difficult period for career. Professional setbacks are possible. Focus on skill development, maintain low profile, and avoid major career decisions during this time.'
            },
            'finance': {
                'excellent': 'Excellent financial period with strong potential for gains, investments, and prosperity. Money flows easily and financial decisions made now tend to be beneficial. Consider investment opportunities.',
                'good': 'Good financial period. Income is stable and opportunities for growth exist. Favorable time for investments and savings. Avoid excessive spending.',
                'moderate': 'Moderate financial period. Mixed influences mean some gains but also expenses. Exercise caution in spending and avoid speculative investments. Save for future.',
                'challenging': 'Challenging financial period. Unexpected expenses may arise, and income may be less than expected. Cut down unnecessary expenses, avoid loans, and focus on building emergency fund.',
                'difficult': 'Difficult financial period requiring extreme caution. Major expenses possible, income may be affected. Avoid all investments, loans, and big purchases. Focus on preserving existing resources.'
            },
            'relationships': {
                'excellent': 'Wonderful period for relationships. Harmony in existing relationships, opportunities for new meaningful connections, and favorable for marriage proposals. Express love and strengthen bonds.',
                'good': 'Good period for relationships. Generally harmonious interactions with loved ones. Good time to resolve past issues and strengthen connections. Socially active period.',
                'moderate': 'Mixed period for relationships. Some harmony but also potential misunderstandings. Practice patience in interactions, avoid confrontations, and communicate clearly.',
                'challenging': 'Challenging period for relationships. Misunderstandings, conflicts, or emotional distances possible. Avoid arguments, practice patience, and give space to partners when needed.',
                'difficult': 'Difficult period for relationships. Emotional turbulence, conflicts possible. Avoid major relationship decisions, practice forgiveness, and focus on self-improvement.'
            },
            'health': {
                'excellent': 'Excellent health period. High energy levels, strong immunity, and overall well-being. Great time to start fitness routines and healthy habits. Maintain positive lifestyle.',
                'good': 'Good health period. Generally stable health and good energy levels. Maintain healthy habits, regular exercise, and balanced diet. Preventive care is beneficial now.',
                'moderate': 'Moderate health period. Some ups and downs in energy levels possible. Pay attention to diet, exercise regularly, and get adequate rest. Don\'t neglect minor health issues.',
                'challenging': 'Challenging period for health. Stress, fatigue, or minor ailments possible. Prioritize rest, avoid overexertion, maintain healthy diet, and consider preventive health checkups.',
                'difficult': 'Difficult period for health requiring extra care. Vulnerable to illnesses, accidents, or chronic issues. Be cautious, avoid risky activities, prioritize rest, and seek medical attention promptly if needed.'
            },
            'education': {
                'excellent': 'Outstanding period for education and learning. Excellent focus, retention, and academic performance. Favorable for exams, competitions, and admission in desired institutions.',
                'good': 'Good period for education. Strong learning capacity and academic progress. Favorable for studies, exams, and intellectual pursuits. Stay consistent and focused.',
                'moderate': 'Moderate period for education. Some progress but also distractions. Maintain discipline, focus on studies, avoid procrastination, and seek help when needed.',
                'challenging': 'Challenging period for education. Difficulty concentrating, retaining information, or performing well academically. Extra effort required, avoid distractions, consider tutoring.',
                'difficult': 'Difficult period for education. Major obstacles in learning, poor concentration, academic setbacks. Put in extra effort, avoid important exams if possible, focus on strengthening fundamentals.'
            }
        }

        return predictions.get(aspect, {}).get(status, f"{aspect} is showing {status} conditions.")

    def _get_default_best_for(self, aspect: str) -> str:
        """Get default 'best for' list"""
        return {
            'career': 'Promotion, Job change, New projects, Professional networking',
            'finance': 'Investment, Savings, Business expansion, Financial planning',
            'relationships': 'Marriage, New relationships, Social gatherings, Resolving conflicts',
            'health': 'Fitness routines, Healthy diet, Preventive care, Stress management',
            'education': 'Exams, Competitive tests, Learning new skills, Academic competitions'
        }.get(aspect, 'Growth and progress')

    def _get_default_avoid(self, aspect: str) -> str:
        """Get default 'avoid' list"""
        return {
            'career': 'Job hopping, Confrontations, Risky ventures',
            'finance': 'Speculation, Big loans, Impulsive purchases',
            'relationships': 'Arguments, Major commitments if unsure, Ego conflicts',
            'health': 'Overexertion, Junk food, Irregular sleep, Risky activities',
            'education': 'Distractions, Procrastination, Cramming, Multiple subjects'
        }.get(aspect, 'Risky decisions')

    def _get_default_aspect_recommendations(self, aspect: str, status: str) -> List[str]:
        """Get default aspect recommendations"""

        recommendations = {
            'career': {
                'excellent': [
                    "Pursue promotion or ask for raise - excellent chance of success",
                    "Apply for new jobs or switch companies - favorable period",
                    "Start new business ventures - stars support entrepreneurial initiatives",
                    "Take on leadership roles and additional responsibilities",
                    "Network with industry leaders and mentors"
                ],
                'good': [
                    "Good time for job performance reviews and appraisals",
                    "Update your resume and LinkedIn profile",
                    "Consider job change if unhappy - moderate support",
                    "Take on new projects at work",
                    "Build professional relationships"
                ],
                'moderate': [
                    "Focus on current job stability rather than seeking changes",
                    "Enhance skills through training and certifications",
                    "Maintain good relationships with colleagues and superiors",
                    "Avoid risky career moves or confrontations at workplace",
                    "Work consistently but don't expect dramatic results"
                ],
                'challenging': [
                    "Maintain low profile and avoid conflicts at workplace",
                    "Focus on skill development rather than seeking recognition",
                    "Don't make major career decisions during this period",
                    "Be patient with career progress - obstacles are temporary",
                    "Consider taking up additional responsibilities to prove worth"
                ],
                'difficult': [
                    "Avoid changing jobs or making major career decisions",
                    "Focus on completing existing projects efficiently",
                    "Be prepared for criticism - take it constructively",
                    "Maintain discipline and professional ethics despite challenges",
                    "This too shall pass - maintain persistence and patience"
                ]
            },
            'finance': {
                'excellent': [
                    "Excellent time for investments - consider equity, mutual funds",
                    "Review and optimize investment portfolio",
                    "Can apply for loans - favorable terms possible",
                    "Consider buying property or making big purchases",
                    "Save and invest surplus income wisely"
                ],
                'good': [
                    "Good period for savings and conservative investments",
                    "Can consider moderate investments in fixed deposits",
                    "Avoid speculative investments but stable growth is possible",
                    "Review financial goals and adjust savings plan",
                    "Build emergency fund if not already done"
                ],
                'moderate': [
                    "Focus on saving rather than spending",
                    "Avoid major investments or speculative ventures",
                    "Cut down unnecessary expenses",
                    "Build cash reserves for emergencies",
                    "Review and stick to budget strictly"
                ],
                'challenging': [
                    "Avoid all investments and speculative activities",
                    "Cut down expenses to bare minimum",
                    "Avoid taking loans or borrowing money",
                    "Focus on preserving existing wealth",
                    "Delay major purchases if possible"
                ],
                'difficult': [
                    "Strict austerity measures needed - avoid all non-essential spending",
                    "Do not take new loans or credit",
                    "Liquidate risky investments if possible",
                    "Focus on debt repayment if any",
                    "Seek professional financial advice if needed"
                ]
            },
            'relationships': {
                'excellent': [
                    "Excellent time for marriage proposals - accept favorable offers",
                    "Strengthen bonds with spouse/partner through quality time",
                    "Expand social circle and network",
                    "Resolve past conflicts through open communication",
                    "Attend social gatherings and family functions"
                ],
                'good': [
                    "Good period for romantic relationships",
                    "Express love and affection to partner",
                    "Social activities and gatherings bring joy",
                    "Resolve minor misunderstandings through dialogue",
                    "Spend quality time with family"
                ],
                'moderate': [
                    "Maintain harmony through patience and understanding",
                    "Avoid confrontations in relationships",
                    "Think twice before making relationship commitments",
                    "Practice forgiveness and let go of ego",
                    "Focus on giving space to partner"
                ],
                'challenging': [
                    "Avoid arguments and conflicts in relationships",
                    "Don't make major relationship decisions",
                    "Practice patience and emotional control",
                    "Seek counseling if relationship issues persist",
                    "Focus on self-growth rather than expecting from others"
                ],
                'difficult': [
                    "Maintain low profile in social life",
                    "Avoid new romantic entanglements",
                    "Focus on spiritual growth rather than emotional needs",
                    "Practice detachment and emotional maturity",
                    "This is a testing period - remain calm and composed"
                ]
            },
            'health': {
                'excellent': [
                    "Excellent time to start new fitness routines",
                    "Focus on preventive health checkups even if feeling fine",
                    "Build healthy habits - diet, exercise, sleep",
                    "Consider detox or wellness programs",
                    "Maintain positive mental attitude through meditation"
                ],
                'good': [
                    "Good period for health - maintain healthy lifestyle",
                    "Start moderate exercise routines",
                    "Focus on balanced diet and regular sleep",
                    "Address minor health issues before they escalate",
                    "Practice stress management techniques"
                ],
                'moderate': [
                    "Pay attention to body signals - don't ignore symptoms",
                    "Avoid overexertion and excessive physical stress",
                    "Maintain regular sleep and eating schedules",
                    "Focus on preventive healthcare measures",
                    "Avoid extreme diets or intense workout routines"
                ],
                'challenging': [
                    "Take extra care of health - prioritize wellness",
                    "Avoid risky activities and extreme sports",
                    "Get regular health checkups",
                    "Focus on stress management and adequate rest",
                    "Address health issues promptly - don't delay"
                ],
                'difficult': [
                    "Maximum health caution needed",
                    "Avoid all strenuous activities",
                    "Get comprehensive health examination",
                    "Follow medical advice strictly",
                    "Focus on rest, recovery, and healing practices"
                ]
            },
            'education': {
                'excellent': [
                    "Excellent time for competitive exams",
                    "Apply to desired colleges or courses",
                    "Deep learning possible - pursue advanced studies",
                    "Participate in academic competitions",
                    "Take up new courses or skill development programs"
                ],
                'good': [
                    "Good period for studies and academic performance",
                    "Focus on weak subjects for improvement",
                    "Join study groups or coaching if needed",
                    "Set academic goals and work towards them",
                    "Develop good study habits"
                ],
                'moderate': [
                    "Focus on consistent study routine",
                    "Avoid distractions and maintain discipline",
                    "Don't take on too many subjects at once",
                    "Seek help from teachers or mentors when stuck",
                    "Practice previous year question papers"
                ],
                'challenging': [
                    "Avoid important exams if possible",
                    "Focus on strengthening basics",
                    "Extra effort required for understanding concepts",
                    "Consider taking guidance from tutors",
                    "Avoid comparison with others - focus on personal progress"
                ],
                'difficult': [
                    "Extremely challenging period for education",
                    "Focus on revision rather than new learning",
                    "Avoid major academic decisions",
                    "Practice patience and persistent effort",
                    "Consider breaking down study material into smaller chunks"
                ]
            }
        }

        aspect_recommendations = recommendations.get(aspect, {}).get(status, [
            f"This {status} period requires balanced approach in {aspect} matters.",
            "Focus on steady progress rather than dramatic results.",
            "Seek expert guidance if needed.",
            "Maintain discipline and patience."
        ])

        return aspect_recommendations

    def _check_special_transits(
        self,
        transits: Dict[str, GocharTransitInfo],
        birth_moon_sign: str,
        birth_chart,
        reference_date: datetime,
        language: str
    ) -> Dict[str, SpecialTransit]:
        """Check for special transits like Sade Sati, Kantak Shani"""

        special = {}

        # Check Saturn transits
        saturn_transit = transits.get('Saturn')
        if saturn_transit:
            # Sade Sati check (12th, 1st, 2nd from Moon)
            saturn_house = saturn_transit.house_from_moon

            if saturn_house in [12, 1, 2]:
                phases = {
                    12: 'rising',
                    1: 'peak',
                    2: 'setting'
                }
                phase_names = {
                    'rising': 'Rising Phase (First 2.5 years)',
                    'peak': 'Peak Phase (Middle 2.5 years)',
                    'setting': 'Setting Phase (Last 2.5 years)'
                }

                started, ends = self._estimate_sade_sati_dates(
                    saturn_house, birth_moon_sign, reference_date
                )

                # Translate Saturn for descriptions
                saturn_hi = self.translation_manager.translate(
                    'planets.Saturn', language, default='Saturn'
                )
                default_desc = f"{saturn_hi} is transiting {saturn_house}th house from your Moon sign, indicating Sade Sati period."

                special['sade_sati'] = SpecialTransit(
                    is_active=True,
                    name="Sade Sati",
                    phase=phase_names[phases[saturn_house]],
                    house=saturn_house,
                    started=started,
                    ends=ends,
                    description=self._translate("gochar_sade_sati_description", language, default_desc),
                    detailed_description=self._translate(f"gochar_sade_sati_{phases[saturn_house]}", language,
                        self._get_sade_sati_detailed(phases[saturn_house])),
                    remedies=self._get_sade_sati_remedies(language),
                    severity='moderate' if saturn_house == 2 else 'severe'
                )

            # Kantak Shani check (4th from Moon)
            if saturn_house == 4:
                started, ends = self._estimate_kantak_shani_dates(
                    birth_moon_sign, reference_date
                )

                # Translate Saturn for descriptions
                saturn_hi = self.translation_manager.translate(
                    'planets.Saturn', language, default='Saturn'
                )
                default_desc = f"{saturn_hi} is transiting the 4th house from your Moon sign, causing Kantak Shani."

                special['kantak_shani'] = SpecialTransit(
                    is_active=True,
                    name="Kantak Shani",
                    house=4,
                    started=started,
                    ends=ends,
                    description=self._translate("gochar_kantak_shani_description", language, default_desc),
                    detailed_description=self._translate("gochar_kantak_shani_detailed", language,
                        "Kantak Shani creates mental stress, domestic problems, and obstacles in matters related to home, mother, property, and peace of mind. This period requires patience, resilience, and consistent remedial measures. Effects are similar to Sade Sati but focused on emotional and domestic spheres."),
                    remedies=[
                        "Recite Hanuman Chalisa daily",
                        "Offer oil to Shani temple on Saturdays",
                        "Wear dark blue or black clothing",
                        "Help the poor and needy",
                        "Avoid conflicts with family members",
                        "Practice meditation for mental peace"
                    ],
                    severity='moderate'
                )

        # If no special transits active, add placeholder
        if not special:
            special['none'] = SpecialTransit(
                is_active=False,
                description="No major special transits currently active.",
                detailed_description="Currently, you are not under the influence of major special transits like Sade Sati or Kantak Shani. Continue to focus on individual planet transit effects.",
                remedies=[]
            )

        return special

    def _estimate_sade_sati_dates(
        self,
        current_house: int,
        birth_moon_sign: str,
        reference_date: datetime
    ) -> Tuple[str, str]:
        """Estimate Sade Sati start and end dates"""
        # Simplified estimation - Saturn stays ~2.5 years per sign
        moon_idx = self.ZODIAC_SIGNS.index(birth_moon_sign)

        if current_house == 12:
            # Rising phase - started ~2.5 years ago, ends in ~5 years
            started = (reference_date - timedelta(days=365*2)).strftime("%Y-%m")
            ends = (reference_date + timedelta(days=365*5)).strftime("%Y-%m")
        elif current_house == 1:
            # Peak phase - started ~2.5 years ago, ends in ~2.5 years
            started = (reference_date - timedelta(days=365*2)).strftime("%Y-%m")
            ends = (reference_date + timedelta(days=365*2)).strftime("%Y-%m")
        else:  # house == 2
            # Setting phase - started ~5 years ago, ends in ~2.5 years
            started = (reference_date - timedelta(days=365*5)).strftime("%Y-%m")
            ends = (reference_date + timedelta(days=365*2)).strftime("%Y-%m")

        return started, ends

    def _estimate_kantak_shani_dates(
        self,
        birth_moon_sign: str,
        reference_date: datetime
    ) -> Tuple[str, str]:
        """Estimate Kantak Shani dates"""
        # Kantak Shani lasts ~2.5 years
        started = (reference_date - timedelta(days=365)).strftime("%Y-%m")
        ends = (reference_date + timedelta(days=365*1.5)).strftime("%Y-%m")
        return started, ends

    def _get_sade_sati_detailed(self, phase: str) -> str:
        """Get detailed Sade Sati description by phase"""
        descriptions = {
            'rising': "Sade Sati Rising Phase: This is the beginning phase when Saturn enters the 12th house from your Moon. You may experience anxiety, fear of the unknown, and anticipation of challenges. Financial expenses may increase, and some obstacles may arise. This phase prepares you for the main period. Focus on building resilience, practicing patience, and starting remedial measures.",
            'peak': "Sade Sati Peak Phase: This is the most intense phase when Saturn transits over your Moon sign. You may face significant challenges in health, career, finance, and relationships. Mental stress, physical ailments, professional setbacks, and domestic problems are possible. This is a testing period that requires maximum patience, discipline, and consistent remedies. Be extremely cautious in all matters.",
            'setting': "Sade Sati Setting Phase: This is the final phase when Saturn is in the 2nd house from your Moon. The intense challenges begin to subside, and relief becomes visible. Financial situation improves, health stabilizes, and opportunities reappear. However, family matters and speech require careful handling. Continue remedies and maintain patience as you near the end of this transformative period."
        }
        return descriptions.get(phase, "")

    def _get_sade_sati_remedies(self, language: str) -> List[str]:
        """Get Sade Sati remedies"""
        remedies = self._translate("gochar_sade_sati_remedies", language, fallback=None)
        if remedies is None:
            return [
                "Recite Hanuman Chalisa daily (preferably on Saturdays)",
                "Offer mustard oil and black sesame seeds to Shani temple",
                "Wear a Blue Sapphire (Neelam) after expert consultation",
                "Feed birds and stray animals regularly",
                "Serve the poor, elderly, and disabled people",
                "Chant Shani mantra: 'Om Sham Shanishcharaya Namah' (108 times daily)",
                "Avoid alcohol, non-vegetarian food, and harsh speech",
                "Maintain moral conduct and speak truth always",
                "Wear dark blue or black clothes on Saturdays",
                "Read or listen to Satyanarayan Katha regularly"
            ]
        if isinstance(remedies, str):
            return [remedies]
        return remedies

    def _get_upcoming_transits(
        self,
        reference_date: datetime,
        birth_moon_sign: str,
        latitude: float,
        longitude: float,
        language: str,
        months_ahead: int = 6
    ) -> List[UpcomingTransit]:
        """Get upcoming significant transits"""

        upcoming = []

        # OPTIMIZATION: Calculate all planetary positions for both dates at once
        # instead of calling _get_planet_position_on_date multiple times
        current_month_positions = self._get_current_planetary_positions(reference_date, latitude, longitude)
        next_month_positions = self._get_current_planetary_positions(
            reference_date + timedelta(days=30), latitude, longitude
        )

        # Check when Jupiter will change sign (happens every ~12 months)
        jupiter_current = current_month_positions.get('Jupiter', {})
        jupiter_next_month = next_month_positions.get('Jupiter', {})

        if jupiter_current.get('sign') != jupiter_next_month.get('sign'):
            # Translate planet name and sign
            jupiter_hi = self.translation_manager.translate(
                'planets.Jupiter', language, default='Jupiter'
            )
            sign_hi = self.translation_manager.translate(
                f'zodiac_signs.{jupiter_next_month["sign"]}', language, default=jupiter_next_month['sign']
            )
            house = self._calculate_house_from_sign(jupiter_next_month['sign'], birth_moon_sign)
            enters_text = self.translation_manager.translate(
                'gochar_enters', language, default='Enters'
            )
            th_text = self.translation_manager.translate(
                'gochar_th', language, default='th'
            )
            from_moon_text = self.translation_manager.translate(
                'gochar_from_moon', language, default='from Moon'
            )
            event_hi = f"{enters_text} {sign_hi} ({house}{th_text} {from_moon_text})"

            upcoming.append(UpcomingTransit(
                planet=jupiter_hi,
                event=event_hi,
                date=(reference_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                duration="~1 year",
                expected_effects=[
                    "Major shift in luck and opportunities",
                    "New areas of growth and expansion",
                    "Changes in fortune and prosperity"
                ],
                recommendations=[
                    "Prepare for positive changes",
                    "Plan important initiatives for this period",
                    "Make the most of Jupiter's beneficial influence"
                ],
                importance_level="high"
            ))

        # Saturn sign change (every ~2.5 years)
        saturn_current = current_month_positions.get('Saturn', {})
        saturn_next_month = next_month_positions.get('Saturn', {})

        if saturn_current.get('sign') != saturn_next_month.get('sign'):
            # Translate planet name and sign
            saturn_hi = self.translation_manager.translate(
                'planets.Saturn', language, default='Saturn'
            )
            sign_hi = self.translation_manager.translate(
                f'zodiac_signs.{saturn_next_month["sign"]}', language, default=saturn_next_month['sign']
            )
            house = self._calculate_house_from_sign(saturn_next_month['sign'], birth_moon_sign)
            enters_text = self.translation_manager.translate(
                'gochar_enters', language, default='Enters'
            )
            th_text = self.translation_manager.translate(
                'gochar_th', language, default='th'
            )
            from_moon_text = self.translation_manager.translate(
                'gochar_from_moon', language, default='from Moon'
            )
            event_hi = f"{enters_text} {sign_hi} ({house}{th_text} {from_moon_text})"

            upcoming.append(UpcomingTransit(
                planet=saturn_hi,
                event=event_hi,
                date=(reference_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                duration="~2.5 years",
                expected_effects=[
                    "Long-term shift in life patterns",
                    "New challenges and responsibilities",
                    "Karmic lessons and maturation"
                ],
                recommendations=[
                    "Prepare for serious commitments",
                    "Build resilience and patience",
                    "Address pending karma through service and discipline"
                ],
                importance_level="critical"
            ))

        return upcoming

    def _get_planet_position_on_date(
        self,
        planet: str,
        target_date: datetime,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Get planet position on a specific date"""
        positions = self._get_current_planetary_positions(target_date, latitude, longitude)
        return positions.get(planet, {})

    def _generate_recommendations(
        self,
        transits: Dict[str, GocharTransitInfo],
        special_transits: Dict[str, SpecialTransit],
        overall_score: OverallGocharScore,
        language: str
    ) -> GocharRecommendations:
        """Generate recommendations based on transits"""

        # Import Hindi recommendations if needed
        if language == 'hi':
            try:
                from gochar_effects_hi import GOCHAR_RECOMMENDATIONS as recommendations
            except ImportError:
                recommendations = GOCHAR_RECOMMENDATIONS
        else:
            recommendations = GOCHAR_RECOMMENDATIONS

        # Map verdict to recommendation key
        verdict_map = {
            'EXCELLENT_PERIOD': 'excellent',
            'FAVORABLE_PERIOD': 'favorable',
            'MODERATE_PERIOD': 'moderate',
            'CHALLENGING_PERIOD': 'challenging'
        }

        rec_key = verdict_map.get(overall_score.verdict, 'moderate')
        rec_data = recommendations.get(rec_key, {})

        do_this_month = rec_data.get('do_this_month', [])
        avoid_this_month = rec_data.get('avoid_this_month', [])
        general_advice = rec_data.get('general_advice', [])

        # Collect remedies from all transits
        all_remedies = []
        for transit in transits.values():
            if transit.nature in ['challenging', 'bad']:
                all_remedies.extend(transit.remedies[:2])  # Top 2 remedies

        # Add special transit remedies
        for special in special_transits.values():
            if special.is_active and special.remedies:
                all_remedies.extend(special.remedies[:3])

        # Remove duplicates and limit
        all_remedies = list(dict.fromkeys(all_remedies))[:10]

        return GocharRecommendations(
            do_this_month=do_this_month,
            avoid_this_month=avoid_this_month,
            general_advice=general_advice,
            remedies=all_remedies,
            color_therapy=self._get_color_therapy(transits, language),
            gemstone_suggestion=self._get_gemstone_suggestion(transits, language),
            mantra_suggestion=self._get_mantra_suggestion(transits, language)
        )

    def _get_color_therapy(
        self,
        transits: Dict[str, GocharTransitInfo],
        language: str
    ) -> str:
        """Get color therapy suggestion"""
        # Find most challenging planet
        challenging = [t for t in transits.values() if t.nature in ['challenging', 'bad']]

        if challenging:
            # Return color based on most challenging planet
            planet_colors = {
                'Sun': 'Red and orange',
                'Moon': 'White and cream',
                'Mars': 'Bright red',
                'Mercury': 'Green',
                'Jupiter': 'Yellow and saffron',
                'Venus': 'White, pink and light blue',
                'Saturn': 'Dark blue, black and grey',
                'Rahu': 'Dark brown and smoky grey',
                'Ketu': 'Multi-color and earthy tones'
            }

            worst = challenging[0]
            color = planet_colors.get(worst.planet, 'White')

            return f"Wear {color} colored clothes on weekdays to strengthen {worst.planet}'s positive influences and mitigate challenges."

        return "Wear bright, cheerful colors to maintain positive energy."

    def _get_gemstone_suggestion(
        self,
        transits: Dict[str, GocharTransitInfo],
        language: str
    ) -> str:
        """Get gemstone suggestion"""
        return "Consult a qualified astrologer before wearing any gemstone. Gemstones should only be worn after proper analysis of birth chart and current transits."

    def _get_mantra_suggestion(
        self,
        transits: Dict[str, GocharTransitInfo],
        language: str
    ) -> str:
        """Get mantra suggestion"""

        mantras = {
            'Sun': 'Om Ghrini Suryaya Namah',
            'Moon': 'Om Som Somaya Namah',
            'Mars': 'Om Ang Angarkaya Namah',
            'Mercury': 'Om Budhaya Namah',
            'Jupiter': 'Om Brim Brihaspataya Namah',
            'Venus': 'Om Shum Shukraya Namah',
            'Saturn': 'Om Sham Shanishcharaya Namah',
            'Rahu': 'Om Rahave Namah',
            'Ketu': 'Om Ketave Namah'
        }

        # Find challenging planets
        challenging = [t.planet for t in transits.values() if t.nature in ['challenging', 'bad']]

        if challenging:
            suggestions = [f"{mantras.get(p, 'Om')} - For {p}" for p in challenging[:2]]
            return " | ".join(suggestions)

        return "Om Namah Shivaya - General peace and protection"

    def _generate_astrologer_notes(
        self,
        transits: Dict[str, GocharTransitInfo],
        special_transits: Dict[str, SpecialTransit],
        overall_score: OverallGocharScore,
        language: str
    ) -> AstrologerNotes:
        """Generate notes for astrologers"""

        key_points = []

        # Overall assessment
        key_points.append(f"Overall {overall_score.verdict}: {overall_score.percentage}% favorable")

        # Best transits
        best = [t for t in transits.values() if t.nature == 'excellent']
        if best:
            key_points.append(f"Best transit: {best[0].planet} in {best[0].house_from_moon}th from Moon")

        # Worst transits
        worst = [t for t in transits.values() if t.nature in ['challenging', 'bad']]
        if worst:
            key_points.append(f"Most challenging: {worst[0].planet} in {worst[0].house_from_moon}th from Moon")

        # Special transit notes
        for name, special in special_transits.items():
            if special.is_active and name != 'none':
                key_points.append(f"{special.name} is active ({special.severity if special.severity else 'moderate'} intensity)")

        # Priority aspects based on overall score
        if overall_score.verdict in ['EXCELLENT_PERIOD', 'FAVORABLE_PERIOD']:
            priority_aspects = ['Career (Highest Priority)', 'Finance (High Priority)',
                'Relationships (Medium Priority)', 'Health (Maintain)']
        elif overall_score.verdict == 'MODERATE_PERIOD':
            priority_aspects = ['Career (Caution needed)', 'Finance (Conservative approach)',
                'Health (Pay attention)', 'Relationships (Maintain harmony)']
        else:
            priority_aspects = ['Health (Top Priority)', 'Finance (Extreme caution)',
                'Career (Maintain status quo)', 'Relationships (Avoid conflicts)']

        # Technical observations
        technical_observations = []

        # Check mutual aspects
        technical_observations.append("All calculations based on Lahiri Ayanamsa")
        technical_observations.append("Moon sign used as primary reference for Gochar")

        # Jupiter-Saturn combined effect
        jupiter = transits.get('Jupiter')
        saturn = transits.get('Saturn')
        if jupiter and saturn:
            if jupiter.nature == 'good' and saturn.nature in ['challenging', 'bad']:
                technical_observations.append("Jupiter's benefic effect may partially mitigate Saturn's challenges")
            elif jupiter.nature in ['challenging', 'bad'] and saturn.nature in ['challenging', 'bad']:
                technical_observations.append("Both Jupiter and Saturn are unfavorable - major caution required")

        return AstrologerNotes(
            key_points=key_points,
            priority_aspects=priority_aspects,
            technical_observations=technical_observations,
            special_considerations=[
                "Remedies should be performed consistently for best results",
                "Transit effects manifest based on dasha period and birth chart strength",
                "Individual results may vary based on personal karma and actions"
            ]
        )

    def _prepare_transit_chart_data_for_svg_v2(
        self,
        gochar_analysis,
        lang: str = 'en'
    ) -> Dict:
        """
        Prepare transit chart data in North Indian format for SVG generator.
        Fixed version - uses actual transit sign for house numbering.

        This creates a gochar chart showing:
        - Moon sign as House 1 (reference point for gochar)
        - Transit planets in their actual transit sign houses
        - Color coding by nature (green=good, red=challenging)
        """
        from svg_chart_generator import get_planet_abbreviation, PLANET_COLORS

        # Add transit nature colors
        TRANSIT_NATURE_COLORS = {
            'excellent': "#290ea3",  # Green
            'good': "#e309a2",  # Light green
            'neutral': "#f52e0b",  # Gray
            'challenging': '#f97316',  # Orange
            'bad': '#dc2626'  # Red
        }

        moon_sign = gochar_analysis.birth_chart_reference.moon_sign
        moon_sign_idx = self.ZODIAC_SIGNS.index(moon_sign)

        # Create house data structure
        house_data = {str(h): {"sign_num": "", "planets": []} for h in range(1, 13)}

        # Populate house numbers with ACTUAL TRANSIT SIGNS
        for house_num in range(1, 13):
            house_sign_index = (moon_sign_idx + house_num - 1) % 12
            house_data[str(house_num)]["sign_num"] = house_sign_index + 1  # Convert to 1-based sign number

        # Add Moon (Lagna) to House 1
        if lang == 'hi':
            # Use full Hindi names
            moon_name = self.translation_manager.translate(
                'planets.Moon', lang, default='Moon'
            )
            lagna_name = self.translation_manager.translate(
                'planets.Lagna', lang, default='Lagna'
            )
            moon_display = f"{moon_name} ({lagna_name})"
        else:
            # For English, use abbreviations
            moon_abbr = get_planet_abbreviation("Moon", lang)
            moon_display = f"{moon_abbr} (Lagna)"

        house_data['1']["planets"].append({
            "text": moon_display,
            "color": PLANET_COLORS.get("Moon", "#333")
        })

        # Add transit planets to their ACTUAL TRANSIT SIGN HOUSES
        # CRITICAL FIX: Make a copy to avoid mutating original current_transits dict
        current_transits_copy = dict(gochar_analysis.current_transits)

        for planet_name, transit_info in current_transits_copy.items():
            actual_sign = transit_info.current_sign
            actual_sign_idx = self.ZODIAC_SIGNS.index(actual_sign)

            # Calculate house from Moon for this transit sign
            house_from_moon = ((actual_sign_idx - moon_sign_idx) % 12) + 1

            # DEBUG LOGGING
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[GOCHAR_PLANET] {planet_name}: actual_sign={actual_sign} (idx={actual_sign_idx}), moon_sign_idx={moon_sign_idx}")
            logger.info("[GOCHAR_PLANET] house_from_moon={}".format(house_from_moon))

            # Get color based on transit nature
            nature_color = TRANSIT_NATURE_COLORS.get(transit_info.nature, '#333')

            # For Hindi, use full planet names instead of abbreviations
            if lang == 'hi':
                # Use translation_manager to get full Hindi planet names
                # Try to get from planets category first, then fallback to direct key
                planet_display = self.translation_manager.translate(
                    f'planets.{planet_name}', lang, default=planet_name
                )
            else:
                # For English, use abbreviations
                abbr = get_planet_abbreviation(planet_name, lang)
                planet_display = abbr

            degree = transit_info.current_degree

            display_text = f"{planet_display} {degree:.2f}°"
            planet_info = {
                "text": display_text,
                "color": nature_color  # Use nature-based color
            }
            house_data[str(house_from_moon)]["planets"].append(planet_info)

        return house_data

    def _translate(self, key: str, language: str, category: str = None, fallback: str = None) -> str:
        """Get translation for a key"""
        try:
            # First, try to get all translations for the language
            all_translations = self.translation_manager.translations.get(language, {})

            # If category is specified, get that category first
            if category:
                category_data = all_translations.get(category, {})
                if isinstance(category_data, dict) and key in category_data:
                    result = category_data[key]
                    return result if not isinstance(result, dict) else result

            # Try direct key access at root level
            if key in all_translations:
                result = all_translations[key]
                # Return the result (could be string, dict, etc.)
                # Don't convert dict to string - let caller handle it
                return result

            # If not found, try fallback
            return fallback if fallback is not None else key
        except Exception as e:
            # Log error and return fallback
            if fallback:
                return fallback
            return key
