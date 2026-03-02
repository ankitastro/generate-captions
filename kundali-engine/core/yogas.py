"""
Yoga Detection Module

This module provides rule-based detection of various yogas (combinations) in Vedic astrology
including Gaja Kesari, Budhaditya, Chandra-Mangal, Neechabhanga Raja Yoga, and others.
"""

from typing import Dict, List, Any, Set
from dataclasses import dataclass


@dataclass
class YogaInfo:
    """Information about a detected yoga"""
    name: str
    description: str
    strength: str  # Strong, Moderate, Weak
    planets_involved: List[str]
    houses_involved: List[int]
    significance: str
    effects: List[str]


class YogaDetector:
    """
    Advanced yoga detection engine for Vedic astrology
    """

    # Zodiac signs for reference
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    # Kendra houses (1, 4, 7, 10)
    KENDRA_HOUSES = [1, 4, 7, 10]

    # Trikona houses (1, 5, 9)
    TRIKONA_HOUSES = [1, 5, 9]

    # Trishadaya houses (3, 6, 11)
    TRISHADAYA_HOUSES = [3, 6, 11]

    # Dusthana houses (6, 8, 12)
    DUSTHANA_HOUSES = [6, 8, 12]

    # Planetary friendships and enmities
    PLANETARY_FRIENDS = {
        'Sun': ['Moon', 'Mars', 'Jupiter'],
        'Moon': ['Sun', 'Mercury'],
        'Mars': ['Sun', 'Moon', 'Jupiter'],
        'Mercury': ['Sun', 'Venus'],
        'Jupiter': ['Sun', 'Moon', 'Mars'],
        'Venus': ['Mercury', 'Saturn'],
        'Saturn': ['Mercury', 'Venus'],
        'Rahu': [],  # No natural friends
        'Ketu': []   # No natural friends
    }

    # Exaltation and debilitation signs
    EXALTATION_SIGNS = {
        'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn',
        'Mercury': 'Virgo', 'Jupiter': 'Cancer', 'Venus': 'Pisces',
        'Saturn': 'Libra', 'Rahu': 'Gemini', 'Ketu': 'Sagittarius'
    }

    DEBILITATION_SIGNS = {
        'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer',
        'Mercury': 'Pisces', 'Jupiter': 'Capricorn', 'Venus': 'Virgo',
        'Saturn': 'Aries', 'Rahu': 'Sagittarius', 'Ketu': 'Gemini'
    }

    # Own signs
    OWN_SIGNS = {
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

    def __init__(self):
        """Initialize the Yoga Detector"""
        pass

    def detect_all_yogas(self, planet_positions: List[Any], rasi_chart: Dict[str, List[str]],
                        lagna_sign: str) -> List[YogaInfo]:
        """
        Detect all yogas in the given chart

        Args:
            planet_positions: List of planet positions
            rasi_chart: Rasi chart with planets in houses
            lagna_sign: Lagna sign

        Returns:
            List of detected yogas
        """
        detected_yogas = []

        try:
            # Convert planet positions to convenient format
            planets_by_house = self._get_planets_by_house(planet_positions)
            planets_by_sign = self._get_planets_by_sign(planet_positions)

            print(f"DEBUG: Planets by house: {planets_by_house}")
            print(f"DEBUG: Planets by sign: {planets_by_sign}")

            # Detect various yogas
            detected_yogas.extend(self._detect_gaja_kesari_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_budhaditya_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_chandra_mangal_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_neechabhanga_raja_yoga(planet_positions, planets_by_sign))
            detected_yogas.extend(self._detect_hamsa_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_malavya_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_bhadra_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_ruchaka_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_sasha_yoga(planets_by_house, planets_by_sign))
            detected_yogas.extend(self._detect_kendra_trikona_yoga(planets_by_house))
            detected_yogas.extend(self._detect_viparita_raja_yoga(planets_by_house))
            detected_yogas.extend(self._detect_adhi_yoga(planets_by_house))
            detected_yogas.extend(self._detect_chamara_yoga(planets_by_house))
            detected_yogas.extend(self._detect_pushkala_yoga(planets_by_house))

            print(f"DEBUG: Total yogas detected: {len(detected_yogas)}")

        except Exception as e:
            print(f"Error detecting yogas: {e}")

        return detected_yogas

    def _get_planets_by_house(self, planet_positions: List[Any]) -> Dict[int, List[str]]:
        """Convert planet positions to house-based dictionary"""
        planets_by_house = {}

        for planet in planet_positions:
            house = planet.house
            if house not in planets_by_house:
                planets_by_house[house] = []
            planets_by_house[house].append(planet.planet)

        return planets_by_house

    def _get_planets_by_sign(self, planet_positions: List[Any]) -> Dict[str, List[str]]:
        """Convert planet positions to sign-based dictionary"""
        planets_by_sign = {}

        for planet in planet_positions:
            sign = planet.sign
            if sign not in planets_by_sign:
                planets_by_sign[sign] = []
            planets_by_sign[sign].append(planet.planet)

        return planets_by_sign

    def _detect_gaja_kesari_yoga(self, planets_by_house: Dict[int, List[str]],
                                planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Gaja Kesari Yoga
        Moon and Jupiter in Kendra from each other
        """
        yogas = []

        try:
            # Find Moon and Jupiter houses
            moon_house = None
            jupiter_house = None

            for house, planets in planets_by_house.items():
                if 'Moon' in planets:
                    moon_house = house
                if 'Jupiter' in planets:
                    jupiter_house = house

            if moon_house and jupiter_house:
                # Check if they are in Kendra from each other
                house_diff = abs(moon_house - jupiter_house)
                is_kendra = house_diff in [0, 3, 6, 9] or house_diff == 0

                if is_kendra:
                    # Determine strength
                    strength = self._determine_yoga_strength(['Moon', 'Jupiter'], planets_by_sign)

                    yogas.append(YogaInfo(
                        name="Gaja Kesari Yoga",
                        description="Moon and Jupiter in Kendra relationship",
                        strength=strength,
                        planets_involved=['Moon', 'Jupiter'],
                        houses_involved=[moon_house, jupiter_house],
                        significance="One of the most auspicious yogas",
                        effects=[
                            "Wisdom and knowledge",
                            "Good reputation and fame",
                            "Spiritual inclination",
                            "Prosperity and wealth",
                            "Leadership qualities"
                        ]
                    ))

        except Exception as e:
            print(f"Error detecting Gaja Kesari Yoga: {e}")

        return yogas

    def _detect_budhaditya_yoga(self, planets_by_house: Dict[int, List[str]],
                               planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Budhaditya Yoga
        Sun and Mercury in the same house/sign
        """
        yogas = []

        try:
            # Check if Sun and Mercury are in the same sign
            for sign, planets in planets_by_sign.items():
                if 'Sun' in planets and 'Mercury' in planets:
                    # Find the house
                    house = None
                    for h, p in planets_by_house.items():
                        if 'Sun' in p and 'Mercury' in p:
                            house = h
                            break

                    if house:
                        strength = self._determine_yoga_strength(['Sun', 'Mercury'], planets_by_sign)

                        yogas.append(YogaInfo(
                            name="Budhaditya Yoga",
                            description="Sun and Mercury conjunction",
                            strength=strength,
                            planets_involved=['Sun', 'Mercury'],
                            houses_involved=[house],
                            significance="Excellent for intelligence and learning",
                            effects=[
                                "Sharp intellect and communication skills",
                                "Success in education",
                                "Good writing and speaking abilities",
                                "Administrative capabilities",
                                "Wealth through knowledge"
                            ]
                        ))

        except Exception as e:
            print(f"Error detecting Budhaditya Yoga: {e}")

        return yogas

    def _detect_chandra_mangal_yoga(self, planets_by_house: Dict[int, List[str]],
                                   planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Chandra Mangal Yoga
        Moon and Mars in conjunction or mutual aspect
        """
        yogas = []

        try:
            # Check if Moon and Mars are in the same sign
            for sign, planets in planets_by_sign.items():
                if 'Moon' in planets and 'Mars' in planets:
                    # Find the house
                    house = None
                    for h, p in planets_by_house.items():
                        if 'Moon' in p and 'Mars' in p:
                            house = h
                            break

                    if house:
                        strength = self._determine_yoga_strength(['Moon', 'Mars'], planets_by_sign)

                        yogas.append(YogaInfo(
                            name="Chandra Mangal Yoga",
                            description="Moon and Mars conjunction",
                            strength=strength,
                            planets_involved=['Moon', 'Mars'],
                            houses_involved=[house],
                            significance="Combines emotion with action",
                            effects=[
                                "Strong determination and willpower",
                                "Success in real estate business",
                                "Wealth accumulation",
                                "Strong mother-child relationship",
                                "Courage and emotional strength"
                            ]
                        ))

        except Exception as e:
            print(f"Error detecting Chandra Mangal Yoga: {e}")

        return yogas

    def _detect_neechabhanga_raja_yoga(self, planet_positions: List[Any],
                                      planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Neechabhanga Raja Yoga
        Debilitated planet's debilitation is cancelled
        """
        yogas = []

        try:
            for planet in planet_positions:
                planet_name = planet.planet
                planet_sign = planet.sign

                # Check if planet is debilitated
                if self.DEBILITATION_SIGNS.get(planet_name) == planet_sign:
                    # Check for cancellation conditions
                    is_cancelled = False
                    cancellation_reason = ""

                    # Condition 1: Debilitation lord is in Kendra from Lagna or Moon
                    # Condition 2: Exaltation lord is in Kendra from Lagna or Moon
                    # Condition 3: Debilitated planet is aspected by its own sign lord

                    # Simplified check: if any strong planet is in Kendra
                    for house in self.KENDRA_HOUSES:
                        for h, planets in planets_by_sign.items():
                            if len(planets) > 0:
                                # Check if any planet in Kendra is strong
                                for p in planets:
                                    if (self.EXALTATION_SIGNS.get(p) == h or
                                        h in self.OWN_SIGNS.get(p, [])):
                                        is_cancelled = True
                                        cancellation_reason = f"{p} is strong in Kendra"
                                        break

                    if is_cancelled:
                        yogas.append(YogaInfo(
                            name="Neechabhanga Raja Yoga",
                            description=f"Debilitation of {planet_name} cancelled",
                            strength="Strong",
                            planets_involved=[planet_name],
                            houses_involved=[planet.house],
                            significance="Transforms weakness into strength",
                            effects=[
                                "Rise from humble beginnings",
                                "Unexpected success and recognition",
                                "Overcoming obstacles",
                                "Hidden talents surface",
                                "Spiritual growth through challenges"
                            ]
                        ))

        except Exception as e:
            print(f"Error detecting Neechabhanga Raja Yoga: {e}")

        return yogas

    def _detect_hamsa_yoga(self, planets_by_house: Dict[int, List[str]],
                          planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Hamsa Yoga (Pancha Mahapurusha Yoga)
        Jupiter in Kendra in its own sign or exaltation
        """
        yogas = []

        try:
            for house in self.KENDRA_HOUSES:
                if house in planets_by_house and 'Jupiter' in planets_by_house[house]:
                    # Find Jupiter's sign
                    jupiter_sign = None
                    for sign, planets in planets_by_sign.items():
                        if 'Jupiter' in planets:
                            jupiter_sign = sign
                            break

                    if jupiter_sign:
                        # Check if Jupiter is in own sign or exaltation
                        is_own_sign = jupiter_sign in self.OWN_SIGNS.get('Jupiter', [])
                        is_exalted = jupiter_sign == self.EXALTATION_SIGNS.get('Jupiter')

                        if is_own_sign or is_exalted:
                            yogas.append(YogaInfo(
                                name="Hamsa Yoga",
                                description="Jupiter in Kendra in own sign or exaltation",
                                strength="Strong",
                                planets_involved=['Jupiter'],
                                houses_involved=[house],
                                significance="One of the Pancha Mahapurusha Yogas",
                                effects=[
                                    "Wisdom and spiritual knowledge",
                                    "Respect and honor in society",
                                    "Good fortune and prosperity",
                                    "Religious inclination",
                                    "Teaching and guiding abilities"
                                ]
                            ))

        except Exception as e:
            print(f"Error detecting Hamsa Yoga: {e}")

        return yogas

    def _detect_malavya_yoga(self, planets_by_house: Dict[int, List[str]],
                           planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Malavya Yoga (Pancha Mahapurusha Yoga)
        Venus in Kendra in its own sign or exaltation
        """
        yogas = []

        try:
            for house in self.KENDRA_HOUSES:
                if house in planets_by_house and 'Venus' in planets_by_house[house]:
                    # Find Venus's sign
                    venus_sign = None
                    for sign, planets in planets_by_sign.items():
                        if 'Venus' in planets:
                            venus_sign = sign
                            break

                    if venus_sign:
                        # Check if Venus is in own sign or exaltation
                        is_own_sign = venus_sign in self.OWN_SIGNS.get('Venus', [])
                        is_exalted = venus_sign == self.EXALTATION_SIGNS.get('Venus')

                        if is_own_sign or is_exalted:
                            yogas.append(YogaInfo(
                                name="Malavya Yoga",
                                description="Venus in Kendra in own sign or exaltation",
                                strength="Strong",
                                planets_involved=['Venus'],
                                houses_involved=[house],
                                significance="One of the Pancha Mahapurusha Yogas",
                                effects=[
                                    "Artistic talents and creativity",
                                    "Luxurious lifestyle",
                                    "Harmonious relationships",
                                    "Beauty and attraction",
                                    "Success in arts and entertainment"
                                ]
                            ))

        except Exception as e:
            print(f"Error detecting Malavya Yoga: {e}")

        return yogas

    def _detect_bhadra_yoga(self, planets_by_house: Dict[int, List[str]],
                           planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Bhadra Yoga (Pancha Mahapurusha Yoga)
        Mercury in Kendra in its own sign or exaltation
        """
        yogas = []

        try:
            for house in self.KENDRA_HOUSES:
                if house in planets_by_house and 'Mercury' in planets_by_house[house]:
                    # Find Mercury's sign
                    mercury_sign = None
                    for sign, planets in planets_by_sign.items():
                        if 'Mercury' in planets:
                            mercury_sign = sign
                            break

                    if mercury_sign:
                        # Check if Mercury is in own sign or exaltation
                        is_own_sign = mercury_sign in self.OWN_SIGNS.get('Mercury', [])
                        is_exalted = mercury_sign == self.EXALTATION_SIGNS.get('Mercury')

                        if is_own_sign or is_exalted:
                            yogas.append(YogaInfo(
                                name="Bhadra Yoga",
                                description="Mercury in Kendra in own sign or exaltation",
                                strength="Strong",
                                planets_involved=['Mercury'],
                                houses_involved=[house],
                                significance="One of the Pancha Mahapurusha Yogas",
                                effects=[
                                    "Exceptional intelligence and wit",
                                    "Excellence in communication",
                                    "Business acumen",
                                    "Analytical abilities",
                                    "Success in intellectual pursuits"
                                ]
                            ))

        except Exception as e:
            print(f"Error detecting Bhadra Yoga: {e}")

        return yogas

    def _detect_ruchaka_yoga(self, planets_by_house: Dict[int, List[str]],
                           planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Ruchaka Yoga (Pancha Mahapurusha Yoga)
        Mars in Kendra in its own sign or exaltation
        """
        yogas = []

        try:
            for house in self.KENDRA_HOUSES:
                if house in planets_by_house and 'Mars' in planets_by_house[house]:
                    # Find Mars's sign
                    mars_sign = None
                    for sign, planets in planets_by_sign.items():
                        if 'Mars' in planets:
                            mars_sign = sign
                            break

                    if mars_sign:
                        # Check if Mars is in own sign or exaltation
                        is_own_sign = mars_sign in self.OWN_SIGNS.get('Mars', [])
                        is_exalted = mars_sign == self.EXALTATION_SIGNS.get('Mars')

                        if is_own_sign or is_exalted:
                            yogas.append(YogaInfo(
                                name="Ruchaka Yoga",
                                description="Mars in Kendra in own sign or exaltation",
                                strength="Strong",
                                planets_involved=['Mars'],
                                houses_involved=[house],
                                significance="One of the Pancha Mahapurusha Yogas",
                                effects=[
                                    "Courage and valor",
                                    "Leadership qualities",
                                    "Physical strength",
                                    "Military or police success",
                                    "Fearless nature"
                                ]
                            ))

        except Exception as e:
            print(f"Error detecting Ruchaka Yoga: {e}")

        return yogas

    def _detect_sasha_yoga(self, planets_by_house: Dict[int, List[str]],
                          planets_by_sign: Dict[str, List[str]]) -> List[YogaInfo]:
        """
        Detect Sasha Yoga (Pancha Mahapurusha Yoga)
        Saturn in Kendra in its own sign or exaltation
        """
        yogas = []

        try:
            for house in self.KENDRA_HOUSES:
                if house in planets_by_house and 'Saturn' in planets_by_house[house]:
                    # Find Saturn's sign
                    saturn_sign = None
                    for sign, planets in planets_by_sign.items():
                        if 'Saturn' in planets:
                            saturn_sign = sign
                            break

                    if saturn_sign:
                        # Check if Saturn is in own sign or exaltation
                        is_own_sign = saturn_sign in self.OWN_SIGNS.get('Saturn', [])
                        is_exalted = saturn_sign == self.EXALTATION_SIGNS.get('Saturn')

                        if is_own_sign or is_exalted:
                            yogas.append(YogaInfo(
                                name="Sasha Yoga",
                                description="Saturn in Kendra in own sign or exaltation",
                                strength="Strong",
                                planets_involved=['Saturn'],
                                houses_involved=[house],
                                significance="One of the Pancha Mahapurusha Yogas",
                                effects=[
                                    "Discipline and perseverance",
                                    "Long-term success",
                                    "Administrative abilities",
                                    "Justice and fairness",
                                    "Spiritual maturity"
                                ]
                            ))

        except Exception as e:
            print(f"Error detecting Sasha Yoga: {e}")

        return yogas

    def _detect_kendra_trikona_yoga(self, planets_by_house: Dict[int, List[str]]) -> List[YogaInfo]:
        """
        Detect Kendra Trikona Yoga
        Lords of Kendra and Trikona houses together
        """
        yogas = []

        try:
            # Simplified: Check if any planets are in both Kendra and Trikona
            kendra_planets = set()
            trikona_planets = set()

            for house, planets in planets_by_house.items():
                if house in self.KENDRA_HOUSES:
                    kendra_planets.update(planets)
                if house in self.TRIKONA_HOUSES:
                    trikona_planets.update(planets)

            # Check if there are common planets or conjunctions
            if kendra_planets and trikona_planets:
                yogas.append(YogaInfo(
                    name="Kendra Trikona Yoga",
                    description="Connection between Kendra and Trikona houses",
                    strength="Moderate",
                    planets_involved=list(kendra_planets.union(trikona_planets)),
                    houses_involved=self.KENDRA_HOUSES + self.TRIKONA_HOUSES,
                    significance="Combines power with purpose",
                    effects=[
                        "Balanced life approach",
                        "Success through righteous means",
                        "Good fortune and prosperity",
                        "Spiritual and material progress",
                        "Recognition and respect"
                    ]
                ))

        except Exception as e:
            print(f"Error detecting Kendra Trikona Yoga: {e}")

        return yogas

    def _detect_viparita_raja_yoga(self, planets_by_house: Dict[int, List[str]]) -> List[YogaInfo]:
        """
        Detect Viparita Raja Yoga
        Lords of Dusthana houses (6, 8, 12) in mutual positions
        """
        yogas = []

        try:
            dusthana_planets = set()

            for house, planets in planets_by_house.items():
                if house in self.DUSTHANA_HOUSES:
                    dusthana_planets.update(planets)

            # Simplified check: if multiple planets are in dusthana houses
            if len(dusthana_planets) >= 2:
                yogas.append(YogaInfo(
                    name="Viparita Raja Yoga",
                    description="Planets in Dusthana houses creating positive results",
                    strength="Moderate",
                    planets_involved=list(dusthana_planets),
                    houses_involved=self.DUSTHANA_HOUSES,
                    significance="Turns difficulties into opportunities",
                    effects=[
                        "Success through overcoming obstacles",
                        "Unexpected gains",
                        "Victory over enemies",
                        "Strong resilience",
                        "Hidden talents emerge"
                    ]
                ))

        except Exception as e:
            print(f"Error detecting Viparita Raja Yoga: {e}")

        return yogas

    def _detect_adhi_yoga(self, planets_by_house: Dict[int, List[str]]) -> List[YogaInfo]:
        """
        Detect Adhi Yoga
        Benefics in 6th, 7th, 8th from Moon
        """
        yogas = []

        try:
            # Find Moon's house
            moon_house = None
            for house, planets in planets_by_house.items():
                if 'Moon' in planets:
                    moon_house = house
                    break

            if moon_house:
                # Check 6th, 7th, 8th from Moon
                target_houses = [
                    ((moon_house + 5) % 12) + 1,  # 6th from Moon
                    ((moon_house + 6) % 12) + 1,  # 7th from Moon
                    ((moon_house + 7) % 12) + 1   # 8th from Moon
                ]

                benefics_found = []
                for house in target_houses:
                    if house in planets_by_house:
                        for planet in planets_by_house[house]:
                            if planet in ['Jupiter', 'Venus', 'Mercury']:
                                benefics_found.append(planet)

                if benefics_found:
                    yogas.append(YogaInfo(
                        name="Adhi Yoga",
                        description="Benefics in 6th, 7th, 8th from Moon",
                        strength="Moderate",
                        planets_involved=benefics_found + ['Moon'],
                        houses_involved=[moon_house] + target_houses,
                        significance="Enhances Moon's positive effects",
                        effects=[
                            "Good health and longevity",
                            "Prosperity and comfort",
                            "Success in endeavors",
                            "Respect and honor",
                            "Happy family life"
                        ]
                    ))

        except Exception as e:
            print(f"Error detecting Adhi Yoga: {e}")

        return yogas

    def _detect_chamara_yoga(self, planets_by_house: Dict[int, List[str]]) -> List[YogaInfo]:
        """
        Detect Chamara Yoga
        Lagna lord exalted in Kendra or Trikona
        """
        yogas = []

        try:
            # Simplified: Check if any strong planet is in Kendra or Trikona
            for house in self.KENDRA_HOUSES + self.TRIKONA_HOUSES:
                if house in planets_by_house:
                    for planet in planets_by_house[house]:
                        # Check if planet is strong (simplified)
                        if planet in ['Jupiter', 'Venus', 'Sun']:
                            yogas.append(YogaInfo(
                                name="Chamara Yoga",
                                description="Strong planet in Kendra or Trikona",
                                strength="Moderate",
                                planets_involved=[planet],
                                houses_involved=[house],
                                significance="Brings royal treatment",
                                effects=[
                                    "Recognition and fame",
                                    "Leadership positions",
                                    "Comfortable lifestyle",
                                    "Respect from others",
                                    "Success in chosen field"
                                ]
                            ))
                            break

        except Exception as e:
            print(f"Error detecting Chamara Yoga: {e}")

        return yogas

    def _detect_pushkala_yoga(self, planets_by_house: Dict[int, List[str]]) -> List[YogaInfo]:
        """
        Detect Pushkala Yoga
        Lagna lord, Moon sign lord, and dispositor of Lagna lord are in mutual Kendras
        """
        yogas = []

        try:
            # Simplified: Check if multiple benefics are in Kendra
            kendra_benefics = []
            for house in self.KENDRA_HOUSES:
                if house in planets_by_house:
                    for planet in planets_by_house[house]:
                        if planet in ['Jupiter', 'Venus', 'Mercury', 'Moon']:
                            kendra_benefics.append(planet)

            if len(kendra_benefics) >= 2:
                yogas.append(YogaInfo(
                    name="Pushkala Yoga",
                    description="Multiple benefics in Kendra positions",
                    strength="Strong",
                    planets_involved=kendra_benefics,
                    houses_involved=self.KENDRA_HOUSES,
                    significance="Abundant prosperity",
                    effects=[
                        "Abundant wealth and prosperity",
                        "Multiple sources of income",
                        "Large family and social circle",
                        "Generous and charitable nature",
                        "Success in business ventures"
                    ]
                ))

        except Exception as e:
            print(f"Error detecting Pushkala Yoga: {e}")

        return yogas

    def _determine_yoga_strength(self, planets_involved: List[str],
                                planets_by_sign: Dict[str, List[str]]) -> str:
        """Determine the strength of a yoga based on planetary positions"""
        strong_count = 0

        for planet in planets_involved:
            for sign, planets in planets_by_sign.items():
                if planet in planets:
                    # Check if planet is strong
                    if (sign == self.EXALTATION_SIGNS.get(planet) or
                        sign in self.OWN_SIGNS.get(planet, [])):
                        strong_count += 1
                    break

        if strong_count >= len(planets_involved):
            return "Strong"
        elif strong_count >= len(planets_involved) // 2:
            return "Moderate"
        else:
            return "Weak"

    def get_yoga_summary(self, detected_yogas: List[YogaInfo]) -> Dict[str, Any]:
        """Get a summary of detected yogas"""
        return {
            "total_yogas": len(detected_yogas),
            "strong_yogas": [yoga.name for yoga in detected_yogas if yoga.strength == "Strong"],
            "moderate_yogas": [yoga.name for yoga in detected_yogas if yoga.strength == "Moderate"],
            "weak_yogas": [yoga.name for yoga in detected_yogas if yoga.strength == "Weak"],
            "most_significant": detected_yogas[0].name if detected_yogas else None
        }
