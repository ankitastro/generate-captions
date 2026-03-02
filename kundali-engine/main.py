"""
FastAPI application for Kundali Generation Service

Refactored to use modular endpoint structure
"""

from datetime import datetime
import logging
import os
import traceback
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

# Import modular routers
from api.endpoints import (
    common_router,
    kundli_router,
    charts_router,
    calculators_router,
    specialized_router,
    dasha_router,
    gochar_router
)

# Import models and other dependencies still needed in main.py
from models import KundaliRequest, MinimalKundliInput
from api.input_normalizer import minimal_to_kundali_request
from kundali_engine import KundaliEngine
from core.interpretation_engine import InterpretationEngine
from translation_manager import get_translation_manager
from horoscope.narrative_horoscope import generate_structured_horoscope, ZODIAC_SIGNS
from api.services.kundli_service import get_engine, get_translation_mgr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Kundali Generation Service",
    description="A comprehensive Vedic astrology service for generating Kundali (birth charts) using drik-panchanga",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)

# Setup Jinja2 templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(templates_dir))

# Initialize the Kundali Engine (shared across modules)
kundali_engine = KundaliEngine()

# Initialize Translation Manager
translation_manager = get_translation_manager()

# ==================== INCLUDE ROUTERS ====================

# Common endpoints (health, languages, docs, root)
app.include_router(common_router, prefix="/api/v1/kundali")

# Kundli core endpoints (generate-kundli, birth-details, kundli, yogas, interpretation, report)
app.include_router(kundli_router, prefix="/api/v1/kundali")

# Charts endpoints (api/charts)
app.include_router(charts_router, prefix="/api/v1/kundali")

# Calculator endpoints (rashi, sun-sign, nakshatra, numerology)
app.include_router(calculators_router, prefix="/api/v1/kundali")

# Specialized endpoints (kp-system, bhava-chalit, horoscope, doshas, matching, ashtakavarga, complete)
app.include_router(specialized_router, prefix="/api/v1/kundali")

# Dasha endpoints (vimshottari, pratyantar, sukshma, prana dasha levels)
app.include_router(dasha_router, prefix="/api/v1/kundali")

# Gochar (Transit) endpoints (current transits, date-range, upcoming transits, special-focus, sade-sati, compare)
app.include_router(gochar_router,prefix="/api/v1/kundali")


# ==================== HTML FORM ENDPOINT ====================

@app.get("/form", response_class=HTMLResponse)
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


# ==================== HTML REPORT ENDPOINT ====================

@app.post("/generate-kundali-html", response_class=HTMLResponse)
async def generate_kundali_html(min_req: MinimalKundliInput):
    """
    Generate a complete styled Kundali HTML report from minimal birth details.

    This is a complex endpoint that generates a full HTML report with varga charts.
    Kept in main.py due to its complexity and template dependencies.
    """
    try:
        kundali_engine = get_engine()
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

        # ---- Domain validations ----
        if full_req.datetime > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Birth date cannot be in the future.")

        # ---- Generate base kundali data ----
        kundali = kundali_engine.generate_kundali(full_req)

        # ---- Varga Charts & Strengths (simplified - would include full implementation) ----
        major_vargas = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 30]
        additional_vargas = [27, 40, 45, 60]

        # Prepare degrees for strength analysis
        sign_order = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                      "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        planet_degrees = {}
        for p in kundali.planets:
            sign_index = sign_order.index(p.sign)
            abs_long = sign_index * 30 + p.degree
            planet_degrees[p.planet] = abs_long

        from core import varga_engine
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

        # Simplified strength calculation
        varga_strengths = {}
        for v, chart in major_varga_raw.items():
            label = varga_names.get(v, f"D{v}")
            from api.utils.constants import SIGN_NAMES
            varga_strengths[label] = varga_engine.get_varga_planet_strength(planet_degrees, v)

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

        # ---- Prepare Translated Labels ----
        lang = min_req.language if min_req.language else 'en'
        translation_manager = get_translation_mgr()
        labels = {
            "description": translation_manager.translate('yogas.description', lang, default='Description'),
            "significance": translation_manager.translate('yogas.significance', lang, default='Significance'),
            "effects": translation_manager.translate('yogas.effects', lang, default='Effects'),
            "planets_involved": translation_manager.translate('yogas.planets_involved', lang, default='Planets Involved'),
            "houses_involved": translation_manager.translate('yogas.houses_involved', lang, default='Houses Involved'),
            "strength": translation_manager.translate('yogas.strength', lang, default='Strength')
        }

        # ---- Prepare Template Data ----
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


# ==================== PLANETARY HOROSCOPE ENDPOINT ====================

@app.get("/api/v1/planetary-horoscope/{sign}")
async def get_planetary_horoscope(
    sign: str,
    scope: str = Query("daily", description="Time scope (currently only 'daily' supported)"),
    latitude: float = Query(12.972, description="Latitude for calculations (default: Bangalore)"),
    longitude: float = Query(77.594, description="Longitude for calculations (default: Bangalore)"),
    timezone: float = Query(5.5, description="Timezone offset (default: IST +5.5)"),
    date: str = Query(None, description="Date in YYYY-MM-DD format (default: today)"),
    language: str = Query("en", description="Language code: en (English) or hi (Hindi)")
):
    """
    Get planetary horoscope based on real astronomical data using Swiss Ephemeris
    """
    try:
        from horoscope import generate_planetary_horoscope, VALID_SCOPES

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


# ==================== ADDITIONAL UTILITY ENDPOINTS ====================

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
    from horoscope import VALID_SCOPES
    return {
        "error": False,
        "data": {
            "scopes": VALID_SCOPES,
            "static_horoscope_scopes": VALID_SCOPES,
            "planetary_horoscope_scopes": ["daily"]
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/docs")
async def get_api_docs():
    """API documentation for horoscope endpoints"""
    from horoscope import VALID_SCOPES
    docs = {
        "api_version": "v1",
        "service": "Kundali & Horoscope API",
        "endpoints": {
            "kundali_endpoints": {
                "POST /generate-kundli": "Generate Vedic birth chart",
                "POST /generate-kundali-html": "Generate HTML birth chart report",
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


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
