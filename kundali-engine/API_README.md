# Horoscope API Documentation

A comprehensive REST API for generating horoscopes using both static templates and real astronomical data.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the Server

```bash
python api_server.py
```

The API server will start on `http://localhost:5000`

## API Endpoints

### Base URL
```
http://localhost:5000/api/v1
```

### Authentication
No authentication required for current version.

---

## Core Endpoints

### 1. Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Horoscope API",
  "version": "v1",
  "timestamp": "2025-01-08T10:30:00"
}
```

### 2. API Documentation
```http
GET /api/v1/docs
```

Returns comprehensive API documentation in JSON format.

---

## Horoscope Endpoints

### 3. Static Horoscope (Template-based)
```http
GET /api/v1/horoscope/{sign}?scope={scope}
```

**Parameters:**
- `sign` (path, required): Zodiac sign
- `scope` (query, optional): Time scope - `daily`, `weekly`, `monthly`, `yearly` (default: `daily`)

**Example Requests:**
```bash
# Daily horoscope for Scorpio
GET /api/v1/horoscope/Scorpio

# Weekly horoscope for Leo
GET /api/v1/horoscope/Leo?scope=weekly

# Monthly horoscope for Aries
GET /api/v1/horoscope/Aries?scope=monthly

# Yearly horoscope for Pisces
GET /api/v1/horoscope/Pisces?scope=yearly
```

**Response Format:**

**Daily Response:**
```json
{
  "error": false,
  "data": {
    "date": "2025-01-08",
    "sign": "Scorpio",
    "categories": {
      "lucky_color": "Crimson Red",
      "lucky_number": 42,
      "lucky_time": "14:00 PM – 16:00 PM",
      "mood": "Intense",
      "love": {
        "score": 75,
        "text": "Passionate energies surround your romantic life today..."
      },
      "career": {
        "score": 68,
        "text": "Professional opportunities emerge through determination..."
      },
      "money": {
        "score": 72,
        "text": "Financial insights lead to wise investment decisions..."
      },
      "health": {
        "score": 65,
        "text": "Physical vitality peaks during afternoon hours..."
      },
      "travel": {
        "score": 70,
        "text": "Short journeys prove beneficial for mental clarity..."
      }
    }
  },
  "timestamp": "2025-01-08T10:30:00"
}
```

**Weekly/Monthly/Yearly Response:**
```json
{
  "error": false,
  "data": {
    "sign": "Scorpio",
    "scope": "weekly",
    "date_range": "2025-01-06 to 2025-01-12",
    "theme": "Transformation and Renewal",
    "insights": {
      "summary": "This week brings significant opportunities for Scorpio natives...",
      "personal": "Your personal magnetism reaches new heights...",
      "travel": "Travel plans receive favorable cosmic support...",
      "health": "Your vitality and energy levels receive a boost...",
      "emotion": "Emotional clarity and stability characterize this period...",
      "remedy": "To maximize this week's positive energy, spend time in nature..."
    }
  },
  "timestamp": "2025-01-08T10:30:00"
}
```

### 4. Planetary Horoscope (Astronomical Data)
```http
GET /api/v1/planetary-horoscope/{sign}?scope={scope}&latitude={lat}&longitude={lon}&timezone={tz}&date={date}
```

**Parameters:**
- `sign` (path, required): Zodiac sign
- `scope` (query, optional): Time scope - currently only `daily` supported (default: `daily`)
- `latitude` (query, optional): Latitude for calculations (default: `12.972` - Bangalore)
- `longitude` (query, optional): Longitude for calculations (default: `77.594` - Bangalore)
- `timezone` (query, optional): Timezone offset (default: `5.5` - IST)
- `date` (query, optional): Date in YYYY-MM-DD format (default: today)

**Example Requests:**
```bash
# Daily planetary horoscope for Scorpio (default location)
GET /api/v1/planetary-horoscope/Scorpio

# Daily planetary horoscope for Leo in New York
GET /api/v1/planetary-horoscope/Leo?latitude=40.7128&longitude=-74.0060&timezone=-5.0

# Daily planetary horoscope for specific date
GET /api/v1/planetary-horoscope/Gemini?date=2025-01-15

