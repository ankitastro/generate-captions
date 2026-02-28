"""
Specialized endpoints - KP System, Bhava Chalit, Horoscope, Matching, Doshas, Ashtakavarga, Complete
"""

import logging
import traceback
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from models import MinimalKundliInput, KundliMatchingRequest, KundliMatchingResponse
from api.input_normalizer import minimal_to_kundali_request
from api.services.kundli_service import get_engine, get_translation_mgr
from ashtakoota_matcher import AshtakootaMatcher
from ashtavarga import calculate_ashtakavarga
from dosha_analyzer import calculate_mangal_dosha, calculate_kalasarpa_dosha
from svg_chart_generator import create_ashtakavarga_svg, create_bhava_chalit_svg
from kp_system import KPSystem, BhavaChalitSystem, calculate_kp_and_bhava_chalit
from horoscope.narrative_horoscope import generate_structured_horoscope, ZODIAC_SIGNS
from api.utils.constants import SIGN_NAMES
from core.varga_engine import get_all_varga_charts, get_all_varga_charts_detailed, VARGA_NAMES

logger = logging.getLogger(__name__)
router = APIRouter()


# =================== ASHTAKAVARGA ENDPOINTS ===================

@router.post("/api/ashtakavarga-data")
def get_ashtakavarga_data(
    min_req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG chart in response")
):
    """
    Returns the raw Ashtakavarga data in JSON format.

    Args:
        min_req: Minimal kundli input with birth details
        svg: If True, includes SVG chart in response. Default is False.
    """
    try:
        kundali_engine = get_engine()
        # Step 1: Get full birth details from the minimal input
        full_req = minimal_to_kundali_request(min_req)

        # Step 2: Perform only the essential calculations from the engine
        jd = kundali_engine._datetime_to_jd(full_req.datetime, full_req.timezone)
        planets, lagna_info, _ = kundali_engine._calculate_positions_with_kerykeion(full_req)
        lagna_sign = lagna_info['sign']

        # Step 3: Prepare the data for the calculator
        planet_signs = {p_name: p_data.sign for p_name, p_data in planets.items()}

        # Step 4: Calculate the Ashtakavarga data directly
        ashtakavarga_data = calculate_ashtakavarga(planet_signs, lagna_sign)

        # Create minimal response dict
        response_dict = {
            "name": full_req.name,
            "ashtakavarga": ashtakavarga_data
        }

        # Only generate SVG if svg flag is True
        if svg:
            svg_string = create_ashtakavarga_svg(ashtakavarga_data, lagna_sign)
            response_dict["ashtakavarga_svg"] = svg_string

        return response_dict
    except Exception as e:
        logger.error(f"Error in /ashtakavarga-data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ashtakavarga-svg")
async def get_ashtakavarga_svg_standalone(min_req: MinimalKundliInput):
    """
    Calculates Ashtakavarga and returns the chart as a single SVG image.
    This endpoint is self-contained and performs only the necessary calculations.
    """
    try:
        kundali_engine = get_engine()
        # Step 1: Get full birth details from the minimal input
        full_req = minimal_to_kundali_request(min_req)

        # Step 2: Perform only the essential calculations from the engine
        jd = kundali_engine._datetime_to_jd(full_req.datetime, full_req.timezone)
        planets, lagna_info, _ = kundali_engine._calculate_positions_with_kerykeion(full_req)
        lagna_sign = lagna_info['sign']

        # Step 3: Prepare the data for the calculator
        planet_signs = {p_name: p_data.sign for p_name, p_data in planets.items()}

        # Step 4: Calculate the Ashtakavarga data directly
        ashtakavarga_data = calculate_ashtakavarga(planet_signs, lagna_sign)

        # Step 5: Generate the SVG string from the data
        svg_string = create_ashtakavarga_svg(ashtakavarga_data, lagna_sign)

        if not svg_string:
            raise HTTPException(status_code=500, detail="Ashtakavarga SVG string is empty.")

        # Step 6: Return the SVG image
        from fastapi.responses import Response
        return Response(content=svg_string, media_type="image/svg+xml")

    except Exception as e:
        logger.error(f"Error in /ashtakavarga-svg endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating Ashtakavarga SVG: {e}")


# =================== DOSHAS ENDPOINTS ===================

