"""
Krishnamurti Paddhati (KP) System Implementation
Clean implementation using Swiss Ephemeris for accurate calculations
"""

import swisseph as swe
import math
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from models import PlanetPosition


class KPSystem:
    """Krishnamurti Paddhati astrology system using Swiss Ephemeris"""

    # Zodiac signs
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    # KP Star Lords (Nakshatra Lords) - 27 nakshatras
    KP_STAR_LORDS = [
        'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',  # Aswini to Punarvasu
        'Saturn', 'Mercury', 'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',  # Pushya to Hasta
        'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus', 'Sun',  # Chitra to Purvashadha
        'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'  # Uttarashadha to Revati
    ]

    # Planet abbreviations for KP format
    PLANET_ABBREV = {
        'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
        'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra',
        'Ketu': 'Ke'
    }

    # Sign lord abbreviations for KP format
    SIGN_LORDS = {
        'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
        'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
        'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
    }

    def __init__(self):
        """Initialize KP System calculator"""
        pass

    def get_kp_house_cusps(self, jd: float, latitude: float, longitude: float) -> Dict[int, float]:
        """
        Calculate KP house cusps using Placidus system
        Returns house cusps in degrees (sidereal with KP Ayanamsa)
        """
        try:
            # Get KP Ayanamsa first
            # Convert JD to year for KP ayanamsa calculation
            utc_datetime = swe.jdut1_to_utc(jd)
            year = utc_datetime[0]
            kp_ayanamsa = self.calculate_kp_ayanamsa(year)

            # Get Placidus house cusps using SIDEREAL mode
            # Use SIDEREAL flag with KP ayanamsa
            cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'P')

            # Convert tropical cusps to sidereal using KP ayanamsa
            sidereal_cusps = {}
            for i in range(12):
                # Subtract ayanamsa to convert tropical to sidereal
                sidereal_degree = (cusps[i] - kp_ayanamsa) % 360
                sidereal_cusps[i + 1] = sidereal_degree

            return sidereal_cusps

        except Exception as e:
            print(f"Error calculating house cusps: {e}")
            import traceback
            traceback.print_exc()
            # Return empty dict if calculation fails
            return {}

    def get_kp_planet_house(self, planet_longitude: float, house_cusps: Dict[int, float]) -> int:
        """
        Determine which KP house a planet falls into using Placidus house cusps
        """
        # Normalize planet longitude to 0-360
        planet_longitude = planet_longitude % 360

        for house in range(1, 13):
            next_house = house + 1 if house < 12 else 1
            current_cusp = house_cusps[house]
            next_cusp = house_cusps[next_house]

            # Handle wraparound at 360/0 degrees
            if current_cusp <= next_cusp:
                if current_cusp <= planet_longitude < next_cusp:
                    return house
            else:  # Wraparound case
                if planet_longitude >= current_cusp or planet_longitude < next_cusp:
                    return house

        return 1  # Default fallback

    def get_nakshatra_info(self, longitude: float) -> Dict[str, Any]:
        """
        Get nakshatra information for a given longitude
        Returns nakshatra number, name, lord, and pada
        """
        # Each nakshatra is 13°20' (800 minutes)
        nakshatra_span = 13 + 20/60  # 13.333...

        nakshatra_number = int(longitude / nakshatra_span) + 1
        if nakshatra_number > 27:
            nakshatra_number = 27

        # Calculate position within nakshatra for pada
        position_in_nakshatra = longitude % nakshatra_span
        pada = int(position_in_nakshatra / (nakshatra_span / 4)) + 1

        # Get star lord
        star_lord = self.KP_STAR_LORDS[nakshatra_number - 1]

        return {
            'nakshatra_number': nakshatra_number,
            'star_lord': star_lord,
            'pada': pada,
            'longitude_in_nakshatra': position_in_nakshatra
        }

    def get_sub_lord(self, longitude: float) -> str:
        """
        Calculate the sub-lord for a given longitude using VedicAstro KP method
        """
        # VedicAstro KP sub-lord calculation algorithm
        duration = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

        # Normalize longitude and convert to KP sub-lord logic
        deg = longitude % 360
        deg = deg - 120 * int(deg / 120)
        degcum = 0
        i = 0

        while i < 9:
            deg_nl = 360 / 27  # Each nakshatra is 360/27 degrees
            j = i
            while True:
                deg_sl = deg_nl * duration[j] / 120
                k = j
                while True:
                    deg_ss = deg_sl * duration[k] / 120
                    degcum += deg_ss
                    if degcum >= deg:
                        return lords[j]  # Return sub-lord
                    k = (k + 1) % 9
                    if k == j:
                        break
                j = (j + 1) % 9
                if j == i:
                    break
            i += 1

        # Fallback to first lord
        return lords[0]

    def get_kp_significators(self, house_number: int, house_cusps: Dict[int, float],
                           planet_data: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Get KP significators for a house
        Returns strong, medium, and weak significators
        """
        significators = {'strong': [], 'medium': [], 'weak': []}

        # House cusp sub-lord is strongest significator
        cusp_longitude = house_cusps[house_number]
        cusp_sub_lord = self.get_sub_lord(cusp_longitude)
        significators['strong'].append(f"House {house_number} Cusp Sub-Lord: {cusp_sub_lord}")

        # Planets in the house are strong significators
        for planet_name, planet_info in planet_data.items():
            planet_house = self.get_kp_planet_house(planet_info['longitude'], house_cusps)
            if planet_house == house_number:
                significators['strong'].append(f"{planet_name} (in house)")

        # Star lords of planets in the house are medium significators
        for planet_name, planet_info in planet_data.items():
            planet_house = self.get_kp_planet_house(planet_info['longitude'], house_cusps)
            if planet_house == house_number:
                star_lord = planet_info['star_lord']
                if star_lord not in [s.split()[0] for s in significators['strong']]:
                    significators['medium'].append(f"{star_lord} (star lord of {planet_name})")

        # Sub-lords of planets in the house are weak significators
        for planet_name, planet_info in planet_data.items():
            planet_house = self.get_kp_planet_house(planet_info['longitude'], house_cusps)
            if planet_house == house_number:
                sub_lord = planet_info['sub_lord']
                if sub_lord not in [s.split()[0] for s in significators['strong'] + significators['medium']]:
                    significators['weak'].append(f"{sub_lord} (sub-lord of {planet_name})")

        return significators


    def get_sign_from_longitude(self, longitude: float) -> str:
        """Get zodiac sign from longitude"""
        sign_index = int(longitude // 30)
        return self.ZODIAC_SIGNS[sign_index]

    def get_day_lord(self, jd: float) -> str:
        """
        Calculate Day Lord based on the day of the week
        """
        # Get day of week (0 = Sunday, 1 = Monday, etc.)
        day_of_week = int(jd + 1.5) % 7  # Julian Day to day of week conversion

        day_lords = {
            0: 'Sun',      # Sunday
            1: 'Moon',     # Monday
            2: 'Mars',     # Tuesday
            3: 'Mercury',  # Wednesday
            4: 'Jupiter',  # Thursday
            5: 'Venus',    # Friday
            6: 'Saturn'    # Saturday
        }

        return day_lords.get(day_of_week, 'Sun')

    def calculate_ruling_planets(self, moon_longitude: float, ascendant_longitude: float, jd: float) -> Dict[str, Dict[str, str]]:
        """
        Calculate Ruling Planets: Moon (Mo), Ascendant (Asc), and Day Lord
        """
        ruling_planets = {}

        # Moon (Mo) ruling planets
        moon_sign = self.get_sign_from_longitude(moon_longitude)
        moon_sign_lord = self.SIGN_LORDS.get(moon_sign, '')
        moon_nakshatra_info = self.get_nakshatra_info(moon_longitude)
        moon_star_lord = self.PLANET_ABBREV.get(moon_nakshatra_info['star_lord'], '')
        moon_sub_lord = self.PLANET_ABBREV.get(self.get_sub_lord(moon_longitude), '')

        ruling_planets['Mo'] = {
            'sign_lord': moon_sign_lord,
            'star_lord': moon_star_lord,
            'sub_lord': moon_sub_lord
        }

        # Ascendant (Asc) ruling planets
        asc_sign = self.get_sign_from_longitude(ascendant_longitude)
        asc_sign_lord = self.SIGN_LORDS.get(asc_sign, '')
        asc_nakshatra_info = self.get_nakshatra_info(ascendant_longitude)
        asc_star_lord = self.PLANET_ABBREV.get(asc_nakshatra_info['star_lord'], '')
        asc_sub_lord = self.PLANET_ABBREV.get(self.get_sub_lord(ascendant_longitude), '')

        ruling_planets['Asc'] = {
            'sign_lord': asc_sign_lord,
            'star_lord': asc_star_lord,
            'sub_lord': asc_sub_lord
        }

        # Day Lord
        day_lord = self.get_day_lord(jd)
        day_lord_abbrev = self.PLANET_ABBREV.get(day_lord, day_lord)

        ruling_planets['Day Lord'] = {
            'planet': day_lord_abbrev
        }

        return ruling_planets

    def format_kp_tables(self, jd: float, latitude: float, longitude: float,
                        planets: Dict[str, Any], house_cusps: Dict[int, float]) -> Dict[str, Any]:
        """
        Format KP data in traditional tabular format (Vedic planets only)
        """
        # Planets table
        planets_table = []

        # Process main planets (traditional Vedic planets only)
        for planet_name, planet in planets.items():
            if hasattr(planet, '_abs_lon_sid'):
                longitude_val = planet._abs_lon_sid
                kp_house = self.get_kp_planet_house(longitude_val, house_cusps)
                sign = self.get_sign_from_longitude(longitude_val)
                sign_lord = self.SIGN_LORDS.get(sign, '')

                nakshatra_info = self.get_nakshatra_info(longitude_val)
                star_lord = self.PLANET_ABBREV.get(nakshatra_info['star_lord'], '')
                sub_lord = self.PLANET_ABBREV.get(self.get_sub_lord(longitude_val), '')

                planets_table.append({
                    'Planet': planet_name,
                    'Cusp': kp_house,
                    'Sign': sign,
                    'Sign_Lord': sign_lord,
                    'Star_Lord': star_lord,
                    'Sub_Lord': sub_lord
                })

        # Cusps table
        cusps_table = []
        for cusp_num in range(1, 13):
            cusp_longitude = house_cusps[cusp_num]
            sign = self.get_sign_from_longitude(cusp_longitude)
            sign_lord = self.SIGN_LORDS.get(sign, '')

            nakshatra_info = self.get_nakshatra_info(cusp_longitude)
            star_lord = self.PLANET_ABBREV.get(nakshatra_info['star_lord'], '')
            sub_lord = self.PLANET_ABBREV.get(self.get_sub_lord(cusp_longitude), '')

            cusps_table.append({
                'Cusp': cusp_num,
                'Degree': round(cusp_longitude, 2),
                'Sign': sign,
                'Sign_Lord': sign_lord,
                'Star_Lord': star_lord,
                'Sub_Lord': sub_lord
            })

        return {
            'planets': planets_table,
            'cusps': cusps_table
        }

    def generate_kp_chart_astrosage_format(self, year: int, month: int, day: int, hour: int, minute: int,
                                          latitude: float, longitude: float, timezone: str) -> Dict[str, Any]:
        """
        Generate complete KP chart using VedicAstro library
        """
        # Create VedicAstro horoscope with KP settings
        horoscope = VedicAstro.VedicHoroscopeData(
            year=year, month=month, day=day,
            hour=hour, minute=minute, second=0,
            latitude=latitude, longitude=longitude,
            tz=timezone,
            ayanamsa="Krishnamurti",  # Use KP Ayanamsa
            house_system="Placidus"   # Use Placidus houses for KP
        )

        # Generate chart
        chart = horoscope.generate_chart()

        # Get planets and houses data
        planets_data = horoscope.get_planets_data_from_chart(chart)
        houses_data = horoscope.get_houses_data_from_chart(chart)

        # Format planets table for KP output
        planets_table = []
        for planet in planets_data:
            planets_table.append({
                'Planet': planet.Object,
                'Cusp': planet.HouseNr,
                'Sign': planet.Rasi,
                'Sign_Lord': self.PLANET_ABBREV.get(planet.RasiLord, planet.RasiLord),
                'Star_Lord': self.PLANET_ABBREV.get(planet.NakshatraLord, planet.NakshatraLord),
                'Sub_Lord': self.PLANET_ABBREV.get(planet.SubLord, planet.SubLord)
            })

        # Format cusps table for KP output
        cusps_table = []
        for house in houses_data:
            cusps_table.append({
                'Cusp': house.HouseNr,
                'Degree': house.LonDecDeg,
                'Sign': house.Rasi,
                'Sign_Lord': self.PLANET_ABBREV.get(house.RasiLord, house.RasiLord),
                'Star_Lord': self.PLANET_ABBREV.get(house.NakshatraLord, house.NakshatraLord),
                'Sub_Lord': self.PLANET_ABBREV.get(house.SubLord, house.SubLord)
            })

        # Calculate ruling planets
        moon_data = next((p for p in planets_data if p.Object == 'Moon'), None)
        asc_data = next((h for h in houses_data if h.HouseNr == 1), None)

        ruling_planets = {}
        if moon_data and asc_data:
            # Day Lord calculation
            from datetime import datetime
            dt = datetime(year, month, day)
            day_of_week = dt.weekday()  # 0 = Monday
            day_lords = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
            day_lord = day_lords[day_of_week]

            ruling_planets = {
                'Mo': {
                    'sign_lord': self.PLANET_ABBREV.get(moon_data.RasiLord, moon_data.RasiLord),
                    'star_lord': self.PLANET_ABBREV.get(moon_data.NakshatraLord, moon_data.NakshatraLord),
                    'sub_lord': self.PLANET_ABBREV.get(moon_data.SubLord, moon_data.SubLord)
                },
                'Asc': {
                    'sign_lord': self.PLANET_ABBREV.get(asc_data.RasiLord, asc_data.RasiLord),
                    'star_lord': self.PLANET_ABBREV.get(asc_data.NakshatraLord, asc_data.NakshatraLord),
                    'sub_lord': self.PLANET_ABBREV.get(asc_data.SubLord, asc_data.SubLord)
                },
                'Day Lord': {
                    'planet': self.PLANET_ABBREV.get(day_lord, day_lord)
                }
            }

        # Get significators
        planet_significators = horoscope.get_planet_wise_significators(planets_data, houses_data)
        house_significators = horoscope.get_house_wise_significators(planets_data, houses_data)

        # Create KP chart layout
        kp_chart = {}
        for i in range(1, 13):
            kp_chart[str(i)] = []

        # Add Lagna to first house
        kp_chart['1'].append('Lagna')

        # Add planets to their houses
        for planet in planets_data:
            house_num = str(planet.HouseNr)
            if house_num in kp_chart:
                kp_chart[house_num].append(planet.Object)

        return {
            'planets_table': planets_table,
            'cusps_table': cusps_table,
            'ruling_planets': ruling_planets,
            'house_significators': house_significators,
            'kp_chart': kp_chart,
            'system': 'Krishnamurti Paddhati (KP) - VedicAstro'
        }

    def calculate_kp_ayanamsa(self, year: float) -> float:
        """
        Calculate KP Ayanamsa using the New KP Ayanamsa (NKPA) formula
        NKPA = 22° 22' 30" + (Year - 1900) × 50.2388475" + (Year - 1900)² × 0.000111/3600
        """
        base_ayanamsa = 22 + (22/60) + (30/3600)  # 22° 22' 30" in decimal degrees
        year_diff = year - 1900

        # Linear term: (Year - 1900) × 50.2388475"
        linear_term = year_diff * 50.2388475 / 3600  # Convert arcseconds to degrees

        # Quadratic term: (Year - 1900)² × 0.000111/3600
        quadratic_term = (year_diff ** 2) * 0.000111 / 3600

        kp_ayanamsa = base_ayanamsa + linear_term + quadratic_term
        return kp_ayanamsa

    def get_planet_positions_kp(self, jd: float) -> Dict[str, Dict[str, Any]]:
        """
        Get planet positions with KP calculations using Swiss Ephemeris
        """
        # Planet IDs in Swiss Ephemeris
        planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN, 'Rahu': swe.TRUE_NODE
        }

        # Calculate KP ayanamsa
        year = swe.jdut1_to_utc(jd)[0]
        kp_ayanamsa = self.calculate_kp_ayanamsa(year)

        planet_data = {}

        for planet_name, planet_id in planets.items():
            # Calculate planet position
            if planet_name == 'Rahu':
                # Rahu calculation
                result = swe.calc_ut(jd, planet_id)
                longitude = result[0][0]
            else:
                result = swe.calc_ut(jd, planet_id)
                longitude = result[0][0]

            # Convert to sidereal using KP ayanamsa
            sidereal_longitude = (longitude - kp_ayanamsa) % 360

            # Get sign and degree
            sign_index = int(sidereal_longitude // 30)
            degree_in_sign = sidereal_longitude % 30
            sign_name = self.ZODIAC_SIGNS[sign_index]

            # Get nakshatra info
            nakshatra_info = self.get_nakshatra_info(sidereal_longitude)

            # Get sub-lord
            sub_lord = self.get_sub_lord(sidereal_longitude)

            planet_data[planet_name] = {
                'longitude': sidereal_longitude,
                'sign': sign_name,
                'degree': degree_in_sign,
                'sign_lord': self.SIGN_LORDS.get(sign_name, ''),
                'star_lord': nakshatra_info['star_lord'],
                'sub_lord': sub_lord,
                'nakshatra_number': nakshatra_info['nakshatra_number'],
                'pada': nakshatra_info['pada']
            }

        # Add Ketu (opposite to Rahu)
        rahu_longitude = planet_data['Rahu']['longitude']
        ketu_longitude = (rahu_longitude + 180) % 360

        sign_index = int(ketu_longitude // 30)
        degree_in_sign = ketu_longitude % 30
        sign_name = self.ZODIAC_SIGNS[sign_index]
        nakshatra_info = self.get_nakshatra_info(ketu_longitude)
        sub_lord = self.get_sub_lord(ketu_longitude)

        planet_data['Ketu'] = {
            'longitude': ketu_longitude,
            'sign': sign_name,
            'degree': degree_in_sign,
            'sign_lord': self.SIGN_LORDS.get(sign_name, ''),
            'star_lord': nakshatra_info['star_lord'],
            'sub_lord': sub_lord,
            'nakshatra_number': nakshatra_info['nakshatra_number'],
            'pada': nakshatra_info['pada']
        }

        return planet_data

    def generate_kp_astrosage_format(self, year: int, month: int, day: int, hour: int, minute: int,
                                   latitude: float, longitude: float, timezone: str) -> Dict[str, Any]:
        """
        Generate KP chart in AstroSage format using Swiss Ephemeris

        IMPORTANT: year, month, day, hour, minute should be in LOCAL TIME
        This method will convert to UTC before calculations
        """
        import pytz

        # Create local datetime with timezone
        local_dt = datetime(year, month, day, hour, minute)
        tz = pytz.timezone(timezone)
        localized_dt = tz.localize(local_dt)

        # Convert to UTC
        utc_dt = localized_dt.astimezone(pytz.UTC)

        # Now extract UTC components for Swiss Ephemeris
        utc_year = utc_dt.year
        utc_month = utc_dt.month
        utc_day = utc_dt.day
        utc_hour = utc_dt.hour
        utc_minute = utc_dt.minute

        # Convert to Julian Day (using UTC time!)
        jd = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0)

        # Get house cusps using our existing method
        house_cusps = self.get_kp_house_cusps(jd, latitude, longitude)

        # Get planet positions
        planet_data = self.get_planet_positions_kp(jd)

        # Calculate which house each planet is in using Placidus cusps
        planet_house_assignments = {}
        for planet_name, planet_info in planet_data.items():
            planet_house = self.get_kp_planet_house(planet_info['longitude'], house_cusps)
            planet_house_assignments[planet_name] = planet_house

        # Format planets table with calculated house assignments
        planets_table = []
        for planet_name, planet_info in planet_data.items():
            planet_house = planet_house_assignments.get(planet_name, 1)

            planets_table.append({
                'Planet': planet_name,
                'Cusp': planet_house,
                'Sign': planet_info['sign'],
                'Sign_Lord': self.PLANET_ABBREV.get(planet_info['sign_lord'], planet_info['sign_lord']),
                'Star_Lord': self.PLANET_ABBREV.get(planet_info['star_lord'], planet_info['star_lord']),
                'Sub_Lord': self.PLANET_ABBREV.get(planet_info['sub_lord'], planet_info['sub_lord'])
            })

        # Format cusps table
        cusps_table = []
        for cusp_num in range(1, 13):
            cusp_longitude = house_cusps[cusp_num]
            sign = self.get_sign_from_longitude(cusp_longitude)
            sign_lord = self.SIGN_LORDS.get(sign, '')

            nakshatra_info = self.get_nakshatra_info(cusp_longitude)
            star_lord = nakshatra_info['star_lord']
            sub_lord = self.get_sub_lord(cusp_longitude)

            cusps_table.append({
                'Cusp': cusp_num,
                'Degree': round(cusp_longitude, 2),
                'Sign': sign,
                'Sign_Lord': self.PLANET_ABBREV.get(sign_lord, sign_lord),
                'Star_Lord': self.PLANET_ABBREV.get(star_lord, star_lord),
                'Sub_Lord': self.PLANET_ABBREV.get(sub_lord, sub_lord)
            })

        # Calculate ruling planets
        moon_data = planet_data.get('Moon')
        ascendant_longitude = house_cusps[1]

        ruling_planets = {}
        if moon_data:
            # Day Lord calculation
            dt = datetime(year, month, day)
            day_of_week = dt.weekday()
            day_lords = ['Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Sun']
            day_lord = day_lords[day_of_week]

            # Get Ascendant info from cusps table (already calculated correctly above)
            # Find the Ascendant cusp data from cusps_table
            asc_cusp_data = next((c for c in cusps_table if c['Cusp'] == 1), None)
            if asc_cusp_data:
                # Values from cusps_table are already abbreviated
                asc_sign_lord = asc_cusp_data['Sign_Lord']
                asc_star_lord = asc_cusp_data['Star_Lord']
                asc_sub_lord = asc_cusp_data['Sub_Lord']
            else:
                # Fallback: calculate directly
                asc_sign = self.get_sign_from_longitude(ascendant_longitude)
                asc_sign_lord = self.SIGN_LORDS.get(asc_sign, '')
                asc_nakshatra_info = self.get_nakshatra_info(ascendant_longitude)
                asc_star_lord = asc_nakshatra_info['star_lord']
                asc_sub_lord = self.get_sub_lord(ascendant_longitude)
                # Abbreviate the fallback values
                asc_sign_lord = self.PLANET_ABBREV.get(asc_sign_lord, asc_sign_lord)
                asc_star_lord = self.PLANET_ABBREV.get(asc_star_lord, asc_star_lord)
                asc_sub_lord = self.PLANET_ABBREV.get(asc_sub_lord, asc_sub_lord)

            ruling_planets = {
                'Mo': {
                    'sign_lord': self.PLANET_ABBREV.get(moon_data['sign_lord'], moon_data['sign_lord']),
                    'star_lord': self.PLANET_ABBREV.get(moon_data['star_lord'], moon_data['star_lord']),
                    'sub_lord': self.PLANET_ABBREV.get(moon_data['sub_lord'], moon_data['sub_lord'])
                },
                'Asc': {
                    'sign_lord': asc_sign_lord,
                    'star_lord': asc_star_lord,
                    'sub_lord': asc_sub_lord
                },
                'Day Lord': {
                    'planet': self.PLANET_ABBREV.get(day_lord, day_lord)
                }
            }

        # Create KP chart layout using calculated house assignments
        kp_chart = {}
        for i in range(1, 13):
            kp_chart[str(i)] = []

        # Add Lagna to first house
        kp_chart['1'].append('Lagna')

        # Add planets using calculated house assignments
        for planet_name in planet_data.keys():
            planet_house = planet_house_assignments.get(planet_name, 1)
            house_key = str(planet_house)
            if house_key in kp_chart:
                kp_chart[house_key].append(planet_name)

        # Calculate significators (simplified version)
        house_significators = {}
        for house in range(1, 13):
            house_significators[house] = self.get_kp_significators(house, house_cusps, planet_data)

        return {
            'planets_table': planets_table,
            'cusps_table': cusps_table,
            'ruling_planets': ruling_planets,
            'house_significators': house_significators,
            'kp_chart': kp_chart,
            'chart_layout': planet_house_assignments,
            'system': 'Krishnamurti Paddhati (KP) - Clean Swiss Ephemeris'
        }


class BhavaChalitSystem:
    """Bhava Chalit (Equal House from Ascendant) system calculations"""

    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    def __init__(self):
        """Initialize Bhava Chalit system calculator"""
        import swisseph as swe
        self.swe = swe

    def calculate_planetary_positions_swisseph(self, jd: float, latitude: float, longitude: float) -> Dict[str, Dict[str, Any]]:
        """
        Calculate planetary positions using Swiss Ephemeris with Lahiri Ayanamsa

        This is used ONLY for Bhava Chalit and KP system to ensure accuracy.
        Other charts (Rasi, Navamsa, etc.) continue using their existing methods.

        Args:
            jd: Julian Day in UTC
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Dictionary with planet data including sidereal longitudes
        """
        # Get Lahiri Ayanamsa
        ayanamsa = self.swe.get_ayanamsa_ut(jd)
        if isinstance(ayanamsa, tuple):
            ayanamsa = ayanamsa[0]

        # Planet IDs in Swiss Ephemeris
        planets = {
            'Sun': self.swe.SUN,
            'Moon': self.swe.MOON,
            'Mercury': self.swe.MERCURY,
            'Venus': self.swe.VENUS,
            'Mars': self.swe.MARS,
            'Jupiter': self.swe.JUPITER,
            'Saturn': self.swe.SATURN,
            'Rahu': self.swe.TRUE_NODE,
        }

        planet_data = {}

        for planet_name, planet_id in planets.items():
            try:
                # Calculate tropical position
                result = self.swe.calc_ut(jd, planet_id)
                tropical_longitude = result[0][0]

                # Convert to sidereal using Lahiri Ayanamsa
                sidereal_longitude = (tropical_longitude - ayanamsa) % 360

                # Get sign and degree
                sign_index = int(sidereal_longitude // 30)
                sign_name = self.ZODIAC_SIGNS[sign_index]
                degree_in_sign = sidereal_longitude % 30

                planet_data[planet_name] = {
                    'longitude': sidereal_longitude,
                    'sign': sign_name,
                    'degree': degree_in_sign,
                }
            except Exception as e:
                print(f"Error calculating {planet_name}: {e}")
                continue

        # Calculate Ketu (opposite to Rahu)
        if 'Rahu' in planet_data:
            rahu_longitude = planet_data['Rahu']['longitude']
            ketu_longitude = (rahu_longitude + 180) % 360

            sign_index = int(ketu_longitude // 30)
            sign_name = self.ZODIAC_SIGNS[sign_index]
            degree_in_sign = ketu_longitude % 30

            planet_data['Ketu'] = {
                'longitude': ketu_longitude,
                'sign': sign_name,
                'degree': degree_in_sign,
            }

        return planet_data

    def calculate_ascendant_swisseph(self, jd: float, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Calculate Ascendant using Swiss Ephemeris with Lahiri Ayanamsa

        Args:
            jd: Julian Day in UTC
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Dictionary with ascendant data
        """
        # Calculate houses to get ASC (Ascendant) - this is the correct method!
        # swe.houses returns (cusps, ascmc) where ascmc[0] is the Ascendant
        houses, ascmc = self.swe.houses(jd, latitude, longitude, b'P')
        tropical_ascendant = ascmc[0]

        # Get Lahiri Ayanamsa
        ayanamsa = self.swe.get_ayanamsa_ut(jd)
        if isinstance(ayanamsa, tuple):
            ayanamsa = ayanamsa[0]

        # Convert to sidereal
        sidereal_ascendant = (tropical_ascendant - ayanamsa) % 360

        # Get sign and degree
        sign_index = int(sidereal_ascendant // 30)
        sign_name = self.ZODIAC_SIGNS[sign_index]
        degree_in_sign = sidereal_ascendant % 30

        return {
            'longitude': sidereal_ascendant,
            'sign': sign_name,
            'degree': degree_in_sign,
        }

    def calculate_vedic_bhava_chalit_cusps(self, lagna_longitude: float) -> Dict[int, Dict[str, Any]]:
        """
        Calculate Vedic Bhava Chalit house cusps (Equal 30° houses with Lagna at CENTER)

        This matches AstroTalk & AstroSage implementation:
        - Lagna degree is the CENTER of House 1
        - House 1 spans from (Lagna - 15°) to (Lagna + 15°)
        - Each house is exactly 30°
        - No latitude distortion, no Placidus math

        Args:
            lagna_longitude: Ascendant/Lagna degree in sidereal (0-360)

        Returns:
            Dictionary with house number (1-12) as key, containing:
            - start: Starting longitude of house
            - center: Center longitude of house
            - end: Ending longitude of house
            - sign: Zodiac sign containing the center
            - degree: Degree within that sign
        """
        bhava_cusps = {}

        # Lagna is center of House 1, so House 1 starts at (Lagna - 15°)
        house_1_start = (lagna_longitude - 15) % 360

        for house in range(1, 13):
            # Each house spans exactly 30 degrees
            start = (house_1_start + (house - 1) * 30) % 360
            center = (start + 15) % 360
            end = (start + 30) % 360

            # Determine sign and degree for center point
            sign_index = int(center // 30)
            degree_in_sign = center % 30
            sign_name = self.ZODIAC_SIGNS[sign_index]

            bhava_cusps[house] = {
                'start': start,
                'center': center,
                'end': end,
                'longitude': center,  # For backward compatibility
                'sign': sign_name,
                'degree': degree_in_sign
            }

        return bhava_cusps

    def get_vedic_bhava_house(self, planet_longitude: float, bhava_cusps: Dict[int, Dict[str, Any]]) -> int:
        """
        Determine which Vedic Bhava house a planet falls into (Equal House System)

        This matches the AstroTalk & AstroSage method using direct mathematical formula.
        No loops, no comparisons - pure math that handles all edge cases correctly.

        Formula:
        1. Normalize angles to 0-360°
        2. Calculate offset from Lagna center (with Lagna at 0°)
        3. Add 15° to shift reference to house boundary
        4. Divide by 30° to get house index
        5. Add 1 for 1-based numbering

        Args:
            planet_longitude: Planet's longitude in sidereal (0-360)
            bhava_cusps: House cusps from calculate_vedic_bhava_chalit_cusps()

        Returns:
            House number (1-12)
        """
        # Get Lagna longitude (center of House 1)
        lagna_longitude = bhava_cusps[1]['center']

        # Normalize both longitudes to 0-360
        planet_norm = planet_longitude % 360
        lagna_norm = lagna_longitude % 360

        # Calculate angular offset from Lagna (handles wraparound automatically)
        # This gives us the angle with Lagna at 0°
        offset = (planet_norm - lagna_norm + 360) % 360

        # Shift by +15° because Lagna is at CENTER of House 1, not the start
        # House 1 spans from -15° to +15° relative to Lagna
        # So we add 15° to shift the reference point
        offset_from_start = (offset + 15) % 360

        # Each house is exactly 30°, so divide by 30 to get house index
        # Use floor() to get the house number (0-11)
        house_index_zero_based = int(offset_from_start // 30)

        # Convert to 1-based numbering (1-12)
        house_number = house_index_zero_based + 1

        return house_number

    def generate_vedic_bhava_chalit_chart_from_scratch(self, year: int, month: int, day: int,
                                                       hour: int, minute: int,
                                                       latitude: float, longitude: float,
                                                       timezone: str) -> Dict[str, Any]:
        """
        Generate Vedic Bhava Chalit chart using Swiss Ephemeris with Lahiri Ayanamsa

        This method:
        - Calculates planetary positions using Swiss Ephemeris (NOT Kerykeion)
        - Uses Lahiri Ayanamsa for sidereal conversion
        - Generates equal 30° houses with Lagna at center
        - Matches AstroTalk & AstroSage exactly

        IMPORTANT: This ONLY affects Bhava Chalit/KP calculations.
        Other charts (Rasi, Navamsa, etc.) are unaffected.

        Args:
            year: Year in local time
            month: Month in local time
            day: Day in local time
            hour: Hour in local time
            minute: Minute in local time
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            timezone: Timezone string (e.g., 'Asia/Kolkata')

        Returns:
            Complete Bhava Chalit chart data
        """
        import pytz
        from datetime import datetime

        # Convert local time to UTC
        local_dt = datetime(year, month, day, hour, minute)
        tz = pytz.timezone(timezone)
        localized_dt = tz.localize(local_dt)
        utc_dt = localized_dt.astimezone(pytz.UTC)

        # Extract UTC components
        utc_year = utc_dt.year
        utc_month = utc_dt.month
        utc_day = utc_dt.day
        utc_hour = utc_dt.hour
        utc_minute = utc_dt.minute

        # Calculate Julian Day (UTC)
        jd = self.swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0)

        # Calculate Ascendant using Swiss Ephemeris + Lahiri Ayanamsa
        ascendant_data = self.calculate_ascendant_swisseph(jd, latitude, longitude)
        lagna_longitude = ascendant_data['longitude']

        # Calculate planetary positions using Swiss Ephemeris + Lahiri Ayanamsa
        planet_data_swisseph = self.calculate_planetary_positions_swisseph(jd, latitude, longitude)

        # Calculate Vedic Bhava Chalit cusps (Lagna at center)
        bhava_cusps = self.calculate_vedic_bhava_chalit_cusps(lagna_longitude)

        # Create chart structure
        bhava_chart = {}
        planet_details = {}

        # Initialize all houses with empty lists
        for i in range(1, 13):
            bhava_chart[str(i)] = []

        # Add Lagna to House 1
        bhava_chart['1'].append('Lagna')

        # Assign planets to houses
        for planet_name, planet_info in planet_data_swisseph.items():
            planet_longitude = planet_info['longitude']

            # Get Bhava house using direct formula
            bhava_house = self.get_vedic_bhava_house(planet_longitude, bhava_cusps)

            # Calculate degree from house start
            house_start = bhava_cusps[bhava_house]['start']
            degree_from_start = (planet_longitude - house_start) % 360

            planet_details[planet_name] = {
                'longitude': round(planet_longitude, 6),
                'bhava_house': bhava_house,
                'degree_from_house_start': round(degree_from_start, 2),
                'sign': planet_info['sign'],
                'degree': planet_info['degree']
            }

            # Add planet to chart
            house_key = str(bhava_house)
            if house_key in bhava_chart:
                bhava_chart[house_key].append(planet_name)

        return {
            'bhava_chart': bhava_chart,
            'planet_details': planet_details,
            'bhava_cusps': bhava_cusps,
            'lagna_longitude': round(lagna_longitude, 6),
            'house_system': 'Vedic Equal House (Lagna at Center) - Swiss Ephemeris + Lahiri',
            'ayanamsa_used': 'Lahiri Ayanamsa (Swiss Ephemeris)',
            'calculation_method': 'Swiss Ephemeris (NOT Kerykeion)'
        }

    def calculate_bhava_cusps(self, ascendant_longitude: float) -> Dict[int, Dict[str, Any]]:
        """
        Calculate Bhava Chalit house cusps (30° equal divisions from ascendant)

        DEPRECATED: This method treats ascendant as START of House 1, not center.
        Use calculate_vedic_bhava_chalit_cusps() for AstroTalk/AstroSage compatibility.
        """
        bhava_cusps = {}

        for house in range(1, 13):
            # Each house is exactly 30 degrees
            cusp_longitude = (ascendant_longitude + (house - 1) * 30) % 360

            # Determine sign and degree within sign
            sign_index = int(cusp_longitude // 30)
            degree_in_sign = cusp_longitude % 30
            sign_name = self.ZODIAC_SIGNS[sign_index]

            bhava_cusps[house] = {
                'longitude': cusp_longitude,
                'sign': sign_name,
                'degree': degree_in_sign
            }

        return bhava_cusps

    def calculate_kp_ayanamsa(self, year: float) -> float:
        """
        Calculate KP Ayanamsa using the New KP Ayanamsa (NKPA) formula
        NKPA = 22° 22' 30" + (Year - 1900) × 50.2388475" + (Year - 1900)² × 0.000111/3600
        """
        base_ayanamsa = 22 + (22/60) + (30/3600)  # 22° 22' 30" in decimal degrees
        year_diff = year - 1900

        # Linear term: (Year - 1900) × 50.2388475"
        linear_term = year_diff * 50.2388475 / 3600  # Convert arcseconds to degrees

        # Quadratic term: (Year - 1900)² × 0.000111/3600
        quadratic_term = (year_diff ** 2) * 0.000111 / 3600

        kp_ayanamsa = base_ayanamsa + linear_term + quadratic_term
        return kp_ayanamsa

    def calculate_placidus_cusps(self, jd: float, latitude: float, longitude: float) -> Dict[int, float]:
        """
        Calculate Placidus house cusps using Swiss Ephemeris with KP Ayanamsa
        """
        try:
            import pyswisseph as swe

            # Calculate KP Ayanamsa for the given time
            dt_utc = datetime.utcfromtimestamp((jd - 2440587.5) * 86400.0)
            kp_ayanamsa = self.calculate_kp_ayanamsa(dt_utc.year + (dt_utc.month - 1)/12)

            # Calculate Placidus house cusps using Swiss Ephemeris
            # swe.houses() returns (cusps, ascmc) where cusps[1-12] are the house cusps
            cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')  # 'P' for Placidus

            placidus_cusps = {}
            for i in range(1, 13):
                # cusps[i] contains the tropical longitude of house i
                tropical_cusp = cusps[i]

                # Convert to sidereal using KP Ayanamsa
                sidereal_cusp = (tropical_cusp - kp_ayanamsa) % 360
                placidus_cusps[i] = sidereal_cusp

            return placidus_cusps

        except Exception as e:
            print(f"Error calculating Placidus cusps with Swiss Ephemeris: {e}")
            # Fallback to equal house system with KP ayanamsa
            asc_data = swe.calc_ut(jd, swe.ASC, swe.FLG_SIDEREAL)
            ascendant_longitude = asc_data[0]

            # Apply KP ayanamsa correction
            dt_utc = datetime.utcfromtimestamp((jd - 2440587.5) * 86400.0)
            kp_ayanamsa = self.calculate_kp_ayanamsa(dt_utc.year + (dt_utc.month - 1)/12)
            lahiri_ayanamsa = swe.get_ayanamsa(jd)
            ayanamsa_correction = kp_ayanamsa - lahiri_ayanamsa
            corrected_ascendant = (ascendant_longitude + ayanamsa_correction) % 360

            fallback_cusps = {}
            for house in range(1, 13):
                fallback_cusps[house] = (corrected_ascendant + (house - 1) * 30) % 360
            return fallback_cusps

    def get_kp_house(self, planet_longitude: float, house_cusps) -> int:
        """
        Determine which KP house a planet falls into using house cusps
        """
        # Normalize planet longitude to 0-360
        planet_longitude = planet_longitude % 360

        for house in range(1, 13):
            # Handle both dict and float types for cusps
            if isinstance(house_cusps[house], dict):
                current_cusp = house_cusps[house]['longitude']
                next_house = (house % 12) + 1
                next_cusp = house_cusps[next_house]['longitude']
            else:
                current_cusp = house_cusps[house]
                next_house = (house % 12) + 1
                next_cusp = house_cusps[next_house]

            # Handle the wrap-around case (e.g., house 12 to house 1)
            if next_cusp < current_cusp:
                if planet_longitude >= current_cusp or planet_longitude < next_cusp:
                    return house
            else:
                if current_cusp <= planet_longitude < next_cusp:
                    return house

        return 1  # Fallback to house 1

    def generate_vedic_bhava_chalit_chart(self, lagna_longitude: float,
                                         planets: Dict[str, PlanetPosition]) -> Dict[str, Any]:
        """
        Generate Vedic Bhava Chalit chart (Equal House System - Lagna at CENTER)

        This matches AstroTalk & AstroSage implementation:
        - Lagna is the CENTER of House 1 (not the start)
        - House 1 spans (Lagna - 15°) to (Lagna + 15°)
        - Each house is exactly 30° (no latitude distortion)
        - Planets assigned based on equal 30° intervals using direct math formula

        Args:
            lagna_longitude: Ascendant/Lagna degree in sidereal (0-360)
            planets: Dictionary of planet objects with _abs_lon_sid attribute

        Returns:
            Dictionary containing:
            - bhava_chart: House numbers with planet lists
            - planet_details: Detailed info for each planet
            - bhava_cusps: House boundaries (start, center, end)
            - house_system: Description of system used
        """
        # Calculate Vedic Bhava Chalit cusps (Lagna at center of House 1)
        bhava_cusps = self.calculate_vedic_bhava_chalit_cusps(lagna_longitude)

        # Create chart structure
        bhava_chart = {}
        planet_details = {}

        # Initialize all houses with empty lists
        for i in range(1, 13):
            bhava_chart[str(i)] = []

        # Add Lagna to House 1
        bhava_chart['1'].append('Lagna')

        # Assign planets to houses based on Vedic Bhava system
        for planet_name, planet in planets.items():
            if hasattr(planet, '_abs_lon_sid'):
                planet_longitude = planet._abs_lon_sid

                # Get Bhava house using direct math formula (not loop-based comparison)
                bhava_house = self.get_vedic_bhava_house(planet_longitude, bhava_cusps)

                # Calculate degree from house start
                house_start = bhava_cusps[bhava_house]['start']
                degree_from_start = (planet_longitude - house_start) % 360

                planet_details[planet_name] = {
                    'longitude': round(planet_longitude, 6),
                    'bhava_house': bhava_house,
                    'degree_from_house_start': round(degree_from_start, 2),
                    'sign': planet.sign,
                    'degree': planet.degree
                }

                # Add planet to chart
                house_key = str(bhava_house)
                if house_key in bhava_chart:
                    bhava_chart[house_key].append(planet_name)

        return {
            'bhava_chart': bhava_chart,
            'planet_details': planet_details,
            'bhava_cusps': bhava_cusps,
            'lagna_longitude': round(lagna_longitude, 6),
            'house_system': 'Vedic Equal House (Lagna at Center) - Matches AstroTalk/AstroSage',
            'ayanamsa_used': 'Lahiri Ayanamsa'
        }

    def generate_kp_bhava_chalit_chart(self, jd: float, latitude: float, longitude: float,
                                     planets: Dict[str, PlanetPosition]) -> Dict[str, Any]:
        """
        Generate KP Bhava Chalit chart using Placidus House System

        NOTE: This uses KP Placidus (unequal houses) which differs from
        the Vedic Bhava Chalit system used by AstroTalk/AstroSage.

        For AstroTalk/AstroSage compatibility, use generate_vedic_bhava_chalit_chart() instead.
        """
        # Calculate KP house cusps (Placidus) using KPSystem method
        kp_system = KPSystem()
        house_cusps = kp_system.get_kp_house_cusps(jd, latitude, longitude)
        ascendant_longitude = house_cusps[1]

        # Use Placidus house cusps for Bhava Chalit (not equal houses!)
        bhava_chart = {'1': ['Lagna']}  # Ascendant always in first house
        planet_details = {}

        for planet_name, planet in planets.items():
            if hasattr(planet, '_abs_lon_sid'):
                planet_longitude = planet._abs_lon_sid

                # Calculate Bhava house using Placidus cusps (same as KP system)
                bhava_house = kp_system.get_kp_planet_house(planet_longitude, house_cusps)

                # Calculate degree from house cusp
                house_cusp_longitude = house_cusps[bhava_house]
                degree_from_cusp = (planet_longitude - house_cusp_longitude) % 360

                planet_details[planet_name] = {
                    'longitude': planet_longitude,
                    'bhava_house': bhava_house,
                    'degree_from_cusp': round(degree_from_cusp, 2),
                    'sign': planet.sign,
                    'degree': planet.degree
                }

                # Add to chart
                house_key = str(bhava_house)
                if house_key not in bhava_chart:
                    bhava_chart[house_key] = []
                bhava_chart[house_key].append(planet_name)

        # Fill empty houses
        for i in range(1, 13):
            if str(i) not in bhava_chart:
                bhava_chart[str(i)] = []

        return {
            'bhava_chart': bhava_chart,
            'planet_details': planet_details,
            'house_cusps': {str(k): round(v, 2) for k, v in house_cusps.items()},
            'ayanamsa_used': 'KP Ayanamsa',
            'house_system': 'Placidus (KP) - Differs from AstroTalk/AstroSage'
        }

    def generate_bhava_chalit_chart(self, ascendant_longitude: float,
                                  planets: Dict[str, PlanetPosition]) -> Dict[str, Any]:
        """
        Generate complete Bhava Chalit chart
        """
        # This method needs JD, lat, lng for proper Placidus calculation
        # For now, use equal house as fallback - should be called with JD, lat, lng
        bhava_cusps = self.calculate_bhava_cusps(ascendant_longitude)

        # Create chart
        bhava_chart = {}
        planet_details = {}

        # Add ascendant to first house
        bhava_chart['1'] = ['Lagna']

        for planet_name, planet in planets.items():
            if hasattr(planet, '_abs_lon_sid'):
                planet_longitude = planet._abs_lon_sid

                # Get Bhava house using equal house system (fallback)
                bhava_house = self.get_kp_house(planet_longitude, bhava_cusps)

                # Calculate degree from house cusp
                house_cusp_longitude = bhava_cusps[bhava_house]['longitude']
                degree_from_cusp = (planet_longitude - house_cusp_longitude) % 360

                planet_details[planet_name] = {
                    'longitude': planet_longitude,
                    'bhava_house': bhava_house,
                    'degree_from_cusp': degree_from_cusp,
                    'sign': planet.sign,
                    'degree': planet.degree
                }

                # Add to chart
                if str(bhava_house) not in bhava_chart:
                    bhava_chart[str(bhava_house)] = []
                bhava_chart[str(bhava_house)].append(planet_name)

        # Fill empty houses
        for i in range(1, 13):
            if str(i) not in bhava_chart:
                bhava_chart[str(i)] = []
            elif i == 1 and 'Lagna' not in bhava_chart[str(i)]:
                bhava_chart[str(i)].insert(0, 'Lagna')

        return {
            'bhava_cusps': bhava_cusps,
            'bhava_chart': bhava_chart,
            'planet_details': planet_details,
            'ascendant_longitude': ascendant_longitude,
            'system': 'Bhava Chalit (Equal Houses from Ascendant)'
        }

    def get_house_strength(self, house_number: int, bhava_chart: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Calculate strength of a house in Bhava Chalit system
        """
        house_planets = bhava_chart.get(str(house_number), [])

        # Remove Lagna from count if present
        planets_only = [p for p in house_planets if p != 'Lagna']

        strength_factors = {
            'planet_count': len(planets_only),
            'has_benefics': False,
            'has_malefics': False,
            'planets': planets_only
        }

        # Basic benefic/malefic classification
        benefics = ['Venus', 'Jupiter', 'Mercury', 'Moon']
        malefics = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu']

        for planet in planets_only:
            if planet in benefics:
                strength_factors['has_benefics'] = True
            elif planet in malefics:
                strength_factors['has_malefics'] = True

        return strength_factors




def calculate_kp_and_bhava_chalit(year: int, month: int, day: int, hour: int, minute: int,
                                latitude: float, longitude: float, timezone: str) -> Dict[str, Any]:
    """
    Main function to calculate both KP and Bhava Chalit systems

    KP System: Uses Placidus houses with sub-lords
    Bhava Chalit: Uses Vedic Equal House system (Lagna at center) - matches AstroTalk/AstroSage
    """
    import pytz

    kp_system = KPSystem()
    bhava_system = BhavaChalitSystem()

    # Generate KP chart using Swiss Ephemeris with AstroSage format
    kp_results = kp_system.generate_kp_astrosage_format(year, month, day, hour, minute, latitude, longitude, timezone)

    # Generate Bhava Chalit chart using Vedic Equal House system
    # First, convert local time to UTC
    local_dt = datetime(year, month, day, hour, minute)
    tz = pytz.timezone(timezone)
    localized_dt = tz.localize(local_dt)
    utc_dt = localized_dt.astimezone(pytz.UTC)

    # Use UTC time for Julian Day calculation
    utc_year = utc_dt.year
    utc_month = utc_dt.month
    utc_day = utc_dt.day
    utc_hour = utc_dt.hour
    utc_minute = utc_dt.minute

    # Get ascendant (Lagna) from KP house cusps using UTC time
    jd = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0)
    house_cusps = kp_system.get_kp_house_cusps(jd, latitude, longitude)
    lagna_longitude = house_cusps[1]

    # Get planet positions for Bhava Chalit
    planet_data = kp_system.get_planet_positions_kp(jd)

    # Create dummy planets dict for compatibility with existing BhavaChalitSystem
    planets = {}
    for planet_name, planet_info in planet_data.items():
        # Create a simple object that mimics PlanetPosition
        class SimplePlanet:
            def __init__(self, lon, sign, degree):
                self._abs_lon_sid = lon
                self.sign = sign
                self.degree = degree

        planets[planet_name] = SimplePlanet(
            planet_info['longitude'],
            planet_info['sign'],
            planet_info['degree']
        )

    # Generate Vedic Bhava Chalit chart (Equal House - Lagna at center)
    # This matches AstroTalk & AstroSage implementation
    bhava_results = bhava_system.generate_vedic_bhava_chalit_chart(lagna_longitude, planets)

    # House strength analysis for Bhava Chalit
    house_strengths = {}
    for house in range(1, 13):
        house_strengths[house] = bhava_system.get_house_strength(house, bhava_results['bhava_chart'])

    return {
        'kp_system': kp_results,
        'bhava_chalit': bhava_results,
        'bhava_house_strengths': house_strengths,
        'comparison': {
            'kp_uses': 'Placidus house cusps with sub-lord system (Swiss Ephemeris + KP Ayanamsa)',
            'bhava_chalit_uses': 'Vedic Equal 30° houses with Lagna at center (matches AstroTalk/AstroSage)',
            'main_difference': 'KP uses unequal Placidus houses with sub-lords; Bhava Chalit uses equal 30° houses (Lagna-centered)'
        }
    }