# Krishnamurti Paddhati (KP) API Documentation

## Overview

The KP System API provides comprehensive Krishnamurti Paddhati astrology calculations using Swiss Ephemeris for maximum accuracy. This system implements clean, dependency-free calculations with AstroSage-compatible output format.

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for local development. For production, implement appropriate security measures.

---

## API Endpoints

### 1. KP System Analysis
**Endpoint:** `POST /api/kp-system`

**Description:** Generate complete KP chart with planets, cusps, ruling planets, and significators.

**Request Body:**
```json
{
  "year": 2024,
  "month": 9,
  "day": 13,
  "hour": 16,
  "minute": 18,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timezone": "Asia/Kolkata",
  "name": "Sample Chart",
  "place": "New Delhi, India"
}
```

**Response Example:**
```json
{
  "planets_table": [
    {
      "Planet": "Sun",
      "Cusp": 6,
      "Sign": "Leo",
      "Sign_Lord": "Su",
      "Star_Lord": "Su",
      "Sub_Lord": "Su"
    },
    {
      "Planet": "Moon",
      "Cusp": 7,
      "Sign": "Sagittarius",
      "Sign_Lord": "Ju",
      "Star_Lord": "Su",
      "Sub_Lord": "Su"
    }
  ],
  "cusps_table": [
    {
      "Cusp": 1,
      "Degree": 33.35,
      "Sign": "Taurus",
      "Sign_Lord": "Ve",
      "Star_Lord": "Su",
      "Sub_Lord": "Sa"
    }
  ],
  "ruling_planets": {
    "Mo": {
      "sign_lord": "Ju",
      "star_lord": "Su",
      "sub_lord": "Su"
    },
    "Asc": {
      "sign_lord": "Ve",
      "star_lord": "Su",
      "sub_lord": "Sa"
    },
    "Day Lord": {
      "planet": "Ve"
    }
  },
  "house_significators": {
    "1": {
      "strong": ["House 1 Cusp Sub-Lord: Saturn"],
      "medium": ["Mars (star lord of Jupiter)"],
      "weak": []
    }
  },
  "kp_chart": {
    "1": ["Lagna"],
    "2": ["Ketu"],
    "6": ["Sun"],
    "7": ["Moon"],
    "8": ["Mercury", "Saturn"],
    "11": ["Venus", "Mars", "Jupiter"],
    "12": ["Rahu"]
  },
  "chart_layout": {
    "Sun": 6,
    "Moon": 7,
    "Mars": 11,
    "Mercury": 8,
    "Jupiter": 11,
    "Venus": 11,
    "Saturn": 8,
    "Rahu": 12,
    "Ketu": 2
  },
  "system": "Krishnamurti Paddhati (KP) - Clean Swiss Ephemeris"
}
```

---

### 2. Bhava Chalit System
**Endpoint:** `POST /api/bhava-chalit`

**Description:** Generate Bhava Chalit chart using equal house system from Ascendant.

**Request Body:**
```json
{
  "year": 2024,
  "month": 9,
  "day": 13,
  "hour": 16,
  "minute": 18,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timezone": "Asia/Kolkata"
}
```

**Response Example:**
```json
{
  "bhava_cusps": {
    "1": 33.35,
    "2": 63.35,
    "3": 93.35,
    "4": 123.35,
    "5": 153.35,
    "6": 183.35,
    "7": 213.35,
    "8": 243.35,
    "9": 273.35,
    "10": 303.35,
    "11": 333.35,
    "12": 3.35
  },
  "bhava_chart": {
    "1": ["Lagna"],
    "2": ["Ketu"],
    "6": ["Sun"],
    "7": ["Moon"],
    "8": ["Mercury", "Saturn"],
    "11": ["Venus", "Mars", "Jupiter"],
    "12": ["Rahu"]
  },
  "planet_details": {
    "Sun": {
      "house": 6,
      "longitude": 173.98,
      "sign": "Virgo"
    }
  },
  "ascendant_longitude": 33.35,
  "system": "Bhava Chalit (Equal Houses from Ascendant)"
}
```

---

### 3. Combined KP & Bhava Chalit Analysis
**Endpoint:** `POST /api/kp-bhava-combined`

**Description:** Generate both KP and Bhava Chalit charts with comparative analysis.

**Request Body:**
```json
{
  "year": 2024,
  "month": 9,
  "day": 13,
  "hour": 16,
  "minute": 18,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timezone": "Asia/Kolkata"
}
```

**Response Example:**
```json
{
  "kp_system": {
    "planets_table": [...],
    "cusps_table": [...],
    "ruling_planets": {...},
    "house_significators": {...},
    "kp_chart": {...},
    "system": "Krishnamurti Paddhati (KP) - Clean Swiss Ephemeris"
  },
  "bhava_chalit": {
    "bhava_cusps": {...},
    "bhava_chart": {...},
    "planet_details": {...},
    "system": "Bhava Chalit (Equal Houses from Ascendant)"
  },
  "bhava_house_strengths": {
    "1": {
      "strength_score": 5,
      "planets": ["Lagna"],
      "analysis": "Strong house with ascendant presence"
    }
  },
  "comparison": {
    "kp_uses": "Placidus house cusps with sub-lord system (Swiss Ephemeris + AstroSage format)",
    "bhava_chalit_uses": "Equal 30° houses from ascendant",
    "main_difference": "KP focuses on sub-lords and significators, Bhava Chalit on equal house divisions"
  }
}
```

---

## Request Parameters

