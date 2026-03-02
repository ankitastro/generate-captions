"""
Common API endpoints - health check, languages, documentation
"""

from datetime import datetime
from fastapi import APIRouter

router = APIRouter()


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
    from api.services.kundli_service import get_translation_mgr
    translation_manager = get_translation_mgr()

    return {
        "success": True,
        "supported_languages": translation_manager.get_available_languages(),
        "default_language": "en",
        "usage": "Add 'language' parameter to your request body with values: en, hi, kn, mr, te, ta"
    }


@router.get("/example-request")
async def get_example_request():
    """Get example request formats for API testing"""
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


@router.get("/")
async def root():
    """API root endpoint with available endpoints"""
    return {
        "message": "Kundali Modular API running.",
        "version": "2.0.0",
        "endpoints": {
            "generate": "POST /generate-kundli",
            "birth_details": "POST /api/birth-details",
            "kundli": "POST /api/kundli",
            "charts": "POST /api/charts",
            "yogas": "POST /api/yogas",
            "interpretation": "POST /api/interpretation",
            "report": "POST /api/report",
            "ashtakavarga": "POST /api/ashtakavarga-data",
            "doshas": "POST /api/doshas",
            "complete": "POST /api/complete",
        },
    }
