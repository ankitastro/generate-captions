"""
FastAPI application for Kundali Generation Service
"""

import hashlib
from core import varga_engine
from fastapi import FastAPI, HTTPException, Request, Query, Body,APIRouter
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
import traceback
import logging
import os
from jinja2 import Environment, FileSystemLoader
from typing import Any, Dict, Optional
from core.varga_engine import get_all_varga_charts, get_all_varga_charts_detailed, VARGA_NAMES

# Import our models and engine
from models import KundaliRequest, KundaliResponse, ErrorResponse, PlanetPosition,MinimalKundliInput,KundliMatchingRequest,KundliMatchingResponse
from ashtakoota_matcher import AshtakootaMatcher
from kundali_engine import KundaliEngine
from core.interpretation_engine import InterpretationEngine
from api.input_normalizer import minimal_to_kundali_request
from fastapi.responses import Response
import svg_chart_generator
from ashtavarga import calculate_ashtakavarga
from svg_chart_generator import create_ashtakavarga_svg

from dosha_analyzer import calculate_mangal_dosha, calculate_kalasarpa_dosha
from models import MinimalKundliInput, MangalDoshaResult, KalasarpaDoshaResult, KundaliResponse, PlanetPosition

from horoscope.narrative_horoscope import generate_structured_horoscope, ZODIAC_SIGNS

SIGN_NAMES = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]



# Import horoscope engines
from horoscope import (
    generate_horoscope,
    generate_planetary_horoscope,
    ZODIAC_SIGNS,
    VALID_SCOPES
)

# Import KP and Bhava Chalit systems
from kp_system import calculate_kp_and_bhava_chalit, KPSystem, BhavaChalitSystem

# Import translation manager
from translation_manager import get_translation_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Kundali Generation Service",
    description="A comprehensive Vedic astrology service for generating Kundali (birth charts) using drik-panchanga",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
 )


router = APIRouter(prefix="/api/v1/kundali")
# Initialize the Kundali Engine
kundali_engine = KundaliEngine()

# Initialize Translation Manager
translation_manager = get_translation_manager()

KUNDALI_CACHE: Dict[str, KundaliResponse] = {}

# Setup Jinja2 templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(templates_dir))


def _compute(req: MinimalKundliInput):
    try:
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info("Computing Kundali for %s (lat=%.4f lon=%.4f tz=%s lang=%s)",
                   kr.name, kr.latitude, kr.longitude, kr.timezone, kr.language)

        # Generate Kundali
        kundali_response = kundali_engine.generate_kundali(kr)

        # Translate response if language is not English
        if kr.language and kr.language != 'en':
            response_dict = kundali_response.dict()
            translated_dict = translation_manager.translate_full_response(response_dict, kr.language)
            # Return translated dict directly (FastAPI will serialize it)
            return translated_dict

        return kundali_response
    except Exception as e:
        logger.exception("Error computing Kundali")
        raise HTTPException(status_code=500, detail=str(e))

def _compute_birth_details(req: MinimalKundliInput):
    """Optimized calculation for birth-details endpoint - only panchanga + enhanced_panchanga"""
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

        # Create minimal response object (use original request fields)
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
    """Optimized calculation for yogas endpoint - only yoga detection"""
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
    """Optimized calculation for ashtakavarga-data endpoint - only ashtakavarga"""
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
    """Optimized calculation for charts endpoint - only varga charts + SVGs"""
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

def _make_kundali_id(req: KundaliRequest) -> str:
    """
    Create a deterministic ID from name, datetime, lat, lon, tz.
    """
    base = f"{req.name}|{req.datetime.isoformat()}|{req.latitude:.6f}|{req.longitude:.6f}|{req.timezone}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

def deg_to_dms_str(deg: float) -> str:
    d = int(deg)
    m_float = abs(deg - d) * 60.0
    m = int(m_float)
    s = round((m_float - m) * 60.0)
    # Handle rollover (59m 60s -> +1m etc.)
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        if deg >= 0:
            d += 1
        else:
            d -= 1
    sign_char = ""  # we report signed by numeric sign outside, not prefix
    return f"{sign_char}{d}°{m:02d}′{s:02d}″"


def _augment_planet_positions(planets):
    """
    Accepts list[PlanetPosition] or list[dict].
    Returns list of dicts with added 'degree_dms' & 'full_degree' (sign+deg).
    """
    out = []
    for p in planets:
        if isinstance(p, PlanetPosition):
            planet = p.planet
            sign = p.sign
            deg = p.degree
            retro = p.retrograde
            house = p.house
            sign_lord = p.sign_lord
            nakshatra_lord = p.nakshatra_lord
            nakshatra_name = p.nakshatra_name
            planet_awasta = p.planet_awasta
            status = p.status

        else:
            planet = p["planet"]
            sign = p["sign"]
            deg = p["degree"]
            retro = p["retrograde"]
            house = p["house"]
            sign_lord = p["sign_lord"]
            nakshatra_lord = p["nakshatra_lord"]
            nakshatra_name = p["nakshatra_name"]
            planet_awasta = p["planet_awasta"]
            status = p.get("status")


        dms = deg_to_dms_str(deg)
        full_deg = f"{dms} {sign}"
        out.append({
            "planet": planet,
            "sign": sign,
            "degree": deg,
            "degree_dms": dms,
            "full_degree": full_deg,
            "retrograde": retro,
            "house": house,
            "sign_lord": sign_lord,
            "nakshatra_lord": nakshatra_lord,
            "nakshatra_name": nakshatra_name,
            "planet_awasta": planet_awasta,
            "status": status,
        })
    return out

def _augment_lagna(sign: str, deg: float) -> Dict[str, Any]:
    return {
        "sign": sign,
        "degree": deg,
        "degree_dms": deg_to_dms_str(deg),
        "full_degree": f"{deg_to_dms_str(deg)} {sign}",
    }

def _response_to_dict(resp: KundaliResponse) -> Dict[str, Any]:
    """
    Convert full KundaliResponse to dict and augment DMS for degrees.
    """
    data = resp.dict()
    data["lagna_info"] = _augment_lagna(resp.lagna, resp.lagna_degree)
    data["planets_aug"] = _augment_planet_positions(resp.planets)
    return data

