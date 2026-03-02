"""
Core Kundali computation service
Contains all the business logic for computing Kundali data
"""

import logging
from typing import Dict
from fastapi import HTTPException

from models import KundaliRequest, KundaliResponse, MinimalKundliInput
from kundali_engine import KundaliEngine
from api.input_normalizer import minimal_to_kundali_request
from translation_manager import get_translation_manager

logger = logging.getLogger(__name__)

# Global engine instance
kundali_engine = KundaliEngine()
translation_manager = get_translation_manager()


def _compute(min_req: MinimalKundliInput, svg: bool = False):
    """
    Main computation function for full Kundali generation

    Args:
        min_req: MinimalKundliInput with birth details
        svg: If True, includes SVG charts in response. Default is False.

    Returns:
        KundaliResponse or translated dict (with or without SVGs based on svg parameter)
    """
    try:
        kr: KundaliRequest = minimal_to_kundali_request(min_req)
        logger.info("Computing Kundali for %s (lat=%.4f lon=%.4f tz=%s lang=%s svg=%s)",
                   kr.name, kr.latitude, kr.longitude, kr.timezone, kr.language, svg)

        # Generate Kundali
        kundali_response = kundali_engine.generate_kundali(kr)

        # Translate response if language is not English
        if kr.language and kr.language != 'en':
            response_dict = kundali_response.model_dump()
            # Remove SVG fields if svg=False
            if not svg:
                response_dict.pop('rasi_chart_svg', None)
                response_dict.pop('navamsa_chart_svg', None)
                response_dict.pop('ashtavarga_svg', None)
            translated_dict = translation_manager.translate_full_response(response_dict, kr.language)
            return translated_dict

        # Return KundaliResponse object (with SVGs if svg=True, without if svg=False)
        if not svg:
            # Convert to dict and remove SVG fields, return as dict
            # This avoids validation issues when reconstructing the model
            response_dict = kundali_response.model_dump()
            response_dict.pop('rasi_chart_svg', None)
            response_dict.pop('navamsa_chart_svg', None)
            response_dict.pop('ashtavarga_svg', None)
            return response_dict

        # svg=True: Return the full KundaliResponse object with all SVGs
        return kundali_response
    except Exception as e:
        logger.exception("Error computing Kundali")
        raise HTTPException(status_code=500, detail=str(e))


def _compute_birth_details(req: MinimalKundliInput):
    """
    Optimized calculation for birth-details endpoint - only panchanga + enhanced_panchanga

    Args:
        req: MinimalKundliInput with birth details

    Returns:
        Dict with birth details and panchanga info
    """
    try:
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info("Computing birth details for %s (lat=%.4f lon=%.4f tz=%s lang=%s)",
                   kr.name, kr.latitude, kr.longitude, kr.timezone, kr.language)

        # Only calculate what's needed: basic info + panchanga
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

        # Get basic planetary positions (minimal needed for panchanga)
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)

        # Get panchanga details only
        panchanga = kundali_engine._get_panchanga_details(jd, kr.latitude, kr.longitude, kr.timezone)
        enhanced_panchanga = kundali_engine.enhanced_panchanga.get_details(
            jd, kr.latitude, kr.longitude, kr.timezone, person, lang=kr.language or 'en'
        )

        # Create minimal response object
        birth_info = {
            "date_of_birth": req.date_of_birth,
            "time_of_birth": req.time_of_birth,
            "place_of_birth": req.place_of_birth,
            "latitude": kr.latitude,
            "longitude": kr.longitude,
            "timezone": kr.timezone
        }

        # Create minimal response dict
        response_dict = {
            "name": kr.name,
            "birth_info": birth_info,
            "panchanga": panchanga.model_dump() if panchanga else {},
            "enhanced_panchanga": enhanced_panchanga if isinstance(enhanced_panchanga, dict) else (enhanced_panchanga.model_dump() if enhanced_panchanga else {})
        }

        # Translate response if language is not English
        if kr.language and kr.language != 'en':
            translated_dict = translation_manager.translate_full_response(response_dict, kr.language)
            return translated_dict

        return response_dict
    except Exception as e:
        logger.exception("Error computing birth details")
        raise HTTPException(status_code=500, detail=str(e))


