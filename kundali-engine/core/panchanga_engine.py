from datetime import datetime
import pytz
import swisseph as swe
from typing import Dict, Any
from .panchanga import EnhancedPanchanga  # your existing class
from panchanga import Place  # drik-panchanga's struct

def compute_panchanga(jd: float, latitude: float, longitude: float, timezone_str: str = "Asia/Kolkata") -> Dict[str, Any]:
    jd_date = int(jd)
    try:
        tz = pytz.timezone(timezone_str or "Asia/Kolkata")
    except Exception:
        tz = pytz.timezone("Asia/Kolkata")

    offset_hours = tz.utcoffset(datetime(2000, 1, 1)).total_seconds() / 3600.0
    place = Place(latitude, longitude, offset_hours)

    ep = EnhancedPanchanga()
    enhanced = ep.get_daily_panchanga(jd_date, latitude, longitude, timezone_str)

    t = enhanced.get("tithi", {})
    n = enhanced.get("nakshatra", {})
    y = enhanced.get("yoga", {})
    k = enhanced.get("karana", {})
    v = enhanced.get("vaara", {})
    m = enhanced.get("masa", {})
    r = enhanced.get("ritu", {})
    s = enhanced.get("samvatsara", {})
    sr = enhanced.get("sunrise", {})
    ss = enhanced.get("sunset", {})

    basic = {
        "tithi": t.get("name", "Pratipad"),
        "tithi_end_time": t.get("end_time", "00:00:00"),
        "nakshatra": n.get("name", "Ashwini"),
        "nakshatra_end_time": n.get("end_time", "00:00:00"),
        "yoga": y.get("name", "Vishkambha"),
        "yoga_end_time": y.get("end_time", "00:00:00"),
        "karana": k.get("name", "Bava"),
        "vaara": v.get("name", "Sunday"),
        "masa": m.get("name", "Chaitra"),
        "ritu": r.get("name", "Vasanta"),
        "samvatsara": s.get("name", "Samvatsara 0"),
        "sunrise": sr.get("time", "06:00:00"),
        "sunset": ss.get("time", "18:00:00"),
    }

    return {"basic": basic, "enhanced": enhanced}