@router.post("/api/doshas")
def doshas(min_req: MinimalKundliInput):
    """
    Calculates and returns detailed Mangal Dosha and Kalasarpa Dosha information.
    """
    try:
        from api.services.kundli_service import _compute
        from models import MangalDoshaResult, KalasarpaDoshaResult
        from typing import Dict

        # Step 1: Compute the full KundaliResponse using your existing _compute function
        res = _compute(min_req)

        # If response is already a dict (translated), extract dosha data directly
        if isinstance(res, dict):
            return {
                "mangal_dosha": res.get("mangal_dosha", {}),
                "kalasarpa_dosha": res.get("kalasarpa_dosha", {})
            }

        # Step 2: Extract the necessary raw planet data from the 'res' (KundaliResponse object)
        planet_houses: Dict[str, int] = {}
        planet_signs: Dict[str, str] = {}
        planet_longitudes: Dict[str, float] = {}

        for planet_pos in res.planets:
            planet_name = planet_pos.planet
            planet_houses[planet_name] = planet_pos.house
            planet_signs[planet_name] = planet_pos.sign

            # To get absolute longitude (0-360)
            try:
                sign_index = SIGN_NAMES.index(planet_pos.sign)
                absolute_longitude = sign_index * 30 + planet_pos.degree
                planet_longitudes[planet_name] = absolute_longitude
            except ValueError:
                logger.warning(f"Could not find sign '{planet_pos.sign}' in sign_order for planet {planet_name}.")
                continue

        aspects = {}

        # Step 3: Calculate detailed dosha results using the enhanced functions
        mangal_dosha_detailed = calculate_mangal_dosha(
            planet_houses=planet_houses,
            planet_signs=planet_signs,
            planet_degrees=planet_longitudes,
            lagna_house=1,
            aspects=aspects
        )

        kalasarpa_dosha_detailed = calculate_kalasarpa_dosha(
            planet_longitudes=planet_longitudes,
            planet_houses=planet_houses
        )

        # Step 4: Return the detailed results, instantiating the Pydantic models
        return {
            "mangal_dosha": MangalDoshaResult(**mangal_dosha_detailed),
            "kalasarpa_dosha": KalasarpaDoshaResult(**kalasarpa_dosha_detailed)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /doshas endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# =================== MATCHING ENDPOINTS ===================

@router.post("/api/kundli-matching")
def get_kundli_matching(matching_request: KundliMatchingRequest):
    """
    Performs Ashtakoota Milan (Guna Milan) and Mangal Dosha compatibility check for a couple.

    This endpoint takes the birth details of a groom and a bride, generates their individual
    Kundlis, and then calculates their marital compatibility score out of 36 gunas.
    """
    try:
        from api.services.kundli_service import _compute

        # Step 1: Compute Kundali for both Groom and Bride (returns dict)
        logger.info(f"Computing Kundali for Groom: {matching_request.groom.name}")
        groom_kundali = _compute(matching_request.groom)

        logger.info(f"Computing Kundali for Bride: {matching_request.bride.name}")
        bride_kundali = _compute(matching_request.bride)

        # Step 2: Perform the matching using the dedicated matcher class
        logger.info("Performing Ashtakoota matching...")
        matcher = AshtakootaMatcher(groom_kundali, bride_kundali)
        match_result = matcher.calculate_all_kootas()

        logger.info(f"Matching complete. Score: {match_result['total_points_obtained']}/36")

        # Step 3: Return the structured response
        return KundliMatchingResponse(**match_result)

    except ValueError as ve:
        logger.error(f"Validation error during matching: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"An unexpected error occurred during matching: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the match.")


# =================== KP SYSTEM & BHAVA CHALIT ENDPOINTS ===================

@router.post("/api/kp-system")
async def generate_kp_system(req: MinimalKundliInput):
    """
    Generate Krishnamurti Paddhati (KP) system chart

    Returns KP house cusps, significators, star lords, sub-lords, and detailed analysis
    """
    try:
        kundali_engine = get_engine()
        # Convert to KundaliRequest
        kr = minimal_to_kundali_request(req)

        # Extract datetime components (kr.datetime is a datetime object)
        year = kr.datetime.year
        month = kr.datetime.month
        day = kr.datetime.day
        hour = kr.datetime.hour
        minute = kr.datetime.minute

        # Calculate KP system using Swiss Ephemeris
        kp_system = KPSystem()
        kp_results = kp_system.generate_kp_astrosage_format(
            year, month, day, hour, minute,
            kr.latitude, kr.longitude, kr.timezone
        )

        response = {
            "birth_details": {
                "name": req.name,
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth
            },
            "kp_system": kp_results,
            "status": "success"
        }

        # Translate response if language is not English
        lang = kr.language if kr.language else 'en'
        if lang and lang != 'en':
            translation_manager = get_translation_mgr()
            response = translation_manager.translate_full_response(response, lang)

        return response

    except Exception as e:
        logger.exception("Error generating KP system")
        raise HTTPException(status_code=500, detail=f"KP system calculation failed: {str(e)}")


@router.post("/api/bhava-chalit")
async def generate_bhava_chalit(
    req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG chart in response")
):
    """
    Generate Bhava Chalit (Vedic Equal House) chart

    Returns equal 30° houses with Lagna at center of House 1 (matches AstroTalk/AstroSage)

    IMPORTANT: This endpoint uses SWISS EPHEMERIS with LAHIRI Ayanamsa for accuracy.
    Other charts (Rasi, Navamsa, etc.) continue using their existing methods and are unaffected.

    Args:
        req: Minimal kundli input with birth details
        svg: If True, includes SVG chart in response. Default is False.
    """
    try:
        # Convert to KundaliRequest
        kr = minimal_to_kundali_request(req)

        # Extract datetime components (kr.datetime is a datetime object)
        year = kr.datetime.year
        month = kr.datetime.month
        day = kr.datetime.day
        hour = kr.datetime.hour
        minute = kr.datetime.minute

        # Calculate Vedic Bhava Chalit using Swiss Ephemeris with Lahiri Ayanamsa
        # This is ISOLATED from other calculations - does NOT affect kundali_engine
        bhava_system = BhavaChalitSystem()
        bhava_results = bhava_system.generate_vedic_bhava_chalit_chart_from_scratch(
            year, month, day, hour, minute,
            kr.latitude, kr.longitude, kr.timezone
        )

        # Calculate house strengths
        house_strengths = {}
        for house in range(1, 13):
            house_strengths[house] = bhava_system.get_house_strength(house, bhava_results['bhava_chart'])

        # Get Lagna longitude for SVG
        lagna_longitude = bhava_results['lagna_longitude']

        # Prepare response
        response = {
            "birth_details": {
                "name": req.name,
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth
            },
            "bhava_chalit": bhava_results,
            "house_strengths": house_strengths,
            "status": "success"
        }

        # Get language and translation manager
        translation_manager = get_translation_mgr()
        lang = kr.language if kr.language else 'en'

        # Translate response if language is not English
        if lang and lang != 'en':
            response = translation_manager.translate_full_response(response, lang)

        # Generate SVG if requested
        if svg:
            # Translate title for any language
            title = translation_manager.translate('charts.Bhava Chalit', lang, default="Bhava Chalit (Vedic)")

            bhava_chalit_svg = create_bhava_chalit_svg(
                title=title,
                bhava_chart=bhava_results['bhava_chart'],
                ascendant_longitude=lagna_longitude,
                lang=lang
            )
            response["bhava_chalit_svg"] = bhava_chalit_svg

        return response

    except Exception as e:
        logger.exception("Error generating Bhava Chalit chart")
        raise HTTPException(status_code=500, detail=f"Bhava Chalit calculation failed: {str(e)}")


@router.post("/api/kp-bhava-combined")
async def generate_kp_bhava_combined(
    req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG charts in response")
):
    """
    Generate both KP and Bhava Chalit systems in one response

    Returns comprehensive analysis with both house systems

    Args:
        req: Minimal kundli input with birth details
        svg: If True, includes SVG charts in response. Default is False.
    """
    try:
        kundali_engine = get_engine()
        # Convert to KundaliRequest
        kr = minimal_to_kundali_request(req)

        # Generate basic kundli to get planetary positions
        kundali_result = kundali_engine.generate_kundali(kr)

        # Extract required data
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        lagna_sign_index = kundali_engine.ZODIAC_SIGNS.index(kundali_result.lagna.sign)
        ascendant_longitude = lagna_sign_index * 30 + kundali_result.lagna.degree

        # Convert planet positions
        planets = {}
        for planet_data in kundali_result.planets:
            if hasattr(planet_data, '_abs_lon_sid'):
                planets[planet_data.planet] = planet_data
            else:
                # Create mock _abs_lon_sid from sign and degree
                sign_index = kundali_engine.ZODIAC_SIGNS.index(planet_data.sign)
                abs_longitude = sign_index * 30 + planet_data.degree
                planet_data._abs_lon_sid = abs_longitude
                planets[planet_data.planet] = planet_data

        # Extract datetime components (kr.datetime is a datetime object)
        year = kr.datetime.year
        month = kr.datetime.month
        day = kr.datetime.day
        hour = kr.datetime.hour
        minute = kr.datetime.minute

        combined_results = calculate_kp_and_bhava_chalit(year, month, day, hour, minute, kr.latitude, kr.longitude, kr.timezone)

        response = {
            "birth_details": {
                "name": req.name,
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth
            },
            **combined_results,
            "status": "success"
        }

        # Get language and translation manager
        translation_manager = get_translation_mgr()
        lang = kr.language if kr.language else 'en'

        # Translate response if language is not English
        if lang and lang != 'en':
            response = translation_manager.translate_full_response(response, lang)

        # Generate Bhava Chalit SVG if requested
        if svg:
            # Translate title for any language
            title = translation_manager.translate('charts.Bhava Chalit', lang, default="Bhava Chalit (Vedic)")

            # Get Bhava Chalit data from combined results
            # Note: combined_results is already merged into response
            bhava_data = response.get('bhava_chalit', {})
            bhava_chart = bhava_data.get('bhava_chart', {})

            bhava_chalit_svg = create_bhava_chalit_svg(
                title=title,
                bhava_chart=bhava_chart,
                ascendant_longitude=ascendant_longitude,
                lang=lang
            )
            response["bhava_chalit_svg"] = bhava_chalit_svg

        return response

    except Exception as e:
        logger.exception("Error generating combined KP and Bhava Chalit systems")
        raise HTTPException(status_code=500, detail=f"Combined system calculation failed: {str(e)}")


# =================== HOROSCOPE ENDPOINTS ===================

@router.get("/horoscope/daily/{sign}")
async def get_daily_structured_horoscope(
    sign: str,
    language: str = Query("en", description="Language code: en (English) or hi (Hindi)"),
    date_str: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format (defaults to today)")
):
    """
    Provides a high-quality, structured daily horoscope in the AstroTalk format,
    fusing accurate planetary data with rich, human-readable interpretations.

    Args:
        sign: Zodiac sign (Aries, Taurus, Gemini, etc.)
        language: Language code (en or hi)
    """
    sign = sign.capitalize()
    if sign not in ZODIAC_SIGNS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid zodiac sign. Must be one of: {', '.join(ZODIAC_SIGNS)}"
        )

    try:
        # Parse date parameter
        if date_str:
            try:
                horoscope_date = date.fromisoformat(date_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        else:
            horoscope_date = date.today()

        translation_manager = get_translation_mgr()
        # Call the narrative engine with language support
        prediction = generate_structured_horoscope(sign, date=horoscope_date, language=language)

        # Translate sign name if language is Hindi
        translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', language, default=sign)

        # Translate mood and color in lucky insights
        if language == 'hi' and 'lucky_insights' in prediction:
            lucky_insights = prediction['lucky_insights']
            if 'mood' in lucky_insights:
                lucky_insights['mood'] = translation_manager.translate(f'moods.{lucky_insights["mood"]}', language, default=lucky_insights['mood'])
            if 'lucky_color' in lucky_insights:
                lucky_insights['lucky_color'] = translation_manager.translate(f'colors.{lucky_insights["lucky_color"]}', language, default=lucky_insights['lucky_color'])

        return {
            "success": True,
            "sign": translated_sign,
            "date": horoscope_date.isoformat(),
            "language": language,
            "horoscope": prediction
        }
    except Exception as e:
        logger.error(f"Error in structured horoscope generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating the horoscope."
        )


@router.get("/horoscope/transits")
async def get_planetary_transits(
    date_str: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format (defaults to today)")
):
    """
    Returns actual planetary positions (sidereal, Lahiri ayanamsa) for a given date.
    Use this to feed real transit data to an LLM for rashifal generation.
    """
    if date_str:
        try:
            horoscope_date = date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        horoscope_date = date.today()

    try:
        import sys, os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'drik-panchanga'))
        from panchanga import gregorian_to_jd, Date as PanchangaDate
        from horoscope.planetary_horoscope_engine import PlanetaryHoroscopeEngine

        engine = PlanetaryHoroscopeEngine()
        date_struct = PanchangaDate(horoscope_date.year, horoscope_date.month, horoscope_date.day)
        jd = gregorian_to_jd(date_struct)
        positions = engine.get_planetary_positions(jd)
        aspects = engine.get_planetary_aspects(positions)

        return {
            "success": True,
            "date": horoscope_date.isoformat(),
            "planets": {
                name: {
                    "rashi": data["rashi"],
                    "degrees": round(data["degrees_in_sign"], 2),
                    "longitude": round(data["longitude"], 2),
                }
                for name, data in positions.items()
            },
            "aspects": aspects[:10],  # top 10 aspects
        }
    except Exception as e:
        logger.exception("Error fetching planetary transits")
        raise HTTPException(status_code=500, detail=str(e))