def _compute_kundali_data(req: KundaliRequest):
    """
    Compute full Kundali once; raise HTTPException on invalid input.
    Mirrors validation used in /generate-kundali.
    """
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    if not (-90 <= req.latitude <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")

    if not (-180 <= req.longitude <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")

    if req.datetime > datetime.now():
        raise HTTPException(status_code=400, detail="Birth date cannot be in the future")

    return kundali_engine.generate_kundali(req)

def _compute_kundali(req: KundaliRequest) -> KundaliResponse:
    """
    Wrapper to call engine.generate_kundali and catch errors.
    """
    try:
        logger.info("Computing Kundali for %s", req.name)
        return kundali_engine.generate_kundali(req)
    except Exception as e:
        logger.exception("Error computing Kundali: %s", e)
        raise HTTPException(status_code=500, detail=f"Error computing Kundali: {e}")

@router.post("/generate-kundli")
def generate_kundli(min_req: MinimalKundliInput):
    return _compute(min_req)


@router.post("/kundali/basic")
async def kundali_basic(request: KundaliRequest):
    """
    Lightweight Kundali summary: birth, lagna, Moon nakshatra, current dasha, panchanga summary.
    Same request body as /generate-kundali.
    """
    try:
        kd = _compute_kundali_data(request)

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


@router.get("/")
async def root():
    return {
        "message": "Kundali Modular API running.",
        "version": "2.0.0",
        "endpoints": {
            "generate": "POST /generate-kundli",
            "birth_details": "GET /birth_details/{kundali_id}",
            "kundli": "GET /kundli/{kundali_id}",
            "charts": "GET /charts/{kundali_id}",
            "yogas": "GET /yogas/{kundali_id}",
            "interpretation": "GET /interpretation/{kundali_id}",
            "on_demand": {
                "birth_details": "POST /birth_details",
                "kundli": "POST /kundli",
                "charts": "POST /charts",
                "yogas": "POST /yogas",
                "interpretation": "POST /interpretation",
            },
        },
    }

@router.get("/form", response_class=HTMLResponse)
async def kundali_form():
    """
    Serve the Kundali generation form page

    This endpoint serves an HTML form where users can enter their birth details
    and generate a Kundali report directly from their browser.

    Returns:
        HTMLResponse: Interactive form page for Kundali generation
    """
    try:
        template = jinja_env.get_template("kundali_form.html")
        html_content = template.render()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Error serving form page: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error loading form page"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "kundali-generation-service"
    }

@router.get("/languages")
async def get_available_languages():
    """Get list of supported languages for API responses"""
    return {
        "success": True,
        "supported_languages": translation_manager.get_available_languages(),
        "default_language": "en",
        "usage": "Add 'language' parameter to your request body with values: en, hi, kn, mr, te, ta"
    }

def _get_cached_or_404(kundali_id: str) -> KundaliResponse:
    resp = KUNDALI_CACHE.get(kundali_id)
    if not resp:
        raise HTTPException(status_code=404, detail=f"Kundali ID '{kundali_id}' not found. Regenerate via POST /generate-kundli.")
    return resp


@router.post("/api/birth-details")
def birth_details(min_req: MinimalKundliInput):
    res = _compute_birth_details(min_req)

    # Handle both dict (translated) and object (English) responses
    if isinstance(res, dict):
        # Apply additional panchanga translations if language is Hindi
        if min_req.language and min_req.language == 'hi':
            panchanga = res.get("panchanga", {})
            enhanced_panchanga = res.get("enhanced_panchanga", {})

            # Translate basic panchanga fields (they might still be in English)
            if panchanga:
                translated_panchanga = panchanga.copy()
                translated_panchanga['tithi'] = translation_manager.translate(f'tithi_names.{panchanga.get("tithi", "")}', min_req.language, default=panchanga.get("tithi", ""))
                translated_panchanga['yoga'] = translation_manager.translate(f'yoga_types.{panchanga.get("yoga", "")}', min_req.language, default=panchanga.get("yoga", ""))
                translated_panchanga['karana'] = translation_manager.translate(f'karana_types.{panchanga.get("karana", "")}', min_req.language, default=panchanga.get("karana", ""))
                translated_panchanga['vaara'] = translation_manager.translate(f'vaara_names.{panchanga.get("vaara", "")}', min_req.language, default=panchanga.get("vaara", ""))
                translated_panchanga['masa'] = translation_manager.translate(f'masa_names.{panchanga.get("masa", "")}', min_req.language, default=panchanga.get("masa", ""))
                translated_panchanga['ritu'] = translation_manager.translate(f'ritu_names.{panchanga.get("ritu", "")}', min_req.language, default=panchanga.get("ritu", ""))
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
                        elif key == 'masa' and 'type' in value:
                            translated_value['type'] = translation_manager.translate(f'masa_types.{value["type"]}', min_req.language, default=value["type"])

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
            # Already translated response (not Hindi)
            return {
                "name": res.get("name"),
                "birth_info": res.get("birth_info", {}),
                "panchanga": res.get("panchanga", {}),
                "enhanced_panchanga": res.get("enhanced_panchanga", {}),
            }

    # English response (KundaliResponse object) - translate if needed
    if min_req.language and min_req.language != 'en':
        # Translate basic panchanga fields
        translated_panchanga = res.panchanga.copy()
        translated_panchanga['tithi'] = translation_manager.translate(f'tithi_names.{res.panchanga.get("tithi", "")}', min_req.language, default=res.panchanga.get("tithi", ""))
        translated_panchanga['yoga'] = translation_manager.translate(f'yoga_types.{res.panchanga.get("yoga", "")}', min_req.language, default=res.panchanga.get("yoga", ""))
        translated_panchanga['karana'] = translation_manager.translate(f'karana_types.{res.panchanga.get("karana", "")}', min_req.language, default=res.panchanga.get("karana", ""))
        translated_panchanga['vaara'] = translation_manager.translate(f'vaara_names.{res.panchanga.get("vaara", "")}', min_req.language, default=res.panchanga.get("vaara", ""))
        translated_panchanga['masa'] = translation_manager.translate(f'masa_names.{res.panchanga.get("masa", "")}', min_req.language, default=res.panchanga.get("masa", ""))
        translated_panchanga['ritu'] = translation_manager.translate(f'ritu_names.{res.panchanga.get("ritu", "")}', min_req.language, default=res.panchanga.get("ritu", ""))

        # Translate enhanced panchanga fields
        translated_enhanced = {}
        for key, value in res.enhanced_panchanga.items():
            if isinstance(value, dict) and 'name' in value:
                translated_value = value.copy()
                original_name = value['name']

                if key == 'tithi':
                    translated_value['name'] = translation_manager.translate(f'tithi_names.{original_name}', min_req.language, default=original_name)
                elif key == 'yoga':
                    translated_value['name'] = translation_manager.translate(f'yoga_types.{original_name}', min_req.language, default=original_name)
                elif key == 'karana':
                    translated_value['name'] = translation_manager.translate(f'karana_types.{original_name}', min_req.language, default=original_name)
                elif key == 'vaara':
                    translated_value['name'] = translation_manager.translate(f'vaara_names.{original_name}', min_req.language, default=original_name)
                elif key == 'masa':
                    translated_value['name'] = translation_manager.translate(f'masa_names.{original_name}', min_req.language, default=original_name)
                    if 'type' in value:
                        translated_value['type'] = translation_manager.translate(f'masa_types.{value["type"]}', min_req.language, default=value["type"])
                elif key == 'ritu':
                    translated_value['name'] = translation_manager.translate(f'ritu_names.{original_name}', min_req.language, default=original_name)

                translated_enhanced[key] = translated_value
            else:
                translated_enhanced[key] = value

        return {
            "name": res.name,
            "birth_info": res.birth_info,
            "panchanga": translated_panchanga,
            "enhanced_panchanga": translated_enhanced,
        }
    else:
        # Original English response
        return {
            "name": res.name,
            "birth_info": res.birth_info,
            "panchanga": res.panchanga,
            "enhanced_panchanga": res.enhanced_panchanga,
        }
@router.post("/api/kundli")
def kundli_core(min_req: MinimalKundliInput):
    res = _compute(min_req)

    # If response is already a dict (translated), return it with selected fields
    if isinstance(res, dict):
        return {
            "name": res.get("name"),
            "lagna": res.get("lagna", {}).get("sign"),
            "lagna_degree": res.get("lagna", {}).get("degree"),
            "planets": res.get("planets", []),
            "rasi_chart": res.get("rasi_chart", {}),
            "moon_nakshatra": res.get("moon_nakshatra", {}),
            "vimshottari_dasha": res.get("vimshottari_dasha", []),
            "current_dasha_detailed": res.get("current_dasha_detailed", {}),
            "rasi_chart_svg": res.get("rasi_chart_svg"),
            "navamsa_chart_svg": res.get("navamsa_chart_svg"),
        }

    # English response (KundaliResponse object)
    return {
        "name": res.name,
        "lagna": res.lagna.sign,
        "lagna_degree": res.lagna.degree,
        "planets": [p.model_dump() for p in res.planets],
        "rasi_chart": res.rasi_chart,
        "moon_nakshatra": res.moon_nakshatra,
        "vimshottari_dasha": [d.model_dump() for d in res.vimshottari_dasha],
        "current_dasha_detailed": res.current_dasha_detailed,
        "rasi_chart_svg": res.rasi_chart_svg,
        "navamsa_chart_svg": res.navamsa_chart_svg,
    }

@router.post("/api/charts")
def charts(min_req: MinimalKundliInput):
    try:
        # For charts endpoint, we need planetary positions but can optimize by not running full engine
        kr: KundaliRequest = minimal_to_kundali_request(min_req)
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)

        # Generate basic charts needed for this endpoint
        rasi_chart = kundali_engine._generate_rasi_chart(planets, lagna_info['sign'])

        # Update planetary positions with house information (needed for SVG)
        updated_planets = kundali_engine._update_planetary_houses(planets, lagna_info['sign'])

        # Generate SVGs using the same method as original
        chart_lang = kr.language if kr.language else 'en'
        translation_manager = get_translation_manager()

        # Rasi chart SVG
        rasi_chart_title = translation_manager.translate('charts.Rasi Chart', chart_lang, default="Rasi (D1)")
        rasi_svg_data = kundali_engine._prepare_rasi_data_for_svg(updated_planets, lagna_info, lang=chart_lang)
        rasi_chart_svg = svg_chart_generator.create_single_chart_svg(rasi_chart_title, rasi_svg_data, lang=chart_lang)

        # Navamsa chart SVG
        navamsa_chart = kundali_engine.divisional_charts.get_navamsa_chart(planets, lagna_info)
        navamsa_degree_map = {p.planet: p.degree for p in updated_planets}
        navamsa_degree_map['Lagna'] = lagna_info['degree']
        for p_name, p_info in navamsa_chart['navamsa_positions'].items():
            navamsa_degree_map[p_name] = p_info['degree']

        navamsa_chart_title = translation_manager.translate('charts.Navamsa Chart', chart_lang, default="Navamsa (D9)")
        navamsa_svg_data = kundali_engine._prepare_navamsa_data_for_svg(
            navamsa_chart['navamsa_chart'],
            navamsa_chart['navamsa_lagna'],
            navamsa_degree_map,
            lang=chart_lang
        )
        navamsa_chart_svg = svg_chart_generator.create_single_chart_svg(navamsa_chart_title, navamsa_svg_data, lang=chart_lang)

        # Convert planets to format needed for varga calculations
        planet_degrees = {}
        for planet_name, planet_data in planets.items():
            sign_idx = SIGN_NAMES.index(planet_data.sign) if planet_data.sign in SIGN_NAMES else 0
            planet_degrees[planet_name] = sign_idx * 30 + planet_data.degree
        planet_degrees['Lagna'] = lagna_info['abs_longitude']

        # Prepare degree map for SVG
        degree_map_for_svg = {planet_name: planet_data.degree for planet_name, planet_data in planets.items()}
        degree_map_for_svg['Lagna'] = lagna_info['degree']

        # 2. Calculate all Varga charts
        vargas_to_calc = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 60]
        all_varga_charts = get_all_varga_charts(planet_degrees, vargas_to_calc)

        # 2b. Calculate detailed varga charts with planet positions
        all_varga_charts_detailed = get_all_varga_charts_detailed(planet_degrees, vargas_to_calc)

        # 4. Generate the dictionary of individual SVGs (with language support)
        varga_svg_dictionary = svg_chart_generator.create_all_varga_svgs(
            all_varga_data=all_varga_charts,
            varga_names=VARGA_NAMES,
            degree_map=degree_map_for_svg,
            lang=min_req.language if min_req.language else 'en'
        )

        # The JSON for the raw data, can be useful for the frontend (backward compatibility)
        major_varga_charts = {
           VARGA_NAMES.get(v, f"D{v}"): chart
           for v, chart in all_varga_charts.items()
        }

        # Translate major varga charts if language is not English
        if min_req.language and min_req.language != 'en':
            translated_major_varga_charts = {}
            for chart_name, chart_data in major_varga_charts.items():
                translated_chart = {}
                for sign, planets_list in chart_data.items():
                    # Translate sign name
                    translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', min_req.language, default=sign)

                    # Translate planet names
                    translated_planets = []
                    for planet_name in planets_list:
                        translated_planet = translation_manager.translate(f'planets.{planet_name}', min_req.language, default=planet_name)
                        translated_planets.append(translated_planet)

                    translated_chart[translated_sign] = translated_planets
                # Translate chart name
                translated_chart_name = translation_manager.translate(f'charts.{chart_name}', min_req.language, default=chart_name)
                translated_major_varga_charts[translated_chart_name] = translated_chart
            major_varga_charts_named = translated_major_varga_charts
        else:
            major_varga_charts_named = major_varga_charts

        # Detailed varga charts with planet info (new format for app team)
        # If language is not English, translate planet names in varga charts
        detailed_varga_charts_named = {}
        for v, chart in all_varga_charts_detailed.items():
            chart_name = VARGA_NAMES.get(v, f"D{v}")
            chart_data = {"chart_name": chart_name, "chart_number": v, **chart}

            # Translate if needed
            if min_req.language and min_req.language != 'en':
                translated_chart = {}
                for sign, planets_list in chart.items():
                    translated_planets = []
                    for planet_info in planets_list:
                        if isinstance(planet_info, dict):
                            translated_planet = planet_info.copy()
                            if 'planet' in translated_planet:
                                translated_planet['planet'] = translation_manager.translate(
                                    f'planets.{planet_info["planet"]}', min_req.language
                                )
                            # Translate the sign field inside planet info
                            if 'sign' in translated_planet:
                                translated_planet['sign'] = translation_manager.translate(
                                    f'zodiac_signs.{planet_info["sign"]}', min_req.language,
                                    default=planet_info["sign"]
                                )
                            translated_planets.append(translated_planet)
                        else:
                            # Translate planet name string
                            translated_planets.append(
                                translation_manager.translate(f'planets.{planet_info}', min_req.language)
                            )
                    # Translate sign name
                    translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', min_req.language)
                    translated_chart[translated_sign] = translated_planets

                # Translate chart name
                translated_chart_name = translation_manager.translate(f'charts.{chart_name}', min_req.language, default=chart_name)
                chart_data = {"chart_name": translated_chart_name, "chart_number": v, **translated_chart}
            else:
                chart_data = {"chart_name": chart_name, "chart_number": v, **chart}

            # Use translated chart name as key if translated, otherwise original
            if min_req.language and min_req.language != 'en':
                detailed_varga_charts_named[translated_chart_name] = chart_data
            else:
                detailed_varga_charts_named[chart_name] = chart_data

        return {
            "rasi_chart_svg": rasi_chart_svg,
            "navamsa_chart_svg": navamsa_chart_svg,
            "varga_charts_svgs": varga_svg_dictionary,
            "major_varga_charts": major_varga_charts_named,
            "detailed_varga_charts": detailed_varga_charts_named
        }
    except Exception as e:
        logger.error(f"Error in /charts endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/complete")
def complete_kundli(min_req: MinimalKundliInput):
    """
    Unified endpoint that combines all kundli-related data in a single response.
    This endpoint combines the functionality of:
    - /api/birth-details: Returns birth information and panchanga details
    - /api/kundli: Returns core kundli data including planets, lagna, charts, and dasha
    - /api/charts: Returns all varga charts (divisional charts) and SVG representations
    - /api/doshas: Returns Mangal Dosha and Kalasarpa Dosha analysis
    - /api/ashtakavarga-data: Returns Ashtakavarga data
    All data is computed once and returned in a structured format.
    Args:
        min_req: MinimalKundliInput containing birth details (name, date_of_birth,
                 time_of_birth, place_of_birth, latitude, longitude, timezone)
    Returns:
        Dictionary containing all kundli data organized by section:
        - birth_details: Name, birth info, panchanga, enhanced panchanga
        - kundli: Core kundli data (lagna, planets, rasi chart, nakshatra, dasha, SVG charts)
        - charts: All varga charts with SVG representations
        - doshas: Mangal Dosha and Kalasarpa Dosha analysis
        - ashtakavarga: Ashtakavarga data
    Raises:
        HTTPException: If there's an error in calculation or processing
    """
    try:
        # Step 1: Compute the full KundaliResponse once
        res = _compute(min_req)

        # Handle both dict (translated) and object (English) responses
        if isinstance(res, dict):
            # For translated responses, we need to recompute the complete structure
            # since the translation manager only handles the basic KundaliResponse
            # We compute the English version first, then translate the complete response
            kr: KundaliRequest = minimal_to_kundali_request(min_req)
            kundali_response = kundali_engine.generate_kundali(kr)

            # Now build the complete response structure using the English response
            return _build_complete_response(kundali_response, kr.language)
        else:
            # English response - build complete structure directly
            return _build_complete_response(res, min_req.language)

    except HTTPException:
        raise  # Re-raise FastAPI HTTP exceptions directly
    except Exception as e:
        logger.error(f"Error in /api/complete endpoint: {e}")
        logger.error(traceback.format_exc())  # Log the full traceback for debugging
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