### Required Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| year | integer | Birth year | 2024 |
| month | integer | Birth month (1-12) | 9 |
| day | integer | Birth day (1-31) | 13 |
| hour | integer | Birth hour (0-23) | 16 |
| minute | integer | Birth minute (0-59) | 18 |
| latitude | float | Birth latitude in decimal degrees | 28.6139 |
| longitude | float | Birth longitude in decimal degrees | 77.2090 |
| timezone | string | Timezone identifier | "Asia/Kolkata" |

### Optional Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| name | string | Person's name | "John Doe" |
| place | string | Birth place | "New Delhi, India" |

---

## Response Data Structure

### Planets Table
Each planet entry contains:
- **Planet**: Name (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
- **Cusp**: House number (1-12)
- **Sign**: Zodiac sign name
- **Sign_Lord**: Ruling planet of the sign (abbreviated)
- **Star_Lord**: Nakshatra lord (abbreviated)
- **Sub_Lord**: Sub-division lord (abbreviated)

### Cusps Table
Each cusp entry contains:
- **Cusp**: House number (1-12)
- **Degree**: Exact degree position (0-360)
- **Sign**: Zodiac sign name
- **Sign_Lord**: Sign ruling planet
- **Star_Lord**: Nakshatra ruling planet
- **Sub_Lord**: Sub-division ruling planet

### Ruling Planets
- **Mo (Moon)**: sign_lord, star_lord, sub_lord
- **Asc (Ascendant)**: sign_lord, star_lord, sub_lord
- **Day Lord**: planet ruling the day of birth

### House Significators
For each house (1-12):
- **strong**: Planets in house + cusp sub-lord
- **medium**: Star lords of planets in house
- **weak**: Sub-lords of planets in house

### Planet Abbreviations
- Su = Sun, Mo = Moon, Ma = Mars, Me = Mercury
- Ju = Jupiter, Ve = Venus, Sa = Saturn
- Ra = Rahu, Ke = Ketu

---

## Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (Invalid parameters)
- **422**: Unprocessable Entity (Validation error)
- **500**: Internal Server Error

### Error Response Format
```json
{
  "detail": "Invalid birth date parameters",
  "error_code": "INVALID_DATE",
  "message": "Year must be between 1800 and 2100"
}
```

### Common Errors
1. **Invalid Date**: Birth date outside valid range
2. **Invalid Coordinates**: Latitude/longitude out of bounds
3. **Invalid Timezone**: Unrecognized timezone identifier
4. **Missing Parameters**: Required fields not provided

---

## Integration Examples

### Python Example
```python
import requests
import json

# KP System API call
url = "http://localhost:8000/api/kp-system"
data = {
    "year": 2024,
    "month": 9,
    "day": 13,
    "hour": 16,
    "minute": 18,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata",
    "name": "Sample Chart"
}

response = requests.post(url, json=data)
kp_data = response.json()

# Access specific data
planets = kp_data['planets_table']
ruling_planets = kp_data['ruling_planets']
significators = kp_data['house_significators']
```

### JavaScript Example
```javascript
const kpApiCall = async () => {
  const response = await fetch('http://localhost:8000/api/kp-system', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      year: 2024,
      month: 9,
      day: 13,
      hour: 16,
      minute: 18,
      latitude: 28.6139,
      longitude: 77.2090,
      timezone: 'Asia/Kolkata'
    })
  });

  const kpData = await response.json();
  console.log('KP Chart:', kpData.kp_chart);
  console.log('Ruling Planets:', kpData.ruling_planets);
};
```

### cURL Example
```bash
curl -X POST "http://localhost:8000/api/kp-system" \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2024,
    "month": 9,
    "day": 13,
    "hour": 16,
    "minute": 18,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata"
  }'
```

---

## Technical Details

### Calculation Methods
- **Planetary Positions**: Swiss Ephemeris (pyswisseph)
- **Ayanamsa**: KP Ayanamsa formula: NKPA = 22° 22' 30" + (Year - 1900) × 50.2388475" + (Year - 1900)² × 0.000111/3600
- **House System**: Placidus for KP, Equal Houses for Bhava Chalit
- **Sub-Lords**: Proportional division based on Vimshottari Dasha periods
- **Coordinate System**: Sidereal zodiac with KP corrections

### Accuracy & Limitations
- **Valid Date Range**: 5000 BCE to 5000 CE
- **Precision**: Sub-degree level calculations
- **Geographic Range**: Global coordinates supported
- **Performance**: ~100-200ms response time for single chart

### Data Dependencies
- **Swiss Ephemeris**: Astronomical calculations
- **No External APIs**: Self-contained calculation engine
- **No Database**: Stateless API design

---

## Best Practices

### Request Optimization
1. **Batch Requests**: For multiple charts, use separate API calls
2. **Caching**: Cache results for identical birth data
3. **Validation**: Validate input parameters client-side
4. **Error Handling**: Implement retry logic for network failures

### Data Processing
1. **Significator Analysis**: Use strong/medium/weak hierarchy
2. **House Analysis**: Combine KP and Bhava Chalit for comprehensive reading
3. **Planet Positions**: Consider both sign and sub-lord for accurate predictions
4. **Chart Comparison**: Use both systems for timing vs. nature analysis

### Security Considerations
1. **Input Validation**: Sanitize all input parameters
2. **Rate Limiting**: Implement appropriate rate limits
3. **CORS**: Configure CORS headers for web applications
4. **Logging**: Log requests for debugging and analytics

---

## Support & Contact

For API support, technical questions, or bug reports:
- **Documentation**: This file
- **Source Code**: `/kp_system.py`, `/main.py`
- **Test Files**: `/test_kp_system.py`
- **Example Output**: `/kp_output.json`

---

**Last Updated**: January 13, 2025
**API Version**: 1.0
**System**: Krishnamurti Paddhati (KP) - Clean Swiss Ephemeris Implementation