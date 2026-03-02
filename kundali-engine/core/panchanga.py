"""
Enhanced Panchanga Module

This module provides comprehensive daily panchanga calculations using the
drik-panchanga library for accurate astronomical data.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import pytz
import swisseph as swe
from skyfield import almanac
from .skyfield_helper import ts, eph, get_observer
from skyfield.api import wgs84


# Add the drik-panchanga directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'drik-panchanga'))

try:
    from panchanga import (
        gregorian_to_jd, Date, Place, tithi, nakshatra, yoga, karana,
        vaara, masa, ritu, samvatsara, sunrise, sunset
    )
except ImportError:
    print("Warning: Could not import from panchanga module, using basic implementation")
    # Fallback to basic implementation if drik-panchanga is not available


from models import PanchangaInfo

class EnhancedPanchanga:
    """
    Enhanced Panchanga calculator providing comprehensive daily panchanga details
    """

    # Sanskrit names mapping
    TITHI_NAMES = [
        "Pratipad", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti", "Saptami",
        "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
        "Purnima", "Pratipad", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashti",
        "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi",
        "Chaturdashi", "Amavasya"
    ]

    NAKSHATRA_NAMES = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
        "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
        "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
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

    SAMVATSARA_NAMES = [
        "Prabhava", "Vibhava", "Shukla", "Pramodoota", "Prajothpatti", "Angirasa", "Shrimukha",
        "Bhava", "Yuva", "Dhata", "Ishvara", "Bahudhanya", "Pramathin", "Vikrama", "Vrisha",
        "Chitrabhanu", "Swabhanu", "Tarana", "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari",
        "Virodhin", "Vikrita", "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
        "Hemalambi", "Vilamba", "Vikari", "Sharvari", "Plava", "Shubhakrit", "Sobhakrit",
        "Krodhin", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka", "Saumya", "Sadharana",
        "Virodhikrit", "Paridhavin", "Pramadin", "Ananda", "Rakshasa", "Nala", "Pingala",
        "Kalayukti", "Siddharthi", "Raudri", "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi",
        "Krodhana", "Akshaya"
    ]

    def __init__(self):
        """Initialize the Enhanced Panchanga calculator"""
        self.translation_manager = None

    def _get_translation_manager(self):
        """Lazy load translation manager to avoid circular imports"""
        if self.translation_manager is None:
            try:
                from translation_manager import get_translation_manager
                self.translation_manager = get_translation_manager()
            except ImportError:
                self.translation_manager = None
        return self.translation_manager

    def _translate_panchanga_value(self, category: str, value: str, lang: str = 'en') -> str:
        """Translate a panchanga value using the translation manager"""
        if lang == 'en':
            return value

        tm = self._get_translation_manager()
        if tm is None:
            return value

        # Map categories to translation keys
        category_map = {
            'tithi': 'tithi_names',
            'yoga': 'yoga_names',
            'karana': 'karana_names',
            'vaara': 'vaara_names',
            'masa': 'masa_names',
            'ritu': 'ritu_names',
            'paksha': 'paksha_names',
            'masa_type': 'masa_type'
        }

        translation_key = category_map.get(category)
        if translation_key:
            return tm.translate(f'{translation_key}.{value}', lang, default=value)

        return value

    def get_details(self, jd: float, latitude: float, longitude: float, timezone_str: str, person_obj, lang: str = 'en') -> Dict[str, Any]:
        """
        Get comprehensive daily panchanga details in the correct nested dictionary format.
        """
        try:
            tz = pytz.timezone(timezone_str)
            greg_tuple = swe.revjul(jd, swe.GREG_CAL)
            naive_dt = datetime(greg_tuple[0], greg_tuple[1], greg_tuple[2], int(greg_tuple[3]), int((greg_tuple[3] % 1) * 60))
            aware_dt = tz.localize(naive_dt)
            offset = aware_dt.utcoffset().total_seconds() / 3600.0
            place = Place(latitude, longitude, offset)

            # Calculate all panchanga components
            tithi_info = self._get_tithi_details(jd, place)
            nakshatra_info = self._get_nakshatra_details(jd, place)
            yoga_info = self._get_yoga_details(jd, place)
            karana_info = self._get_karana_details(jd, place)
            vaara_info = self._get_vaara_details(jd)
            masa_info = self._get_masa_details(jd, place)
            ritu_info = self._get_ritu_details(masa_info["number"])
            samvatsara_info = self._get_samvatsara_details(jd, masa_info["number"])
            rise_set_info = self._get_sunrise_and_sunset(jd, place, timezone_str)
            sunrise_info = rise_set_info["sunrise"]
            sunset_info = rise_set_info["sunset"]

            # Calculate day duration from the correct values
            day_duration_hours = (sunset_info['local_time'] - sunrise_info['local_time']) * 24
            day_duration_ghatikas = day_duration_hours * 2.5

            # Translate values if language is not English
            if lang != 'en':
                tithi_info = self._translate_tithi_info(tithi_info, lang)
                nakshatra_info = self._translate_nakshatra_info(nakshatra_info, lang)
                yoga_info = self._translate_yoga_info(yoga_info, lang)
                karana_info = self._translate_karana_info(karana_info, lang)
                vaara_info = self._translate_vaara_info(vaara_info, lang)
                masa_info = self._translate_masa_info(masa_info, lang)
                ritu_info = self._translate_ritu_info(ritu_info, lang)

            # Assemble the final nested dictionary correctly
            return {
                "tithi": tithi_info,
                "nakshatra": nakshatra_info,
                "yoga": yoga_info,
                "karana": karana_info,
                "vaara": vaara_info,
                "masa": masa_info,
                "ritu": ritu_info,
                "samvatsara": samvatsara_info,
                "sunrise": sunrise_info, # Use the dictionary directly
                "sunset": sunset_info,   # Use the dictionary directly
                "day_duration": {
                    "hours": round(day_duration_hours, 2),
                    "ghatikas": round(day_duration_ghatikas, 2)
                }
            }
        except Exception as e:
            print(f"Error in detailed panchanga calculation: {e}")
            return self._get_fallback_panchanga()


    def _get_tithi_details(self, jd: float, place) -> Dict[str, Any]:
        """Get detailed tithi information"""
        try:
            tithi_info = tithi(jd, place)

            # Handle different return formats
            if isinstance(tithi_info, (list, tuple)) and len(tithi_info) >= 2:
                tithi_num = int(tithi_info[0]) if isinstance(tithi_info[0], (int, float)) else 1
                tithi_end = tithi_info[1] if len(tithi_info) > 1 else [0, 0, 0]
            else:
                tithi_num = int(tithi_info) if isinstance(tithi_info, (int, float)) else 1
                tithi_end = [0, 0, 0]

            # Ensure tithi_num is in valid range
            if tithi_num < 1 or tithi_num > 30:
                tithi_num = 1

            paksha = "Shukla" if tithi_num <= 15 else "Krishna"

            # Format time safely
            if isinstance(tithi_end, (list, tuple)) and len(tithi_end) >= 3:
                end_time = f"{int(tithi_end[0]):02d}:{int(tithi_end[1]):02d}:{int(tithi_end[2]):02d}"
            else:
                end_time = "00:00:00"

            return {
                "name": self.TITHI_NAMES[tithi_num - 1],
                "number": tithi_num,
                "end_time": end_time,
                "paksha": paksha
            }
        except Exception as e:
            print(f"Error calculating tithi: {e}")
            return {"name": "Pratipad", "number": 1, "end_time": "00:00:00", "paksha": "Shukla"}

    def _get_nakshatra_details(self, jd: float, place) -> Dict[str, Any]:
        """Get detailed nakshatra information"""
        try:
            nak_info = nakshatra(jd, place)

            # Handle different return formats
            if isinstance(nak_info, (list, tuple)) and len(nak_info) >= 2:
                nak_num = int(nak_info[0]) if isinstance(nak_info[0], (int, float)) else 1
                nak_end = nak_info[1] if len(nak_info) > 1 else [0, 0, 0]
            else:
                nak_num = int(nak_info) if isinstance(nak_info, (int, float)) else 1
                nak_end = [0, 0, 0]

            # Ensure nak_num is in valid range
            if nak_num < 1 or nak_num > 27:
                nak_num = 1

            # Nakshatra lords in order
            nakshatra_lords = [
                "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
                "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon",
                "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
                "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
                "Saturn", "Mercury"
            ]

            # Format time safely
            if isinstance(nak_end, (list, tuple)) and len(nak_end) >= 3:
                end_time = f"{int(nak_end[0]):02d}:{int(nak_end[1]):02d}:{int(nak_end[2]):02d}"
            else:
                end_time = "00:00:00"

            return {
                "name": self.NAKSHATRA_NAMES[nak_num - 1],
                "number": nak_num,
                "end_time": end_time,
                "lord": nakshatra_lords[nak_num - 1]
            }
        except Exception as e:
            print(f"Error calculating nakshatra: {e}")
            return {"name": "Ashwini", "number": 1, "end_time": "00:00:00", "lord": "Ketu"}

    def _get_yoga_details(self, jd: float, place) -> Dict[str, Any]:
        """Get detailed yoga information"""
        try:
            yoga_info = yoga(jd, place)

            # Handle different return formats
            if isinstance(yoga_info, (list, tuple)) and len(yoga_info) >= 2:
                yoga_num = int(yoga_info[0]) if isinstance(yoga_info[0], (int, float)) else 1
                yoga_end = yoga_info[1] if len(yoga_info) > 1 else [0, 0, 0]
            else:
                yoga_num = int(yoga_info) if isinstance(yoga_info, (int, float)) else 1
                yoga_end = [0, 0, 0]

            # Ensure yoga_num is in valid range
            if yoga_num < 1 or yoga_num > 27:
                yoga_num = 1

            # Format time safely
            if isinstance(yoga_end, (list, tuple)) and len(yoga_end) >= 3:
                end_time = f"{int(yoga_end[0]):02d}:{int(yoga_end[1]):02d}:{int(yoga_end[2]):02d}"
            else:
                end_time = "00:00:00"

            return {
                "name": self.YOGA_NAMES[yoga_num - 1],
                "number": yoga_num,
                "end_time": end_time
            }
        except Exception as e:
            print(f"Error calculating yoga: {e}")
            return {"name": "Vishkambha", "number": 1, "end_time": "00:00:00"}

    def _get_karana_details(self, jd: float, place) -> Dict[str, Any]:
        """Get detailed karana information"""
        try:
            karana_info = karana(jd, place)

            # Handle different return formats
            if isinstance(karana_info, (list, tuple)):
                karana_num = int(karana_info[0]) if len(karana_info) > 0 else 1
            else:
                karana_num = int(karana_info) if isinstance(karana_info, (int, float)) else 1

            # Adjust for karana names array
            if karana_num > len(self.KARANA_NAMES):
                karana_num = (karana_num - 1) % len(self.KARANA_NAMES) + 1

            # Ensure karana_num is in valid range
            if karana_num < 1:
                karana_num = 1

            return {
                "name": self.KARANA_NAMES[karana_num - 1],
                "number": karana_num
            }
        except Exception as e:
            print(f"Error calculating karana: {e}")
            return {"name": "Bava", "number": 1}

    def _get_vaara_details(self, jd: float) -> Dict[str, Any]:
        """Get detailed vaara (weekday) information"""
        try:
            vaara_num = vaara(jd)

            # Ensure vaara_num is in valid range (0-6)
            if not isinstance(vaara_num, int) or vaara_num < 0 or vaara_num > 6:
                vaara_num = 0

            # Vaara lords
            vaara_lords = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

            return {
                "name": self.VAARA_NAMES[vaara_num],
                "number": vaara_num,
                "lord": vaara_lords[vaara_num]
            }
        except Exception as e:
            print(f"Error calculating vaara: {e}")
            return {"name": "Sunday", "number": 0, "lord": "Sun"}

    def _get_masa_details(self, jd: float, place) -> Dict[str, Any]:
        """Get detailed masa information"""
        try:
            masa_info = masa(jd, place)

            # Handle different return formats
            if isinstance(masa_info, (list, tuple)) and len(masa_info) >= 2:
                masa_num = int(masa_info[0]) if isinstance(masa_info[0], (int, float)) else 1
                is_adhika = masa_info[1] if len(masa_info) > 1 else False
            else:
                masa_num = int(masa_info) if isinstance(masa_info, (int, float)) else 1
                is_adhika = False

            # Ensure masa_num is in valid range
            if masa_num < 1 or masa_num > 12:
                masa_num = 1

            return {
                "name": self.MASA_NAMES[masa_num - 1],
                "number": masa_num,
                "type": "Adhika" if is_adhika else "Nija"
            }
        except Exception as e:
            print(f"Error calculating masa: {e}")
            return {"name": "Chaitra", "number": 1, "type": "Nija"}

    def _get_ritu_details(self, masa_num: int) -> Dict[str, Any]:
        """Get ritu (season) details based on masa"""
        try:
            # Ensure masa_num is an integer
            if not isinstance(masa_num, int):
                masa_num = int(masa_num)

            ritu_num = ritu(masa_num)

            # Ensure ritu_num is in valid range
            if not isinstance(ritu_num, int) or ritu_num < 0 or ritu_num >= len(self.RITU_NAMES):
                ritu_num = 0

            return {
                "name": self.RITU_NAMES[ritu_num],
                "number": ritu_num
            }
        except Exception as e:
            print(f"Error calculating ritu: {e}")
            return {"name": "Vasanta", "number": 0}

    def _get_samvatsara_details(self, jd: float, masa_num: int) -> Dict[str, Any]:
        """Get samvatsara (year cycle) details"""
        try:
            # Ensure masa_num is an integer
            if not isinstance(masa_num, int):
                masa_num = int(masa_num)

            samvat_num = samvatsara(jd, masa_num)

            # Ensure samvat_num is valid
            if not isinstance(samvat_num, int):
                samvat_num = 0

            samvat_name = self.SAMVATSARA_NAMES[samvat_num % len(self.SAMVATSARA_NAMES)]

            return {
                "name": samvat_name,
                "number": samvat_num
            }
        except Exception as e:
            print(f"Error calculating samvatsara: {e}")
            return {"name": "Prabhava", "number": 0}
        
    def _get_sunrise_and_sunset(self, jd: float, place: Place, timezone_str: str) -> Dict[str, Dict[str, Any]]:
        """
        Calculates both sunrise and sunset accurately using the modern Skyfield almanac.
        """
        sunrise_result = {"time": "06:00:00", "local_time": jd}
        sunset_result = {"time": "18:00:00", "local_time": jd}

        try:
            # Convert Julian Day to a standard datetime object for the calculation day
            greg_tuple = swe.revjul(jd)
            year, month, day = greg_tuple[0], greg_tuple[1], greg_tuple[2]

            # Define the observer's location
            location = wgs84.latlon(place.latitude, place.longitude)
            
            # Define the time range for the specified day
            t0 = ts.utc(year, month, day, 0)
            t1 = ts.utc(year, month, day, 23, 59, 59)

            # Use the correct almanac function to find rise/set events
            f = almanac.sunrise_sunset(eph, location)
            times, events = almanac.find_discrete(t0, t1, f)
            
            user_timezone = pytz.timezone(timezone_str)

            for t, event_code in zip(times, events):
                # event_code == 1 means sunrise, 0 means sunset
                if event_code == 1 and sunrise_result["time"] == "06:00:00": # Found first sunrise
                    sunrise_dt_local = t.astimezone(user_timezone)
                    sunrise_result["time"] = sunrise_dt_local.strftime('%H:%M:%S')
                    sunrise_result["local_time"] = t.tdb
                    
                elif event_code == 0: # Found a sunset
                    sunset_dt_local = t.astimezone(user_timezone)
                    sunset_result["time"] = sunset_dt_local.strftime('%H:%M:%S')
                    sunset_result["local_time"] = t.tdb

            return {"sunrise": sunrise_result, "sunset": sunset_result}

        except Exception as e:
            print(f"ERROR calculating Skyfield rise/set: {e}")
            return {"sunrise": sunrise_result, "sunset": sunset_result}

    def _translate_tithi_info(self, tithi_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate tithi information"""
        translated = tithi_info.copy()
        translated['name'] = self._translate_panchanga_value('tithi', tithi_info['name'], lang)
        translated['paksha'] = self._translate_panchanga_value('paksha', tithi_info['paksha'], lang)
        return translated

    def _translate_nakshatra_info(self, nakshatra_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate nakshatra information"""
        translated = nakshatra_info.copy()
        tm = self._get_translation_manager()
        if tm:
            translated['name'] = tm.translate(f'nakshatras.{nakshatra_info["name"]}', lang, default=nakshatra_info['name'])
            translated['lord'] = tm.translate(f'planets.{nakshatra_info["lord"]}', lang, default=nakshatra_info['lord'])
        return translated

    def _translate_yoga_info(self, yoga_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate yoga information"""
        translated = yoga_info.copy()
        translated['name'] = self._translate_panchanga_value('yoga', yoga_info['name'], lang)
        return translated

    def _translate_karana_info(self, karana_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate karana information"""
        translated = karana_info.copy()
        translated['name'] = self._translate_panchanga_value('karana', karana_info['name'], lang)
        return translated

    def _translate_vaara_info(self, vaara_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate vaara (weekday) information"""
        translated = vaara_info.copy()
        translated['name'] = self._translate_panchanga_value('vaara', vaara_info['name'], lang)
        tm = self._get_translation_manager()
        if tm:
            translated['lord'] = tm.translate(f'planets.{vaara_info["lord"]}', lang, default=vaara_info['lord'])
        return translated

    def _translate_masa_info(self, masa_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate masa information"""
        translated = masa_info.copy()
        translated['name'] = self._translate_panchanga_value('masa', masa_info['name'], lang)
        translated['type'] = self._translate_panchanga_value('masa_type', masa_info['type'], lang)
        return translated

    def _translate_ritu_info(self, ritu_info: Dict[str, Any], lang: str) -> Dict[str, Any]:
        """Translate ritu information"""
        translated = ritu_info.copy()
        translated['name'] = self._translate_panchanga_value('ritu', ritu_info['name'], lang)
        return translated

    def _get_fallback_panchanga(self) -> Dict[str, Any]:
        """Fallback panchanga when calculation fails"""
        return {
            "tithi": {"name": "Pratipad", "number": 1, "end_time": "00:00:00", "paksha": "Shukla"},
            "nakshatra": {"name": "Ashwini", "number": 1, "end_time": "00:00:00", "lord": "Ketu"},
            "yoga": {"name": "Vishkambha", "number": 1, "end_time": "00:00:00"},
            "karana": {"name": "Bava", "number": 1},
            "vaara": {"name": "Sunday", "number": 0, "lord": "Sun"},
            "masa": {"name": "Chaitra", "number": 1, "type": "Nija"},
            "ritu": {"name": "Vasanta", "number": 0},
            "samvatsara": {"name": "Prabhava", "number": 0},
            "sunrise": {"time": "06:00:00", "local_time": 0},
            "sunset": {"time": "18:00:00", "local_time": 0},
            "day_duration": {"hours": 12, "ghatikas": 30}
        }