def _build_complete_response(res: KundaliResponse, language: str) -> dict:
    """
    Helper function to build the complete response structure.
    Handles translation for non-English languages.
    """
    # Step 2: Extract birth_details section (from /api/birth-details)
    birth_details_section = {
        "name": res.name,
        "birth_info": res.birth_info,
        "panchanga": res.panchanga,
        "enhanced_panchanga": res.enhanced_panchanga,
    }

    # Step 3: Extract kundli section (from /api/kundli)
    kundli_section = {
        "name": res.name,
        "lagna": res.lagna.sign,
        "lagna_degree": res.lagna.degree,
        "planets": [p.model_dump() for p in res.planets],
        "rasi_chart": res.rasi_chart,
        "moon_nakshatra": res.moon_nakshatra,
        "vimshottari_dasha": [d.model_dump() for d in res.vimshottari_dasha],
        "current_dasha_detailed": res.current_dasha_detailed,
        "rasi_chart_svg": res.rasi_chart_svg,
        "navamsa_chart_svg": res.navamsa_chart_svg,
    }

    # Step 4: Extract charts section with varga calculations (from /api/charts)
    # Prepare data for Varga engine
    planet_degrees = {p.planet: (SIGN_NAMES.index(p.sign) * 30 + p.degree) for p in res.planets}
    planet_degrees['Lagna'] = res.lagna.abs_longitude

    # Calculate all Varga charts
    vargas_to_calc = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 60]
    all_varga_charts = get_all_varga_charts(planet_degrees, vargas_to_calc)

    # Calculate detailed varga charts with planet positions
    all_varga_charts_detailed = get_all_varga_charts_detailed(planet_degrees, vargas_to_calc)

    # Prepare degree map for display
    degree_map_for_svg = {p.planet: p.degree for p in res.planets}
    degree_map_for_svg['Lagna'] = res.lagna.degree

    # Generate the dictionary of individual SVGs
    varga_svg_dictionary = svg_chart_generator.create_all_varga_svgs(
        all_varga_data=all_varga_charts,
        varga_names=VARGA_NAMES,
        degree_map=degree_map_for_svg,
        lang=language if language else 'en'
    )

    # The JSON for the raw data, can be useful for the frontend (backward compatibility)
    major_varga_charts = {
       VARGA_NAMES.get(v, f"D{v}"): chart
       for v, chart in all_varga_charts.items()
    }

    # Translate major varga charts if language is not English
    if language and language != 'en':
        translated_major_varga_charts = {}
        for chart_name, chart_data in major_varga_charts.items():
            translated_chart = {}
            for sign, planets_list in chart_data.items():
                # Translate sign name
                translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', language, default=sign)

                # Translate planet names
                translated_planets = []
                for planet_name in planets_list:
                    translated_planet = translation_manager.translate(f'planets.{planet_name}', language, default=planet_name)
                    translated_planets.append(translated_planet)

                translated_chart[translated_sign] = translated_planets
            # Translate chart name
            translated_chart_name = translation_manager.translate(f'charts.{chart_name}', language, default=chart_name)
            translated_major_varga_charts[translated_chart_name] = translated_chart
        major_varga_charts_named = translated_major_varga_charts
    else:
        major_varga_charts_named = major_varga_charts

    # Detailed varga charts with planet info (new format for app team)
    # If language is not English, translate planet names in varga charts
    detailed_varga_charts_named = {}
    for v, chart in all_varga_charts_detailed.items():
        chart_name = VARGA_NAMES.get(v, f"D{v}")
        chart_data = {"chart_name": chart_name, "chart_number": v, **chart}

        # Translate if needed
        if language and language != 'en':
            translated_chart = {}
            for sign, planets_list in chart.items():
                translated_planets = []
                for planet_info in planets_list:
                    if isinstance(planet_info, dict):
                        translated_planet = planet_info.copy()
                        if 'planet' in translated_planet:
                            translated_planet['planet'] = translation_manager.translate(
                                f'planets.{planet_info["planet"]}', language, default=planet_info["planet"]
                            )
                        if 'sign' in translated_planet:
                            translated_planet['sign'] = translation_manager.translate(
                                f'zodiac_signs.{planet_info["sign"]}', language, default=planet_info["sign"]
                            )
                        translated_planets.append(translated_planet)
                    else:
                        # It's just a planet name string
                        translated_planet = translation_manager.translate(f'planets.{planet_info}', language, default=planet_info)
                        translated_planets.append(translated_planet)
                translated_chart[sign] = translated_planets
            # Update chart data with translated planets
            chart_data.update(translated_chart)
            # Also translate the chart name
            chart_data['chart_name'] = translation_manager.translate(f'charts.{chart_name}', language, default=chart_name)

        detailed_varga_charts_named[chart_name] = chart_data

    charts_section = {
        "rasi_chart_svg": res.rasi_chart_svg,
        "navamsa_chart_svg": res.navamsa_chart_svg,
        "varga_charts_svgs": varga_svg_dictionary,
        "major_varga_charts": major_varga_charts_named,
        "detailed_varga_charts": detailed_varga_charts_named
    }

    # Step 5: Extract doshas section (from /api/doshas)
    # Extract planet data for dosha calculations
    planet_houses: Dict[str, int] = {}
    planet_signs: Dict[str, str] = {}
    planet_longitudes: Dict[str, float] = {}

    for planet_pos in res.planets:
        planet_name = planet_pos.planet
        planet_houses[planet_name] = planet_pos.house
        planet_signs[planet_name] = planet_pos.sign

        # Convert sign + degree to absolute longitude (0-360)
        sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        try:
            sign_index = sign_order.index(planet_pos.sign)
            absolute_longitude = sign_index * 30 + planet_pos.degree
            planet_longitudes[planet_name] = absolute_longitude
        except ValueError:
            logger.warning(f"Could not find sign '{planet_pos.sign}' in sign_order for planet {planet_name}.")
            continue

    aspects = {}  # Empty dict as per existing doshas endpoint implementation

    # Calculate detailed dosha results
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

    doshas_section = {
        "mangal_dosha": MangalDoshaResult(**mangal_dosha_detailed),
        "kalasarpa_dosha": KalasarpaDoshaResult(**kalasarpa_dosha_detailed)
    }

    # Step 6: Extract ashtakavarga section (from /api/ashtakavarga-data)
    ashtakavarga_section = {
        "ashtakavarga": res.ashtakavarga
    }

    # Step 7: Combine all sections into unified response
    complete_response = {
        "birth_details": birth_details_section,
        "kundli": kundli_section,
        "charts": charts_section,
        "doshas": doshas_section,
        "ashtakavarga": ashtakavarga_section
    }

    # Step 8: Translate the complete response if language is not English
    if language and language != 'en':
        # Translate each section individually
        complete_response = _translate_complete_response(complete_response, language)

    return complete_response


def _translate_complete_response(complete_response: dict, language: str) -> dict:
    """
    Helper function to translate the complete response structure.
    This handles the nested structure with sections like birth_details, kundli, etc.
    """
    # Create a copy to avoid modifying the original
    translated = complete_response.copy()

    # Translate birth_details section
    if 'birth_details' in translated:
        if 'panchanga' in translated['birth_details']:
            panchanga_data = translated['birth_details']['panchanga']
            # Convert PanchangaInfo object to dict if needed
            if hasattr(panchanga_data, 'model_dump'):
                panchanga_data = panchanga_data.model_dump()
            elif hasattr(panchanga_data, 'dict'):
                panchanga_data = panchanga_data.dict()
            elif not isinstance(panchanga_data, dict):
                panchanga_data = dict(panchanga_data)

            # Apply translations like the birth-details endpoint does
            if language == 'hi' and panchanga_data:
                translated_panchanga = panchanga_data.copy()
                translated_panchanga['tithi'] = translation_manager.translate(f'tithi_names.{panchanga_data.get("tithi", "")}', language, default=panchanga_data.get("tithi", ""))
                translated_panchanga['yoga'] = translation_manager.translate(f'yoga_types.{panchanga_data.get("yoga", "")}', language, default=panchanga_data.get("yoga", ""))
                translated_panchanga['karana'] = translation_manager.translate(f'karana_types.{panchanga_data.get("karana", "")}', language, default=panchanga_data.get("karana", ""))
                translated_panchanga['vaara'] = translation_manager.translate(f'vaara_names.{panchanga_data.get("vaara", "")}', language, default=panchanga_data.get("vaara", ""))
                translated_panchanga['masa'] = translation_manager.translate(f'masa_names.{panchanga_data.get("masa", "")}', language, default=panchanga_data.get("masa", ""))
                translated_panchanga['ritu'] = translation_manager.translate(f'ritu_names.{panchanga_data.get("ritu", "")}', language, default=panchanga_data.get("ritu", ""))
                translated_panchanga['nakshatra'] = translation_manager.translate(f'nakshatras.{panchanga_data.get("nakshatra", "")}', language, default=panchanga_data.get("nakshatra", ""))
                translated['birth_details']['panchanga'] = translated_panchanga
            else:
                translated['birth_details']['panchanga'] = panchanga_data
        if 'enhanced_panchanga' in translated['birth_details']:
            # enhanced_panchanga may need additional translation for yoga names
            enhanced_panchanga_data = translated['birth_details']['enhanced_panchanga']

            # Convert EnhancedPanchangaInfo object to dict if needed
            if hasattr(enhanced_panchanga_data, 'model_dump'):
                enhanced_panchanga_data = enhanced_panchanga_data.model_dump()
            elif hasattr(enhanced_panchanga_data, 'dict'):
                enhanced_panchanga_data = enhanced_panchanga_data.dict()
            elif not isinstance(enhanced_panchanga_data, dict):
                enhanced_panchanga_data = dict(enhanced_panchanga_data)

            if language == 'hi' and enhanced_panchanga_data:
                translated_enhanced = {}
                for key, value in enhanced_panchanga_data.items():
                    if isinstance(value, dict) and 'name' in value:
                        translated_value = value.copy()
                        original_name = value['name']

                        if key == 'yoga':
                            translated_value['name'] = translation_manager.translate(f'yoga_types.{original_name}', language, default=original_name)
                        elif key == 'karana':
                            translated_value['name'] = translation_manager.translate(f'karana_types.{original_name}', language, default=original_name)
                        elif key == 'masa' and 'type' in value:
                            translated_value['type'] = translation_manager.translate(f'masa_types.{value["type"]}', language, default=value["type"])
                        elif key == 'samvatsara':
                            translated_value['name'] = translation_manager.translate(f'samvatsara_names.{original_name}', language, default=original_name)

                        translated_enhanced[key] = translated_value
                    else:
                        translated_enhanced[key] = value
                translated['birth_details']['enhanced_panchanga'] = translated_enhanced

    # Translate kundli section
    if 'kundli' in translated:
        # Translate planets
        if 'planets' in translated['kundli']:
            translated['kundli']['planets'] = [
                translation_manager.translate_planet_position(p, language)
                for p in translated['kundli']['planets']
            ]

        # Translate lagna
        if 'lagna' in translated['kundli']:
            translated['kundli']['lagna'] = translation_manager.translate(
                f'zodiac_signs.{translated["kundli"]["lagna"]}', language,
                default=translated['kundli']['lagna']
            )

        # Translate rasi chart
        if 'rasi_chart' in translated['kundli']:
            translated['kundli']['rasi_chart'] = translation_manager.translate_rasi_chart(
                translated['kundli']['rasi_chart'], language
            )

        # Translate moon nakshatra
        if 'moon_nakshatra' in translated['kundli']:
            translated['kundli']['moon_nakshatra'] = translation_manager.translate_nakshatra_info(
                translated['kundli']['moon_nakshatra'], language
            )

        # Translate vimshottari dasha
        if 'vimshottari_dasha' in translated['kundli']:
            translated['kundli']['vimshottari_dasha'] = [
                translation_manager.translate_dasha_info(d, language)
                for d in translated['kundli']['vimshottari_dasha']
            ]

        # Translate current dasha
        if 'current_dasha_detailed' in translated['kundli']:
            translated['kundli']['current_dasha_detailed'] = translation_manager.translate_dasha_info(
                translated['kundli']['current_dasha_detailed'], language
            )

    # Translate doshas section
    if 'doshas' in translated:
        # Translate mangal dosha
        if 'mangal_dosha' in translated['doshas']:
            mangal_dosha = translated['doshas']['mangal_dosha']
            if hasattr(mangal_dosha, 'dict'):
                mangal_dosha = mangal_dosha.dict()
            if isinstance(mangal_dosha, dict):
                # Translate key fields in mangal dosha
                for key in mangal_dosha:
                    if key in translated['doshas']['mangal_dosha']:
                        translated['doshas']['mangal_dosha'][key] = mangal_dosha[key]

        # Translate kalasarpa dosha
        if 'kalasarpa_dosha' in translated['doshas']:
            kalasarpa_dosha = translated['doshas']['kalasarpa_dosha']
            if hasattr(kalasarpa_dosha, 'dict'):
                kalasarpa_dosha = kalasarpa_dosha.dict()
            if isinstance(kalasarpa_dosha, dict):
                # Translate key fields in kalasarpa dosha
                for key in kalasarpa_dosha:
                    if key in translated['doshas']['kalasarpa_dosha']:
                        translated['doshas']['kalasarpa_dosha'][key] = kalasarpa_dosha[key]

    # Add UI labels for better frontend experience
    translated['ui_labels'] = {
        'birth_details': {
            'name': translation_manager.translate('ui_labels.name', language, default='Name'),
            'birth_info': translation_manager.translate('ui_labels.birth_info', language, default='Birth Information'),
            'panchanga': translation_manager.translate('ui_labels.panchanga', language, default='Panchanga'),
            'enhanced_panchanga': translation_manager.translate('ui_labels.enhanced_panchanga', language, default='Enhanced Panchanga')
        },
        'kundli': {
            'lagna': translation_manager.translate('ui_labels.lagna', language, default='Lagna'),
            'planets': translation_manager.translate('ui_labels.planets', language, default='Planets'),
            'rasi_chart': translation_manager.translate('ui_labels.rasi_chart', language, default='Rasi Chart'),
            'moon_nakshatra': translation_manager.translate('ui_labels.moon_nakshatra', language, default='Moon Nakshatra'),
            'vimshottari_dasha': translation_manager.translate('ui_labels.vimshottari_dasha', language, default='Vimshottari Dasha'),
            'current_dasha': translation_manager.translate('ui_labels.current_dasha', language, default='Current Dasha')
        },
        'charts': {
            'varga_charts': translation_manager.translate('ui_labels.varga_charts', language, default='Varga Charts'),
            'navamsa_chart': translation_manager.translate('ui_labels.navamsa_chart', language, default='Navamsa Chart')
        },
        'doshas': {
            'mangal_dosha': translation_manager.translate('ui_labels.mangal_dosha', language, default='Mangal Dosha'),
            'kalasarpa_dosha': translation_manager.translate('ui_labels.kalasarpa_dosha', language, default='Kalasarpa Dosha')
        },
        'ashtakavarga': {
            'ashtakavarga': translation_manager.translate('ui_labels.ashtakavarga', language, default='Ashtakavarga')
        }
    }

    return translated


