"""
Vimshottari Dasha System Implementation
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple


class VimshottariDasha:
    """
    Vimshottari Dasha calculator based on Moon's nakshatra at birth
    """

    # Vimshottari Dasha periods in years
    DASHA_PERIODS = {
        'Ketu': 7,
        'Venus': 20,
        'Sun': 6,
        'Moon': 10,
        'Mars': 7,
        'Rahu': 18,
        'Jupiter': 16,
        'Saturn': 19,
        'Mercury': 17
    }

    # Nakshatra lords mapping (1-27)
    NAKSHATRA_LORDS = {
        1: 'Ketu',    # Ashwini
        2: 'Venus',   # Bharani
        3: 'Sun',     # Krittika
        4: 'Moon',    # Rohini
        5: 'Mars',    # Mrigashirsha
        6: 'Rahu',    # Ardra
        7: 'Jupiter', # Punarvasu
        8: 'Saturn',  # Pushya
        9: 'Mercury', # Ashlesha
        10: 'Ketu',   # Magha
        11: 'Venus',  # Purva Phalguni
        12: 'Sun',    # Uttara Phalguni
        13: 'Moon',   # Hasta
        14: 'Mars',   # Chitra
        15: 'Rahu',   # Swati
        16: 'Jupiter', # Vishakha
        17: 'Saturn', # Anuradha
        18: 'Mercury', # Jyeshtha
        19: 'Ketu',   # Mula
        20: 'Venus',  # Purva Ashadha
        21: 'Sun',    # Uttara Ashadha
        22: 'Moon',   # Shravana
        23: 'Mars',   # Dhanishta
        24: 'Rahu',   # Shatabhisha
        25: 'Jupiter', # Purva Bhadrapada
        26: 'Saturn', # Uttara Bhadrapada
        27: 'Mercury' # Revati
    }

    # Dasha order starting from each planet
    DASHA_ORDER = [
        'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
    ]

    def __init__(self, birth_date: datetime, moon_nakshatra: int, moon_degree_in_nakshatra: float):
        """
        Initialize Vimshottari Dasha calculator

        Args:
            birth_date: Birth date and time
            moon_nakshatra: Moon's nakshatra (1-27)
            moon_degree_in_nakshatra: Moon's position within the nakshatra (0-13.33 degrees)
        """
        self.birth_date = birth_date
        self.moon_nakshatra = moon_nakshatra
        self.moon_degree_in_nakshatra = moon_degree_in_nakshatra

        # Calculate the first dasha lord
        self.first_dasha_lord = self.NAKSHATRA_LORDS[moon_nakshatra]

        # Calculate how much of the first dasha is already completed
        self.first_dasha_completed_ratio = moon_degree_in_nakshatra / 13.333333  # Each nakshatra spans 13.33 degrees

        # Generate the dasha periods
        self.dasha_periods = self._calculate_dasha_periods()

    def _calculate_dasha_periods(self) -> List[Dict]:
        """Calculate all dasha periods from birth"""
        periods = []

        # Find the starting index in the dasha order
        start_index = self.DASHA_ORDER.index(self.first_dasha_lord)

        current_date = self.birth_date

        for i in range(9):  # 9 dashas in total
            planet_index = (start_index + i) % 9
            planet = self.DASHA_ORDER[planet_index]
            total_duration = self.DASHA_PERIODS[planet]

            if i == 0:
                # First dasha - account for already completed portion
                remaining_duration = total_duration * (1 - self.first_dasha_completed_ratio)
            else:
                remaining_duration = total_duration

            end_date = current_date + timedelta(days=remaining_duration * 365.25)

            periods.append({
                'planet': planet,
                'start_date': current_date,
                'end_date': end_date,
                'duration_years': remaining_duration
            })

            current_date = end_date

        return periods

    def get_current_dasha(self, date: datetime = None) -> Dict:
        """Get the current dasha for a given date (default: today)"""
        if date is None:
            date = datetime.now()

        for period in self.dasha_periods:
            if period['start_date'] <= date <= period['end_date']:
                return period

        # If no current dasha found, return the last one
        return self.dasha_periods[-1]

    def get_all_dashas(self) -> List[Dict]:
        """Get all dasha periods"""
        return self.dasha_periods

    def get_dasha_at_age(self, age_years: float) -> Dict:
        """Get dasha at a specific age"""
        target_date = self.birth_date + timedelta(days=age_years * 365.25)
        return self.get_current_dasha(target_date)


def calculate_moon_nakshatra_info(moon_longitude: float) -> Tuple[int, float, float]:
    """
    Calculate moon's nakshatra information from longitude

    Args:
        moon_longitude: Moon's longitude in degrees (0-360)

    Returns:
        Tuple of (nakshatra_number, degree_in_nakshatra, nakshatra_pada)
    """
    # Each nakshatra spans 13.333333 degrees (360/27)
    nakshatra_span = 360.0 / 27.0

    # Calculate which nakshatra (1-27)
    nakshatra_number = int(moon_longitude / nakshatra_span) + 1

    # Calculate degree within the nakshatra
    degree_in_nakshatra = moon_longitude % nakshatra_span

    # Calculate pada (1-4) - each nakshatra has 4 padas
    pada = int(degree_in_nakshatra / (nakshatra_span / 4)) + 1

    return nakshatra_number, degree_in_nakshatra, pada


def get_nakshatra_lord(nakshatra_number: int) -> str:
    """Get the lord of a nakshatra"""
    return VimshottariDasha.NAKSHATRA_LORDS.get(nakshatra_number, 'Unknown')


def get_nakshatra_name(nakshatra_number: int) -> str:
    """Get the name of a nakshatra"""
    nakshatra_names = {
        1: 'Ashwini', 2: 'Bharani', 3: 'Krittika', 4: 'Rohini',
        5: 'Mrigashirsha', 6: 'Ardra', 7: 'Punarvasu', 8: 'Pushya',
        9: 'Ashlesha', 10: 'Magha', 11: 'Purva Phalguni', 12: 'Uttara Phalguni',
        13: 'Hasta', 14: 'Chitra', 15: 'Swati', 16: 'Vishakha',
        17: 'Anuradha', 18: 'Jyeshtha', 19: 'Mula', 20: 'Purva Ashadha',
        21: 'Uttara Ashadha', 22: 'Shravana', 23: 'Dhanishta', 24: 'Shatabhisha',
        25: 'Purva Bhadrapada', 26: 'Uttara Bhadrapada', 27: 'Revati'
    }
    return nakshatra_names.get(nakshatra_number, 'Unknown')
