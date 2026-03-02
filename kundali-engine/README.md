# Kundali Generation Service

A comprehensive Vedic astrology service for generating Kundali (birth charts) using the open-source `drik-panchanga` library and Swiss Ephemeris.

## Features

### 🌟 Complete Kundali Generation
- **Planetary Positions**: Accurate positions of all 9 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
- **Rasi Chart**: Birth chart showing planets in their respective houses
- **Lagna (Ascendant)**: Precise calculation of the rising sign and degree
- **Nakshatra & Pada**: Moon's nakshatra with pada information
- **Vimshottari Dasha**: Current Maha Dasha period with start/end dates

### 📅 Panchanga Details
- **Tithi**: Lunar day with end time
- **Nakshatra**: Lunar mansion with end time
- **Yoga**: Auspicious combinations with end time
- **Karana**: Half-day periods
- **Vaara**: Weekday
- **Masa**: Lunar month
- **Ritu**: Season
- **Samvatsara**: Year name
- **Sunrise/Sunset**: Accurate timings

### 🔧 Technical Features
- **FastAPI**: Modern, fast web framework
- **Swiss Ephemeris**: Highly accurate astronomical calculations
- **Timezone Support**: Automatic timezone handling
- **Error Handling**: Comprehensive error handling and validation
- **API Documentation**: Auto-generated OpenAPI documentation

## Prerequisites

- Python 3.8+
- Swiss Ephemeris library
- pyswisseph

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd kundali-engine
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up the drik-panchanga library**:
The drik-panchanga library is already cloned in the project directory.

## Usage

### Starting the Service

```bash
# Using Python directly
python main.py

# Using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The service will start on `http://localhost:8000`

### API Endpoints

#### 1. Generate Kundali
**POST** `/generate-kundali`

Generate a complete Kundali from birth details.

**Request Body**:
```json
{
  "name": "Ashish Gupta",
  "datetime": "1990-07-05T14:25:00",
  "timezone": "Asia/Kolkata",
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

**Response**:
```json
{
  "name": "Ashish Gupta",
  "birth_info": {
    "datetime": "1990-07-05 14:25:00",
    "timezone": "Asia/Kolkata",
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "lagna": "Scorpio",
  "lagna_degree": 15.45,
  "planets": [
    {
      "planet": "Sun",
      "sign": "Gemini",
      "degree": 20.15,
      "retrograde": false,
      "house": 8
    }
    // ... more planets
  ],
  "rasi_chart": {
    "1": ["Lagna"],
    "2": ["Venus"],
    "3": ["Sun", "Mercury"],
    // ... more houses
  },
  "moon_nakshatra": {
    "name": "Rohini",
    "pada": 2,
    "lord": "Moon"
  },
  "current_dasha": {
    "planet": "Venus",
    "start_date": "1988-07-05",
    "end_date": "2008-07-05",
    "duration_years": 20.0
  },
  "panchanga": {
    "tithi": "Chaturthi",
    "tithi_end_time": "14:25:30",
    "nakshatra": "Rohini",
    "nakshatra_end_time": "16:45:20",
    // ... more panchanga details
  }
}
```

#### 2. Health Check
**GET** `/health`

Check if the service is running.

#### 3. Example Request
**GET** `/example-request`

Get an example request body for testing.

#### 4. API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Using curl

```bash
curl -X POST "http://localhost:8000/generate-kundali" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Ashish Gupta",
       "datetime": "1990-07-05T14:25:00",
       "timezone": "Asia/Kolkata",
       "latitude": 28.6139,
       "longitude": 77.2090
     }'
```

## Input Format

### Required Fields
- **name**: Full name of the person (string)
- **datetime**: Birth date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
- **timezone**: Timezone identifier (e.g., "Asia/Kolkata", "America/New_York")
- **latitude**: Latitude of birth place (-90 to 90)
- **longitude**: Longitude of birth place (-180 to 180)

### Timezone Examples
- India: `Asia/Kolkata`
- USA East: `America/New_York`
- USA West: `America/Los_Angeles`
- UK: `Europe/London`
- Australia: `Australia/Sydney`

## Architecture

### Core Components

1. **KundaliEngine**: Main calculation engine
   - Integrates drik-panchanga with Swiss Ephemeris
   - Handles planetary calculations
   - Generates charts and dasha

2. **VimshottariDasha**: Dasha calculation system
   - Calculates Maha Dasha periods
   - Based on Moon's nakshatra at birth

3. **Models**: Pydantic models for request/response
   - Input validation
   - Type safety
   - API documentation

4. **FastAPI Application**: Web service layer
   - HTTP API endpoints
   - Error handling
   - Documentation

### Calculation Process

1. **Input Processing**: Parse and validate birth details
2. **Coordinate Conversion**: Convert to Julian Day and apply timezone
3. **Planetary Positions**: Calculate all planet positions using Swiss Ephemeris
4. **Lagna Calculation**: Calculate ascendant using house system
5. **Chart Generation**: Generate Rasi chart with planet placements
6. **Nakshatra Analysis**: Calculate Moon's nakshatra and pada
7. **Dasha Calculation**: Calculate current Vimshottari Dasha
8. **Panchanga Calculation**: Calculate all panchanga elements
9. **Response Assembly**: Format and return complete response

## Accuracy

The service uses:
- **Swiss Ephemeris**: Extremely accurate planetary positions (±0.001 arcseconds)
- **Lahiri Ayanamsa**: Standard ayanamsa for Vedic astrology
- **Drik-Panchanga**: Observational calculations (not Surya Siddhanta)

Accuracy is maintained for dates from 5000 BCE to 5000 CE, with best accuracy in the range 2500 BCE to 2500 CE.

## Error Handling

The service includes comprehensive error handling:
- Input validation (coordinates, dates, etc.)
- Swiss Ephemeris calculation errors
- Timezone conversion errors
- Internal server errors with logging

## Development

### Project Structure
```
kundali-engine/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── kundali_engine.py    # Core calculation engine
├── dasha.py             # Vimshottari Dasha calculator
├── requirements.txt     # Dependencies
├── README.md           # This file
└── drik-panchanga/     # drik-panchanga library
    ├── panchanga.py
    ├── gui.py
    └── ...
```

### Adding New Features

1. **New Planetary Calculations**: Add to `KundaliEngine._calculate_planetary_positions()`
2. **New Chart Types**: Add new chart generation methods
3. **New Dasha Systems**: Extend or create new dasha calculators
4. **New API Endpoints**: Add to `main.py`

## Dependencies

- **FastAPI**: Web framework
- **pydantic**: Data validation
- **uvicorn**: ASGI server
- **pyswisseph**: Swiss Ephemeris Python interface
- **pytz**: Timezone handling

## License

This project uses the drik-panchanga library which is licensed under GNU Affero GPL version 3.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the error messages in responses
3. Check the server logs for detailed error information

## Acknowledgments

- **drik-panchanga** library by Satish BD
- **Swiss Ephemeris** by Astrodienst
- **pyswisseph** Python interface