@router.post("/api/yogas")
def yogas(min_req: MinimalKundliInput):
    res = _compute_yogas(min_req)

    # Handle both dict (translated) and object (English) responses
    if isinstance(res, dict):
        return {
            "detected_yogas": res.get("detected_yogas", []),
            "yoga_summary": res.get("yoga_summary", {}),
            "ui_labels": res.get("ui_labels", {}),
        }

    # English response (KundaliResponse object)
    return {
        "detected_yogas": [y.model_dump() for y in res.detected_yogas],
        "yoga_summary": res.yoga_summary,
    }
@router.post("/api/interpretation")
def interpretation(min_req: MinimalKundliInput):
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

@router.post("/api/ashtakavarga-data")
def get_ashtakavarga_data(min_req: MinimalKundliInput):
    """
    Returns the raw Ashtakavarga data in JSON format.
    """
    try:
        res = _compute_ashtakavarga(min_req)

        # Handle both dict (translated) and object (English) responses
        if isinstance(res, dict):
            return {
                "ashtakavarga": res.get("ashtakavarga", {})
            }

        # English response (KundaliResponse object)
        return {
            "ashtakavarga": res.ashtakavarga
        }
    except Exception as e:
        logger.error(f"Error in /ashtakavarga-data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/ashtakavarga-svg", response_class=Response)
def get_ashtakavarga_svg_standalone(min_req: MinimalKundliInput):
    """
    Calculates Ashtakavarga and returns the chart as a single SVG image.
    This endpoint is self-contained and performs only the necessary calculations.
    """
    try:
        # Step 1: Get full birth details from the minimal input
        full_req: KundaliRequest = minimal_to_kundali_request(min_req)

        # Step 2: Perform only the essential calculations from the engine
        jd = kundali_engine._datetime_to_jd(full_req.datetime, full_req.timezone)
        planets, lagna_info,_ = kundali_engine._calculate_positions_with_kerykeion(full_req)
        lagna_sign = lagna_info['sign']

        # Step 3: Prepare the data for the calculator
        planet_signs = {p_name: p_data.sign for p_name, p_data in planets.items()}

        # Step 4: Calculate the Ashtakavarga data directly
        ashtakavarga_data = calculate_ashtakavarga(planet_signs, lagna_sign)

        # Step 5: Generate the SVG string from the data
        svg_string = create_ashtakavarga_svg(ashtakavarga_data,lagna_sign)

        if not svg_string:
            raise HTTPException(status_code=500, detail="Ashtakavarga SVG string is empty.")

        # Step 6: Return the SVG image
        return Response(content=svg_string, media_type="image/svg+xml")

    except Exception as e:
        logger.error(f"Error in /ashtakavarga-svg endpoint: {e}")
        import traceback
        traceback.print_exc() # This will give a detailed error in your logs
        raise HTTPException(status_code=500, detail=f"Error generating Ashtakavarga SVG: {e}")



