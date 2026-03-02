"""
Translation Manager for Multi-lingual Kundali API
Supports Hindi, English and extensible for other Indian languages
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# Import interpretation data modules
try:
    import interpretation_data
    import interpretation_data_hi
except ImportError as e:
    logging.warning(f"Could not import interpretation data: {e}")
    interpretation_data = None
    interpretation_data_hi = None

logger = logging.getLogger(__name__)


class TranslationManager:
    """
    Manages translations for the Kundali API

    Supports:
    - Hindi (hi)
    - English (en)
    - Extensible for Kannada (kn), Marathi (mr), Telugu (te), Tamil (ta), etc.
    """

    # Supported languages
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'हिन्दी (Hindi)',
        'kn': 'ಕನ್ನಡ (Kannada)',  # Future
        'mr': 'मराठी (Marathi)',    # Future
        'te': 'తెలుగు (Telugu)',    # Future
        'ta': 'தமிழ் (Tamil)',      # Future
    }

    DEFAULT_LANGUAGE = 'en'

    def __init__(self):
        """Initialize translation manager and load translation files"""
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.translations_dir = Path(__file__).parent / "translations"
        self._load_translations()

    def _load_translations(self):
        """Load all translation files from the translations directory"""
        try:
            if not self.translations_dir.exists():
                logger.warning(f"Translations directory not found: {self.translations_dir}")
                return

            for lang_code in ['en', 'hi', 'kn', 'mr', 'te', 'ta']:
                lang_file = self.translations_dir / f"{lang_code}.json"
                if lang_file.exists():
                    try:
                        with open(lang_file, 'r', encoding='utf-8') as f:
                            self.translations[lang_code] = json.load(f)
                        logger.info(f"Loaded translations for: {lang_code}")
                    except Exception as e:
                        logger.error(f"Error loading {lang_code}.json: {e}")
                else:
                    logger.debug(f"Translation file not found: {lang_file}")

            # Ensure at least English is loaded
            if 'en' not in self.translations:
                logger.error("English translations not loaded. System may not work correctly.")

        except Exception as e:
            logger.error(f"Error in _load_translations: {e}")

    def is_language_supported(self, lang_code: str) -> bool:
        """Check if a language is supported and has translations loaded"""
        return lang_code in self.translations

    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages with translations"""
        return {
            code: name
            for code, name in self.SUPPORTED_LANGUAGES.items()
            if code in self.translations
        }

    def translate(self, key_path: str, lang: str = 'en', default: Optional[str] = None) -> str:
        """
        Translate a key path (e.g., 'planets.Sun', 'common.name')

        Args:
            key_path: Dot-separated path to the translation key (e.g., 'planets.Sun')
            lang: Language code (default: 'en')
            default: Default value if translation not found

        Returns:
            Translated string or default/original key
        """
        # Validate language
        if not self.is_language_supported(lang):
            logger.warning(f"Language '{lang}' not supported, falling back to '{self.DEFAULT_LANGUAGE}'")
            lang = self.DEFAULT_LANGUAGE

        # Split the key path
        keys = key_path.split('.')

        # Navigate through the translation dictionary
        try:
            value = self.translations[lang]
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            # Fallback to English if key not found in requested language
            if lang != self.DEFAULT_LANGUAGE:
                try:
                    value = self.translations[self.DEFAULT_LANGUAGE]
                    for key in keys:
                        value = value[key]
                    return value
                except (KeyError, TypeError):
                    pass

            # Return default or the last key as fallback
            return default if default is not None else keys[-1]

    def translate_dict(self, data: Dict[str, Any], lang: str = 'en',
                      translate_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Recursively translate dictionary values

        Args:
            data: Dictionary to translate
            lang: Target language
            translate_keys: List of keys to translate (if None, translates common keys)

        Returns:
            Translated dictionary
        """
        if translate_keys is None:
            # Default translatable keys
            translate_keys = [
                'planet', 'sign', 'nakshatra', 'house', 'lord', 'name',
                'tithi', 'yoga', 'karana', 'vaara', 'masa', 'ritu'
            ]

        translated = {}
        for key, value in data.items():
            # Translate the key itself if it's in common translations
            translated_key = self.translate(f'common.{key}', lang, default=key)

            if isinstance(value, dict):
                translated[key] = self.translate_dict(value, lang, translate_keys)
            elif isinstance(value, list):
                translated[key] = [
                    self.translate_dict(item, lang, translate_keys) if isinstance(item, dict) else item
                    for item in value
                ]
            elif key in translate_keys and isinstance(value, str):
                # Try to translate the value
                for category in ['planets', 'zodiac_signs', 'nakshatras', 'houses', 'common']:
                    translated_value = self.translate(f'{category}.{value}', lang, default=None)
                    if translated_value != value:
                        translated[key] = translated_value
                        break
                else:
                    translated[key] = value
            else:
                translated[key] = value

        return translated

    def translate_planet_position(self, planet_data: Dict[str, Any], lang: str = 'en') -> Dict[str, Any]:
        """Translate a planet position dictionary"""
        translated = planet_data.copy()

        # Translate planet name
        if 'planet' in translated:
            translated['planet'] = self.translate(f'planets.{planet_data["planet"]}', lang)

        # Translate sign
        if 'sign' in translated:
            translated['sign'] = self.translate(f'zodiac_signs.{planet_data["sign"]}', lang)

        # Translate nakshatra name
        if 'nakshatra_name' in translated and translated['nakshatra_name']:
            translated['nakshatra_name'] = self.translate(
                f'nakshatras.{planet_data["nakshatra_name"]}', lang
            )

        # Translate sign lord
        if 'sign_lord' in translated and translated['sign_lord']:
            translated['sign_lord'] = self.translate(
                f'planets.{planet_data["sign_lord"]}', lang
            )

        # Translate nakshatra lord
        if 'nakshatra_lord' in translated and translated['nakshatra_lord']:
            translated['nakshatra_lord'] = self.translate(
                f'planets.{planet_data["nakshatra_lord"]}', lang
            )

        # Translate planet state/status
        if 'status' in translated and translated['status']:
            status_key = translated['status'].lower().replace(' ', '_')
            translated['status'] = self.translate(
                f'planet_states.{status_key}', lang, default=translated['status']
            )

        # Translate avastha
        if 'planet_awasta' in translated and translated['planet_awasta']:
            avastha_key = translated['planet_awasta'].lower()
            translated['planet_awasta'] = self.translate(
                f'avastha.{avastha_key}', lang, default=translated['planet_awasta']
            )

        return translated

    def translate_nakshatra_info(self, nakshatra_data: Dict[str, Any], lang: str = 'en') -> Dict[str, Any]:
        """Translate nakshatra information"""
        translated = nakshatra_data.copy()

        if 'name' in translated:
            translated['name'] = self.translate(f'nakshatras.{nakshatra_data["name"]}', lang)

        if 'lord' in translated:
            translated['lord'] = self.translate(f'planets.{nakshatra_data["lord"]}', lang)

        return translated

    def translate_rasi_chart(self, chart: Dict[str, List[str]], lang: str = 'en') -> Dict[str, List[str]]:
        """Translate rasi chart house-wise planet placement"""
        translated_chart = {}

        for house, planets in chart.items():
            translated_planets = []
            for planet in planets:
                if planet == 'Lagna':
                    translated_planets.append(self.translate('planets.Lagna', lang))
                else:
                    translated_planets.append(self.translate(f'planets.{planet}', lang))
            translated_chart[house] = translated_planets

        return translated_chart

    def translate_panchanga(self, panchanga_data: Dict[str, Any], lang: str = 'en') -> Dict[str, Any]:
        """Translate panchanga information"""
        translated = {}

        # These are already in the target format, just return as-is
        # The keys themselves can be translated by the response wrapper
        for key, value in panchanga_data.items():
            translated[key] = value

        return translated

    def translate_dasha_info(self, dasha_data: Dict[str, Any], lang: str = 'en') -> Dict[str, Any]:
        """Translate dasha information including nested sub_periods"""
        translated = dasha_data.copy()

        # Translate main planet
        if 'planet' in translated:
            translated['planet'] = self.translate(f'planets.{dasha_data["planet"]}', lang)

        # Translate sub_periods recursively
        if 'sub_periods' in translated and isinstance(translated['sub_periods'], list):
            translated['sub_periods'] = [
                self.translate_dasha_info(sub_period, lang)
                for sub_period in translated['sub_periods']
            ]

        return translated

    def translate_full_response(self, response: Dict[str, Any], lang: str = 'en') -> Dict[str, Any]:
        """
        Translate a complete Kundali response

        Args:
            response: Full API response dictionary
            lang: Target language code

        Returns:
            Fully translated response with UI labels
        """
        if lang == 'en' or not self.is_language_supported(lang):
            return response

        translated = response.copy()

        # Add translated UI labels for frontend
        translated['ui_labels'] = {
            'yogas': {
                'name': self.translate('yogas.name', lang, default='Name'),
                'description': self.translate('yogas.description', lang, default='Description'),
                'significance': self.translate('yogas.significance', lang, default='Significance'),
                'effects': self.translate('yogas.effects', lang, default='Effects'),
                'planets_involved': self.translate('yogas.planets_involved', lang, default='Planets Involved'),
                'houses_involved': self.translate('yogas.houses_involved', lang, default='Houses Involved'),
                'strength': self.translate('yogas.strength', lang, default='Strength')
            },
            'yoga_summary': {
                'total_yogas': self.translate('yogas.total_yogas', lang, default='Total Yogas'),
                'strong_yogas': self.translate('yogas.strong_yogas', lang, default='Strong Yogas'),
                'moderate_yogas': self.translate('yogas.moderate_yogas', lang, default='Moderate Yogas'),
                'weak_yogas': self.translate('yogas.weak_yogas', lang, default='Weak Yogas'),
                'most_significant': self.translate('yogas.most_significant', lang, default='Most Significant')
            }
        }

        # Translate planets
        if 'planets' in translated:
            translated['planets'] = [
                self.translate_planet_position(p, lang)
                for p in translated['planets']
            ]

        # Translate lagna
        if 'lagna' in translated and isinstance(translated['lagna'], dict):
            if 'sign' in translated['lagna']:
                translated['lagna']['sign'] = self.translate(
                    f'zodiac_signs.{response["lagna"]["sign"]}', lang
                )

        # Translate rasi chart
        if 'rasi_chart' in translated:
            translated['rasi_chart'] = self.translate_rasi_chart(
                translated['rasi_chart'], lang
            )

        # Translate moon nakshatra
        if 'moon_nakshatra' in translated:
            translated['moon_nakshatra'] = self.translate_nakshatra_info(
                translated['moon_nakshatra'], lang
            )

        # Translate current dasha
        if 'current_dasha' in translated:
            translated['current_dasha'] = self.translate_dasha_info(
                translated['current_dasha'], lang
            )

        # Translate vimshottari dasha
        if 'vimshottari_dasha' in translated:
            translated['vimshottari_dasha'] = [
                self.translate_dasha_info(d, lang)
                for d in translated['vimshottari_dasha']
            ]

        # Translate navamsa chart if present
        if 'navamsa_chart' in translated and 'navamsa_chart' in translated['navamsa_chart']:
            translated['navamsa_chart']['navamsa_chart'] = self.translate_rasi_chart(
                translated['navamsa_chart']['navamsa_chart'], lang
            )

        # Translate detected yogas (planets involved, name, description, significance, effects, strength)
        if 'detected_yogas' in translated and isinstance(translated['detected_yogas'], list):
            for i, yoga in enumerate(translated['detected_yogas']):
                # Get original yoga data to use as lookup key
                original_yoga = response.get('detected_yogas', [])[i] if i < len(response.get('detected_yogas', [])) else yoga
                original_name = original_yoga.get('name', yoga.get('name', ''))

                # Translate yoga name
                if 'name' in yoga:
                    yoga['name'] = self.translate(f'yoga_names.{original_name}', lang, default=yoga['name'])

                # Translate yoga description
                if 'description' in yoga:
                    yoga['description'] = self.translate(f'yoga_descriptions.{original_name}', lang, default=yoga['description'])

                # Translate yoga significance
                if 'significance' in yoga:
                    yoga['significance'] = self.translate(f'yoga_significance.{original_name}', lang, default=yoga['significance'])

                # Translate yoga strength
                if 'strength' in yoga:
                    yoga['strength'] = self.translate(f'yoga_strength.{yoga["strength"]}', lang, default=yoga['strength'])

                # Translate yoga effects
                if 'effects' in yoga and isinstance(yoga['effects'], list):
                    translated_effects = self.translate(f'yoga_effects.{original_name}', lang, default=None)
                    if translated_effects and isinstance(translated_effects, list):
                        yoga['effects'] = translated_effects

                # Translate planets involved
                if 'planets_involved' in yoga and isinstance(yoga['planets_involved'], list):
                    yoga['planets_involved'] = [
                        self.translate(f'planets.{planet}', lang, default=planet)
                        for planet in yoga['planets_involved']
                    ]

        # Translate panchanga data
        if 'panchanga' in translated and isinstance(translated['panchanga'], dict):
            translated['panchanga'] = self.translate_panchanga(translated['panchanga'], lang)

        # Translate enhanced_panchanga
        if 'enhanced_panchanga' in translated and isinstance(translated['enhanced_panchanga'], dict):
            ep = translated['enhanced_panchanga']
            # Translate nakshatra lord
            if 'nakshatra' in ep and isinstance(ep['nakshatra'], dict) and 'lord' in ep['nakshatra']:
                ep['nakshatra']['lord'] = self.translate(f'planets.{ep["nakshatra"]["lord"]}', lang, default=ep['nakshatra']['lord'])
            # Translate vaara lord
            if 'vaara' in ep and isinstance(ep['vaara'], dict) and 'lord' in ep['vaara']:
                ep['vaara']['lord'] = self.translate(f'planets.{ep["vaara"]["lord"]}', lang, default=ep['vaara']['lord'])

        # Translate yoga_summary if present
        if 'yoga_summary' in translated and isinstance(translated['yoga_summary'], dict):
            yoga_summary = translated['yoga_summary']

            # Translate strong_yogas list
            if 'strong_yogas' in yoga_summary and isinstance(yoga_summary['strong_yogas'], list):
                yoga_summary['strong_yogas'] = [
                    self.translate(f'yoga_names.{yoga_name}', lang, default=yoga_name)
                    for yoga_name in yoga_summary['strong_yogas']
                ]

            # Translate moderate_yogas list
            if 'moderate_yogas' in yoga_summary and isinstance(yoga_summary['moderate_yogas'], list):
                yoga_summary['moderate_yogas'] = [
                    self.translate(f'yoga_names.{yoga_name}', lang, default=yoga_name)
                    for yoga_name in yoga_summary['moderate_yogas']
                ]

            # Translate weak_yogas list
            if 'weak_yogas' in yoga_summary and isinstance(yoga_summary['weak_yogas'], list):
                yoga_summary['weak_yogas'] = [
                    self.translate(f'yoga_names.{yoga_name}', lang, default=yoga_name)
                    for yoga_name in yoga_summary['weak_yogas']
                ]

            # Translate most_significant yoga
            if 'most_significant' in yoga_summary and yoga_summary['most_significant']:
                yoga_summary['most_significant'] = self.translate(
                    f'yoga_names.{yoga_summary["most_significant"]}',
                    lang,
                    default=yoga_summary['most_significant']
                )

        # Translate mangal_dosha and kalasarpa_dosha (no planet names to translate, just keeping structure)
        # These are descriptive text reports, so we keep them as-is

        # =================== KP SYSTEM TRANSLATION ===================
        # Translate kp_system data
        if 'kp_system' in translated and isinstance(translated['kp_system'], dict):
            kp_system = translated['kp_system']

            # Translate planets_table
            if 'planets_table' in kp_system and isinstance(kp_system['planets_table'], list):
                for planet_row in kp_system['planets_table']:
                    if isinstance(planet_row, dict):
                        # Translate Planet name
                        if 'Planet' in planet_row:
                            planet_row['Planet'] = self.translate(f'planets.{planet_row["Planet"]}', lang, default=planet_row['Planet'])
                        # Translate Sign name
                        if 'Sign' in planet_row:
                            planet_row['Sign'] = self.translate(f'zodiac_signs.{planet_row["Sign"]}', lang, default=planet_row['Sign'])
                        # Translate Sign_Lord
                        if 'Sign_Lord' in planet_row:
                            planet_row['Sign_Lord'] = self.translate(f'planets.{planet_row["Sign_Lord"]}', lang, default=planet_row['Sign_Lord'])
                        # Translate Star_Lord
                        if 'Star_Lord' in planet_row:
                            planet_row['Star_Lord'] = self.translate(f'planets.{planet_row["Star_Lord"]}', lang, default=planet_row['Star_Lord'])
                        # Translate Sub_Lord
                        if 'Sub_Lord' in planet_row:
                            planet_row['Sub_Lord'] = self.translate(f'planets.{planet_row["Sub_Lord"]}', lang, default=planet_row['Sub_Lord'])

            # Translate cusps_table
            if 'cusps_table' in kp_system and isinstance(kp_system['cusps_table'], list):
                for cusp_row in kp_system['cusps_table']:
                    if isinstance(cusp_row, dict):
                        # Translate Sign name
                        if 'Sign' in cusp_row:
                            cusp_row['Sign'] = self.translate(f'zodiac_signs.{cusp_row["Sign"]}', lang, default=cusp_row['Sign'])
                        # Translate Sign_Lord
                        if 'Sign_Lord' in cusp_row:
                            cusp_row['Sign_Lord'] = self.translate(f'planets.{cusp_row["Sign_Lord"]}', lang, default=cusp_row['Sign_Lord'])
                        # Translate Star_Lord
                        if 'Star_Lord' in cusp_row:
                            cusp_row['Star_Lord'] = self.translate(f'planets.{cusp_row["Star_Lord"]}', lang, default=cusp_row['Star_Lord'])
                        # Translate Sub_Lord
                        if 'Sub_Lord' in cusp_row:
                            cusp_row['Sub_Lord'] = self.translate(f'planets.{cusp_row["Sub_Lord"]}', lang, default=cusp_row['Sub_Lord'])

            # Translate ruling_planets
            if 'ruling_planets' in kp_system and isinstance(kp_system['ruling_planets'], dict):
                # Translate Moon (Mo) ruling planets
                if 'Mo' in kp_system['ruling_planets'] and isinstance(kp_system['ruling_planets']['Mo'], dict):
                    mo = kp_system['ruling_planets']['Mo']
                    if 'sign_lord' in mo:
                        mo['sign_lord'] = self.translate(f'planets.{mo["sign_lord"]}', lang, default=mo['sign_lord'])
                    if 'star_lord' in mo:
                        mo['star_lord'] = self.translate(f'planets.{mo["star_lord"]}', lang, default=mo['star_lord'])
                    if 'sub_lord' in mo:
                        mo['sub_lord'] = self.translate(f'planets.{mo["sub_lord"]}', lang, default=mo['sub_lord'])

                # Translate Ascendant (Asc) ruling planets
                if 'Asc' in kp_system['ruling_planets'] and isinstance(kp_system['ruling_planets']['Asc'], dict):
                    asc = kp_system['ruling_planets']['Asc']
                    if 'sign_lord' in asc:
                        asc['sign_lord'] = self.translate(f'planets.{asc["sign_lord"]}', lang, default=asc['sign_lord'])
                    if 'star_lord' in asc:
                        asc['star_lord'] = self.translate(f'planets.{asc["star_lord"]}', lang, default=asc['star_lord'])
                    if 'sub_lord' in asc:
                        asc['sub_lord'] = self.translate(f'planets.{asc["sub_lord"]}', lang, default=asc['sub_lord'])

                # Translate Day Lord planet name
                if 'Day Lord' in kp_system['ruling_planets'] and isinstance(kp_system['ruling_planets']['Day Lord'], dict):
                    day_lord = kp_system['ruling_planets']['Day Lord']
                    if 'planet' in day_lord:
                        day_lord['planet'] = self.translate(f'planets.{day_lord["planet"]}', lang, default=day_lord['planet'])

            # Translate house_significators (planet names in lists)
            if 'house_significators' in kp_system and isinstance(kp_system['house_significators'], dict):
                for house_num, significators in kp_system['house_significators'].items():
                    if isinstance(significators, dict):
                        for strength_type in ['strong', 'medium', 'weak']:
                            if strength_type in significators and isinstance(significators[strength_type], list):
                                translated_list = []
                                for item in significators[strength_type]:
                                    # Translate planet names in items like "Saturn (in house)"
                                    for planet in self.get_planet_names():
                                        if planet in item:
                                            translated_planet = self.translate(f'planets.{planet}', lang, default=planet)
                                            item = item.replace(planet, translated_planet)
                                            break
                                    translated_list.append(item)
                                significators[strength_type] = translated_list

            # Translate kp_chart (planet names)
            if 'kp_chart' in kp_system and isinstance(kp_system['kp_chart'], dict):
                for house_num, planets in kp_system['kp_chart'].items():
                    if isinstance(planets, list):
                        kp_system['kp_chart'][house_num] = [
                            self.translate(f'planets.{p}', lang, default=p) for p in planets
                        ]

            # Translate chart_layout (planet names as keys)
            if 'chart_layout' in kp_system and isinstance(kp_system['chart_layout'], dict):
                translated_layout = {}
                for planet, house in kp_system['chart_layout'].items():
                    translated_planet = self.translate(f'planets.{planet}', lang, default=planet)
                    translated_layout[translated_planet] = house
                kp_system['chart_layout'] = translated_layout

            # Translate system text (optional - usually kept as-is for technical reference)

        # =================== BHAVA CHALIT TRANSLATION ===================
        # Translate bhava_chalit data
        if 'bhava_chalit' in translated and isinstance(translated['bhava_chalit'], dict):
            bhava = translated['bhava_chalit']

            # Translate bhava_cusps (sign names)
            if 'bhava_cusps' in bhava and isinstance(bhava['bhava_cusps'], dict):
                for cusp_num, cusp_data in bhava['bhava_cusps'].items():
                    if isinstance(cusp_data, dict) and 'sign' in cusp_data:
                        cusp_data['sign'] = self.translate(f'zodiac_signs.{cusp_data["sign"]}', lang, default=cusp_data['sign'])

            # Translate bhava_chart (planet names)
            if 'bhava_chart' in bhava and isinstance(bhava['bhava_chart'], dict):
                for house_num, planets in bhava['bhava_chart'].items():
                    if isinstance(planets, list):
                        bhava['bhava_chart'][house_num] = [
                            self.translate(f'planets.{p}', lang, default=p) for p in planets
                        ]

            # Translate planet_details (planet names, sign names)
            if 'planet_details' in bhava and isinstance(bhava['planet_details'], dict):
                # Collect changes first to avoid modifying dict during iteration
                planet_renames = {}
                for planet_name, details in bhava['planet_details'].items():
                    if isinstance(details, dict):
                        # Translate the planet name key itself
                        translated_planet_name = self.translate(f'planets.{planet_name}', lang, default=planet_name)
                        if translated_planet_name != planet_name:
                            planet_renames[planet_name] = translated_planet_name

                        # Translate sign name
                        if 'sign' in details:
                            details['sign'] = self.translate(f'zodiac_signs.{details["sign"]}', lang, default=details['sign'])

                # Apply the renames after iteration
                for old_name, new_name in planet_renames.items():
                    if old_name in bhava['planet_details']:
                        bhava['planet_details'][new_name] = bhava['planet_details'].pop(old_name)

            # Translate system text (optional - usually kept as-is for technical reference)

        # =================== BHAVA HOUSE STRENGTHS ===================
        # Translate bhava_house_strengths (planet names)
        if 'bhava_house_strengths' in translated and isinstance(translated['bhava_house_strengths'], dict):
            for house_num, strength_data in translated['bhava_house_strengths'].items():
                if isinstance(strength_data, dict) and 'planets' in strength_data and isinstance(strength_data['planets'], list):
                    strength_data['planets'] = [
                        self.translate(f'planets.{p}', lang, default=p) for p in strength_data['planets']
                    ]

        # =================== COMPARISON ===================
        # Translate comparison text (optional - can keep as-is for technical reference)

        # =================== STATUS ===================
        # Translate status
        if 'status' in translated and translated['status'] == 'success':
            translated['status'] = self.translate('status.success', lang, default='success')

        return translated

    def get_interpretation_data(self, lang: str = 'en') -> Any:
        """
        Get interpretation data module for the specified language

        Args:
            lang: Language code ('en' or 'hi')

        Returns:
            interpretation_data module for the language (falls back to English if not available)
        """
        if lang == 'hi' and interpretation_data_hi is not None:
            return interpretation_data_hi

        # Default to English
        return interpretation_data if interpretation_data is not None else None

    def get_zodiac_traits(self, sign: str, lang: str = 'en') -> Dict[str, str]:
        """
        Get zodiac traits (Rashi and Lagna descriptions) for a sign in the specified language

        Args:
            sign: Zodiac sign name (e.g., 'Aries', 'Taurus')
            lang: Language code

        Returns:
            Dictionary with 'Rashi' and 'Lagna' descriptions
        """
        data = self.get_interpretation_data(lang)
        if data and hasattr(data, 'ZODIAC_TRAITS'):
            return data.ZODIAC_TRAITS.get(sign, {})
        return {}

    def get_house_sign_interpretation(self, house: int, sign: str, lang: str = 'en') -> str:
        """
        Get house-sign interpretation in the specified language

        Args:
            house: House number (1-12)
            sign: Zodiac sign name
            lang: Language code

        Returns:
            Interpretation text
        """
        data = self.get_interpretation_data(lang)
        if data and hasattr(data, 'HOUSE_SIGN_INTERPRETATIONS'):
            return data.HOUSE_SIGN_INTERPRETATIONS.get(house, {}).get(sign, "")
        return ""

    def get_planet_personality(self, planet: str, lang: str = 'en') -> Dict[str, Any]:
        """
        Get planet personality traits in the specified language

        Args:
            planet: Planet name (e.g., 'Sun', 'Moon')
            lang: Language code

        Returns:
            Dictionary with positive_traits, negative_traits, neutral_traits, effects_on_signs
        """
        data = self.get_interpretation_data(lang)
        if data and hasattr(data, 'PLANET_PERSONALITY'):
            return data.PLANET_PERSONALITY.get(planet, {})
        return {}

    def get_extended_planetary_details(self, planet: str, lang: str = 'en') -> Dict[str, Any]:
        """
        Get extended planetary details (significance, deity, remedies) in the specified language

        Args:
            planet: Planet name (e.g., 'Sun', 'Moon')
            lang: Language code

        Returns:
            Dictionary with planetary_significance, presiding_deity_and_divine_energy,
            influence_in_astrology, remedies_and_worship
        """
        data = self.get_interpretation_data(lang)
        if data and hasattr(data, 'EXTENDED_PLANETARY_DETAILS'):
            return data.EXTENDED_PLANETARY_DETAILS.get(planet, {})
        return {}

    def get_house_theme(self, house: int, lang: str = 'en') -> str:
        """
        Get house theme description in the specified language

        Args:
            house: House number (1-12)
            lang: Language code

        Returns:
            House theme description
        """
        data = self.get_interpretation_data(lang)
        if data and hasattr(data, 'HOUSE_THEMES'):
            return data.HOUSE_THEMES.get(house, "")
        return ""

    def get_planet_names(self) -> list:
        """
        Get list of all planet names for translation purposes

        Returns:
            List of planet names (English)
        """
        return [
            'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn',
            'Rahu', 'Ketu', 'Lagna', 'Ascendant', 'Asc'
        ]


# Global translation manager instance
_translation_manager = None


def get_translation_manager() -> TranslationManager:
    """Get or create the global translation manager instance"""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def translate(key_path: str, lang: str = 'en', default: Optional[str] = None) -> str:
    """Convenience function for translation"""
    return get_translation_manager().translate(key_path, lang, default)
