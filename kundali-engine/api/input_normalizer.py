# utils/input_normalization.py
from __future__ import annotations
from typing import Tuple
from datetime import datetime
import re
import os
import pytz
import googlemaps
from timezonefinder import TimezoneFinder
from dotenv import load_dotenv

load_dotenv()


from models import KundaliRequest
from models import MinimalKundliInput

DATE_PAT = re.compile(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*$")
TIME_PAT = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp][Mm])?\s*$")

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
_tf = TimezoneFinder()


def _parse_date(date_str: str) -> Tuple[int, int, int]:
    m = DATE_PAT.match(date_str)
    if not m:
        raise ValueError(f"Invalid date_of_birth format: {date_str}")
    d, mth, y = map(int, m.groups())
    return y, mth, d


def _parse_time(time_str: str) -> Tuple[int, int, int]:
    m = TIME_PAT.match(time_str)
    if not m:
        raise ValueError(f"Invalid time_of_birth format: {time_str}")
    hh, mm, ss, ampm = m.groups()
    hh = int(hh)
    mm = int(mm)
    ss = int(ss) if ss else 0
    if ampm:
        ampm = ampm.lower()
        if ampm == "pm" and hh < 12:
            hh += 12
        if ampm == "am" and hh == 12:
            hh = 0
    if not (0 <= hh < 24 and 0 <= mm < 60 and 0 <= ss < 60):
        raise ValueError(f"Bad time components in: {time_str}")
    return hh, mm, ss


def _geocode_google(place: str) -> Tuple[float, float]:
    result = gmaps.geocode(place)
    if not result:
        raise ValueError(f"Could not geocode place: {place}")
    location = result[0]["geometry"]["location"]
    return location["lat"], location["lng"]


def _tz_from_latlon(lat: float, lon: float) -> str:
    tzname = _tf.timezone_at(lat=lat, lng=lon)
    return tzname or "Asia/Kolkata"


def minimal_to_kundali_request(inp: MinimalKundliInput) -> KundaliRequest:
    y, mth, d = _parse_date(inp.date_of_birth)
    hh, mm, ss = _parse_time(inp.time_of_birth)

    # Use provided coordinates if available, otherwise geocode from place_of_birth
    if inp.pob_lat and inp.pob_long:
        # Use provided coordinates directly (convert from string to float)
        lat = float(inp.pob_lat)
        lon = float(inp.pob_long)
    else:
        # Geocode from place_of_birth string
        lat, lon = _geocode_google(inp.place_of_birth)

    tzname = _tz_from_latlon(lat, lon)

    tz = pytz.timezone(tzname)
    local_dt = tz.localize(datetime(y, mth, d, hh, mm, ss))

    return KundaliRequest(
        name=inp.name,
        datetime=local_dt.replace(tzinfo=None),  # engine expects naive
        timezone=tzname,
        latitude=lat,
        longitude=lon,
        place_of_birth=inp.place_of_birth,
        language=inp.language if hasattr(inp, 'language') else 'en',
    )