@router.post("/api/doshas")
def doshas(min_req: MinimalKundliInput) -> Dict:
    """
    Calculates and returns detailed Mangal Dosha and Kalasarpa Dosha information.
    """
    try:
        # Step 1: Compute the full KundaliResponse using your existing _compute function
        res = _compute(min_req)

        # If response is already a dict (translated), extract dosha data directly
        if isinstance(res, dict):
            return {
                "mangal_dosha": res.get("mangal_dosha", {}),
                "kalasarpa_dosha": res.get("kalasarpa_dosha", {})
            }

        # Step 2: Extract the necessary raw planet data from the 'res' (KundaliResponse object)
        # Iterate through the list of PlanetPosition objects to build the required dictionaries
        planet_houses: Dict[str, int] = {}
        planet_signs: Dict[str, str] = {}
        planet_longitudes: Dict[str, float] = {}

        for planet_pos in res.planets:
            planet_name = planet_pos.planet
            planet_houses[planet_name] = planet_pos.house
            planet_signs[planet_name] = planet_pos.sign

            # To get absolute longitude (0-360), you need to convert sign + degree
            # Assuming sign_order is defined somewhere accessible, or hardcoded if consistent
            sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            try:
                sign_index = sign_order.index(planet_pos.sign)
                absolute_longitude = sign_index * 30 + planet_pos.degree
                planet_longitudes[planet_name] = absolute_longitude
            except ValueError:
                logger.warning(f"Could not find sign '{planet_pos.sign}' in sign_order for planet {planet_name}.")
                # Handle cases where sign might not be in order, or skip if crucial
                continue # Skip this planet if sign isn't recognized


        # You mentioned aspects in the dosha_analyzer, but your current KundaliResponse
        # doesn't directly provide a pre-calculated 'aspects' dictionary.
        # If you want aspect-based cancellation rules, you'd either:
        # A) Modify kundali_engine.generate_kundali to calculate and include aspects in KundaliResponse, OR
        # B) Implement aspect calculation here in the endpoint, which would be more complex.
        # For now, we'll pass an empty dict for aspects, so aspect-based rules won't activate.
        aspects = {} # Or derive this from res if KundaliResponse somehow provides aspect data

        # Step 3: Calculate detailed dosha results using the enhanced functions
        mangal_dosha_detailed = calculate_mangal_dosha(
            planet_houses=planet_houses,
            planet_signs=planet_signs,
            planet_degrees=planet_longitudes,
            lagna_house=1, # Assuming lagna_degree implies lagna house, or use lagna_house from KundaliResponse if available.
                                          # Note: lagna_degree is typically the degree *within* the lagna sign, not the house number.
                                          # You might need the actual Lagna house number from KundaliResponse if it exists.
                                          # For now, let's assume `lagna_house` in `calculate_mangal_dosha` needs the numeric house.
                                          # If `res.lagna` gives the sign, you'd need to convert it to a house number, or pass `res.lagna` to the function
                                          # and update `calculate_mangal_dosha` to handle lagna_sign.
                                          # Assuming `res.lagna_house` is available for simplicity. If not, you need to derive it.
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
        raise # Re-raise FastAPI HTTP exceptions directly
    except Exception as e:
        logger.error(f"Error in /doshas endpoint: {e}")
        logger.error(traceback.format_exc()) # Log the full traceback for debugging
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")



@router.post("/api/kundli-matching", response_model=KundliMatchingResponse, tags=["Matching"])
def get_kundli_matching(matching_request: KundliMatchingRequest):
    """
    Performs Ashtakoota Milan (Guna Milan) and Mangal Dosha compatibility check for a couple.

    This endpoint takes the birth details of a groom and a bride, generates their individual
    Kundlis, and then calculates their marital compatibility score out of 36 gunas.
    """
    try:
        # Step 1: Compute Kundali for both Groom and Bride
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


# @app.post("/generate-kundali", response_model=KundaliResponse)
# async def generate_kundali(request: KundaliRequest):
#     """
#     Generate a complete Kundali (Vedic horoscope) from birth details

#     This endpoint accepts birth details and returns a comprehensive horoscope including:
#     - Planetary positions in signs and houses
#     - Rasi chart (birth chart)
#     - Moon's nakshatra and pada
#     - Current Vimshottari Dasha
#     - Panchanga details (tithi, nakshatra, yoga, karana, etc.)

#     Args:
#         request: KundaliRequest containing birth details

#     Returns:
#         KundaliResponse with complete horoscope data

#     Raises:
#         HTTPException: If there's an error in calculation
#     """
#     try:
#         logger.info(f"Generating Kundali for {request.name}")

#         # Validate input
#         if not request.name.strip():
#             raise HTTPException(status_code=400, detail="Name cannot be empty")

#         if not (-90 <= request.latitude <= 90):
#             raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")

#         if not (-180 <= request.longitude <= 180):
#             raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")

#         # Check if birth date is not in the future
#         if request.datetime > datetime.now():
#             raise HTTPException(status_code=400, detail="Birth date cannot be in the future")

#         # Generate the Kundali
#         result = kundali_engine.generate_kundali(request)

#         logger.info(f"Successfully generated Kundali for {request.name}")
#         return result

#     except HTTPException:
#         # Re-raise HTTP exceptions
#         raise
#     except Exception as e:
#         logger.error(f"Error generating Kundali: {str(e)}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal server error: {str(e)}"
#         )


@router.post("/generate-interpretation")
async def generate_interpretation(kundali_data: dict):
    """
    Generate human-readable interpretation for existing Kundali data

    This endpoint accepts a Kundali data dictionary and returns
    a human-readable interpretation without recalculating the chart.
    """
    try:
        # Initialize interpretation engine
        interpretation_engine = InterpretationEngine()

        # Generate interpretation
        interpretation = interpretation_engine.generate_kundali_interpretation(kundali_data)

        return {
            "status": "success",
            "interpretation": interpretation,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating interpretation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating interpretation: {str(e)}"
        )


@app.post("/generate-kundali-html", response_class=HTMLResponse)
async def generate_kundali_html(min_req: MinimalKundliInput):
    """
    Generate a complete styled Kundali HTML report from minimal birth details.

    Payload:
    {
        "name": "Full Name",
        "date_of_birth": "DD/MM/YYYY",
        "time_of_birth": "HH:MM or HH:MM:SS or HH:MMAM/PM",
        "place_of_birth": "City, State, Country"
    }
    """
    try:
        logger.info("HTML report request received for %s", min_req.name)

        # ---- Convert minimal -> full (geocode + timezone + datetime parse) ----
        try:
            full_req: KundaliRequest = minimal_to_kundali_request(min_req)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Conversion minimal_to_kundali_request failed")
            raise HTTPException(status_code=400, detail=f"Invalid input: {e}")

        logger.info(
            "Computed full request: name=%s lat=%.4f lon=%.4f tz=%s dt=%s",
            full_req.name, full_req.latitude, full_req.longitude,
            full_req.timezone, full_req.datetime.isoformat()
        )

        # ---- Domain validations (optional, because helper likely already does) ----
        if full_req.datetime > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Birth date cannot be in the future.")

        # ---- Generate base kundali data ----
        kundali: KundaliResponse = kundali_engine.generate_kundali(full_req)

        # ----------------- Varga Charts & Strengths -----------------
        major_vargas = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 30]
        additional_vargas = [27, 40, 45, 60]

        # Prepare degrees for strength analysis once
        sign_order = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                      "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        planet_degrees = {}
        for p in kundali.planets:
            sign_index = sign_order.index(p.sign)
            abs_long = sign_index * 30 + p.degree
            planet_degrees[p.planet] = abs_long

        major_varga_raw = kundali_engine.get_all_varga_charts(kundali.planets, major_vargas)
        additional_varga_raw = kundali_engine.get_all_varga_charts(kundali.planets, additional_vargas)

        varga_names = {
            2:"Hora (D2)", 3:"Drekkana (D3)", 4:"Chaturthamsa (D4)", 7:"Saptamsa (D7)",
            9:"Navamsa (D9)", 10:"Dasamsa (D10)", 12:"Dwadasamsa (D12)", 16:"Shodasamsa (D16)",
            20:"Vimsamsa (D20)", 24:"Chaturvimsamsa (D24)", 30:"Trimsamsa (D30)"
        }
        additional_names = {
            27:"Saptavimsamsa (D27)", 40:"Khavedamsa (D40)",
            45:"Akshavedamsa (D45)", 60:"Shastyamsa (D60)"
        }

        major_varga_charts_named = {
            varga_names.get(v, f"D{v}"): chart
            for v, chart in major_varga_raw.items()
        }

        # Strengths
        varga_strengths = {}
        for v, chart in major_varga_raw.items():
            label = varga_names.get(v, f"D{v}")
            varga_strengths[label] = get_varga_planet_strength(planet_degrees, v)

        additional_varga_charts = {}
        for v, chart in additional_varga_raw.items():
            label = additional_names.get(v, f"D{v}")
            occupied_signs = []
            most_populated = []
            max_ct = 0
            for sign, plist in chart.items():
                if plist:
                    occupied_signs.append(f"{sign}({len(plist)})")
                    if len(plist) > max_ct:
                        max_ct = len(plist)
                        most_populated = [sign]
                    elif len(plist) == max_ct and max_ct > 0:
                        most_populated.append(sign)
            additional_varga_charts[label] = {
                "occupied_signs": occupied_signs,
                "most_populated_signs": most_populated
            }

        # Strength distribution summary
        strength_tally = {}
        planet_strength_counts = {}
        for label, strengths in varga_strengths.items():
            for planet, status in strengths.items():
                strength_tally[status] = strength_tally.get(status, 0) + 1
                if planet not in planet_strength_counts:
                    planet_strength_counts[planet] = {"Exalted":0, "Own Sign":0, "Debilitated":0, "Neutral":0}
                planet_strength_counts[planet][status] += 1

        key_observations = []
        for planet, counts in planet_strength_counts.items():
            if counts["Exalted"] >= 3:
                key_observations.append(
                    f"{planet} exalted in {counts['Exalted']} divisional charts -> strong area indications."
                )
            if counts["Debilitated"] >= 3:
                key_observations.append(
                    f"{planet} debilitated in {counts['Debilitated']} charts -> challenges in its domains."
                )
            if counts["Own Sign"] >= 4:
                key_observations.append(
                    f"{planet} in own sign in {counts['Own Sign']} charts -> stable constructive influence."
                )

        for label, chart in major_varga_charts_named.items():
            for sign, plist in chart.items():
                if len(plist) >= 4:
                    key_observations.append(
                        f"{len(plist)} planets concentrated in {sign} in {label} chart."
                    )

        if not key_observations:
            key_observations = [
                "Balanced distribution of planetary dignities across divisional charts.",
                "No extreme exaltation/debilitation clusters observed."
            ]

        varga_analysis_summary = {
            "strength_distribution": strength_tally,
            "key_observations": key_observations[:5]
        }

        varga_divisions = {
            "D2": "15°00'", "D3": "10°00'", "D4": "7°30'", "D7": "4°17'",
            "D9": "3°20'", "D10": "3°00'", "D12": "2°30'", "D16": "1°52'",
            "D20": "1°30'", "D24": "1°15'", "D27": "1°07'", "D30": "1°00'",
            "D40": "0°45'", "D45": "0°40'", "D60": "0°30'"
        }

        # -------------- Prepare Translated Labels --------------
        lang = min_req.language if min_req.language else 'en'
        labels = {
            "description": translation_manager.translate('yogas.description', lang, default='Description'),
            "significance": translation_manager.translate('yogas.significance', lang, default='Significance'),
            "effects": translation_manager.translate('yogas.effects', lang, default='Effects'),
            "planets_involved": translation_manager.translate('yogas.planets_involved', lang, default='Planets Involved'),
            "houses_involved": translation_manager.translate('yogas.houses_involved', lang, default='Houses Involved'),
            "strength": translation_manager.translate('yogas.strength', lang, default='Strength')
        }

        # -------------- Prepare Template Data --------------
        template_data = {
            "name": kundali.name,
            "birth_info": kundali.birth_info,
            "lagna": kundali.lagna,
            "lagna_degree": kundali.lagna_degree,
            "planets": [p.dict() for p in kundali.planets],
            "rasi_chart": kundali.rasi_chart,
            "moon_nakshatra": kundali.moon_nakshatra.dict(),
            "current_dasha": kundali.current_dasha.dict(),
            "panchanga": kundali.panchanga.dict() if kundali.panchanga else None,
            "enhanced_panchanga": kundali.enhanced_panchanga.dict() if kundali.enhanced_panchanga else None,
            "vimshottari_dasha": [d.dict() for d in kundali.vimshottari_dasha],
            "current_dasha_detailed": kundali.current_dasha_detailed.dict() if kundali.current_dasha_detailed else None,
            "navamsa_chart": kundali.navamsa_chart.dict() if kundali.navamsa_chart else None,
            "detected_yogas": [y.dict() for y in kundali.detected_yogas],
            "yoga_summary": kundali.yoga_summary.dict() if kundali.yoga_summary else None,
            "interpretation": kundali.interpretation,

            # Varga extras
            "varga_charts": True,
            "major_varga_charts": major_varga_charts_named,
            "varga_strengths": varga_strengths,
            "additional_varga_charts": additional_varga_charts,
            "varga_analysis_summary": varga_analysis_summary,
            "varga_divisions": varga_divisions,

            # Translated labels for template
            "labels": labels
        }

        template = jinja_env.get_template("kundali_template.html")
        html = template.render(**template_data)

        logger.info("HTML Kundali successfully generated for %s", kundali.name)
        return HTMLResponse(content=html, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unhandled error in generate_kundali_html: %s", e)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# ====== HOROSCOPE API ENDPOINTS ======

# @app.get("/api/v1/horoscope/{sign}")
# async def get_horoscope(
#     sign: str,
#     scope: str = Query("daily", description="Time scope: daily, weekly, monthly, yearly")
# ):
#     """
#     Get horoscope for a zodiac sign using static template-based generation
#
#     Args:
#         sign: Zodiac sign (Aries, Taurus, Gemini, etc.)
#         scope: Time scope (daily, weekly, monthly, yearly)
#
#     Returns:
#         JSON response with horoscope data
#     """
#     try:
#         # Validate sign
#         if sign not in ZODIAC_SIGNS:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid zodiac sign: {sign}. Must be one of: {', '.join(ZODIAC_SIGNS)}"
#             )
#
#         # Validate scope
#         scope = scope.lower()
#         if scope not in VALID_SCOPES:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid scope: {scope}. Must be one of: {', '.join(VALID_SCOPES)}"
#             )
#
#         # Generate horoscope
#         horoscope_data = generate_horoscope(sign, scope)
#
#         return {
#             "error": False,
#             "data": horoscope_data,
#             "timestamp": datetime.now().isoformat()
#         }
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error generating horoscope: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal server error while generating horoscope: {str(e)}"
#         )


@app.get("/api/v1/planetary-horoscope/{sign}")
async def get_planetary_horoscope(
    sign: str,
    scope: str = Query("daily", description="Time scope (currently only 'daily' supported)"),
    latitude: float = Query(12.972, description="Latitude for calculations (default: Bangalore)"),
    longitude: float = Query(77.594, description="Longitude for calculations (default: Bangalore)"),
    timezone: float = Query(5.5, description="Timezone offset (default: IST +5.5)"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    language: str = Query("en", description="Language code: en (English) or hi (Hindi)")
):
    """
    Get planetary horoscope based on real astronomical data using Swiss Ephemeris

    Args:
        sign: Zodiac sign (Aries, Taurus, Gemini, etc.)
        scope: Time scope (currently only 'daily' supported)
        latitude: Latitude for calculations
        longitude: Longitude for calculations
        timezone: Timezone offset
        date: Date in YYYY-MM-DD format

    Returns:
        JSON response with planetary horoscope data including astronomical information
    """
    try:
        # Validate sign
        if sign not in ZODIAC_SIGNS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid zodiac sign: {sign}. Must be one of: {', '.join(ZODIAC_SIGNS)}"
            )

        # Validate scope
        scope = scope.lower()
        if scope not in VALID_SCOPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scope: {scope}. Must be one of: {', '.join(VALID_SCOPES)}"
            )

        # Check if scope is supported for planetary horoscope
        if scope != 'daily':
            raise HTTPException(
                status_code=400,
                detail=f"Planetary horoscope currently only supports 'daily' scope. Requested: {scope}"
            )

        # Parse date
        parsed_date = None
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )

        # Generate planetary horoscope
        horoscope_data = generate_planetary_horoscope(
            sign=sign,
            scope=scope,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            date=parsed_date,
            language=language
        )

        return {
            "error": False,
            "data": horoscope_data,
            "language": language,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating planetary horoscope: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while generating planetary horoscope: {str(e)}"
        )