def _compute_yogas(req: MinimalKundliInput):
    """
    Optimized calculation for yogas endpoint - only yoga detection

    Args:
        req: MinimalKundliInput with birth details

    Returns:
        Dict with detected yogas and summary
    """
    try:
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info("Computing yogas for %s (lat=%.4f lon=%.4f tz=%s lang=%s)",
                   kr.name, kr.latitude, kr.longitude, kr.timezone, kr.language)

        # Only calculate what's needed for yoga detection
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)

        # Convert to list for yoga detector
        planets_list = list(planets.values())

        # Detect yogas only (need rasi_chart and lagna_sign as per original)
        rasi_chart = kundali_engine._generate_rasi_chart(planets, lagna_info['sign'])
        detected_yogas = kundali_engine.yoga_detector.detect_all_yogas(planets_list, rasi_chart, lagna_info['sign'])
        yoga_summary = kundali_engine.yoga_detector.get_yoga_summary(detected_yogas)

        # Convert detected yogas to the proper format (same as original)
        yogas_info = []
        for yoga in detected_yogas:
            if hasattr(yoga, 'name'):  # YogaInfo dataclass
                from models import YogaInfo
                yogas_info.append(YogaInfo(
                    name=yoga.name,
                    description=yoga.description,
                    strength=yoga.strength,
                    planets_involved=yoga.planets_involved,
                    houses_involved=yoga.houses_involved,
                    significance=yoga.significance,
                    effects=yoga.effects
                ))

        # Create minimal response dict
        response_dict = {
            "name": kr.name,
            "detected_yogas": [yoga.model_dump() for yoga in yogas_info],
            "yoga_summary": yoga_summary if yoga_summary else {},
        }

        # Translate response if language is not English
        if kr.language and kr.language != 'en':
            translated_dict = translation_manager.translate_full_response(response_dict, kr.language)
            return translated_dict

        return response_dict
    except Exception as e:
        logger.exception("Error computing yogas")
        raise HTTPException(status_code=500, detail=str(e))


def _compute_ashtakavarga(req: MinimalKundliInput):
    """
    Optimized calculation for ashtakavarga-data endpoint - only ashtakavarga

    Args:
        req: MinimalKundliInput with birth details

    Returns:
        Dict with ashtakavarga data
    """
    try:
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info("Computing ashtakavarga for %s (lat=%.4f lon=%.4f tz=%s lang=%s)",
                   kr.name, kr.latitude, kr.longitude, kr.timezone, kr.language)

        # Only calculate what's needed for ashtakavarga
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)

        # Extract planet signs for ashtakavarga calculation
        planet_signs = {planet_name: planet_data.sign for planet_name, planet_data in planets.items()}
        lagna_sign = lagna_info['sign']

        # Calculate ashtakavarga only
        from ashtavarga import calculate_ashtakavarga
        ashtakavarga_data = calculate_ashtakavarga(planet_signs, lagna_sign)

        # Create minimal response dict
        response_dict = {
            "name": kr.name,
            "ashtakavarga": ashtakavarga_data
        }

        # Ashtakavarga data is numerical, no translation needed
        return response_dict
    except Exception as e:
        logger.exception("Error computing ashtakavarga")
        raise HTTPException(status_code=500, detail=str(e))


def _compute_charts(req: MinimalKundliInput):
    """
    Optimized calculation for charts endpoint - only varga charts + SVGs

    Args:
        req: MinimalKundliInput with birth details

    Returns:
        Dict with chart data and SVGs
    """
    try:
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info("Computing charts for %s (lat=%.4f lon=%.4f tz=%s lang=%s)",
                   kr.name, kr.latitude, kr.longitude, kr.timezone, kr.language)

        # Only calculate what's needed for charts
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)

        # Get basic planetary data
        planets_list = list(planets.values())

        # Generate basic charts (without full dasha/yogas)
        rasi_chart = kundali_engine._generate_rasi_chart(planets, lagna_info['sign'])

        # Generate basic SVGs
        import svg_chart_generator
        rasi_chart_svg = svg_chart_generator.create_rasi_chart_svg(
            planets, lagna_info, kr.language if kr.language else 'en'
        )

        # Get navamsa data
        navamsa_chart = kundali_engine._get_navamsa_chart(planets, lagna_info['sign'])
        navamsa_chart_svg = svg_chart_generator.create_navamsa_chart_svg(
            planets, lagna_info, kr.language if kr.language else 'en'
        )

        # Create minimal response dict
        response_dict = {
            "name": kr.name,
            "rasi_chart": rasi_chart,
            "rasi_chart_svg": rasi_chart_svg,
            "navamsa_chart": navamsa_chart.dict() if navamsa_chart else {},
            "navamsa_chart_svg": navamsa_chart_svg,
        }

        # Translate response if language is not English (except SVGs which are already handled)
        if kr.language and kr.language != 'en':
            # Only translate the chart data, not SVGs
            translated_dict = response_dict.copy()
            if isinstance(response_dict.get("navamsa_chart"), dict):
                translated_dict["navamsa_chart"] = translation_manager.translate_full_response(
                    response_dict["navamsa_chart"], kr.language
                )
            return translated_dict

        return response_dict
    except Exception as e:
        logger.exception("Error computing charts")
        raise HTTPException(status_code=500, detail=str(e))


def get_engine() -> KundaliEngine:
    """Get the global KundaliEngine instance"""
    return kundali_engine


def get_translation_mgr():
    """Get the global translation manager instance"""
    return translation_manager
