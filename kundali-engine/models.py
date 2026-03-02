from pydantic import BaseModel , Field, validator
from datetime import datetime
from typing import List, Dict, Optional, Union, Any ,Optional


class KundaliRequest(BaseModel):
    """Input model for Kundali generation request"""
    name: str
    datetime: datetime
    timezone: str
    latitude: float
    longitude: float
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = Field(None, alias="min")
    second: Optional[int] = Field(None, alias="sec")
    place_of_birth: str
    language: Optional[str] = Field('en', description="Response language code")

    @validator("datetime", always=True)
    def build_datetime_if_missing(cls, v, values):
        if v:
            return v
        if all(values.get(k) is not None for k in ["year", "month", "day"]):
            return datetime(
                year=values["year"],
                month=values["month"],
                day=values["day"],
                hour=values.get("hour") or 0,
                minute=values.get("minute") or 0,
                second=values.get("second") or 0,
            )
        raise ValueError("Either 'datetime' or (year, month, day, hour...) must be provided.")

class MinimalKundliInput(BaseModel):
    name: str = Field(..., description="Full name")
    date_of_birth: str = Field(..., description="DD/MM/YYYY")
    time_of_birth: str = Field(..., description="HH:MM[:SS][AM|PM] 24h or 12h")
    place_of_birth: str = Field(..., description="Freeform place string (City, State, Country)")
    pob_lat: Optional[str] = Field(None, description="Optional: Place of birth latitude (string format)")
    pob_long: Optional[str] = Field(None, description="Optional: Place of birth longitude (string format)")
    language: Optional[str] = Field('en', description="Response language: 'en' (English), 'hi' (Hindi), 'kn' (Kannada), 'mr' (Marathi), 'te' (Telugu), 'ta' (Tamil)")


class PlanetPosition(BaseModel):
    """Position of a planet in the chart"""
    planet: str
    sign: str
    degree: float
    retrograde: bool
    house: int
    degree_dms: Optional[str] = None
    sign_lord: Optional[str] = None
    nakshatra_lord: Optional[str] = None
    nakshatra_name: Optional[str] = None
    planet_awasta: Optional[str] = None
    status: Optional[str] = None




class NakshatraInfo(BaseModel):
    """Nakshatra information"""
    name: str
    pada: int
    lord: str


class DashaInfo(BaseModel):
    """Dasha information"""
    planet: str
    start_date: str
    end_date: str
    duration_years: float

class LagnaInfo(BaseModel):
    sign: str
    degree: float
    abs_longitude: float

# Enhanced models for advanced features
class EnhancedPanchangaInfo(BaseModel):
    """Enhanced Panchanga information with detailed timing"""
    tithi: Dict[str, Any]  # name, number, end_time, paksha, percentage_left
    nakshatra: Dict[str, Any]  # name, number, end_time, lord, pada
    yoga: Dict[str, Any]  # name, number, end_time
    karana: Dict[str, Any]  # name, number
    vaara: Dict[str, Any]  # name, number, lord
    masa: Dict[str, Any]  # name, number, type
    ritu: Dict[str, Any]  # name, number
    samvatsara: Dict[str, Any]  # name, number
    sunrise: Dict[str, Any]  # time, local_time
    sunset: Dict[str, Any]  # time, local_time
    day_duration: Dict[str, Any]  # hours, ghatikas


class AntarDashaInfo(BaseModel):
    """Antar Dasha information"""
    planet: str
    start_date: str
    end_date: str
    duration_years: float


class MahaDashaInfo(BaseModel):
    """Maha Dasha information with sub-periods"""
    planet: str
    start_date: str
    end_date: str
    duration_years: float
    sub_periods: List[AntarDashaInfo]


class CurrentDashaInfo(BaseModel):
    """Current running Dasha information"""
    maha_dasha: Dict[str, Any]
    antar_dasha: Dict[str, Any]


