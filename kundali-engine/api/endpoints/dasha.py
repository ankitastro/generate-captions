"""
Dasha endpoints - separate endpoints for different dasha depth levels
"""

import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime

from models import MinimalKundliInput
from api.input_normalizer import minimal_to_kundali_request
from api.services.kundli_service import get_engine, get_translation_mgr
from core.dasha import VimshottariDashaTree

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_jd_and_birth_date(min_req: MinimalKundliInput):
    """Helper to get Julian Day and birth date from minimal request"""
    kr = minimal_to_kundali_request(min_req)
    kundali_engine = get_engine()

    # Convert to Julian Day
    jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

    return jd, kr.datetime, kr.language


def _translate_dasha_tree(dasha_tree: list, language: str, translation_manager) -> list:
    """Recursively translate dasha tree planets to the specified language"""
    if not dasha_tree or language == 'en':
        return dasha_tree

    translated_tree = []
    for dasha_period in dasha_tree:
        translated_period = dasha_period.copy()

        # Translate planet name
        if 'planet' in translated_period:
            translated_period['planet'] = translation_manager.translate(
                f'planets.{dasha_period["planet"]}', language, default=dasha_period["planet"]
            )

        # Recursively translate sub_periods
        if 'sub_periods' in translated_period and isinstance(translated_period['sub_periods'], list):
            translated_period['sub_periods'] = _translate_dasha_tree(
                translated_period['sub_periods'], language, translation_manager
            )

        translated_tree.append(translated_period)

    return translated_tree


def _translate_current_dasha(current_dasha: dict, language: str, translation_manager) -> dict:
    """Translate current dasha planets to the specified language"""
    if not current_dasha or language == 'en':
        return current_dasha

    translated = {}
    for level_name, level_data in current_dasha.items():
        if isinstance(level_data, dict) and 'planet' in level_data:
            translated[level_name] = level_data.copy()
            translated[level_name]['planet'] = translation_manager.translate(
                f'planets.{level_data["planet"]}', language, default=level_data["planet"]
            )
        else:
            translated[level_name] = level_data

    return translated


@router.post("/api/dasha/vimshottari")
def vimshottari_dasha(min_req: MinimalKundliInput):
    """
    Get 2-level Vimshottari Dasha (Maha + Antar Dasha)

    This is the default dasha calculation included in /api/kundli endpoint.
    Returns the complete dasha tree with Maha Dasha periods and their Antar Dasha sub-periods.

    Returns:
        - vimshottari_dasha: List of Maha Dasha periods with Antar Dasha sub-periods
        - current_dasha_detailed: Current running dashas at Maha and Antar levels
    """
    try:
        jd, birth_date, language = _get_jd_and_birth_date(min_req)
        translation_manager = get_translation_mgr()

        # Calculate 2-level dasha (Maha + Antar)
        dasha_calculator = VimshottariDashaTree()
        dasha_tree = dasha_calculator.get_full_dasha_tree(jd, birth_date, max_depth=2)
        current_dasha = dasha_calculator.get_current_dasha(jd, birth_date, max_depth=2)

        # Translate planet names if language is not English
        translated_dasha_tree = _translate_dasha_tree(dasha_tree, language, translation_manager)
        translated_current_dasha = _translate_current_dasha(current_dasha, language, translation_manager)

        return {
            "name": min_req.name,
            "vimshottari_dasha": translated_dasha_tree,
            "current_dasha_detailed": translated_current_dasha,
            "dasha_level": "Maha + Antar Dasha (2 levels)"
        }

    except Exception as e:
        logger.error(f"Error calculating vimshottari dasha: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/dasha/pratyantar")
def pratyantar_dasha(min_req: MinimalKundliInput):
    """
    Get 3-level Vimshottari Dasha (Maha + Antar + Pratyantar Dasha)

    Returns the complete dasha tree with Maha Dasha periods,
    their Antar Dasha sub-periods, and Pratyantar Dasha sub-sub-periods.

    Returns:
        - vimshottari_dasha: List of Maha Dasha periods with Antar and Pratyantar sub-periods
        - current_dasha_detailed: Current running dashas at Maha, Antar, and Pratyantar levels
    """
    try:
        jd, birth_date, language = _get_jd_and_birth_date(min_req)
        translation_manager = get_translation_mgr()

        # Calculate 3-level dasha (Maha + Antar + Pratyantar)
        dasha_calculator = VimshottariDashaTree()
        dasha_tree = dasha_calculator.get_full_dasha_tree(jd, birth_date, max_depth=3)
        current_dasha = dasha_calculator.get_current_dasha(jd, birth_date, max_depth=3)

        # Translate planet names if language is not English
        translated_dasha_tree = _translate_dasha_tree(dasha_tree, language, translation_manager)
        translated_current_dasha = _translate_current_dasha(current_dasha, language, translation_manager)

        return {
            "name": min_req.name,
            "vimshottari_dasha": translated_dasha_tree,
            "current_dasha_detailed": translated_current_dasha,
            "dasha_level": "Maha + Antar + Pratyantar Dasha (3 levels)"
        }

    except Exception as e:
        logger.error(f"Error calculating pratyantar dasha: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/dasha/sukshma")
