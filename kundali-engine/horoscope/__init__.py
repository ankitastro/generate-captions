"""
Horoscope Generation Package

This package provides comprehensive horoscope generation functionality
for all 12 zodiac signs across multiple time scopes.
"""

from .horoscope_engine import generate_horoscope, HoroscopeEngine, ZODIAC_SIGNS, VALID_SCOPES
from .planetary_horoscope_engine import generate_planetary_horoscope, PlanetaryHoroscopeEngine

__version__ = "1.0.0"
__all__ = [
    "generate_horoscope",
    "HoroscopeEngine",
    "generate_planetary_horoscope",
    "PlanetaryHoroscopeEngine",
    "ZODIAC_SIGNS",
    "VALID_SCOPES"
]
