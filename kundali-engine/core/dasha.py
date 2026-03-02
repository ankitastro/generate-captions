"""
Full Vimshottari Dasha Tree Module

This module provides comprehensive Vimshottari Dasha calculations including
the complete dasha tree with Maha and Antar Dasha periods.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import swisseph as swe

# Set Swiss Ephemeris to use Lahiri ayanamsa (consistent with kundali_engine)
swe.set_sid_mode(swe.SIDM_LAHIRI)


class VimshottariDashaTree:
    """
    Complete Vimshottari Dasha system calculator providing full dasha tree
    with Maha Dasha and Antar Dasha periods
    """

    # Vimshottari Dasha order and periods (in years)
    DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

    DASHA_PERIODS = {
        "Ketu": 7,
        "Venus": 20,
        "Sun": 6,
        "Moon": 10,
        "Mars": 7,
        "Rahu": 18,
        "Jupiter": 16,
        "Saturn": 19,
        "Mercury": 17
    }

    # Total cycle is 120 years
    TOTAL_CYCLE_YEARS = 120

    # Nakshatra lords for determining birth dasha
    NAKSHATRA_LORDS = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",      # 1-7
        "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon",            # 8-13
        "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",         # 14-19
        "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",              # 20-25
        "Saturn", "Mercury"                                              # 26-27
    ]

    NAKSHATRA_NAMES = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
        "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
        "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]

    def __init__(self):
        """Initialize the Vimshottari Dasha calculator"""
        pass

    def get_full_dasha_tree(self, jd: float, birth_date: datetime, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Get the Vimshottari Dasha tree with configurable depth

        Args:
            jd: Julian Day number of birth
            birth_date: Birth datetime
            max_depth: Maximum depth to calculate (1=Maha only, 2=Maha+Antar, 3=+Pratyantar, 4=+Sukshma, 5=+Prana)

        Returns:
            List of Maha Dasha periods with sub-periods up to max_depth
        """
        try:
            # Get birth nakshatra and calculate starting dasha
            moon_nakshatra = self._get_moon_nakshatra(jd)
            birth_dasha_lord = self._get_birth_dasha_lord(moon_nakshatra)
            dasha_balance = self._calculate_dasha_balance(jd, moon_nakshatra)

            print(f"DEBUG: Birth Nakshatra: {moon_nakshatra['name']}, Lord: {birth_dasha_lord}")
            print(f"DEBUG: Dasha balance: {dasha_balance} years, max_depth: {max_depth}")

            # Generate the dasha tree up to specified depth
            dasha_tree = self._generate_complete_dasha_tree(birth_date, birth_dasha_lord, dasha_balance, max_depth)

            return dasha_tree

        except Exception as e:
            print(f"Error calculating dasha tree: {e}")
            return self._get_fallback_dasha_tree(birth_date)

    def get_current_dasha(self, jd: float, birth_date: datetime, current_date: datetime = None, max_depth: int = 5) -> Dict[str, Any]:
        """
        Get the current running dasha at specified levels

        Args:
            jd: Julian Day number of birth
            birth_date: Birth datetime
            current_date: Current date (default: today)
            max_depth: Maximum depth to calculate (1-5)

        Returns:
            Dictionary with current dasha details at specified levels:
            maha_dasha, antar_dasha, pratyantar_dasha, sukshma_dasha, prana_dasha
        """
        if current_date is None:
            current_date = datetime.now()

        try:
            dasha_tree = self.get_full_dasha_tree(jd, birth_date, max_depth)

            def find_current_dasha_at_level(dasha_list: List[Dict], target_date: datetime, max_depth: int = 5, path: List[Dict] = None) -> Dict[str, Any]:
                """Recursively find current dasha at all levels"""
                if path is None:
                    path = []

                for dasha in dasha_list:
                    start_date = datetime.strptime(dasha["start_date"], "%Y-%m-%d")
                    end_date = datetime.strptime(dasha["end_date"], "%Y-%m-%d")

                    if start_date <= target_date <= end_date:
                        # Add this dasha to the path
                        current_path = path + [dasha]
                        level_names = ["", "maha_dasha", "antar_dasha", "pratyantar_dasha", "sukshma_dasha", "prana_dasha"]

                        # Build result with all levels in the current path
                        result = {}
                        for i, path_dasha in enumerate(current_path[:max_depth]):
                            if i + 1 <= max_depth:
                                level_name = level_names[i + 1]
                                result[level_name] = {
                                    "planet": path_dasha["planet"],
                                    "start_date": path_dasha["start_date"],
                                    "end_date": path_dasha["end_date"],
                                    "duration_years": path_dasha["duration_years"]
                                }

                        # Continue searching in sub-periods if they exist
                        if "sub_periods" in dasha and dasha["sub_periods"] and len(current_path) < max_depth:
                            sub_result = find_current_dasha_at_level(dasha["sub_periods"], target_date, max_depth, current_path)
                            # Merge results, preferring deeper levels
                            result.update(sub_result)

                        return result

                # If no dasha found at this level, return empty dict
                return {}

            # Find current dashas at all levels
            current_dashas = find_current_dasha_at_level(dasha_tree, current_date, max_depth)

            # Ensure we always have maha_dasha and antar_dasha (required by model)
            if not current_dashas or "maha_dasha" not in current_dashas:
                if dasha_tree:
                    first_maha = dasha_tree[0]
                    current_dashas["maha_dasha"] = {
                        "planet": first_maha["planet"],
                        "start_date": first_maha["start_date"],
                        "end_date": first_maha["end_date"],
                        "duration_years": first_maha["duration_years"]
                    }

                    # Add first antar if available and antar_dasha is missing
                    if "antar_dasha" not in current_dashas and first_maha.get("sub_periods"):
                        first_antar = first_maha["sub_periods"][0]
                        current_dashas["antar_dasha"] = {
                            "planet": first_antar["planet"],
                            "start_date": first_antar["start_date"],
                            "end_date": first_antar["end_date"],
                            "duration_years": first_antar["duration_years"]
                        }

            return current_dashas

        except Exception as e:
            print(f"Error finding current dasha: {e}")

        return self._get_fallback_current_dasha(birth_date)

    def get_dasha_at_depth(self, jd: float, birth_date: datetime, depth: int = 3,
                          limit_maha: int = 2) -> List[Dict[str, Any]]:
        """
        Get dasha tree at specified depth level

        Args:
            jd: Julian Day number of birth
            birth_date: Birth datetime
            depth: Depth level (1=Maha, 2=Maha+Antar, 3=+Pratyantar, 4=+Sukshma, 5=+Prana)
            limit_maha: Number of Maha dashas to include in output

        Returns:
            Dasha tree at specified depth
        """
        try:
            # Generate tree only to the requested depth for performance
            dasha_tree = self.get_full_dasha_tree(jd, birth_date, max_depth=depth)

            if depth == 1:
                # Return only Maha dashas
                result = []
                for maha in dasha_tree[:limit_maha]:
                    result.append({
                        "planet": maha["planet"],
                        "start_date": maha["start_date"],
                        "end_date": maha["end_date"],
                        "duration_years": maha["duration_years"],
                        "level": 1,
                        "type": "Maha Dasha"
                    })
                return result

            elif depth == 2:
                # Return Maha + Antar dashas
                result = []
                for maha in dasha_tree[:limit_maha]:
                    maha_entry = {
                        "planet": maha["planet"],
                        "start_date": maha["start_date"],
                        "end_date": maha["end_date"],
                        "duration_years": maha["duration_years"],
                        "level": 1,
                        "type": "Maha Dasha",
                        "sub_periods": []
                    }

                    for antar in maha.get("sub_periods", [])[:9]:  # Limit antar dashas
                        maha_entry["sub_periods"].append({
                            "planet": antar["planet"],
                            "start_date": antar["start_date"],
                            "end_date": antar["end_date"],
                            "duration_years": antar["duration_years"],
                            "level": 2,
                            "type": "Antar Dasha"
                        })

                    result.append(maha_entry)
                return result

            else:
                # For depths 3-5, return the full tree (already truncated at max_depth)
                return dasha_tree[:limit_maha]

        except Exception as e:
            print(f"Error getting dasha at depth {depth}: {e}")
            return self._get_fallback_dasha_tree(birth_date)[:limit_maha]

    def _get_moon_nakshatra(self, jd: float) -> Dict[str, Any]:
        """Get Moon's nakshatra at birth"""
        try:
            # CRITICAL: Set Lahiri ayanamsa mode BEFORE any calculations
            # This fixes the issue where the mode gets reset to default
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            # Get Moon's position
            moon_pos = swe.calc_ut(jd, swe.MOON)
            moon_longitude = moon_pos[0][0]  # Extract longitude from nested tuple

            # Apply ayanamsa for sidereal longitude
            ayanamsa = swe.get_ayanamsa_ut(jd)
            if isinstance(ayanamsa, tuple):
                ayanamsa = ayanamsa[0]

            sidereal_longitude = (moon_longitude - ayanamsa) % 360

            # Calculate nakshatra (1-27)
            nakshatra_num = int(sidereal_longitude * 27 / 360) + 1
            if nakshatra_num > 27:
                nakshatra_num = 27

            # Calculate pada (1-4)
            pada_num = int((sidereal_longitude % (360/27)) * 4 / (360/27)) + 1
            if pada_num > 4:
                pada_num = 4

            # Calculate the exact position within the nakshatra (0-1)
            nakshatra_position = (sidereal_longitude * 27 / 360) % 1

            return {
                "name": self.NAKSHATRA_NAMES[nakshatra_num - 1],
                "number": nakshatra_num,
                "pada": pada_num,
                "position": nakshatra_position,  # How much of the nakshatra is completed
                "lord": self.NAKSHATRA_LORDS[nakshatra_num - 1]
            }

        except Exception as e:
            print(f"Error calculating moon nakshatra: {e}")
            return {
                "name": "Ashwini", "number": 1, "pada": 1,
                "position": 0.0, "lord": "Ketu"
            }

    def _get_birth_dasha_lord(self, nakshatra_info: Dict[str, Any]) -> str:
        """Get the birth dasha lord based on Moon's nakshatra"""
        return nakshatra_info["lord"]

    def _calculate_dasha_balance(self, jd: float, nakshatra_info: Dict[str, Any]) -> float:
        """
        Calculate the remaining balance of the birth dasha

        The balance is calculated based on how much of the nakshatra is completed
        """
        try:
            dasha_lord = nakshatra_info["lord"]
            total_dasha_years = self.DASHA_PERIODS[dasha_lord]

            # How much of the nakshatra is left (1 - position)
            nakshatra_left = 1.0 - nakshatra_info["position"]

            # Dasha balance is proportional to nakshatra left
            dasha_balance = total_dasha_years * nakshatra_left

            return round(dasha_balance, 4)

        except Exception as e:
            print(f"Error calculating dasha balance: {e}")
            return 7.0  # Default to 7 years

    def _generate_complete_dasha_tree(self, birth_date: datetime, birth_dasha_lord: str, dasha_balance: float, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Generate the Vimshottari Dasha tree up to specified depth"""
        dasha_tree = []
        current_date = birth_date

        # Find the starting position in the dasha order
        start_index = self.DASHA_ORDER.index(birth_dasha_lord)

        # First, add the birth dasha with remaining balance
        if dasha_balance > 0:
            first_dasha = self._create_maha_dasha_period(
                birth_dasha_lord, current_date, dasha_balance, max_depth
            )
            dasha_tree.append(first_dasha)
            current_date += timedelta(days=dasha_balance * 365.25)

        # Add the remaining dashas in order
        for i in range(1, len(self.DASHA_ORDER)):
            dasha_index = (start_index + i) % len(self.DASHA_ORDER)
            dasha_lord = self.DASHA_ORDER[dasha_index]
            dasha_years = self.DASHA_PERIODS[dasha_lord]

            maha_dasha = self._create_maha_dasha_period(
                dasha_lord, current_date, dasha_years, max_depth
            )
            dasha_tree.append(maha_dasha)
            current_date += timedelta(days=dasha_years * 365.25)

            # Stop after completing one full cycle (120 years) or reasonable limit
            if len(dasha_tree) >= 9:  # One complete cycle
                break

        return dasha_tree

    def _create_maha_dasha_period(self, dasha_lord: str, start_date: datetime, total_years: float, max_depth: int = 2) -> Dict[str, Any]:
        """Create a Maha Dasha period with sub-periods up to max_depth"""
        end_date = start_date + timedelta(days=total_years * 365.25)

        # Generate sub-periods only if max_depth > 1
        sub_periods = []
        if max_depth > 1:
            sub_periods = self._generate_antar_dasha_periods(dasha_lord, start_date, total_years, max_depth)

        return {
            "planet": dasha_lord,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "duration_years": round(total_years, 4),
            "sub_periods": sub_periods
        }

    def _generate_antar_dasha_periods(self, maha_lord: str, start_date: datetime, total_years: float, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Generate Antar Dasha periods within a Maha Dasha"""
        sub_periods = []
        current_date = start_date

        # Find starting position for the Maha Dasha lord
        maha_index = self.DASHA_ORDER.index(maha_lord)

        # Calculate Antar Dasha periods
        for i in range(len(self.DASHA_ORDER)):
            antar_index = (maha_index + i) % len(self.DASHA_ORDER)
            antar_lord = self.DASHA_ORDER[antar_index]

            # Antar Dasha duration calculation
            # Formula: (Maha Lord years * Antar Lord years) / 120
            antar_years = (self.DASHA_PERIODS[maha_lord] * self.DASHA_PERIODS[antar_lord]) / self.TOTAL_CYCLE_YEARS

            # Scale to fit within the Maha Dasha period
            antar_duration = (antar_years / self.DASHA_PERIODS[maha_lord]) * total_years

            antar_end_date = current_date + timedelta(days=antar_duration * 365.25)

            # Generate sub-periods only if max_depth > 2
            antar_sub_periods = []
            if max_depth > 2:
                antar_sub_periods = self._generate_pratyantar_dasha_periods(antar_lord, current_date, antar_duration, max_depth)

            sub_periods.append({
                "planet": antar_lord,
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": antar_end_date.strftime("%Y-%m-%d"),
                "duration_years": round(antar_duration, 4),
                "sub_periods": antar_sub_periods
            })

            current_date = antar_end_date

        return sub_periods

    def _generate_pratyantar_dasha_periods(self, antar_lord: str, start_date: datetime, antar_duration: float, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Generate Pratyantar Dasha periods within an Antar Dasha"""
        sub_periods = []
        current_date = start_date

        # Find starting position for the Antar Dasha lord
        antar_index = self.DASHA_ORDER.index(antar_lord)

        # Calculate Pratyantar Dasha periods
        for i in range(len(self.DASHA_ORDER)):
            pratyantar_index = (antar_index + i) % len(self.DASHA_ORDER)
            pratyantar_lord = self.DASHA_ORDER[pratyantar_index]

            # Pratyantar Dasha duration calculation
            # Formula: (Antar Lord years * Pratyantar Lord years) / 120
            pratyantar_years = (self.DASHA_PERIODS[antar_lord] * self.DASHA_PERIODS[pratyantar_lord]) / self.TOTAL_CYCLE_YEARS

            # Scale to fit within the Antar Dasha period
            pratyantar_duration = (pratyantar_years / self.DASHA_PERIODS[antar_lord]) * antar_duration

            pratyantar_end_date = current_date + timedelta(days=pratyantar_duration * 365.25)

            # Generate sub-periods only if max_depth > 3
            pratyantar_sub_periods = []
            if max_depth > 3:
                pratyantar_sub_periods = self._generate_sukshma_dasha_periods(pratyantar_lord, current_date, pratyantar_duration, max_depth)

            sub_periods.append({
                "planet": pratyantar_lord,
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": pratyantar_end_date.strftime("%Y-%m-%d"),
                "duration_years": round(pratyantar_duration, 6),  # Higher precision for smaller periods
                "sub_periods": pratyantar_sub_periods
            })

            current_date = pratyantar_end_date

        return sub_periods

    def _generate_sukshma_dasha_periods(self, pratyantar_lord: str, start_date: datetime, pratyantar_duration: float, max_depth: int = 4) -> List[Dict[str, Any]]:
        """Generate Sukshma Dasha periods within a Pratyantar Dasha"""
        sub_periods = []
        current_date = start_date

        # Find starting position for the Pratyantar Dasha lord
        pratyantar_index = self.DASHA_ORDER.index(pratyantar_lord)

        # Calculate Sukshma Dasha periods
        for i in range(len(self.DASHA_ORDER)):
            sukshma_index = (pratyantar_index + i) % len(self.DASHA_ORDER)
            sukshma_lord = self.DASHA_ORDER[sukshma_index]

            # Sukshma Dasha duration calculation
            # Formula: (Pratyantar Lord years * Sukshma Lord years) / 120
            sukshma_years = (self.DASHA_PERIODS[pratyantar_lord] * self.DASHA_PERIODS[sukshma_lord]) / self.TOTAL_CYCLE_YEARS

            # Scale to fit within the Pratyantar Dasha period
            sukshma_duration = (sukshma_years / self.DASHA_PERIODS[pratyantar_lord]) * pratyantar_duration

            sukshma_end_date = current_date + timedelta(days=sukshma_duration * 365.25)

            # Generate sub-periods only if max_depth > 4
            sukshma_sub_periods = []
            if max_depth > 4:
                sukshma_sub_periods = self._generate_prana_dasha_periods(sukshma_lord, current_date, sukshma_duration)

            sub_periods.append({
                "planet": sukshma_lord,
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": sukshma_end_date.strftime("%Y-%m-%d"),
                "duration_years": round(sukshma_duration, 8),  # Even higher precision
                "sub_periods": sukshma_sub_periods
            })

            current_date = sukshma_end_date

        return sub_periods

    def _generate_prana_dasha_periods(self, sukshma_lord: str, start_date: datetime, sukshma_duration: float) -> List[Dict[str, Any]]:
        """Generate Prana Dasha periods within a Sukshma Dasha (5th level)"""
        sub_periods = []
        current_date = start_date

        # Find starting position for the Sukshma Dasha lord
        sukshma_index = self.DASHA_ORDER.index(sukshma_lord)

        # Calculate Prana Dasha periods
        for i in range(len(self.DASHA_ORDER)):
            prana_index = (sukshma_index + i) % len(self.DASHA_ORDER)
            prana_lord = self.DASHA_ORDER[prana_index]

            # Prana Dasha duration calculation
            # Formula: (Sukshma Lord years * Prana Lord years) / 120
            prana_years = (self.DASHA_PERIODS[sukshma_lord] * self.DASHA_PERIODS[prana_lord]) / self.TOTAL_CYCLE_YEARS

            # Scale to fit within the Sukshma Dasha period
            prana_duration = (prana_years / self.DASHA_PERIODS[sukshma_lord]) * sukshma_duration

            prana_end_date = current_date + timedelta(days=prana_duration * 365.25)

            sub_periods.append({
                "planet": prana_lord,
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": prana_end_date.strftime("%Y-%m-%d"),
                "duration_years": round(prana_duration, 10)  # Highest precision for smallest periods
            })

            current_date = prana_end_date

        return sub_periods

    def _get_fallback_dasha_tree(self, birth_date: datetime) -> List[Dict[str, Any]]:
        """Fallback dasha tree when calculation fails"""
        return [
            {
                "planet": "Mercury",
                "start_date": birth_date.strftime("%Y-%m-%d"),
                "end_date": (birth_date + timedelta(days=17 * 365.25)).strftime("%Y-%m-%d"),
                "duration_years": 17.0,
                "sub_periods": [
                    {
                        "planet": "Mercury",
                        "start_date": birth_date.strftime("%Y-%m-%d"),
                        "end_date": (birth_date + timedelta(days=2.4 * 365.25)).strftime("%Y-%m-%d"),
                        "duration_years": 2.4
                    }
                ]
            }
        ]

    def _get_fallback_current_dasha(self, birth_date: datetime) -> Dict[str, Any]:
        """Fallback current dasha when calculation fails"""
        return {
            "maha_dasha": {
                "planet": "Mercury",
                "start_date": birth_date.strftime("%Y-%m-%d"),
                "end_date": (birth_date + timedelta(days=17 * 365.25)).strftime("%Y-%m-%d"),
                "total_years": 17.0
            },
            "antar_dasha": {
                "planet": "Mercury",
                "start_date": birth_date.strftime("%Y-%m-%d"),
                "end_date": (birth_date + timedelta(days=2.4 * 365.25)).strftime("%Y-%m-%d"),
                "duration_years": 2.4
            }
        }

    def get_dasha_summary(self, jd: float, birth_date: datetime) -> Dict[str, Any]:
        """Get a summary of the dasha system for the chart"""
        try:
            moon_nakshatra = self._get_moon_nakshatra(jd)
            birth_dasha_lord = self._get_birth_dasha_lord(moon_nakshatra)
            dasha_balance = self._calculate_dasha_balance(jd, moon_nakshatra)
            current_dasha = self.get_current_dasha(jd, birth_date)

            return {
                "birth_nakshatra": moon_nakshatra,
                "birth_dasha_lord": birth_dasha_lord,
                "birth_dasha_balance": dasha_balance,
                "current_running": current_dasha
            }

        except Exception as e:
            print(f"Error getting dasha summary: {e}")
            return {
                "birth_nakshatra": {"name": "Unknown", "lord": "Mercury"},
                "birth_dasha_lord": "Mercury",
                "birth_dasha_balance": 17.0,
                "current_running": self._get_fallback_current_dasha(birth_date)
            }