# =================== COMPLETE ENDPOINT ===================

@router.post("/api/complete")
def complete_kundli(
    min_req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG charts in response")
):
    """
    Unified endpoint that combines all kundli-related data in a single response.
    This endpoint combines the functionality of:
    - /api/birth-details: Returns birth information and panchanga details
    - /api/kundli: Returns core kundli data including planets, lagna, charts, and dasha
    - /api/charts: Returns all varga charts (divisional charts) and SVG representations (if svg=True)
    - /api/doshas: Returns Mangal Dosha and Kalasarpa Dosha analysis
    - /api/ashtakavarga-data: Returns Ashtakavarga data
    All data is computed once and returned in a structured format.

    Args:
        min_req: MinimalKundliInput containing birth details (name, date_of_birth,
                 time_of_birth, place_of_birth, latitude, longitude, timezone)
        svg: If True, includes SVG charts in response. Default is False.

    Returns:
        Dictionary containing all kundli data organized by section:
        - birth_details: Name, birth info, panchanga, enhanced panchanga
        - kundli: Core kundli data (lagna, planets, rasi chart, nakshatra, dasha, SVG charts if svg=True)
        - charts: All varga charts with SVG representations (if svg=True)
        - doshas: Mangal Dosha and Kalasarpa Dosha analysis
        - ashtakavarga: Ashtakavarga data
    Raises:
        HTTPException: If there's an error in calculation or processing
    """
    try:
        from api.services.kundli_service import _compute

        # Step 1: Compute the full KundaliResponse once
        # _compute will return a translated dict if language != 'en', or KundaliResponse/object if language == 'en'
        res = _compute(min_req, svg=svg)

        # Get language for translation
        kr = minimal_to_kundali_request(min_req)
        language = kr.language if kr.language else 'en'

        # Handle both dict (translated) and object (English) responses
        if isinstance(res, dict):
            # Response is already translated, build complete response from it
            return _build_complete_response_from_dict(res, language, svg=svg)
        else:
            # Response is in English, translate if needed and build complete response
            return _build_complete_response_from_object(res, language, svg=svg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/complete endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


def _build_complete_response_from_dict(res: dict, language: str, svg: bool = False):
    """
    Helper function to build the complete response structure from an already translated dict.

    Args:
        res: Translated response dictionary
        language: Language code for translations
        svg: If True, includes SVG charts in response. Default is False.
    """
    translation_manager = get_translation_mgr()

    # Step 1: Extract birth_details section
    birth_details_section = {
        "name": res.get("name"),
        "birth_info": res.get("birth_info", {}),
        "panchanga": res.get("panchanga", {}),
        "enhanced_panchanga": res.get("enhanced_panchanga", {}),
    }

    # Step 2: Extract kundli section
    lagna_data = res.get("lagna", {})
    if isinstance(lagna_data, dict):
        lagna_sign = lagna_data.get("sign")
        lagna_degree = lagna_data.get("degree")
    else:
        lagna_sign = res.get("lagna")
        lagna_degree = res.get("lagna_degree")

    kundli_section = {
        "name": res.get("name"),
        "lagna": lagna_sign,
        "lagna_degree": lagna_degree,
        "planets": res.get("planets", []),
        "rasi_chart": res.get("rasi_chart", {}),
        "moon_nakshatra": res.get("moon_nakshatra", {}),
        "vimshottari_dasha": res.get("vimshottari_dasha", []),
        "current_dasha_detailed": res.get("current_dasha_detailed", {}),
    }

    # Only include SVGs if svg flag is True and they exist
    if svg:
        if "rasi_chart_svg" in res:
            kundli_section["rasi_chart_svg"] = res.get("rasi_chart_svg")
        if "navamsa_chart_svg" in res:
            kundli_section["navamsa_chart_svg"] = res.get("navamsa_chart_svg")

    # Step 3: Extract charts section
    charts_section = {}
    if svg:
        if "rasi_chart_svg" in res:
            charts_section["rasi_chart_svg"] = res.get("rasi_chart_svg")
        if "navamsa_chart_svg" in res:
            charts_section["navamsa_chart_svg"] = res.get("navamsa_chart_svg")

    # Step 4: Extract doshas section
    doshas_section = {
        "mangal_dosha": res.get("mangal_dosha", {}),
        "kalasarpa_dosha": res.get("kalasarpa_dosha", {})
    }

    # Step 5: Extract ashtakavarga section
    ashtakavarga_section = {
        "ashtakavarga": res.get("ashtakavarga", {})
    }

    # Step 6: Combine all sections into unified response
    complete_response = {
        "birth_details": birth_details_section,
        "kundli": kundli_section,
        "charts": charts_section,
        "doshas": doshas_section,
        "ashtakavarga": ashtakavarga_section
    }

    return complete_response


def _build_complete_response_from_object(res, language: str, svg: bool = False):
    """
    Helper function to build the complete response structure from a KundaliResponse object.

    Args:
        res: KundaliResponse object
        language: Language code for translations
        svg: If True, includes SVG charts in response. Default is False.
    """
    translation_manager = get_translation_mgr()

    # Step 1: Extract birth_details section
    birth_details_section = {
        "name": res.name,
        "birth_info": res.birth_info,
        "panchanga": res.panchanga.model_dump() if res.panchanga else {},
        "enhanced_panchanga": res.enhanced_panchanga.model_dump() if res.enhanced_panchanga else {},
    }

    # Step 2: Extract kundli section
    kundli_section = {
        "name": res.name,
        "lagna": res.lagna.sign,
        "lagna_degree": res.lagna.degree,
        "planets": [p.model_dump() for p in res.planets],
        "rasi_chart": res.rasi_chart,
        "moon_nakshatra": res.moon_nakshatra.model_dump() if res.moon_nakshatra else {},
        "vimshottari_dasha": [d.model_dump() for d in res.vimshottari_dasha],
        "current_dasha_detailed": res.current_dasha_detailed.model_dump() if res.current_dasha_detailed else {},
    }

    # Only include SVGs if svg flag is True
    if svg:
        kundli_section["rasi_chart_svg"] = res.rasi_chart_svg
        kundli_section["navamsa_chart_svg"] = res.navamsa_chart_svg

    # Step 3: Extract charts section
    charts_section = {}
    if svg:
        charts_section = {
            "rasi_chart_svg": res.rasi_chart_svg,
            "navamsa_chart_svg": res.navamsa_chart_svg,
        }

    # Step 4: Extract doshas section
    doshas_section = {
        "mangal_dosha": res.mangal_dosha.model_dump() if res.mangal_dosha else {},
        "kalasarpa_dosha": res.kalasarpa_dosha.model_dump() if res.kalasarpa_dosha else {}
    }

    # Step 5: Extract ashtakavarga section
    ashtakavarga_section = {
        "ashtakavarga": res.ashtakavarga if res.ashtakavarga else {}
    }

    # Step 6: Apply translation if language is not English
    if language and language != 'en':
        # Translate birth_details section
        birth_details_section = translation_manager.translate_full_response(birth_details_section, language)

        # Translate kundli section (planets, signs, etc.)
        kundli_section = translation_manager.translate_full_response(kundli_section, language)

        # Translate doshas section
        doshas_section = translation_manager.translate_full_response(doshas_section, language)

    # Step 7: Combine all sections into unified response
    complete_response = {
        "birth_details": birth_details_section,
        "kundli": kundli_section,
        "charts": charts_section,
        "doshas": doshas_section,
        "ashtakavarga": ashtakavarga_section
    }

    return complete_response
