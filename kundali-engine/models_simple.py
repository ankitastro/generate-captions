from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional, Union


class KundaliRequest(BaseModel):
    name: str
    datetime: datetime
    timezone: str
    latitude: float
    longitude: float


class PlanetPosition(BaseModel):
    planet: str
    sign: str
    degree: float
    retrograde: bool
    house: int


class NakshatraInfo(BaseModel):
    name: str
    pada: int
    lord: str


class DashaInfo(BaseModel):
    planet: str
    start_date: str
    end_date: str
    duration_years: float


class PanchangaInfo(BaseModel):
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


class KundaliResponse(BaseModel):
    name: str
    birth_info: Dict[str, Union[str, float]]
    lagna: str
    lagna_degree: float
    planets: List[PlanetPosition]
    rasi_chart: Dict[str, List[str]]
    moon_nakshatra: NakshatraInfo
    current_dasha: DashaInfo
    panchanga: PanchangaInfo


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