def sukshma_dasha(min_req: MinimalKundliInput):
    """
    Get 4-level Vimshottari Dasha (Maha + Antar + Pratyantar + Sukshma Dasha)

    Returns the complete dasha tree with Maha Dasha periods,
    Antar Dasha sub-periods, Pratyantar Dasha sub-sub-periods, and Sukshma Dasha periods.

    Returns:
        - vimshottari_dasha: Complete dasha tree with 4 levels
        - current_dasha_detailed: Current running dashas at all 4 levels
    """
    try:
        jd, birth_date, language = _get_jd_and_birth_date(min_req)
        translation_manager = get_translation_mgr()

        # Calculate 4-level dasha
        dasha_calculator = VimshottariDashaTree()
        dasha_tree = dasha_calculator.get_full_dasha_tree(jd, birth_date, max_depth=4)
        current_dasha = dasha_calculator.get_current_dasha(jd, birth_date, max_depth=4)

        # Translate planet names if language is not English
        translated_dasha_tree = _translate_dasha_tree(dasha_tree, language, translation_manager)
        translated_current_dasha = _translate_current_dasha(current_dasha, language, translation_manager)

        return {
            "name": min_req.name,
            "vimshottari_dasha": translated_dasha_tree,
            "current_dasha_detailed": translated_current_dasha,
            "dasha_level": "Maha + Antar + Pratyantar + Sukshma Dasha (4 levels)"
        }

    except Exception as e:
        logger.error(f"Error calculating sukshma dasha: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/dasha/prana")
def prana_dasha(min_req: MinimalKundliInput):
    """
    Get 5-level Vimshottari Dasha (Maha + Antar + Pratyantar + Sukshma + Prana Dasha)

    Returns the complete 5-level Vimshottari Dasha tree. This is the most detailed
    dasha calculation including all five levels: Maha, Antar, Pratyantar, Sukshma, and Prana.

    Note: This endpoint may take longer to compute due to the complexity of
    calculating all 5 levels (9x9x9x9x9 combinations).

    Returns:
        - vimshottari_dasha: Complete 5-level dasha tree
        - current_dasha_detailed: Current running dashas at all 5 levels
    """
    try:
        jd, birth_date, language = _get_jd_and_birth_date(min_req)
        translation_manager = get_translation_mgr()

        # Calculate 5-level dasha (full tree)
        dasha_calculator = VimshottariDashaTree()
        dasha_tree = dasha_calculator.get_full_dasha_tree(jd, birth_date, max_depth=5)
        current_dasha = dasha_calculator.get_current_dasha(jd, birth_date, max_depth=5)

        # Translate planet names if language is not English
        translated_dasha_tree = _translate_dasha_tree(dasha_tree, language, translation_manager)
        translated_current_dasha = _translate_current_dasha(current_dasha, language, translation_manager)

        return {
            "name": min_req.name,
            "vimshottari_dasha": translated_dasha_tree,
            "current_dasha_detailed": translated_current_dasha,
            "dasha_level": "Maha + Antar + Pratyantar + Sukshma + Prana Dasha (5 levels)"
        }

    except Exception as e:
        logger.error(f"Error calculating prana dasha: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/dasha/current")
def current_dasha(min_req: MinimalKundliInput, level: int = 2):
    """
    Get current running dasha at specified level

    Args:
        level: Dasha level to calculate (1=Maha only, 2=Maha+Antar, 3=+Pratyantar, 4=+Sukshma, 5=+Prana)

    Returns:
        - current_dasha_detailed: Current running dasha at specified level(s)
        - birth_dasha_info: Birth dasha lord and balance info
    """
    try:
        jd, birth_date, language = _get_jd_and_birth_date(min_req)
        translation_manager = get_translation_mgr()

        # Validate level
        if level < 1 or level > 5:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 5")

        # Calculate current dasha at specified level
        dasha_calculator = VimshottariDashaTree()
        current_dasha = dasha_calculator.get_current_dasha(jd, birth_date, max_depth=level)

        # Get birth dasha info
        moon_nakshatra = dasha_calculator._get_moon_nakshatra(jd)
        birth_dasha_lord = dasha_calculator._get_birth_dasha_lord(moon_nakshatra)
        dasha_balance = dasha_calculator._calculate_dasha_balance(jd, moon_nakshatra)

        # Translate planet names if language is not English
        translated_current_dasha = _translate_current_dasha(current_dasha, language, translation_manager)
        translated_birth_dasha_lord = translation_manager.translate(
            f'planets.{birth_dasha_lord}', language, default=birth_dasha_lord
        )

        return {
            "name": min_req.name,
            "current_dasha_detailed": translated_current_dasha,
            "birth_dasha_info": {
                "birth_nakshatra": moon_nakshatra["name"],
                "birth_dasha_lord": translated_birth_dasha_lord,
                "dasha_balance_years": dasha_balance
            },
            "dasha_level": f"Level {level}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating current dasha: {e}")
        raise HTTPException(status_code=500, detail=str(e))
