"""
Divisional Charts Module

This module provides calculations for various divisional charts (Varga charts)
with focus on Navamsa (D9) chart for spiritual and marital analysis.
"""

from typing import Dict, List, Any
import swisseph as swe
import traceback

class DivisionalCharts:
    """
    Divisional charts calculator with emphasis on Navamsa (D9) chart
    """

    # Zodiac signs
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    # Navamsa sequence for each sign
    NAVAMSA_SEQUENCE = {
        'Aries': ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius'],
        'Taurus': ['Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo'],
        'Gemini': ['Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini'],
        'Cancer': ['Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'],
        'Leo': ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius'],
        'Virgo': ['Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo'],
        'Libra': ['Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini'],
        'Scorpio': ['Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'],
        'Sagittarius': ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius'],
        'Capricorn': ['Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo'],
        'Aquarius': ['Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces', 'Aries', 'Taurus', 'Gemini'],
        'Pisces': ['Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    }

    # Planet significance in Navamsa
    NAVAMSA_SIGNIFICANCE = {
        'Sun': 'Soul, self-expression, spiritual authority',
        'Moon': 'Mind, emotions, inner happiness',
        'Mars': 'Energy, spouse nature, passion',
        'Mercury': 'Communication, intellect, learning',
        'Jupiter': 'Wisdom, dharma, spiritual growth',
        'Venus': 'Love, marriage, artistic abilities',
        'Saturn': 'Discipline, karma, spiritual lessons',
        'Rahu': 'Desires, obsessions, foreign connections',
        'Ketu': 'Detachment, moksha, past life karma'
    }

    def __init__(self):
        """Initialize the Divisional Charts calculator"""
        pass

    
    def get_navamsa_chart(self, planet_positions: Dict[str, Any], lagna_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Navamsa (D9) chart from planetary positions.
        This is the final, simplified version.
        """
        try:
            # Calculate Navamsa Lagna from the lagna_info dictionary
            navamsa_lagna = self._calculate_navamsa_position(
                lagna_info['sign'], lagna_info['degree']
            )

            navamsa_positions = {}
            # Loop through the planet objects directly
            for planet_name, planet_info in planet_positions.items():
                # Use object-style access, as planet_info is a PlanetPosition object
                navamsa_pos = self._calculate_navamsa_position(planet_info.sign, planet_info.degree)
                navamsa_positions[planet_name] = navamsa_pos

            # Add Lagna to the positions so it's included in the chart layout
            # Note: Use a unique name to avoid overwriting a planet named 'Lagna'
            navamsa_positions['Navamsa Lagna'] = navamsa_lagna
            
            # Generate the chart layout and analysis
            navamsa_chart = self._generate_navamsa_chart_layout(navamsa_positions, navamsa_lagna)
            navamsa_analysis = self._analyze_navamsa_chart(navamsa_positions, navamsa_lagna)

            return {
                "navamsa_lagna": navamsa_lagna,
                "navamsa_positions": navamsa_positions,
                "navamsa_chart": navamsa_chart,
                "navamsa_analysis": navamsa_analysis
            }

        except Exception as e:
            print(f"Error calculating Navamsa chart: {e}")
            traceback.print_exc() # Print full traceback for better debugging
            return self._get_fallback_navamsa_chart()

    def _calculate_navamsa_position(self, sign: str, degree: float) -> Dict[str, Any]:
        """
        Calculate Navamsa position for a given sign and degree

        Each sign is divided into 9 navamsas of 3°20' each
        """
        try:
            # Each navamsa is 3°20' = 3.333... degrees
            navamsa_size = 30.0 / 9.0  # 3.333... degrees

            # Find which navamsa within the sign
            navamsa_number = int(degree / navamsa_size)
            if navamsa_number >= 9:
                navamsa_number = 8  # Cap at 8 (0-8 index)

            # Get the navamsa sign sequence for this sign
            navamsa_sequence = self.NAVAMSA_SEQUENCE[sign]
            navamsa_sign = navamsa_sequence[navamsa_number]

            # Calculate degree within the navamsa sign
            # Each navamsa represents 30° of the navamsa sign
            degree_in_navamsa = (degree % navamsa_size) * 9  # Scale to 30°

            return {
                "sign": navamsa_sign,
                "degree": round(degree_in_navamsa, 4),
                "navamsa_number": navamsa_number + 1,  # 1-9 for display
                "original_sign": sign,
                "original_degree": degree
            }

        except Exception as e:
            print(f"Error calculating navamsa position: {e}")
            return {
                "sign": "Aries",
                "degree": 0.0,
                "navamsa_number": 1,
                "original_sign": sign,
                "original_degree": degree
            }

    def _generate_navamsa_chart_layout(self, navamsa_positions: Dict[str, Any], navamsa_lagna: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate the Navamsa chart layout with planets in houses"""
        chart = {str(i): [] for i in range(1, 13)}

        # Add Navamsa Lagna to the chart
        lagna_sign_num = self.ZODIAC_SIGNS.index(navamsa_lagna['sign'])
        chart['1'].append('Navamsa Lagna')

        # Add planets to their respective houses in Navamsa
        for planet_name, navamsa_pos in navamsa_positions.items():
            planet_sign_num = self.ZODIAC_SIGNS.index(navamsa_pos['sign'])

            # Calculate house relative to Navamsa Lagna
            house_num = ((planet_sign_num - lagna_sign_num) % 12) + 1

            chart[str(house_num)].append(planet_name)

        return chart

    def _analyze_navamsa_chart(self, navamsa_positions: Dict[str, Any], navamsa_lagna: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the Navamsa chart for spiritual and marital insights"""
        analysis = {
            "spiritual_strength": [],
            "marital_indicators": [],
            "planetary_strength": {},
            "significant_combinations": []
        }

        try:
            # Analyze each planet's strength in Navamsa
            for planet_name, navamsa_pos in navamsa_positions.items():
                strength = self._analyze_navamsa_planetary_strength(planet_name, navamsa_pos)
                analysis["planetary_strength"][planet_name] = strength

                # Check for spiritual indicators
                if strength["is_exalted"] or strength["is_own_sign"]:
                    analysis["spiritual_strength"].append(
                        f"{planet_name} is strong in Navamsa ({navamsa_pos['sign']}) - {self.NAVAMSA_SIGNIFICANCE.get(planet_name, 'Positive influence')}"
                    )

                # Check for marital indicators (Venus, Mars, 7th lord)
                if planet_name in ['Venus', 'Mars']:
                    marital_strength = "strong" if (strength["is_exalted"] or strength["is_own_sign"]) else "moderate"
                    analysis["marital_indicators"].append(
                        f"{planet_name} in Navamsa {navamsa_pos['sign']} indicates {marital_strength} marital harmony"
                    )

            # Check for significant combinations
            analysis["significant_combinations"] = self._find_navamsa_combinations(navamsa_positions)

            # Overall assessment
            analysis["overall_assessment"] = self._get_navamsa_overall_assessment(analysis)

        except Exception as e:
            print(f"Error analyzing Navamsa chart: {e}")

        return analysis

    def _analyze_navamsa_planetary_strength(self, planet_name: str, navamsa_pos: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze planetary strength in Navamsa"""
        navamsa_sign = navamsa_pos['sign']

        # Define exaltation and own signs
        exaltation_signs = {
            'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn',
            'Mercury': 'Virgo', 'Jupiter': 'Cancer', 'Venus': 'Pisces',
            'Saturn': 'Libra', 'Rahu': 'Gemini', 'Ketu': 'Sagittarius'
        }

        own_signs = {
            'Sun': ['Leo'],
            'Moon': ['Cancer'],
            'Mars': ['Aries', 'Scorpio'],
            'Mercury': ['Gemini', 'Virgo'],
            'Jupiter': ['Sagittarius', 'Pisces'],
            'Venus': ['Taurus', 'Libra'],
            'Saturn': ['Capricorn', 'Aquarius'],
            'Rahu': [],  # No own signs
            'Ketu': []   # No own signs
        }

        debilitation_signs = {
            'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer',
            'Mercury': 'Pisces', 'Jupiter': 'Capricorn', 'Venus': 'Virgo',
            'Saturn': 'Aries', 'Rahu': 'Sagittarius', 'Ketu': 'Gemini'
        }

        is_exalted = exaltation_signs.get(planet_name) == navamsa_sign
        is_own_sign = navamsa_sign in own_signs.get(planet_name, [])
        is_debilitated = debilitation_signs.get(planet_name) == navamsa_sign

        strength_level = "Strong" if is_exalted else "Good" if is_own_sign else "Weak" if is_debilitated else "Moderate"

        return {
            "is_exalted": is_exalted,
            "is_own_sign": is_own_sign,
            "is_debilitated": is_debilitated,
            "strength_level": strength_level,
            "navamsa_sign": navamsa_sign
        }

    def _find_navamsa_combinations(self, navamsa_positions: Dict[str, Any]) -> List[str]:
        """Find significant combinations in Navamsa chart"""
        combinations = []

        try:
            # Group planets by sign
            sign_planets = {}
            for planet, pos in navamsa_positions.items():
                sign = pos['sign']
                if sign not in sign_planets:
                    sign_planets[sign] = []
                sign_planets[sign].append(planet)

            # Look for conjunctions (2 or more planets in same sign)
            for sign, planets in sign_planets.items():
                if len(planets) >= 2:
                    combinations.append(f"Navamsa conjunction in {sign}: {', '.join(planets)}")

            # Look for specific combinations
            venus_sign = navamsa_positions.get('Venus', {}).get('sign', '')
            mars_sign = navamsa_positions.get('Mars', {}).get('sign', '')
            jupiter_sign = navamsa_positions.get('Jupiter', {}).get('sign', '')

            # Venus-Jupiter combination (beneficial for marriage)
            if venus_sign == jupiter_sign:
                combinations.append("Venus-Jupiter conjunction in Navamsa - Very auspicious for marriage")

            # Mars-Venus combination (passion in marriage)
            if mars_sign == venus_sign:
                combinations.append("Mars-Venus conjunction in Navamsa - Passionate marriage")

        except Exception as e:
            print(f"Error finding Navamsa combinations: {e}")

        return combinations

    def _get_navamsa_overall_assessment(self, analysis: Dict[str, Any]) -> str:
        """Get overall assessment of the Navamsa chart"""
        try:
            strong_planets = sum(1 for strength in analysis["planetary_strength"].values()
                               if strength["strength_level"] in ["Strong", "Good"])

            total_planets = len(analysis["planetary_strength"])

            if strong_planets >= total_planets * 0.6:
                return "Strong Navamsa chart indicating good spiritual growth and harmonious relationships"
            elif strong_planets >= total_planets * 0.4:
                return "Moderate Navamsa chart with mixed influences on spiritual and marital life"
            else:
                return "Challenging Navamsa chart requiring conscious effort for spiritual and relationship growth"

        except Exception as e:
            print(f"Error getting Navamsa assessment: {e}")
            return "Unable to assess Navamsa chart strength"

    def get_other_divisional_charts(self, planet_positions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate other important divisional charts (D2, D3, D10, D12)

        This is a placeholder for future expansion
        """
        return {
            "d2_hora": {"status": "Future implementation"},
            "d3_drekkana": {"status": "Future implementation"},
            "d10_dasamsa": {"status": "Future implementation"},
            "d12_dwadasamsa": {"status": "Future implementation"}
        }

    def _get_fallback_navamsa_chart(self) -> Dict[str, Any]:
        """Fallback Navamsa chart when calculation fails"""
        return {
            "navamsa_lagna": {"sign": "Aries", "degree": 0.0, "navamsa_number": 1},
            "navamsa_positions": {},
            "navamsa_chart": {str(i): [] for i in range(1, 13)},
            "navamsa_analysis": {
                "spiritual_strength": ["Unable to calculate"],
                "marital_indicators": ["Unable to calculate"],
                "planetary_strength": {},
                "significant_combinations": [],
                "overall_assessment": "Unable to assess due to calculation error"
            }
        }
