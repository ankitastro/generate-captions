"""
Gochar (Transit) API Endpoints
Provides endpoints for transit analysis
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models import (
    GocharRequest, GocharAnalysis, GocharDateRangeRequest,
    MinimalKundliInput, ErrorResponse, KundaliRequest
)
from core.gochar import GocharEngine
import svg_chart_generator
from api.input_normalizer import minimal_to_kundali_request
from translation_manager import get_translation_manager


# Create router
router = APIRouter()

# Initialize Gochar engine
gochar_engine = GocharEngine()
translation_manager = get_translation_manager()


@router.post("/current")
async def get_current_gochar(request: GocharRequest):
    """
    Get current Gochar (transit) analysis

    This endpoint provides a comprehensive analysis of current planetary
    transits and their effects on the user's birth chart.

    Args:
        request: GocharRequest containing birth details and optional reference date

    Returns:
        Complete Gochar analysis including:
        - Current planetary positions from Moon and Lagna
        - Nature and effects of each transit
        - Overall score and verdict
        - Life aspect analysis (career, finance, relationships, health, education)
        - Special transits (Sade Sati, Kantak Shani, etc.)
        - Upcoming significant transits
        - Recommendations and remedies
        - Astrologer notes

    Example:
        POST /api/v1/gochar/current
        {
            "input": {
                "name": "John Doe",
                "date_of_birth": "15/08/1990",
                "time_of_birth": "10:30",
                "place_of_birth": "Mumbai, India"
            },
            "reference_date": "2026-02-08",  # Optional
            "language": "en"
        }
    """
    try:
        # Normalize input to KundaliRequest
        kundali_request = minimal_to_kundali_request(request.input)

        # Parse reference date if provided
        reference_date = None
        if request.reference_date:
            try:
                reference_date = datetime.strptime(request.reference_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid reference_date format. Use YYYY-MM-DD"
                )

        # Calculate Gochar analysis
        gochar_analysis = gochar_engine.calculate_gochar(
            kundali_request=kundali_request,
            reference_date=reference_date,
            language=request.language or 'en'
        )

        return gochar_analysis

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating Gochar analysis: {str(e)}"
        )


@router.post("/date-range")
async def get_gochar_for_date_range(request: GocharDateRangeRequest):
    """
    Get Gochar analysis for a date range

    This endpoint calculates Gochar analysis for each month in the specified
    date range, useful for planning future events and understanding
    transit patterns over time.

    Args:
        request: GocharDateRangeRequest containing birth details, start date, and end date

    Returns:
        Dictionary containing monthly Gochar analyses

    Example:
        POST /api/v1/gochar/date-range
        {
            "input": {
                "name": "John Doe",
                "date_of_birth": "15/08/1990",
                "time_of_birth": "10:30",
                "place_of_birth": "Mumbai, India"
            },
            "start_date": "2026-02-01",
            "end_date": "2026-08-01",
            "language": "en"
        }
    """
    try:
        # Normalize input to KundaliRequest
        kundali_request = minimal_to_kundali_request(request.input)

        # Parse dates
        try:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date"
            )

        # Calculate date difference in months
        date_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

        if date_diff > 24:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 24 months"
            )

        # Generate monthly analyses
        monthly_analyses = {}
        current_date = start_date

        while current_date < end_date:
            month_key = current_date.strftime("%Y-%m")

            try:
                gochar_analysis = gochar_engine.calculate_gochar(
                    kundali_request=kundali_request,
                    reference_date=current_date,
                    language=request.language or 'en'
                )

                # Convert to dict for JSON serialization
                monthly_analyses[month_key] = gochar_analysis.dict()

            except Exception as e:
                # If calculation fails for a specific date, continue with next
                monthly_analyses[month_key] = {
                    "error": f"Unable to calculate for this date: {str(e)}"
                }

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        return {
            "input": {
                "name": request.input.name,
                "date_of_birth": request.input.date_of_birth,
                "place_of_birth": request.input.place_of_birth
            },
            "start_date": request.start_date,
            "end_date": request.end_date,
            "total_months": date_diff,
            "monthly_analyses": monthly_analyses
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating date range Gochar: {str(e)}"
        )


@router.post("/upcoming-transits")
async def get_upcoming_transits(
    input: MinimalKundliInput,
    months: int = 6,
    language: str = 'en'
):
    """
    Get upcoming significant transits

    This endpoint provides information about upcoming major planetary transits
    that will significantly impact the user's birth chart. Useful for
    planning and preparation.

    Args:
        input: User's birth details
        months: Number of months to look ahead (default: 6, max: 24)
        language: Response language (default: 'en')

    Returns:
        List of upcoming significant transits with dates, effects, and recommendations

    Example:
        POST /api/v1/gochar/upcoming-transits?months=12&language=en
        {
            "name": "John Doe",
            "date_of_birth": "15/08/1990",
            "time_of_birth": "10:30",
            "place_of_birth": "Mumbai, India"
        }
    """
    try:
        # Validate months parameter
        if months < 1 or months > 24:
            raise HTTPException(
                status_code=400,
                detail="months parameter must be between 1 and 24"
            )

        # Normalize input to KundaliRequest
        kundali_request = minimal_to_kundali_request(input)

        # Calculate current Gochar to get birth chart reference
        current_gochar = gochar_engine.calculate_gochar(
            kundali_request=kundali_request,
            reference_date=datetime.now(),
            language=language
        )

        # Extract upcoming transits from current analysis
        upcoming_transits = current_gochar.upcoming_transits

        # Filter transits within the specified months
        filtered_transits = []
        for transit in upcoming_transits:
            transit_date = datetime.strptime(transit.date, "%Y-%m-%d")
            months_diff = (transit_date.year - datetime.now().year) * 12 + (transit_date.month - datetime.now().month)

            if months_diff <= months:
                filtered_transits.append(transit)

        return {
            "input": {
                "name": input.name,
                "date_of_birth": input.date_of_birth,
                "place_of_birth": input.place_of_birth
            },
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "months_ahead": months,
            "upcoming_transits": filtered_transits,
            "birth_chart_reference": current_gochar.birth_chart_reference.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting upcoming transits: {str(e)}"
        )


@router.post("/special-focus")
async def get_aspect_focused_gochar(
    input: MinimalKundliInput,
    aspect: str,
    reference_date: Optional[str] = None,
    language: str = 'en'
):
    """
    Get Gochar analysis focused on specific life aspect

    This endpoint provides detailed analysis of a specific life aspect
    (career, finance, relationships, health, education) based on
    current planetary transits.

    Args:
        input: User's birth details
        aspect: Life aspect to focus on (career/finance/relationships/health/education)
        reference_date: Date for analysis (default: today)
        language: Response language (default: 'en')

    Returns:
        Detailed analysis of the specified life aspect with predictions,
        recommendations, and influencing planets

    Example:
        POST /api/v1/gochar/special-focus?aspect=career&language=en
        {
            "name": "John Doe",
            "date_of_birth": "15/08/1990",
            "time_of_birth": "10:30",
            "place_of_birth": "Mumbai, India"
        }
    """
    try:
        # Validate aspect parameter
        valid_aspects = ['career', 'finance', 'relationships', 'health', 'education']
        if aspect not in valid_aspects:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid aspect. Must be one of: {', '.join(valid_aspects)}"
            )

        # Normalize input to KundaliRequest
        kundali_request = minimal_to_kundali_request(input)

        # Parse reference date if provided
        ref_date = None
        if reference_date:
            try:
                ref_date = datetime.strptime(reference_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid reference_date format. Use YYYY-MM-DD"
                )

        # Calculate full Gochar analysis
        gochar_analysis = gochar_engine.calculate_gochar(
            kundali_request=kundali_request,
            reference_date=ref_date,
            language=language
        )

        # Extract the focused aspect
        aspect_analysis = gochar_analysis.life_aspects.get(aspect)

        if not aspect_analysis:
            raise HTTPException(
                status_code=500,
                detail=f"Could not retrieve analysis for aspect: {aspect}"
            )

        # Get relevant transits for this aspect
        influencing_planets = aspect_analysis.influencing_planets
        relevant_transits = {
            planet: gochar_analysis.current_transits[planet]
            for planet in influencing_planets
            if planet in gochar_analysis.current_transits
        }

        return {
            "input": {
                "name": input.name,
                "date_of_birth": input.date_of_birth,
                "place_of_birth": input.place_of_birth
            },
            "analysis_date": gochar_analysis.analysis_date,
            "aspect": aspect,
            "aspect_analysis": aspect_analysis.dict(),
            "relevant_transits": relevant_transits,
            "overall_score": gochar_analysis.overall_score.dict(),
            "special_transits": gochar_analysis.special_transits
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating aspect-focused Gochar: {str(e)}"
        )


@router.post("/sade-sati-status")
async def get_sade_sati_status(
    input: MinimalKundliInput,
    language: str = 'en'
):
    """
    Get detailed Sade Sati analysis

    This endpoint provides comprehensive information about Sade Sati period,
    including current phase, effects, remedies, and timeline.

    Args:
        input: User's birth details
        language: Response language (default: 'en')

    Returns:
        Detailed Sade Sati analysis including phase, effects, remedies, and timing

    Example:
        POST /api/v1/gochar/sade-sati-status?language=en
        {
            "name": "John Doe",
            "date_of_birth": "15/08/1990",
            "time_of_birth": "10:30",
            "place_of_birth": "Mumbai, India"
        }
    """
    try:
        # Normalize input to KundaliRequest
        kundali_request = minimal_to_kundali_request(input)

        # Calculate current Gochar analysis
        gochar_analysis = gochar_engine.calculate_gochar(
            kundali_request=kundali_request,
            reference_date=datetime.now(),
            language=language
        )

        # Extract Sade Sati information
        sade_sati_info = gochar_analysis.special_transits.get('sade_sati')

        if sade_sati_info and sade_sati_info.is_active:
            return {
                "input": {
                    "name": input.name,
                    "date_of_birth": input.date_of_birth,
                    "place_of_birth": input.place_of_birth
                },
                "analysis_date": gochar_analysis.analysis_date,
                "is_in_sade_sati": True,
                "moon_sign": gochar_analysis.birth_chart_reference.moon_sign,
                "sade_sati_details": sade_sati_info.dict(),
                "saturn_transit": gochar_analysis.current_transits.get('Saturn').dict() if 'Saturn' in gochar_analysis.current_transits else None,
                "recommendations": gochar_analysis.recommendations.dict()
            }
        else:
            return {
                "input": {
                    "name": input.name,
                    "date_of_birth": input.date_of_birth,
                    "place_of_birth": input.place_of_birth
                },
                "analysis_date": gochar_analysis.analysis_date,
                "is_in_sade_sati": False,
                "message": "You are not currently in Sade Sati period.",
                "moon_sign": gochar_analysis.birth_chart_reference.moon_sign,
                "saturn_transit": gochar_analysis.current_transits.get('Saturn').dict() if 'Saturn' in gochar_analysis.current_transits else None
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating Sade Sati status: {str(e)}"
        )


@router.post("/chart")
async def get_gochar_chart(
    input: MinimalKundliInput,
    reference_date: Optional[str] = None,
    svg: bool = Query(False, description="Include SVG chart in response")
):
    """
    Get Gochar (Transit) Chart

    This endpoint provides transit chart data with optional SVG visualization.

    Args:
        input: User's birth details
        reference_date: Date for transit analysis in YYYY-MM-DD format (default: today)
        svg: If True, includes SVG chart in response. Default is False.
        language: Response language (default: 'en')

    Returns:
        JSON data with transit positions and optional SVG chart

    Example:
        POST /api/v1/kundali/chart?svg=true&language=en
        {
            "name": "John Doe",
            "date_of_birth": "15/08/1990",
            "time_of_birth": "10:30",
            "place_of_birth": "Mumbai, India"
        }
    """
    try:
        # DEBUG: Log incoming request data
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[GOCHAR] Received request: {input.model_dump()}")

        # Normalize input to KundaliRequest
        kundali_request = minimal_to_kundali_request(input)

        # Parse reference date if provided
        ref_date = None
        if reference_date:
            try:
                ref_date = datetime.strptime(reference_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid reference_date format. Use YYYY-MM-DD"
                )

        # Get language from input body (like other endpoints)
        lang = input.language if input.language else 'en'

        # Calculate Gochar analysis
        gochar_analysis = gochar_engine.calculate_gochar(
            kundali_request=kundali_request,
            reference_date=ref_date,
            language=lang
        )

        # Prepare transit chart data using CORRECTED function (always returned)
        transit_chart_data = gochar_engine._prepare_transit_chart_data_for_svg_v2(
            gochar_analysis,
            lang=lang
        )

        # Build response with data (always included)
        response = {
            "input": {
                "name": input.name,
                "date_of_birth": input.date_of_birth,
                "place_of_birth": input.place_of_birth
            },
            "reference_date": gochar_analysis.analysis_date,
            "moon_sign": gochar_analysis.birth_chart_reference.moon_sign,
            "moon_sign_hindi": gochar_analysis.birth_chart_reference.moon_sign_hindi,
            "transit_chart": transit_chart_data
        }

        # Add SVG only if svg=true
        if svg:
            chart_title = "Gochar Chart" if lang == 'en' else "गोचर चार्ट"
            transit_chart_svg = svg_chart_generator.create_transit_chart_svg(
                chart_title,
                transit_chart_data,
                chart_size=400,
                lang=lang
            )
            response["chart_svg"] = transit_chart_svg

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Gochar chart: {str(e)}"
        )



@router.get("/health")
async def gochar_health_check():
    """
    Gochar endpoint health check

    Returns the status of the Gochar calculation engine.
    """
    return {
        "status": "healthy",
        "service": "Gochar (Transit) Calculation Engine",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/v1/kundali/current - Current Gochar analysis",
            "POST /api/v1/kundali/date-range - Gochar for date range",
            "POST /api/v1/kundali/upcoming-transits - Upcoming significant transits",
            "POST /api/v1/kundali/special-focus - Aspect-focused Gochar",
            "POST /api/v1/kundali/sade-sati-status - Sade Sati analysis",
            "POST /api/v1/kundali/compare-dates - Compare multiple dates",
            "POST /api/v1/kundali/chart - Get transit chart SVG",
            "GET /api/v1/kundali/health - This health check"
        ]
    }