class NavamsaInfo(BaseModel):
    """Navamsa chart information"""
    navamsa_lagna: Dict[str, Any]
    navamsa_positions: Dict[str, Any]
    navamsa_chart: Dict[str, List[str]]
    navamsa_analysis: Dict[str, Any]


class YogaInfo(BaseModel):
    """Yoga information"""
    name: str
    description: str
    strength: str
    planets_involved: List[str]
    houses_involved: List[int]
    significance: str
    effects: List[str]


class YogaSummary(BaseModel):
    """Summary of detected yogas"""
    total_yogas: int
    strong_yogas: List[str]
    moderate_yogas: List[str]
    weak_yogas: List[str]
    most_significant: Optional[str]


# Legacy model for backward compatibility
class PanchangaInfo(BaseModel):
    """Basic Panchanga information (for backward compatibility)"""
    tithi: str
    tithi_end_time: str
    nakshatra: str
    nakshatra_end_time: str
    yoga: str
    yoga_end_time: str
    karana: str
    vaara: str
    masa: str
    ritu: str
    samvatsara: str
    sunrise: str
    sunset: str

class MangalDoshaRuleDetail(BaseModel):
    based_on_aspect: List[str] = Field(default_factory=list)
    based_on_house: List[str] = Field(default_factory=list)

class MangalDoshaResult(BaseModel):
    is_present: bool
    is_cancelled: bool
    report: str # This is the original simple report

    # New detailed fields
    manglik_present_rule: MangalDoshaRuleDetail = Field(default_factory=MangalDoshaRuleDetail)
    manglik_cancel_rule: List[str] = Field(default_factory=list)
    is_mars_manglik_cancelled: bool
    manglik_status: str
    percentage_manglik_present: float
    percentage_manglik_after_cancellation: float
    manglik_report: str # This is the more detailed report

# --- For Kalasarpa Dosha (as defined previously) ---
class KalasarpaReportDetail(BaseModel):
    house_id: int
    report: str

class KalasarpaDoshaResult(BaseModel):
    is_present: bool
    # report: str # This is the original simple report

    # New detailed fields
    present: bool
    type: str
    one_line: str
    name: str
    report_detail: KalasarpaReportDetail = Field(..., alias="report") # Use alias to match 'report' key in output


class KundaliResponse(BaseModel):
    """Complete Kundali response with advanced features"""
    name: str
    birth_info: Dict[str, Union[str, float]]
    lagna: LagnaInfo
    planets: List[PlanetPosition]
    rasi_chart: Dict[str, List[str]]
    moon_nakshatra: NakshatraInfo
    current_dasha: DashaInfo
    panchanga: PanchangaInfo  # Basic panchanga for backward compatibility
    rasi_chart_svg: Optional[str] = None


    # Advanced features
    enhanced_panchanga: EnhancedPanchangaInfo
    vimshottari_dasha: List[MahaDashaInfo]
    current_dasha_detailed: CurrentDashaInfo
    navamsa_chart: NavamsaInfo
    navamsa_chart_svg: Optional[str] = None
    detected_yogas: List[YogaInfo]
    yoga_summary: YogaSummary

    # Human-readable interpretation
    interpretation: Optional[str] = None
    report: Optional[str] = None  # New field for human-readable report
    # ashtakavarga: Optional[Dict] = None
    mangal_dosha: Optional[MangalDoshaResult] = None # Now uses the detailed model
    kalasarpa_dosha: Optional[KalasarpaDoshaResult] = None # Now uses the detailed model

    # Example of adding a completely new field
    recommended_remedies: Optional[List[str]] = None
    life_summary: Optional[str] = None
    ashtakavarga_svg: Optional[str] = None
    ashtakavarga: Optional[Dict] = None
    major_varga_charts_svg: Optional[str] = None # ⭐ NEW FIELD ⭐
      # New field for human-readable report



class KundliMatchingRequest(BaseModel):
    """Input model for Kundli Matching request."""
    groom: MinimalKundliInput = Field(..., description="Groom's birth details")
    bride: MinimalKundliInput = Field(..., description="Bride's birth details")
    language: Optional[str] = Field('en', description="Response language code")


