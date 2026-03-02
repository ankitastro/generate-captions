"""
Kundli core endpoints - main kundli generation, birth details, yogas, interpretation, report
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from models import KundaliRequest, KundaliResponse, MinimalKundliInput
from api.services.kundli_service import (
    _compute, _compute_birth_details, _compute_yogas,
    get_engine, get_translation_mgr
)
from core.interpretation_engine import InterpretationEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-kundli")
def generate_kundli(
    min_req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG charts in response")
):
    """
    Generate complete Kundali (Vedic horoscope)

    Main endpoint that generates a complete Kundali with all calculations including:
    - Planetary positions in signs and houses
    - Rasi chart (birth chart)
    - Moon's nakshatra and pada
    - Current Vimshottari Dasha
    - Panchanga details
    - Navamsa chart
    - Yogas
    - Doshas
    - Ashtakavarga

    Args:
        min_req: Minimal kundli input with birth details
        svg: If True, includes SVG charts in response. Default is False.
    """
    return _compute(min_req, svg=svg)


@router.post("/kundali/basic")
async def kundali_basic(request: KundaliRequest):
    """
    Lightweight Kundali summary: birth, lagna, Moon nakshatra, current dasha, panchanga summary.
    Same request body as /generate-kundali.
    """
    try:
        kundali_engine = get_engine()
        kd = kundali_engine.generate_kundali(request)

        # Build lightweight response
        resp = {
            "name": kd.name,
            "birth_info": kd.birth_info,
            "lagna": kd.lagna,
            "lagna_degree": kd.lagna_degree,
            "moon_nakshatra": kd.moon_nakshatra.dict() if kd.moon_nakshatra else None,
            "current_dasha": kd.current_dasha.dict() if kd.current_dasha else None,
            "panchanga": {
                "tithi": kd.panchanga.tithi,
                "nakshatra": kd.panchanga.nakshatra,
                "vaara": kd.panchanga.vaara,
                "sunrise": kd.panchanga.sunrise,
                "sunset": kd.panchanga.sunset,
            } if kd.panchanga else None,
            "timestamp": datetime.now().isoformat(),
        }
        return resp

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /kundali/basic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/birth-details")
def birth_details(min_req: MinimalKundliInput):
    """
    Get birth details and panchanga information

    Returns:
        - Name and birth info
        - Basic panchanga (tithi, nakshatra, yoga, karana, vaara, masa, ritu, samvatsara)
        - Enhanced panchanga with additional details
    """
    res = _compute_birth_details(min_req)
    translation_manager = get_translation_mgr()

    # Handle both dict (translated) and object (English) responses
    if isinstance(res, dict):
        # Apply additional panchanga translations if language is Hindi
        if min_req.language and min_req.language == 'hi':
            panchanga = res.get("panchanga", {})
            enhanced_panchanga = res.get("enhanced_panchanga", {})

            # Translate basic panchanga fields
            if panchanga:
                translated_panchanga = panchanga.copy()
                translated_panchanga['tithi'] = translation_manager.translate(f'tithi_names.{panchanga.get("tithi", "")}', min_req.language, default=panchanga.get("tithi", ""))
                translated_panchanga['nakshatra'] = translation_manager.translate(f'nakshatras.{panchanga.get("nakshatra", "")}', min_req.language, default=panchanga.get("nakshatra", ""))
                translated_panchanga['yoga'] = translation_manager.translate(f'yoga_types.{panchanga.get("yoga", "")}', min_req.language, default=panchanga.get("yoga", ""))
                translated_panchanga['karana'] = translation_manager.translate(f'karana_types.{panchanga.get("karana", "")}', min_req.language, default=panchanga.get("karana", ""))
                translated_panchanga['vaara'] = translation_manager.translate(f'vaara_names.{panchanga.get("vaara", "")}', min_req.language, default=panchanga.get("vaara", ""))
                translated_panchanga['masa'] = translation_manager.translate(f'masa_names.{panchanga.get("masa", "")}', min_req.language, default=panchanga.get("masa", ""))
                translated_panchanga['ritu'] = translation_manager.translate(f'ritu_names.{panchanga.get("ritu", "")}', min_req.language, default=panchanga.get("ritu", ""))
                # Handle samvatsara - extract the actual name if it contains "Samvatsara"
                samvatsara_val = panchanga.get("samvatsara", "")
                if "Samvatsara" in str(samvatsara_val):
                    # If it's in format "Samvatsara 39", try to get the name from enhanced_panchanga
                    if enhanced_panchanga and 'samvatsara' in enhanced_panchanga and isinstance(enhanced_panchanga['samvatsara'], dict):
                        samvatsara_name = enhanced_panchanga['samvatsara'].get('name', '')
                        translated_panchanga['samvatsara'] = translation_manager.translate(f'samvatsara_names.{samvatsara_name}', min_req.language, default=samvatsara_name)
                    else:
                        translated_panchanga['samvatsara'] = samvatsara_val
                else:
                    translated_panchanga['samvatsara'] = translation_manager.translate(f'samvatsara_names.{samvatsara_val}', min_req.language, default=samvatsara_val)
                panchanga = translated_panchanga

            # Translate enhanced panchanga fields
            if enhanced_panchanga:
                translated_enhanced = {}
                for key, value in enhanced_panchanga.items():
                    if isinstance(value, dict) and 'name' in value:
                        translated_value = value.copy()
                        original_name = value['name']

                        if key == 'yoga':
                            translated_value['name'] = translation_manager.translate(f'yoga_types.{original_name}', min_req.language, default=original_name)
                        elif key == 'karana':
                            translated_value['name'] = translation_manager.translate(f'karana_types.{original_name}', min_req.language, default=original_name)
                        elif key == 'nakshatra':
                            translated_value['name'] = translation_manager.translate(f'nakshatras.{original_name}', min_req.language, default=original_name)
                        elif key == 'samvatsara':
                            translated_value['name'] = translation_manager.translate(f'samvatsara_names.{original_name}', min_req.language, default=original_name)
                        elif key == 'masa' and 'type' in value:
                            translated_value['type'] = translation_manager.translate(f'masa_types.{value["type"]}', min_req.language, default=value["type"])
                        elif key == 'vaara' and 'lord' in value:
                            translated_value['lord'] = translation_manager.translate(f'planets.{value["lord"]}', min_req.language, default=value["lord"])

                        translated_enhanced[key] = translated_value
                    else:
                        translated_enhanced[key] = value
                enhanced_panchanga = translated_enhanced

            return {
                "name": res.get("name"),
                "birth_info": res.get("birth_info", {}),
                "panchanga": panchanga,
                "enhanced_panchanga": enhanced_panchanga,
            }
        else:
            return {
                "name": res.get("name"),
                "birth_info": res.get("birth_info", {}),
                "panchanga": res.get("panchanga", {}),
                "enhanced_panchanga": res.get("enhanced_panchanga", {}),
            }

    # English response handling
    if min_req.language and min_req.language != 'en':
        return {
            "name": res.name,
            "birth_info": res.birth_info,
            "panchanga": res.panchanga,
            "enhanced_panchanga": res.enhanced_panchanga,
        }
    else:
        return {
            "name": res.name,
            "birth_info": res.birth_info,
            "panchanga": res.panchanga,
            "enhanced_panchanga": res.enhanced_panchanga,
        }


@router.post("/api/kundli")
def kundli_core(
    min_req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG charts in response")
):
    """
    Get core Kundli data including planets, lagna, charts, dasha

    Args:
        min_req: Minimal kundli input with birth details
        svg: If True, includes SVG charts in response. Default is False.

    Returns:
        - Name, lagna, lagna degree
        - Planets with positions
        - Rasi chart
        - Moon nakshatra
        - Vimshottari dasha
        - Current dasha detailed
        - Rasi and Navamsa SVG charts (if svg=True)
    """
    res = _compute(min_req, svg=svg)

    # If response is already a dict (either translated or svg=False), return selected fields
    if isinstance(res, dict):
        response = {
            "name": res.get("name"),
            "lagna": res.get("lagna", {}).get("sign") if isinstance(res.get("lagna"), dict) else res.get("lagna"),
            "lagna_degree": res.get("lagna", {}).get("degree") if isinstance(res.get("lagna"), dict) else res.get("lagna_degree"),
            "planets": res.get("planets", []),
            "rasi_chart": res.get("rasi_chart", {}),
            "moon_nakshatra": res.get("moon_nakshatra", {}),
            "vimshottari_dasha": res.get("vimshottari_dasha", []),
            "current_dasha_detailed": res.get("current_dasha_detailed", {}),
        }
        # Only include SVGs if svg flag is True and they exist in response
        if svg and "rasi_chart_svg" in res:
            response["rasi_chart_svg"] = res.get("rasi_chart_svg")
            response["navamsa_chart_svg"] = res.get("navamsa_chart_svg")
        return response

    # English response (KundaliResponse object) - only when svg=True
    response = {
        "name": res.name,
        "lagna": res.lagna.sign,
        "lagna_degree": res.lagna.degree,
        "planets": [p.model_dump() for p in res.planets],
        "rasi_chart": res.rasi_chart,
        "moon_nakshatra": res.moon_nakshatra,
        "vimshottari_dasha": [d.model_dump() for d in res.vimshottari_dasha],
        "current_dasha_detailed": res.current_dasha_detailed,
    }
    # Only include SVGs if svg flag is True (should always be True here since object is only returned when svg=True)
    if svg:
        response["rasi_chart_svg"] = res.rasi_chart_svg
        response["navamsa_chart_svg"] = res.navamsa_chart_svg
    return response


@router.post("/api/yogas")
def yogas(min_req: MinimalKundliInput):
    """
    Get detected yogas in the Kundali

    Returns:
        - List of detected yogas with descriptions
        - Yoga summary with strength categories
    """
    res = _compute_yogas(min_req)

    # Handle both dict (translated) and object (English) responses
    if isinstance(res, dict):
        return {
            "detected_yogas": res.get("detected_yogas", []),
            "yoga_summary": res.get("yoga_summary", {}),
        }

    # English response (KundaliResponse object)
    return {
        "detected_yogas": [y.model_dump() for y in res.detected_yogas],
        "yoga_summary": res.yoga_summary,
    }


@router.post("/api/interpretation")
def interpretation(min_req: MinimalKundliInput):
    """
    Get human-readable interpretation of the Kundali

    Returns:
        - Name
        - Interpretation text
    """
    res = _compute(min_req)

    # Handle both dict (translated) and object (English) responses
    if isinstance(res, dict):
        return {
            "name": res.get("name"),
            "interpretation": res.get("interpretation"),
        }

    # English response (KundaliResponse object)
    return {
        "name": res.name,
        "interpretation": res.interpretation,
    }


@router.post("/api/report")
def report(min_req: MinimalKundliInput):
    """
    Get detailed Kundali report

    Returns:
        - Report text
    """
    res = _compute(min_req)

    # Handle both dict (translated) and object (English) responses
    if isinstance(res, dict):
        return {
            "report": res.get("report"),
        }

    # English response (KundaliResponse object)
    return {
        "report": res.report,
    }
