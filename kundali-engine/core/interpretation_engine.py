"""
Interpretation Engine Module

This module provides rule-based interpretations for Vedic astrology Kundali data,
converting technical astrological information into human-readable insights.
"""

from typing import Dict, List, Any


class InterpretationEngine:
    """
    Rule-based interpretation engine for Vedic astrology Kundali analysis
    """

    # Lagna (Ascendant) Sign Interpretations
    LAGNA_INTERPRETATIONS = {
        'Aries': "You are confident, energetic, and a natural leader. You have a pioneering spirit and love to take initiative. Your direct approach and courage help you overcome obstacles, though impatience can sometimes work against you.",
        'Taurus': "You are practical, reliable, and value stability. You have a strong appreciation for beauty, comfort, and material security. Your persistent nature helps you build lasting foundations, though you may resist change.",
        'Gemini': "You are versatile, communicative, and intellectually curious. You adapt quickly to new situations and enjoy learning and sharing information. Your quick wit and social skills are your strengths, though you may sometimes lack focus.",
        'Cancer': "You are nurturing, intuitive, and emotionally sensitive. You have strong family values and care deeply about your loved ones. Your protective nature and empathy are your gifts, though mood swings can be challenging.",
        'Leo': "You are confident, generous, and love the spotlight. You have natural leadership qualities and a warm, magnetic personality. Your creativity and self-expression inspire others, though pride can sometimes create difficulties.",
        'Virgo': "You are analytical, practical, and detail-oriented. You strive for perfection and have excellent organizational skills. Your methodical approach and service-oriented nature are valuable assets, though criticism can be harsh.",
        'Libra': "You are diplomatic, charming, and seek harmony in relationships. You have refined taste and strong sense of justice. Your ability to see both sides and create balance is remarkable, though indecision can be problematic.",
        'Scorpio': "You are intense, determined, and possess great inner strength. You have powerful intuition and ability to transform yourself and situations. Your depth and loyalty are admirable, though jealousy can create issues.",
        'Sagittarius': "You are optimistic, philosophical, and love freedom. You have a broad worldview and enjoy exploring new ideas and places. Your enthusiasm and wisdom inspire others, though restlessness can be limiting.",
        'Capricorn': "You are ambitious, disciplined, and highly responsible. You have strong organizational abilities and work steadily toward your goals. Your reliability and determination bring success, though rigidity can hold you back.",
        'Aquarius': "You are innovative, independent, and humanitarian. You have unique ideas and care about social causes. Your originality and forward-thinking are valuable, though detachment can affect relationships.",
        'Pisces': "You are compassionate, intuitive, and spiritually inclined. You have rich imagination and deep empathy for others. Your creativity and sensitivity are gifts, though escapism can be a challenge."
    }

    # Planetary Placement Interpretations (Planet + Sign + House combinations)
    PLANETARY_PLACEMENTS = {
        # Sun placements
        ('Sun', 'Aries', 1): "Sun in Aries in 1st house: You radiate confidence and natural leadership. Your pioneering spirit and strong will power make you a born leader who inspires others through example.",
        ('Sun', 'Leo', 1): "Sun in Leo in 1st house: You have a magnetic personality with natural charisma. Your creative self-expression and generous nature draw people to you like a magnet.",
        ('Sun', 'Gemini', 10): "Sun in Gemini in 10th house: Your career involves communication, versatility, and intellectual pursuits. You excel in fields requiring adaptability and multi-faceted skills.",
        ('Sun', 'Scorpio', 4): "Sun in Scorpio in 4th house: You have deep emotional connections to home and family. Your transformative nature brings profound changes to your domestic environment.",

        # Moon placements
        ('Moon', 'Cancer', 1): "Moon in Cancer in 1st house: You are deeply intuitive and emotionally sensitive. Your nurturing nature and psychic abilities make you naturally caring and protective.",
        ('Moon', 'Scorpio', 3): "Moon in Scorpio in 3rd house: Your mind is intense and penetrating. You have strong willpower and ability to understand hidden motivations and secrets.",
        ('Moon', 'Taurus', 7): "Moon in Taurus in 7th house: You seek stable and harmonious relationships. Your practical approach to partnerships brings lasting and secure connections.",
        ('Moon', 'Pisces', 9): "Moon in Pisces in 9th house: You have strong spiritual inclinations and intuitive wisdom. Your compassionate nature draws you to higher learning and philosophy.",

        # Mercury placements
        ('Mercury', 'Gemini', 3): "Mercury in Gemini in 3rd house: You have exceptional communication skills and quick intellect. Your ability to process and share information makes you an excellent communicator.",
        ('Mercury', 'Virgo', 6): "Mercury in Virgo in 6th house: Your analytical mind excels in detailed work and problem-solving. You have natural ability for research, analysis, and systematic approaches.",
        ('Mercury', 'Gemini', 10): "Mercury in Gemini in 10th house: Your career involves communication, writing, or intellectual pursuits. Your versatile mind helps you excel in multiple professional areas.",
        ('Mercury', 'Libra', 2): "Mercury in Libra in 2nd house: You have diplomatic communication style and artistic sensibilities. Your balanced approach to finances and values brings harmony.",

        # Mars placements
        ('Mars', 'Aries', 1): "Mars in Aries in 1st house: You are dynamic, courageous, and action-oriented. Your natural leadership and pioneering spirit drive you to initiate new ventures.",
        ('Mars', 'Scorpio', 8): "Mars in Scorpio in 8th house: You have intense energy and ability for deep transformation. Your research abilities and interest in mysteries make you a natural investigator.",
        ('Mars', 'Capricorn', 10): "Mars in Capricorn in 10th house: Your ambition and disciplined action lead to career success. You have excellent organizational skills and ability to lead organizations.",
        ('Mars', 'Leo', 5): "Mars in Leo in 5th house: You have creative energy and passion for self-expression. Your dynamic personality shines in creative and recreational activities.",

        # Jupiter placements
        ('Jupiter', 'Sagittarius', 9): "Jupiter in Sagittarius in 9th house: You have natural wisdom and strong spiritual inclinations. Your philosophical nature and teaching abilities inspire others.",
        ('Jupiter', 'Cancer', 4): "Jupiter in Cancer in 4th house: You have strong family values and nurturing wisdom. Your home becomes a place of learning and spiritual growth.",
        ('Jupiter', 'Pisces', 12): "Jupiter in Pisces in 12th house: You have deep spiritual insights and compassionate nature. Your intuitive wisdom and charitable inclinations bring inner fulfillment.",
        ('Jupiter', 'Gemini', 11): "Jupiter in Gemini in 11th house: Your social network includes intellectuals and teachers. Your communication skills help you achieve your goals through connections.",

        # Venus placements
        ('Venus', 'Taurus', 2): "Venus in Taurus in 2nd house: You have refined taste and strong attraction to beauty and luxury. Your artistic sensibilities and financial acumen work well together.",
        ('Venus', 'Libra', 7): "Venus in Libra in 7th house: You seek harmonious and balanced relationships. Your diplomatic nature and sense of beauty create ideal partnerships.",
        ('Venus', 'Pisces', 12): "Venus in Pisces in 12th house: You have compassionate love nature and spiritual artistic abilities. Your selfless service in love brings deep fulfillment.",
        ('Venus', 'Gemini', 3): "Venus in Gemini in 3rd house: You have charming communication style and artistic versatility. Your creative writing and speaking abilities are naturally attractive.",

        # Saturn placements
        ('Saturn', 'Capricorn', 10): "Saturn in Capricorn in 10th house: You have strong leadership abilities and methodical approach to career. Your disciplined work ethic brings lasting success.",
        ('Saturn', 'Libra', 7): "Saturn in Libra in 7th house: You take relationships seriously and seek long-term commitments. Your balanced approach to partnerships creates stability.",
        ('Saturn', 'Aquarius', 11): "Saturn in Aquarius in 11th house: You work systematically toward your goals through organized groups. Your innovative approach to achievements pays off over time.",
        ('Saturn', 'Sagittarius', 5): "Saturn in Sagittarius in 5th house: You approach creativity and education with discipline and structure. Your philosophical approach to self-expression matures with time."
    }

    # Nakshatra Interpretations
    NAKSHATRA_INTERPRETATIONS = {
        'Ashwini': "brings healing abilities and pioneering spirit",
        'Bharani': "gives strong will and ability to bear responsibilities",
        'Krittika': "provides sharp intellect and ability to cut through illusions",
        'Rohini': "brings creativity, beauty, and material prosperity",
        'Mrigashira': "gives curiosity and quest for knowledge",
        'Ardra': "provides transformative abilities and emotional depth",
        'Punarvasu': "brings optimism and ability to recover from setbacks",
        'Pushya': "gives nurturing qualities and spiritual wisdom",
        'Ashlesha': "provides intuitive abilities and understanding of hidden matters",
        'Magha': "brings leadership qualities and connection to ancestral wisdom",
        'Purva Phalguni': "gives creative talents and love for luxury",
        'Uttara Phalguni': "provides organizational abilities and helpful nature",
        'Hasta': "brings skillful hands and attention to detail",
        'Chitra': "gives artistic abilities and eye for beauty",
        'Swati': "provides independence and flexibility",
        'Vishakha': "brings determination and goal-oriented nature",
        'Anuradha': "gives friendship and devotional qualities",
        'Jyeshtha': "provides leadership abilities and protective nature",
        'Mula': "brings ability to get to the root of matters",
        'Purva Ashadha': "gives invincible spirit and purification abilities",
        'Uttara Ashadha': "provides leadership and lasting achievements",
        'Shravana': "brings learning abilities and good listening skills",
        'Dhanishta': "gives musical talents and rhythmic abilities",
        'Shatabhisha': "provides healing abilities and interest in mysteries",
        'Purva Bhadrapada': "brings idealistic nature and spiritual inclinations",
        'Uttara Bhadrapada': "gives depth of character and spiritual wisdom",
        'Revati': "provides nurturing qualities and completeness"
    }

    # Yoga Effect Summaries (simplified for key yogas)
    YOGA_SUMMARIES = {
        'Gaja Kesari Yoga': "excellent for wisdom, reputation, and prosperity",
        'Budhaditya Yoga': "enhances intelligence, communication, and learning abilities",
        'Chandra Mangal Yoga': "brings wealth accumulation and strong determination",
        'Neechabhanga Raja Yoga': "transforms challenges into opportunities for great success",
        'Hamsa Yoga': "brings spiritual wisdom and respect in society",
        'Malavya Yoga': "enhances artistic talents and luxurious lifestyle",
        'Bhadra Yoga': "provides exceptional intelligence and communication excellence",
        'Ruchaka Yoga': "brings courage, leadership, and physical strength",
        'Sasha Yoga': "gives discipline, organization, and long-term success",
        'Raj Yoga': "indicates potential for leadership and authority",
        'Dhana Yoga': "brings wealth and material prosperity",
        'Kendra Trikona Yoga': "combines power with righteousness for balanced success",
        'Viparita Raja Yoga': "turns obstacles into stepping stones for success",
        'Adhi Yoga': "enhances longevity, health, and prosperity",
        'Chamara Yoga': "brings recognition, fame, and royal treatment"
    }

    def __init__(self):
        """Initialize the Interpretation Engine"""
        pass

    def interpret_lagna(self, lagna: str) -> str:
        """
        Return personality interpretation for the given Lagna sign

        Args:
            lagna: Zodiac sign name (e.g., "Leo", "Virgo")

        Returns:
            String describing personality traits associated with the Lagna
        """
        interpretation = self.LAGNA_INTERPRETATIONS.get(lagna)
        if interpretation:
            return f"Lagna in {lagna}: {interpretation}"
        else:
            return f"Lagna in {lagna}: This is a unique placement that adds special qualities to your personality."

    def interpret_planet_placement(self, planet: str, sign: str, house: int) -> str:
        """
        Return interpretation for specific planetary placement

        Args:
            planet: Planet name (e.g., "Sun", "Moon", "Mercury")
            sign: Zodiac sign name
            house: House number (1-12)

        Returns:
            String describing the planetary placement interpretation
        """
        # Try to find specific placement interpretation
        placement_key = (planet, sign, house)
        specific_interpretation = self.PLANETARY_PLACEMENTS.get(placement_key)

        if specific_interpretation:
            return specific_interpretation

        # If no specific interpretation, provide general guidance
        return f"{planet} in {sign} (House {house}): This placement brings unique influences to your life. Interpretation will be added in future updates."

    def interpret_nakshatra(self, nakshatra: Dict[str, Any]) -> str:
        """
        Return interpretation for Moon's Nakshatra placement

        Args:
            nakshatra: Dictionary with 'name', 'pada', and 'lord' keys

        Returns:
            String describing the nakshatra influence
        """
        nakshatra_name = nakshatra.get('name', 'Unknown')
        pada = nakshatra.get('pada', 1)
        lord = nakshatra.get('lord', 'Unknown')

        # Get nakshatra-specific interpretation
        nakshatra_effect = self.NAKSHATRA_INTERPRETATIONS.get(nakshatra_name, "brings unique spiritual qualities")

        return (f"Your Moon is in Nakshatra {nakshatra_name} (Pada {pada}), ruled by {lord}. "
                f"This nakshatra {nakshatra_effect}, giving you distinctive emotional and mental characteristics.")

    def interpret_yogas(self, yogas: List[Dict[str, Any]]) -> str:
        """
        Return interpretation for detected yogas

        Args:
            yogas: List of yoga dictionaries with 'name', 'strength', and 'effects'

        Returns:
            String describing the yoga influences
        """
        if not yogas:
            return "No major yogas detected in your chart at this time."

        # Count yogas by strength
        strong_yogas = [yoga for yoga in yogas if yoga.get('strength') == 'Strong']
        moderate_yogas = [yoga for yoga in yogas if yoga.get('strength') == 'Moderate']

        interpretation = "You have the following important yogas in your chart:\n\n"

        # Describe strong yogas first
        if strong_yogas:
            interpretation += "Strong Yogas:\n"
            for yoga in strong_yogas:
                yoga_name = yoga.get('name', 'Unknown Yoga')
                yoga_summary = self.YOGA_SUMMARIES.get(yoga_name, "brings positive influences")
                interpretation += f"• {yoga_name}: This powerful yoga {yoga_summary}.\n"
            interpretation += "\n"

        # Then moderate yogas
        if moderate_yogas:
            interpretation += "Moderate Yogas:\n"
            for yoga in moderate_yogas[:3]:  # Limit to top 3 moderate yogas
                yoga_name = yoga.get('name', 'Unknown Yoga')
                yoga_summary = self.YOGA_SUMMARIES.get(yoga_name, "brings beneficial influences")
                interpretation += f"• {yoga_name}: This yoga {yoga_summary}.\n"

        if len(yogas) > 5:
            interpretation += f"\nYour chart contains {len(yogas)} total yogas, indicating a life rich with potential and opportunities."

        return interpretation.strip()

    def interpret_houses(self, planets: List[Dict[str, Any]]) -> str:
        """
        Return interpretation focusing on house placements

        Args:
            planets: List of planet dictionaries

        Returns:
            String describing house-based interpretations
        """
        house_analysis = "\nHouse Analysis:\n"

        # Group planets by houses
        houses = {}
        for planet in planets:
            house = planet.get('house', 1)
            if house not in houses:
                houses[house] = []
            houses[house].append(planet.get('planet', 'Unknown'))

        # Analyze houses with multiple planets
        for house, house_planets in houses.items():
            if len(house_planets) > 1:
                if house == 1:
                    house_analysis += f"• Multiple planets in 1st house ({', '.join(house_planets)}): Strong personality emphasis and leadership potential.\n"
                elif house == 10:
                    house_analysis += f"• Multiple planets in 10th house ({', '.join(house_planets)}): Career and reputation are major life themes.\n"
                elif house == 7:
                    house_analysis += f"• Multiple planets in 7th house ({', '.join(house_planets)}): Relationships and partnerships play a crucial role.\n"
                elif house == 4:
                    house_analysis += f"• Multiple planets in 4th house ({', '.join(house_planets)}): Home, family, and emotional security are central themes.\n"
                else:
                    house_analysis += f"• Multiple planets in {house}th house ({', '.join(house_planets)}): This house becomes a focal point of your life experiences.\n"

        return house_analysis if len(house_analysis) > 20 else ""

    def generate_kundali_interpretation(self, kundali: Dict[str, Any]) -> str:
        """
        Generate comprehensive interpretation combining all elements

        Args:
            kundali: Complete kundali dictionary with all astrological data

        Returns:
            String containing complete interpretation
        """
        interpretation_parts = []

        # 1. Lagna interpretation
        lagna = kundali.get('lagna', 'Unknown')
        interpretation_parts.append(self.interpret_lagna(lagna))

        # 2. Planetary placements
        planets = kundali.get('planets', [])
        interpretation_parts.append("\nPlanetary Placements:")

        for planet_data in planets:
            planet = planet_data.get('planet', 'Unknown')
            sign = planet_data.get('sign', 'Unknown')
            house = planet_data.get('house', 1)

            planet_interpretation = self.interpret_planet_placement(planet, sign, house)
            interpretation_parts.append(f"• {planet_interpretation}")

        # 3. Moon's Nakshatra
        moon_nakshatra = kundali.get('moon_nakshatra', {})
        nakshatra_interpretation = self.interpret_nakshatra(moon_nakshatra)
        interpretation_parts.append(f"\n{nakshatra_interpretation}")

        # 4. House analysis (if applicable)
        house_analysis = self.interpret_houses(planets)
        if house_analysis:
            interpretation_parts.append(house_analysis)

        # 5. Yoga interpretations
        yogas = kundali.get('detected_yogas', [])
        yoga_interpretation = self.interpret_yogas(yogas)
        interpretation_parts.append(f"\n{yoga_interpretation}")

        # 6. Summary note
        interpretation_parts.append("\nThis interpretation provides key insights from your Vedic astrology chart. "
                                   "Your chart is unique and contains many more subtleties that can be explored in detailed consultation.")

        return '\n'.join(interpretation_parts)


# Convenience functions for external use
def interpret_lagna(lagna: str) -> str:
    """Interpret Lagna sign - convenience function"""
    engine = InterpretationEngine()
    return engine.interpret_lagna(lagna)


def interpret_planet_placement(planet: str, sign: str, house: int) -> str:
    """Interpret planetary placement - convenience function"""
    engine = InterpretationEngine()
    return engine.interpret_planet_placement(planet, sign, house)


def interpret_nakshatra(nakshatra: Dict[str, Any]) -> str:
    """Interpret Moon's nakshatra - convenience function"""
    engine = InterpretationEngine()
    return engine.interpret_nakshatra(nakshatra)


def interpret_yogas(yogas: List[Dict[str, Any]]) -> str:
    """Interpret detected yogas - convenience function"""
    engine = InterpretationEngine()
    return engine.interpret_yogas(yogas)


def generate_kundali_interpretation(kundali: Dict[str, Any]) -> str:
    """Generate complete kundali interpretation - convenience function"""
    engine = InterpretationEngine()
    return engine.generate_kundali_interpretation(kundali)