# Combined parameters
GET /api/v1/planetary-horoscope/Cancer?scope=daily&latitude=51.5074&longitude=-0.1278&timezone=0.0&date=2025-01-08
```

**Response Format:**
```json
{
  "error": false,
  "data": {
    "date": "2025-01-08",
    "sign": "Scorpio",
    "categories": {
      "lucky_color": "Silver",
      "lucky_number": 29,
      "lucky_time": "07:00 AM – 09:00 AM",
      "mood": "Intense",
      "love": {
        "score": 75,
        "text": "Venus enhances romantic harmony and attractiveness..."
      },
      "career": {
        "score": 68,
        "text": "Strong planetary support for career advancement..."
      },
      "money": {
        "score": 72,
        "text": "Jupiter's influence brings financial opportunities..."
      },
      "health": {
        "score": 65,
        "text": "Mars energy needs balance and moderation..."
      },
      "travel": {
        "score": 70,
        "text": "Mercury supports beneficial short journeys..."
      }
    },
    "planetary_data": {
      "positions": {
        "Sun": {
          "rashi": "Capricorn",
          "degrees_in_sign": 18.5,
          "longitude": 288.5,
          "tropical_longitude": 288.5
        },
        "Moon": {
          "rashi": "Scorpio",
          "degrees_in_sign": 12.3,
          "longitude": 222.3,
          "tropical_longitude": 246.3
        },
        // ... other planets
      },
      "strengths": {
        "Sun": "Neutral",
        "Moon": "Debilitated",
        "Venus": "Own Sign",
        // ... other planets
      },
      "aspects": [
        {
          "planet1": "Sun",
          "planet2": "Mars",
          "aspect": "sextile",
          "angle": 63.2,
          "orb": 3.2
        },
        // ... other aspects
      ],
      "tithi": 12,
      "nakshatra": 18,
      "sunrise": "06:45",
      "sunset": "18:20"
    }
  },
  "timestamp": "2025-01-08T10:30:00"
}
```

---

## Utility Endpoints

### 5. Get Zodiac Signs
```http
GET /api/v1/signs
```

**Response:**
```json
{
  "error": false,
  "data": {
    "zodiac_signs": [
      "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
  },
  "timestamp": "2025-01-08T10:30:00"
}
```

### 6. Get Time Scopes
```http
GET /api/v1/scopes
```

**Response:**
```json
{
  "error": false,
  "data": {
    "scopes": ["daily", "weekly", "monthly", "yearly"],
    "static_horoscope_scopes": ["daily", "weekly", "monthly", "yearly"],
    "planetary_horoscope_scopes": ["daily"]
  },
  "timestamp": "2025-01-08T10:30:00"
}
```

---

## Error Handling

### Error Response Format
```json
{
  "error": true,
  "message": "Error description",
  "status_code": 400
}
```

### Common Error Codes

- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Endpoint not found
- **405 Method Not Allowed**: Wrong HTTP method
- **500 Internal Server Error**: Server error

### Example Error Responses

**Invalid Zodiac Sign:**
```json
{
  "error": true,
  "message": "Invalid zodiac sign: InvalidSign. Must be one of: Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces",
  "status_code": 400
}
```

**Invalid Scope:**
```json
{
  "error": true,
  "message": "Invalid scope: invalid. Must be one of: daily, weekly, monthly, yearly",
  "status_code": 400
}
```

**Unsupported Planetary Scope:**
```json
{
  "error": true,
  "message": "Planetary horoscope currently only supports 'daily' scope. Requested: weekly",
  "status_code": 400
}
```

---

## Testing

### Running Tests
```bash
# Start the API server in one terminal
python api_server.py

# Run tests in another terminal
python test_api.py
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:5000/

# Daily horoscope
curl "http://localhost:5000/api/v1/horoscope/Scorpio?scope=daily"

# Weekly horoscope
curl "http://localhost:5000/api/v1/horoscope/Leo?scope=weekly"

# Planetary horoscope
curl "http://localhost:5000/api/v1/planetary-horoscope/Scorpio"

# Planetary horoscope with location
curl "http://localhost:5000/api/v1/planetary-horoscope/Gemini?latitude=40.7128&longitude=-74.0060&timezone=-5.0"

# Get all zodiac signs
curl "http://localhost:5000/api/v1/signs"

# Get API documentation
curl "http://localhost:5000/api/v1/docs"
```

---

## Integration Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');

// Get daily horoscope
const response = await axios.get('http://localhost:5000/api/v1/horoscope/Scorpio?scope=daily');
console.log(response.data);

// Get planetary horoscope
const planetaryResponse = await axios.get('http://localhost:5000/api/v1/planetary-horoscope/Leo?scope=daily');
console.log(planetaryResponse.data);
```

### Python
```python
import requests

# Get daily horoscope
response = requests.get('http://localhost:5000/api/v1/horoscope/Scorpio?scope=daily')
horoscope = response.json()
print(horoscope)

# Get planetary horoscope
planetary_response = requests.get('http://localhost:5000/api/v1/planetary-horoscope/Leo?scope=daily')
planetary_horoscope = planetary_response.json()
print(planetary_horoscope)
```

---

## Key Features

### Static Horoscope Engine
- ✅ **Daily, Weekly, Monthly, Yearly** scopes
- ✅ **Consistent reproducible results** based on date
- ✅ **Rich template-based content** with themes and insights
- ✅ **Lucky elements** (color, number, time, mood)
- ✅ **Scored categories** (love, career, money, health, travel)

### Planetary Horoscope Engine
- ✅ **Real astronomical calculations** using Swiss Ephemeris
- ✅ **Location-specific results** (latitude, longitude, timezone)
- ✅ **Actual planetary positions** and aspects
- ✅ **Vedic elements** (tithi, nakshatra, sunrise/sunset)
- ✅ **Planetary strength analysis** (exalted, debilitated, own sign)
- ✅ **Professional-grade accuracy** comparable to commercial software

### API Features
- ✅ **RESTful design** with clear endpoints
- ✅ **JSON responses** with standardized format
- ✅ **Error handling** with meaningful messages
- ✅ **CORS support** for web applications
- ✅ **Parameter validation** with helpful error messages
- ✅ **Built-in documentation** endpoint

---

## Limitations

1. **Planetary horoscope** currently only supports daily scope
2. **Weekly/Monthly/Yearly** planetary horoscopes not yet implemented
3. **No authentication** (public API)
4. **No rate limiting** (use reverse proxy for production)
5. **No caching** (implement Redis for production)

---

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### Using Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "api_server:app"]
```

---

## Support

For issues or questions:
1. Check the `/api/v1/docs` endpoint for latest documentation
2. Run `python test_api.py` to verify functionality
3. Review server logs for error details