class KootaResult(BaseModel):
    obtained_points: float
    max_points: int
    description: str

class MangalDoshaMatchingInfo(BaseModel):
    is_compatible: bool
    report: str
    groom_status: str
    bride_status: str

class KundliMatchingResponse(BaseModel):
    """Response model for a successful Kundli Matching."""
    total_points_obtained: float
    maximum_points: int = 36
    conclusion: str
    mangal_dosha_analysis: MangalDoshaMatchingInfo
    koota_details: Dict[str, KootaResult]

class GocharTransitInfo(BaseModel):
    """Individual planet transit information"""
    planet: str
    current_sign: str
    current_degree: float
    house_from_moon: int
    house_from_lagna: int
    nature: str  # excellent, good, neutral, challenging, bad
    effect_summary: str
    detailed_effect: str
    remedies: List[str]

class BirthChartReference(BaseModel):
    """Birth chart reference points for Gochar"""
    moon_sign: str
    moon_sign_hindi: Optional[str] = None
    moon_lord: str
    lagna_sign: str
    lagna_sign_hindi: Optional[str] = None
    lagna_lord: str

class OverallGocharScore(BaseModel):
    """Overall Gochar score summary"""
    favorable_planets: int
    good_planets: int
    neutral_planets: int
    challenging_planets: int
    total_planets: int
    percentage: float
    verdict: str
    summary: str

class LifeAspectAnalysis(BaseModel):
    """Analysis of specific life aspect based on Gochar"""
    score: int
    status: str
    influencing_planets: List[str]
    prediction: str
    detailed_prediction: str
    best_for: List[str]
    avoid: List[str]
    recommendations: List[str]

class SpecialTransit(BaseModel):
    """Special transit information (Sade Sati, Kantak Shani, etc.)"""
    is_active: bool
    name: Optional[str] = None
    phase: Optional[str] = None
    house: Optional[int] = None
    started: Optional[str] = None
    ends: Optional[str] = None
    description: str
    detailed_description: str
    remedies: List[str]
    severity: Optional[str] = None  # mild, moderate, severe

class UpcomingTransit(BaseModel):
    """Upcoming significant transit information"""
    planet: str
    event: str
    date: str
    duration: str
    expected_effects: List[str]
    recommendations: List[str]
    importance_level: str  # low, medium, high, critical

class GocharRecommendations(BaseModel):
    """Recommendations based on Gochar analysis"""
    do_this_month: List[str]
    avoid_this_month: List[str]
    general_advice: List[str]
    remedies: List[str]
    color_therapy: Optional[str] = None
    gemstone_suggestion: Optional[str] = None
    mantra_suggestion: Optional[str] = None

class AstrologerNotes(BaseModel):
    """Special notes for astrologers"""
    key_points: List[str]
    priority_aspects: List[str]
    technical_observations: List[str]
    special_considerations: List[str]

class GocharAnalysis(BaseModel):
    """Complete Gochar analysis response"""
    analysis_date: str
    reference_type: str  # moon_sign, lagna_sign, or both
    birth_chart_reference: BirthChartReference
    current_transits: Dict[str, GocharTransitInfo]
    overall_score: OverallGocharScore
    life_aspects: Dict[str, LifeAspectAnalysis]
    special_transits: Dict[str, SpecialTransit]
    upcoming_transits: List[UpcomingTransit]
    recommendations: GocharRecommendations
    astrologer_notes: AstrologerNotes

class GocharRequest(BaseModel):
    """Request model for Gochar analysis"""
    input: MinimalKundliInput
    reference_date: Optional[str] = None  # Format: YYYY-MM-DD, defaults to today
    language: Optional[str] = Field('en', description="Response language code")

class GocharDateRangeRequest(BaseModel):
    """Request model for Gochar analysis over a date range"""
    input: MinimalKundliInput
    start_date: str  # Format: YYYY-MM-DD
    end_date: str    # Format: YYYY-MM-DD
    language: Optional[str] = Field('en', description="Response language code")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
