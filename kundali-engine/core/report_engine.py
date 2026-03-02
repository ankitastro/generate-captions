# Report Engine for generating human-readable Kundali reports

from typing import Dict, Any, List
from translation_manager import get_translation_manager

class ReportEngine:
    def __init__(self):
        """Initialize Report Engine with translation manager"""
        self.translation_manager = get_translation_manager()

    def _format_remedies(self, remedies: Dict, language: str = 'en') -> str:
        """Formats the remedies dictionary into a readable string."""
        remedy_parts = []
        for key, text in remedies.items():
            # Try to translate the remedy section title
            translated_key = self.translation_manager.translate(f'remedies.{key}', language, default=key)
            title = translated_key.replace('_', ' ').title()
            remedy_parts.append(f"**{title}:** {text}")
        return "\n".join(remedy_parts)

    def generate_kundali_report(self, kundali_data: Dict[str, Any], language: str = 'en') -> str:
        """
        Generates a full, human-readable interpretation from calculated Kundli data.

        Args:
            kundali_data: Dictionary containing kundali calculation results
            language: Language code ('en', 'hi', etc.)

        Returns:
            Formatted report string
        """
        report_parts = []

        # --- Section 1: Lagna and Rashi ---
        lagna_sign = kundali_data.get('lagna', {}).get('sign', 'Aries')
        planets = kundali_data.get('planets', [])
        moon_sign = next((p['sign'] for p in planets if p['planet'] == 'Moon'), 'Aries')

        # Get zodiac traits from translation manager
        lagna_traits = self.translation_manager.get_zodiac_traits(lagna_sign, lang=language)
        moon_traits = self.translation_manager.get_zodiac_traits(moon_sign, lang=language)

        # Translate sign names
        lagna_sign_translated = self.translation_manager.translate(f'zodiac_signs.{lagna_sign}', language, default=lagna_sign)
        moon_sign_translated = self.translation_manager.translate(f'zodiac_signs.{moon_sign}', language, default=moon_sign)

        # report_parts.append("## 1. Key Chart Points: Lagna and Rashi\n")
        report_parts.append(f"### {self.translation_manager.translate('report_headings.lagna_ascendant', language, default='Lagna (Ascendant)')}\n**{self.translation_manager.translate('common.sign', language, default='Sign')}:** {lagna_sign_translated}")
        report_parts.append(f"**{self.translation_manager.translate('common.trait', language, default='Trait')}:** {lagna_traits.get('Lagna', 'No data.')}\n")

        report_parts.append(f"### {self.translation_manager.translate('report_headings.rashi_moon_sign', language, default='Rashi (Moon sign)')}\n**{self.translation_manager.translate('common.sign', language, default='Sign')}:** {moon_sign_translated}")
        report_parts.append(f"**{self.translation_manager.translate('common.trait', language, default='Trait')}:** {moon_traits.get('Rashi', 'No data.')}\n")

        # # --- Section 2: House-by-House Analysis ---
        # report_parts.append("## 2. Houses and Their Details\n")

        # sign_names = list(ZODIAC_TRAITS.keys())
        # lagna_sign_index = sign_names.index(lagna_sign)

        # for i in range(1, 13):
        #     house_num_str = {1:"1st", 2:"2nd", 3:"3rd"}.get(i, f"{i}th")
        #     sign_in_house = sign_names[(lagna_sign_index + i - 1) % 12]

        #     report_parts.append(f"### {house_num_str} House ({sign_in_house}):")
        #     report_parts.append(f"**Theme:** {HOUSE_THEMES.get(i, '')}")
        #     report_parts.append(HOUSE_SIGN_INTERPRETATIONS.get(f"{i}_House", {}).get(sign_in_house, ''))

        #     planets_in_house = [p for p in planets if p['house'] == i]
        #     if planets_in_house:
        #         planet_names = ", ".join([p['planet'] for p in planets_in_house])
        #         report_parts.append(f"\n**Planets:** {planet_names}.")
        #         # Here you would add the Planet IN House effects if you have that data.
        #     report_parts.append("\n")

        # --- Section 3: Planetary Details ---
        report_parts.append(f"## {self.translation_manager.translate('common.planetary_details', language, default='Planetary Details and Their Extended Information')}\n")

        # Get list of planets that have extended details
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        sorted_planets = sorted([p for p in planets if p['planet'] in planet_names], key=lambda x: x['planet'])

        for p in sorted_planets:
            planet_name = p['planet']

            # Translate planet name, sign, and get personality/extended details
            planet_name_translated = self.translation_manager.translate(f'planets.{planet_name}', language, default=planet_name)
            sign_translated = self.translation_manager.translate(f'zodiac_signs.{p["sign"]}', language, default=p['sign'])
            house_translated = self.translation_manager.translate(f'houses.{p["house"]}', language, default=f"{p['house']}th")
            personality = self.translation_manager.get_planet_personality(planet_name, lang=language)
            extended = self.translation_manager.get_extended_planetary_details(planet_name, lang=language)

            report_parts.append(f"### {planet_name_translated} ({sign_translated}, {house_translated} {self.translation_manager.translate('common.house', language, default='House')}):")
            report_parts.append(f"**{self.translation_manager.translate('common.position', language, default='Position')}:** {p['degree_dms']}")
            report_parts.append(f"**{self.translation_manager.translate('common.retrograde', language, default='Retrograde')}:** {self.translation_manager.translate('yes_no.Yes', language, default='Yes') if p['retrograde'] else self.translation_manager.translate('yes_no.No', language, default='No')}")

            # Translate Awastha
            awastha_value = p.get('planet_awasta', '--')
            if awastha_value != '--':
                translated_awastha = self.translation_manager.translate(f'avastha.{awastha_value.lower()}', language, default=awastha_value)
            else:
                translated_awastha = '--'
            report_parts.append(f"**{self.translation_manager.translate('common.awastha', language, default='Awastha')}:** {translated_awastha}\n")

            if personality.get("positive_traits"):
                report_parts.append(f"**{self.translation_manager.translate('common.positive_traits', language, default='Positive Traits')}:** {' '.join(personality['positive_traits'])}\n")
            if personality.get("negative_traits"):
                report_parts.append(f"**{self.translation_manager.translate('common.negative_traits', language, default='Negative Traits')}:** {' '.join(personality['negative_traits'])}\n")

            if extended:
                report_parts.append(f"**{self.translation_manager.translate('report_headings.extended_details', language, default='Extended Details')}:**")
                report_parts.append(f"- **{self.translation_manager.translate('report_headings.planetary_significance', language, default='Planetary Significance')}:** {extended.get('planetary_significance', '')}")
                report_parts.append(f"- **{self.translation_manager.translate('report_headings.presiding_deity', language, default='Presiding Deity')}:** {extended.get('presiding_deity_and_divine_energy', '')}")
                report_parts.append(f"- **{self.translation_manager.translate('report_headings.influence_in_astrology', language, default='Influence in Astrology')}:** {extended.get('influence_in_astrology', '')}")
                report_parts.append(f"- **{self.translation_manager.translate('report_headings.remedies_and_worship', language, default='Remedies and Worship')}:**")
                remedies_text = self._format_remedies(extended.get('remedies_and_worship', {}), language)
                report_parts.append(remedies_text + "\n")

        return "\n".join(report_parts)