@app.get("/api/v1/signs")
async def get_zodiac_signs():
    """Get list of valid zodiac signs"""
    return {
        "error": False,
        "data": {
            "zodiac_signs": ZODIAC_SIGNS
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/scopes")
async def get_scopes():
    """Get list of valid time scopes"""
    return {
        "error": False,
        "data": {
            "scopes": VALID_SCOPES,
            "static_horoscope_scopes": VALID_SCOPES,
            "planetary_horoscope_scopes": ["daily"]  # Only daily supported currently
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/horoscope/daily/{sign}")
async def get_daily_structured_horoscope(
    sign: str,
    language: str = Query("en", description="Language code: en (English) or hi (Hindi)")
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
        # Call the narrative engine with language support
        prediction = generate_structured_horoscope(sign, language=language)

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
            "date": date.today().isoformat(),
            "language": language,
            "horoscope": prediction
        }
    except Exception as e:
        logger.error(f"Error in structured horoscope generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating the horoscope."
        )

@app.get("/api/v1/docs")
async def get_api_docs():
    """API documentation for horoscope endpoints"""
    docs = {
        "api_version": "v1",
        "service": "Kundali & Horoscope API",
        "endpoints": {
            "kundali_endpoints": {
                "POST /generate-kundali": "Generate Vedic birth chart",
                "POST /generate-kundali-html": "Generate HTML birth chart report",
                "POST /generate-interpretation": "Generate chart interpretation",
                "GET /form": "Kundali generation form",
                "GET /health": "Health check"
            },
            "horoscope_endpoints": {
                "GET /api/v1/horoscope/{sign}": {
                    "description": "Get static horoscope for a zodiac sign",
                    "parameters": {
                        "sign": "Zodiac sign (path parameter)",
                        "scope": "Time scope: daily, weekly, monthly, yearly (query parameter)"
                    },
                    "example": "/api/v1/horoscope/Scorpio?scope=daily"
                },
                "GET /api/v1/planetary-horoscope/{sign}": {
                    "description": "Get planetary horoscope based on real astronomical data",
                    "parameters": {
                        "sign": "Zodiac sign (path parameter)",
                        "scope": "Time scope: daily only (query parameter)",
                        "latitude": "Latitude for calculations (query parameter)",
                        "longitude": "Longitude for calculations (query parameter)",
                        "timezone": "Timezone offset (query parameter)",
                        "date": "Date in YYYY-MM-DD format (query parameter)"
                    },
                    "example": "/api/v1/planetary-horoscope/Leo?scope=daily&latitude=40.7128&longitude=-74.0060&timezone=-5.0&date=2025-01-08"
                },
                "GET /api/v1/signs": "Get list of valid zodiac signs",
                "GET /api/v1/scopes": "Get list of valid time scopes",
                "GET /api/v1/docs": "API documentation"
            }
        },
        "response_format": {
            "success": {
                "error": False,
                "data": "Object containing response data",
                "timestamp": "ISO timestamp"
            },
            "error": {
                "detail": "Error description"
            }
        }
    }

    return {
        "error": False,
        "data": docs,
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred while processing your request"
        }
    )

@app.get("/example-request")
async def get_example_request():
    return {
        "example_iso": {
            "name": "Ashish Gupta",
            "datetime": "1990-07-05T14:25:00",
            "timezone": "Asia/Kolkata",
            "latitude": 28.6139,
            "longitude": 77.2090
        },
        "example_discrete": {
            "name": "Arjun",
            "year": 1990,
            "month": 1,
            "day": 1,
            "hour": 15,
            "min": 22,
            "sec": 10,
            "timezone": "Asia/Kolkata",
            "latitude": 12.97194,
            "longitude": 77.59369
        }
    }

# KP and Bhava Chalit endpoints
@router.post("/api/kp-system")
async def generate_kp_system(req: MinimalKundliInput):
    """
    Generate Krishnamurti Paddhati (KP) system chart

    Returns KP house cusps, significators, star lords, sub-lords, and detailed analysis
    """
    try:
        # Convert to KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)

        # Generate basic kundali to get planetary positions
        kundali_result = kundali_engine.generate_kundali(kr)

        # Extract required data
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        planets = {}

        # Convert planet positions to the format expected by KP system
        for planet_data in kundali_result.planets:
            if hasattr(planet_data, '_abs_lon_sid'):
                planets[planet_data.planet] = planet_data
            else:
                # Create mock _abs_lon_sid from sign and degree
                sign_index = kundali_engine.ZODIAC_SIGNS.index(planet_data.sign)
                abs_longitude = sign_index * 30 + planet_data.degree
                planet_data._abs_lon_sid = abs_longitude
                planets[planet_data.planet] = planet_data

        # Calculate KP system
        kp_system = KPSystem()
        kp_results = kp_system.generate_kp_chart(jd, kr.latitude, kr.longitude, planets)

        return {
            "birth_details": {
                "name": req.name,
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth
            },
            "kp_system": kp_results,
            "status": "success"
        }

    except Exception as e:
        logger.exception("Error generating KP system")
        raise HTTPException(status_code=500, detail=f"KP system calculation failed: {str(e)}")

@router.post("/api/bhava-chalit")
async def generate_bhava_chalit(req: MinimalKundliInput):
    """
    Generate Bhava Chalit (Equal House) chart

    Returns equal house divisions from ascendant with planet positions
    """
    try:
        # Convert to KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)

        # Generate basic kundali to get planetary positions and ascendant
        kundali_result = kundali_engine.generate_kundali(kr)

        # Calculate Julian Day for KP calculations
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

        # Extract ascendant longitude
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

        # Calculate KP Bhava Chalit system using Placidus houses
        bhava_system = BhavaChalitSystem()
        bhava_results = bhava_system.generate_kp_bhava_chalit_chart(jd, kr.latitude, kr.longitude, planets)

        # SVG generation removed as requested

        # Calculate house strengths
        house_strengths = {}
        for house in range(1, 13):
            house_strengths[house] = bhava_system.get_house_strength(house, bhava_results['bhava_chart'])

        return {
            "birth_details": {
                "name": req.name,
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth
            },
            "bhava_chalit": bhava_results,
            "bhava_chalit_svg": bhava_chalit_svg,
            "house_strengths": house_strengths,
            "status": "success"
        }

    except Exception as e:
        logger.exception("Error generating Bhava Chalit chart")
        raise HTTPException(status_code=500, detail=f"Bhava Chalit calculation failed: {str(e)}")

@router.post("/api/kp-bhava-combined")
async def generate_kp_bhava_combined(req: MinimalKundliInput):
    """
    Generate both KP and Bhava Chalit systems in one response

    Returns comprehensive analysis with both house systems
    """
    try:
        # Convert to KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)

        # Generate basic kundali to get planetary positions
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

        # Calculate both systems using VedicAstro
        dt_parts = kr.datetime.split('T')
        date_part = dt_parts[0].split('-')
        time_part = dt_parts[1].split(':')

        year = int(date_part[0])
        month = int(date_part[1])
        day = int(date_part[2])
        hour = int(time_part[0])
        minute = int(time_part[1])

        combined_results = calculate_kp_and_bhava_chalit(year, month, day, hour, minute, kr.latitude, kr.longitude, kr.timezone)

        # SVG generation removed as requested
        bhava_system = BhavaChalitSystem()

        return {
            "birth_details": {
                "name": req.name,
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth
            },
            **combined_results,
            "status": "success"
        }

    except Exception as e:
        logger.exception("Error generating combined KP and Bhava Chalit systems")
        raise HTTPException(status_code=500, detail=f"Combined system calculation failed: {str(e)}")


# ====== CALCULATOR API ENDPOINTS ======

@router.post("/api/calculators/rashi")
async def calculate_rashi_only(req: MinimalKundliInput):
    """
    Calculate Rashi (Moon Sign) using accurate Vedic astrology

    This endpoint calculates the Moon's position at birth to determine the Rashi (Moon Sign).
    Requires: name, date_of_birth, time_of_birth, place_of_birth for accurate calculation.

    Returns:
        - Rashi name and details
        - Moon's nakshatra, pada, and lord
        - Element, quality, and lucky gem
    """
    try:
        # Convert minimal input to full KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info(f"Calculating Rashi for {req.name}")

        # Calculate Julian Day
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

        # Get Moon's nakshatra (which determines Rashi)
        moon_nakshatra = kundali_engine._get_moon_nakshatra(jd)

        # Get Moon's position from planetary calculations
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)
        moon_data = planets.get('Moon')

        if not moon_data:
            raise HTTPException(status_code=500, detail="Could not calculate Moon position")

        # Map Rashi sign to Vedic details
        rashi_details = {
            'Aries': {'sanskrit': 'Mesha', 'lord': 'Mars (Mangal)', 'element': 'Fire', 'quality': 'Movable', 'lucky_gem': 'Red Coral'},
            'Taurus': {'sanskrit': 'Vrishabha', 'lord': 'Venus (Shukra)', 'element': 'Earth', 'quality': 'Fixed', 'lucky_gem': 'Diamond'},
            'Gemini': {'sanskrit': 'Mithuna', 'lord': 'Mercury (Budh)', 'element': 'Air', 'quality': 'Dual', 'lucky_gem': 'Emerald'},
            'Cancer': {'sanskrit': 'Karka', 'lord': 'Moon (Chandra)', 'element': 'Water', 'quality': 'Movable', 'lucky_gem': 'Pearl'},
            'Leo': {'sanskrit': 'Simha', 'lord': 'Sun (Surya)', 'element': 'Fire', 'quality': 'Fixed', 'lucky_gem': 'Ruby'},
            'Virgo': {'sanskrit': 'Kanya', 'lord': 'Mercury (Budh)', 'element': 'Earth', 'quality': 'Dual', 'lucky_gem': 'Emerald'},
            'Libra': {'sanskrit': 'Tula', 'lord': 'Venus (Shukra)', 'element': 'Air', 'quality': 'Movable', 'lucky_gem': 'Diamond'},
            'Scorpio': {'sanskrit': 'Vrishchika', 'lord': 'Mars (Mangal)', 'element': 'Water', 'quality': 'Fixed', 'lucky_gem': 'Red Coral'},
            'Sagittarius': {'sanskrit': 'Dhanu', 'lord': 'Jupiter (Guru)', 'element': 'Fire', 'quality': 'Dual', 'lucky_gem': 'Yellow Sapphire'},
            'Capricorn': {'sanskrit': 'Makara', 'lord': 'Saturn (Shani)', 'element': 'Earth', 'quality': 'Movable', 'lucky_gem': 'Blue Sapphire'},
            'Aquarius': {'sanskrit': 'Kumbha', 'lord': 'Saturn (Shani)', 'element': 'Air', 'quality': 'Fixed', 'lucky_gem': 'Blue Sapphire'},
            'Pisces': {'sanskrit': 'Meena', 'lord': 'Jupiter (Guru)', 'element': 'Water', 'quality': 'Dual', 'lucky_gem': 'Yellow Sapphire'},
        }

        rashi = moon_data.sign
        details = rashi_details.get(rashi, {})

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth,
            },
            "rashi": {
                "sign": rashi,
                "sanskrit_name": details.get('sanskrit', rashi),
                "rashi_lord": details.get('lord', ''),
                "element": details.get('element', ''),
                "quality": details.get('quality', ''),
                "lucky_gem": details.get('lucky_gem', ''),
                "moon_degree": round(moon_data.degree, 2),
                "moon_degree_dms": moon_data.degree_dms,
            },
            "nakshatra": {
                "name": moon_nakshatra.name,
                "pada": moon_nakshatra.pada,
                "lord": moon_nakshatra.lord,
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Rashi: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Rashi: {str(e)}")


@router.post("/api/calculators/sun-sign")
async def calculate_sun_sign_only(req: MinimalKundliInput):
    """
    Calculate Sun Sign (Western/Tropical Zodiac) using accurate astronomical data

    This endpoint calculates the Sun's position at birth to determine the Sun Sign.
    Requires: name, date_of_birth, time_of_birth, place_of_birth for accurate calculation.

    Returns:
        - Sun sign name and symbol
        - Element, quality, and ruling planet
        - Lucky color and number
        - Key personality traits
    """
    try:
        # Convert minimal input to full KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info(f"Calculating Sun Sign for {req.name}")

        # Get Sun's position from planetary calculations
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)
        sun_data = planets.get('Sun')

        if not sun_data:
            raise HTTPException(status_code=500, detail="Could not calculate Sun position")

        # Sun sign details with traits
        sun_sign_details = {
            'Aries': {
                'symbol': '♈', 'element': 'Fire', 'quality': 'Cardinal', 'ruling_planet': 'Mars',
                'lucky_color': 'Red', 'lucky_number': 9,
                'traits': ['Courageous', 'Passionate', 'Confident', 'Direct', 'Independent']
            },
            'Taurus': {
                'symbol': '♉', 'element': 'Earth', 'quality': 'Fixed', 'ruling_planet': 'Venus',
                'lucky_color': 'Green', 'lucky_number': 6,
                'traits': ['Practical', 'Loyal', 'Sensual', 'Determined', 'Stable']
            },
            'Gemini': {
                'symbol': '♊', 'element': 'Air', 'quality': 'Mutable', 'ruling_planet': 'Mercury',
                'lucky_color': 'Yellow', 'lucky_number': 5,
                'traits': ['Versatile', 'Witty', 'Social', 'Quick-thinking', 'Expressive']
            },
            'Cancer': {
                'symbol': '♋', 'element': 'Water', 'quality': 'Cardinal', 'ruling_planet': 'Moon',
                'lucky_color': 'Silver', 'lucky_number': 2,
                'traits': ['Caring', 'Protective', 'Emotional', 'Intuitive', 'Loyal']
            },
            'Leo': {
                'symbol': '♌', 'element': 'Fire', 'quality': 'Fixed', 'ruling_planet': 'Sun',
                'lucky_color': 'Gold', 'lucky_number': 1,
                'traits': ['Creative', 'Passionate', 'Generous', 'Warm-hearted', 'Cheerful']
            },
            'Virgo': {
                'symbol': '♍', 'element': 'Earth', 'quality': 'Mutable', 'ruling_planet': 'Mercury',
                'lucky_color': 'Navy Blue', 'lucky_number': 5,
                'traits': ['Detail-oriented', 'Practical', 'Hardworking', 'Reliable', 'Kind']
            },
            'Libra': {
                'symbol': '♎', 'element': 'Air', 'quality': 'Cardinal', 'ruling_planet': 'Venus',
                'lucky_color': 'Pink', 'lucky_number': 6,
                'traits': ['Balanced', 'Diplomatic', 'Social', 'Fair-minded', 'Gracious']
            },
            'Scorpio': {
                'symbol': '♏', 'element': 'Water', 'quality': 'Fixed', 'ruling_planet': 'Mars/Pluto',
                'lucky_color': 'Maroon', 'lucky_number': 9,
                'traits': ['Passionate', 'Brave', 'Resourceful', 'Stubborn', 'Loyal']
            },
            'Sagittarius': {
                'symbol': '♐', 'element': 'Fire', 'quality': 'Mutable', 'ruling_planet': 'Jupiter',
                'lucky_color': 'Purple', 'lucky_number': 3,
                'traits': ['Adventurous', 'Optimistic', 'Honest', 'Independent', 'Philosophical']
            },
            'Capricorn': {
                'symbol': '♑', 'element': 'Earth', 'quality': 'Cardinal', 'ruling_planet': 'Saturn',
                'lucky_color': 'Brown', 'lucky_number': 8,
                'traits': ['Responsible', 'Disciplined', 'Self-controlled', 'Ambitious', 'Patient']
            },
            'Aquarius': {
                'symbol': '♒', 'element': 'Air', 'quality': 'Fixed', 'ruling_planet': 'Saturn/Uranus',
                'lucky_color': 'Electric Blue', 'lucky_number': 4,
                'traits': ['Independent', 'Progressive', 'Original', 'Humanitarian', 'Intellectual']
            },
            'Pisces': {
                'symbol': '♓', 'element': 'Water', 'quality': 'Mutable', 'ruling_planet': 'Jupiter/Neptune',
                'lucky_color': 'Sea Green', 'lucky_number': 7,
                'traits': ['Compassionate', 'Artistic', 'Intuitive', 'Gentle', 'Wise']
            },
        }

        sun_sign = sun_data.sign
        details = sun_sign_details.get(sun_sign, {})

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth,
            },
            "sun_sign": {
                "sign": sun_sign,
                "symbol": details.get('symbol', ''),
                "element": details.get('element', ''),
                "quality": details.get('quality', ''),
                "ruling_planet": details.get('ruling_planet', ''),
                "lucky_color": details.get('lucky_color', ''),
                "lucky_number": details.get('lucky_number', 0),
                "traits": details.get('traits', []),
                "sun_degree": round(sun_data.degree, 2),
                "sun_degree_dms": sun_data.degree_dms,
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Sun Sign: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Sun Sign: {str(e)}")


@router.post("/api/calculators/nakshatra")
async def calculate_nakshatra_only(req: MinimalKundliInput):
    """
    Calculate Nakshatra (Lunar Mansion) using accurate Vedic astrology

    This endpoint calculates the Moon's nakshatra at birth with detailed information.
    Requires: name, date_of_birth, time_of_birth, place_of_birth for accurate calculation.

    Returns:
        - Nakshatra name, lord, and pada
        - Symbol, deity, and gana
        - Characteristics and element
        - Lucky color
    """
    try:
        # Convert minimal input to full KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info(f"Calculating Nakshatra for {req.name}")

        # Calculate Julian Day
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

        # Get Moon's nakshatra
        moon_nakshatra = kundali_engine._get_moon_nakshatra(jd)

        # Get Moon's position for additional details
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)
        moon_data = planets.get('Moon')

        # Comprehensive nakshatra details
        nakshatra_details = {
            'Ashwini': {
                'symbol': 'Horse Head', 'deity': 'Ashwini Kumaras', 'gana': 'Deva (Divine)',
                'element': 'Earth', 'lucky_color': 'Red',
                'characteristics': ['Quick', 'Healing', 'Pioneering', 'Enthusiastic', 'Independent']
            },
            'Bharani': {
                'symbol': 'Yoni (Womb)', 'deity': 'Yama', 'gana': 'Manushya (Human)',
                'element': 'Earth', 'lucky_color': 'Red',
                'characteristics': ['Creative', 'Passionate', 'Responsible', 'Determined', 'Nurturing']
            },
            'Krittika': {
                'symbol': 'Razor/Flame', 'deity': 'Agni', 'gana': 'Rakshasa (Demon)',
                'element': 'Earth', 'lucky_color': 'White',
                'characteristics': ['Sharp', 'Determined', 'Ambitious', 'Purifying', 'Direct']
            },
            'Rohini': {
                'symbol': 'Cart/Chariot', 'deity': 'Brahma', 'gana': 'Manushya (Human)',
                'element': 'Earth', 'lucky_color': 'White',
                'characteristics': ['Beautiful', 'Creative', 'Sensual', 'Materialistic', 'Growth']
            },
            'Mrigashira': {
                'symbol': 'Deer Head', 'deity': 'Soma', 'gana': 'Deva (Divine)',
                'element': 'Earth', 'lucky_color': 'Silver',
                'characteristics': ['Curious', 'Searching', 'Gentle', 'Suspicious', 'Restless']
            },
            'Ardra': {
                'symbol': 'Teardrop/Diamond', 'deity': 'Rudra', 'gana': 'Manushya (Human)',
                'element': 'Air', 'lucky_color': 'Green',
                'characteristics': ['Transformative', 'Intense', 'Emotional', 'Destructive', 'Renewal']
            },
            'Punarvasu': {
                'symbol': 'Bow and Quiver', 'deity': 'Aditi', 'gana': 'Deva (Divine)',
                'element': 'Air', 'lucky_color': 'Yellow',
                'characteristics': ['Optimistic', 'Repetitive', 'Philosophical', 'Protective', 'Generous']
            },
            'Pushya': {
                'symbol': 'Cow Udder/Lotus', 'deity': 'Brihaspati', 'gana': 'Deva (Divine)',
                'element': 'Water', 'lucky_color': 'Orange',
                'characteristics': ['Nurturing', 'Spiritual', 'Disciplined', 'Conservative', 'Devoted']
            },
            'Ashlesha': {
                'symbol': 'Coiled Serpent', 'deity': 'Nagas', 'gana': 'Rakshasa (Demon)',
                'element': 'Water', 'lucky_color': 'Red',
                'characteristics': ['Mystical', 'Secretive', 'Intuitive', 'Cunning', 'Powerful']
            },
            'Magha': {
                'symbol': 'Royal Throne', 'deity': 'Pitris (Ancestors)', 'gana': 'Rakshasa (Demon)',
                'element': 'Water', 'lucky_color': 'Ivory',
                'characteristics': ['Royal', 'Authoritative', 'Proud', 'Traditional', 'Respectful']
            },
            'Purva Phalguni': {
                'symbol': 'Front Legs of Bed', 'deity': 'Bhaga', 'gana': 'Manushya (Human)',
                'element': 'Water', 'lucky_color': 'Light Brown',
                'characteristics': ['Creative', 'Pleasure-loving', 'Artistic', 'Relaxing', 'Generous']
            },
            'Uttara Phalguni': {
                'symbol': 'Back Legs of Bed', 'deity': 'Aryaman', 'gana': 'Manushya (Human)',
                'element': 'Fire', 'lucky_color': 'Bright Blue',
                'characteristics': ['Generous', 'Friendly', 'Responsible', 'Leadership', 'Helpful']
            },
            'Hasta': {
                'symbol': 'Hand/Fist', 'deity': 'Savitar', 'gana': 'Deva (Divine)',
                'element': 'Fire', 'lucky_color': 'Light Green',
                'characteristics': ['Skillful', 'Hardworking', 'Clever', 'Humorous', 'Dexterous']
            },
            'Chitra': {
                'symbol': 'Bright Jewel/Pearl', 'deity': 'Tvashtar', 'gana': 'Rakshasa (Demon)',
                'element': 'Fire', 'lucky_color': 'Black',
                'characteristics': ['Creative', 'Charismatic', 'Artistic', 'Ambitious', 'Bright']
            },
            'Swati': {
                'symbol': 'Young Sprout/Coral', 'deity': 'Vayu', 'gana': 'Deva (Divine)',
                'element': 'Fire', 'lucky_color': 'Black',
                'characteristics': ['Independent', 'Flexible', 'Business-minded', 'Diplomatic', 'Restless']
            },
            'Vishakha': {
                'symbol': 'Triumphal Archway', 'deity': 'Indra-Agni', 'gana': 'Rakshasa (Demon)',
                'element': 'Fire', 'lucky_color': 'Gold',
                'characteristics': ['Determined', 'Goal-oriented', 'Ambitious', 'Powerful', 'Patient']
            },
            'Anuradha': {
                'symbol': 'Lotus/Triumphal Archway', 'deity': 'Mitra', 'gana': 'Deva (Divine)',
                'element': 'Fire', 'lucky_color': 'Reddish Brown',
                'characteristics': ['Devoted', 'Balanced', 'Friendly', 'Spiritual', 'Disciplined']
            },
            'Jyeshtha': {
                'symbol': 'Circular Amulet/Earring', 'deity': 'Indra', 'gana': 'Rakshasa (Demon)',
                'element': 'Air', 'lucky_color': 'Cream',
                'characteristics': ['Authoritative', 'Protective', 'Responsible', 'Generous', 'Mature']
            },
            'Mula': {
                'symbol': 'Tied Roots/Elephant Goad', 'deity': 'Nirriti', 'gana': 'Rakshasa (Demon)',
                'element': 'Air', 'lucky_color': 'Brown',
                'characteristics': ['Investigative', 'Transformative', 'Philosophical', 'Destructive', 'Rooted']
            },
            'Purva Ashadha': {
                'symbol': 'Elephant Tusk/Fan', 'deity': 'Apas', 'gana': 'Manushya (Human)',
                'element': 'Air', 'lucky_color': 'Black',
                'characteristics': ['Invincible', 'Proud', 'Philosophical', 'Purifying', 'Ambitious']
            },
            'Uttara Ashadha': {
                'symbol': 'Elephant Tusk/Planks of Bed', 'deity': 'Vishvadevas', 'gana': 'Manushya (Human)',
                'element': 'Air', 'lucky_color': 'Copper',
                'characteristics': ['Righteous', 'Leadership', 'Ambitious', 'Grateful', 'Principled']
            },
            'Shravana': {
                'symbol': 'Three Footprints/Ear', 'deity': 'Vishnu', 'gana': 'Deva (Divine)',
                'element': 'Air', 'lucky_color': 'Light Blue',
                'characteristics': ['Listening', 'Learning', 'Communicative', 'Thoughtful', 'Organized']
            },
            'Dhanishta': {
                'symbol': 'Drum/Flute', 'deity': 'Eight Vasus', 'gana': 'Rakshasa (Demon)',
                'element': 'Ether', 'lucky_color': 'Silver Grey',
                'characteristics': ['Musical', 'Wealthy', 'Charitable', 'Bold', 'Adaptable']
            },
            'Shatabhisha': {
                'symbol': 'Empty Circle/1000 Flowers', 'deity': 'Varuna', 'gana': 'Rakshasa (Demon)',
                'element': 'Ether', 'lucky_color': 'Blue Green',
                'characteristics': ['Healing', 'Secretive', 'Scientific', 'Mystical', 'Independent']
            },
            'Purva Bhadrapada': {
                'symbol': 'Front Legs of Funeral Cot/Two Faced Man', 'deity': 'Aja Ekapada', 'gana': 'Manushya (Human)',
                'element': 'Ether', 'lucky_color': 'Silver Grey',
                'characteristics': ['Intense', 'Passionate', 'Transformative', 'Mystical', 'Dualistic']
            },
            'Uttara Bhadrapada': {
                'symbol': 'Back Legs of Funeral Cot/Twins', 'deity': 'Ahir Budhnya', 'gana': 'Manushya (Human)',
                'element': 'Ether', 'lucky_color': 'Purple',
                'characteristics': ['Wise', 'Spiritual', 'Patient', 'Calm', 'Mystical']
            },
            'Revati': {
                'symbol': 'Fish/Drum', 'deity': 'Pushan', 'gana': 'Deva (Divine)',
                'element': 'Ether', 'lucky_color': 'Brown',
                'characteristics': ['Nurturing', 'Protective', 'Compassionate', 'Wealthy', 'Journey']
            },
        }

        nakshatra_name = moon_nakshatra.name
        details = nakshatra_details.get(nakshatra_name, {})

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth,
            },
            "nakshatra": {
                "name": nakshatra_name,
                "pada": moon_nakshatra.pada,
                "lord": moon_nakshatra.lord,
                "symbol": details.get('symbol', ''),
                "deity": details.get('deity', ''),
                "gana": details.get('gana', ''),
                "element": details.get('element', ''),
                "lucky_color": details.get('lucky_color', ''),
                "characteristics": details.get('characteristics', []),
            },
            "moon_position": {
                "sign": moon_data.sign if moon_data else '',
                "degree": round(moon_data.degree, 2) if moon_data else 0,
                "degree_dms": moon_data.degree_dms if moon_data else '',
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Nakshatra: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Nakshatra: {str(e)}")


@router.post("/api/calculators/numerology")
async def calculate_numerology(req: MinimalKundliInput):
    """
    Calculate comprehensive Numerology analysis

    This endpoint calculates multiple numerology numbers from birth date and name.
    Requires: name, date_of_birth for accurate calculation.

    Returns:
        - Life Path Number with meaning
        - Destiny Number (from name)
        - Soul Urge Number (from vowels)
        - Personality Number (from consonants)
        - Lucky Numbers
    """
    try:
        logger.info(f"Calculating Numerology for {req.name}")

        # Parse date of birth
        from api.input_normalizer import _parse_date
        year, month, day = _parse_date(req.date_of_birth)

        # Helper functions for numerology calculations
        def reduce_to_single_digit(num: int) -> int:
            """Reduce a number to single digit, keeping master numbers 11, 22, 33"""
            if num in [11, 22, 33]:
                return num
            while num > 9:
                num = sum(int(digit) for digit in str(num))
            return num

        def get_letter_value(letter: str) -> int:
            """Get numerology value of a letter (A=1, B=2, ... Z=8)"""
            values = {
                'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
                'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
                's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8,
            }
            return values.get(letter.lower(), 0)

        def get_name_value(name: str) -> int:
            """Calculate total value of a name"""
            clean_name = ''.join(c.lower() for c in name if c.isalpha())
            return sum(get_letter_value(char) for char in clean_name)

        # 1. Calculate Life Path Number
        reduced_day = reduce_to_single_digit(day)
        reduced_month = reduce_to_single_digit(month)
        reduced_year = reduce_to_single_digit(year)
        life_path_number = reduce_to_single_digit(reduced_day + reduced_month + reduced_year)

        # 2. Calculate Destiny Number (from full name)
        name_value = get_name_value(req.name)
        destiny_number = reduce_to_single_digit(name_value)

        # 3. Calculate Soul Urge Number (from vowels in name)
        vowels = 'aeiou'
        vowel_value = sum(
            get_letter_value(char)
            for char in req.name.lower()
            if char in vowels
        )
        soul_urge_number = reduce_to_single_digit(vowel_value)

        # 4. Calculate Personality Number (from consonants in name)
        consonant_value = sum(
            get_letter_value(char)
            for char in req.name.lower()
            if char.isalpha() and char not in vowels
        )
        personality_number = reduce_to_single_digit(consonant_value)

        # 5. Calculate Lucky Numbers
        lucky_numbers = list(set([
            life_path_number,
            reduce_to_single_digit(day),
            reduce_to_single_digit(month),
            reduce_to_single_digit(day + month),
            reduce_to_single_digit(life_path_number * 2) if reduce_to_single_digit(life_path_number * 2) <= 9 else reduce_to_single_digit(life_path_number + 1)
        ]))
        lucky_numbers.sort()

        # Number meanings
        life_path_meanings = {
            1: "The Leader - Independent, ambitious, and pioneering. Natural leader with strong willpower.",
            2: "The Peacemaker - Diplomatic, cooperative, and sensitive. Excel in partnerships and teamwork.",
            3: "The Creative - Expressive, optimistic, and social. Gift for communication and creativity.",
            4: "The Builder - Practical, disciplined, and hardworking. Create solid foundations and value stability.",
            5: "The Freedom Seeker - Adventurous, versatile, and energetic. Love freedom and new experiences.",
            6: "The Nurturer - Responsible, caring, and harmonious. Devoted to family and community service.",
            7: "The Seeker - Analytical, spiritual, and introspective. Seek knowledge and deeper understanding.",
            8: "The Powerhouse - Ambitious, authoritative, and success-oriented. Strong business acumen.",
            9: "The Humanitarian - Compassionate, generous, and idealistic. Devoted to making the world better.",
            11: "The Visionary - Intuitive, inspirational, and enlightened. Master number with spiritual insights.",
            22: "The Master Builder - Practical visionary who can turn dreams into reality on a large scale.",
            33: "The Master Teacher - Devoted to uplifting humanity through selfless service and guidance.",
        }

        destiny_meanings = {
            1: "Destined to be a leader and pioneer, breaking new ground and inspiring others.",
            2: "Destiny involves diplomacy, partnership, and bringing people together in harmony.",
            3: "Meant to express yourself creatively and bring joy to others through your talents.",
            4: "Destiny is to build lasting structures and provide stability for yourself and others.",
            5: "Destined for a life of adventure, change, and helping others embrace freedom.",
            6: "Destiny involves nurturing, teaching, and creating harmony in your community.",
            7: "Meant to seek and share wisdom, pursuing spiritual and intellectual growth.",
            8: "Destiny involves achieving material success and using it to benefit others.",
            9: "Destined to serve humanity and make significant contributions to society.",
            11: "Destiny is to inspire and enlighten others with your spiritual insights.",
            22: "Meant to turn grand visions into tangible reality that benefits many.",
            33: "Destiny is to teach and uplift humanity through compassionate service.",
        }

        soul_urge_meanings = {
            1: "Deep desire for independence, leadership, and individual achievement.",
            2: "Inner need for harmony, partnership, and peaceful relationships.",
            3: "Soul craves creative expression, joy, and social interaction.",
            4: "Inner desire for stability, order, and building something lasting.",
            5: "Soul seeks freedom, adventure, and variety in life experiences.",
            6: "Deep need to nurture, serve, and create harmony for others.",
            7: "Inner desire for knowledge, spirituality, and understanding life's mysteries.",
            8: "Soul craves success, power, and material achievement.",
            9: "Deep desire to serve humanity and make a positive difference.",
            11: "Soul seeks spiritual enlightenment and inspiring others.",
            22: "Inner need to build something grand that benefits humanity.",
            33: "Deep desire to teach and heal through compassionate service.",
        }

        personality_meanings = {
            1: "Appear confident, independent, and strong-willed to others.",
            2: "Come across as gentle, diplomatic, and approachable.",
            3: "Appear creative, charming, and socially engaging.",
            4: "Come across as practical, reliable, and hardworking.",
            5: "Appear adventurous, energetic, and freedom-loving.",
            6: "Come across as caring, responsible, and harmonious.",
            7: "Appear mysterious, introspective, and intellectual.",
            8: "Come across as powerful, ambitious, and authoritative.",
            9: "Appear compassionate, generous, and idealistic.",
            11: "Come across as inspiring, intuitive, and enlightened.",
            22: "Appear as a visionary builder with grand plans.",
            33: "Come across as a compassionate teacher and healer.",
        }

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
            },
            "numerology": {
                "life_path_number": {
                    "number": life_path_number,
                    "meaning": life_path_meanings.get(life_path_number, "Unique path with special significance."),
                    "calculation": f"{day} + {month} + {year} = {reduced_day} + {reduced_month} + {reduced_year} = {life_path_number}"
                },
                "destiny_number": {
                    "number": destiny_number,
                    "meaning": destiny_meanings.get(destiny_number, "You have a unique destiny path."),
                    "calculation": f"Name value: {name_value} → {destiny_number}"
                },
                "soul_urge_number": {
                    "number": soul_urge_number,
                    "meaning": soul_urge_meanings.get(soul_urge_number, "Unique inner desires."),
                    "calculation": f"Vowel value: {vowel_value} → {soul_urge_number}"
                },
                "personality_number": {
                    "number": personality_number,
                    "meaning": personality_meanings.get(personality_number, "Unique outer personality."),
                    "calculation": f"Consonant value: {consonant_value} → {personality_number}"
                },
                "lucky_numbers": lucky_numbers,
                "master_number": life_path_number in [11, 22, 33] or destiny_number in [11, 22, 33]
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Numerology: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Numerology: {str(e)}")


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
