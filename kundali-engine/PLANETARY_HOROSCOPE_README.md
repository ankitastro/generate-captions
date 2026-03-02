# Planetary Horoscope Engine

This module provides **astrologically accurate horoscope generation** based on real-time planetary positions using Swiss Ephemeris calculations.

## Features

### 🪐 Real Planetary Calculations
- **Accurate planetary positions** for all major planets (Sun through Pluto)
- **Sidereal calculations** using Lahiri Ayanamsa
- **Planetary strength analysis** (Exalted, Own Sign, Debilitated, Neutral)
- **Planetary aspects** detection (Conjunction, Sextile, Square, Trine, Opposition)

### 📅 Vedic Panchanga Integration
- **Tithi** (lunar day) calculations
- **Nakshatra** (lunar mansion) positions
- **Sunrise/Sunset** times for any location
- Traditional Vedic astronomical data

### 🌍 Location-Based Calculations
- Support for **any geographic location** (latitude, longitude, timezone)
- **Location-specific** sunrise/sunset times
- **Regional variations** in planetary influences

## Usage

### Basic Usage

```python
from horoscope import generate_planetary_horoscope

# Generate horoscope for current date and default location (Bangalore)
horoscope = generate_planetary_horoscope("Scorpio", "daily")

print(f"Lucky Color: {horoscope['categories']['lucky_color']}")
print(f"Love Score: {horoscope['categories']['love']['score']}")
print(f"Career: {horoscope['categories']['career']['text']}")
```

### Advanced Usage with Custom Location

```python
# New York coordinates
horoscope = generate_planetary_horoscope(
    sign="Leo",
    scope="daily",
    latitude=40.7128,
    longitude=-74.0060,
    timezone=-5.0,  # EST
    date=datetime.date(2025, 7, 8)
)

# Access planetary data
planetary_data = horoscope['planetary_data']
print(f"Current Moon sign: {planetary_data['positions']['Moon']['rashi']}")
print(f"Venus strength: {planetary_data['strengths']['Venus']}")
```

### Planetary Position Analysis

```python
positions = horoscope['planetary_data']['positions']

for planet, pos in positions.items():
    print(f"{planet}: {pos['rashi']} {pos['degrees_in_sign']:.1f}°")

# Check planetary aspects
aspects = horoscope['planetary_data']['aspects']
for aspect in aspects:
    print(f"{aspect['planet1']} {aspect['aspect']} {aspect['planet2']}")
```

## Data Structure

### Horoscope Response

```json
{
  "date": "2025-07-08",
  "sign": "Scorpio",
  "categories": {
    "lucky_color": "Silver",
    "lucky_number": 29,
    "lucky_time": "07:00 AM – 09:00 AM",
    "mood": "Intense",
    "love": {"score": 75, "text": "Venus enhances romantic harmony..."},
    "career": {"score": 68, "text": "Strong planetary support for advancement..."},
    "money": {"score": 72, "text": "Jupiter's influence brings opportunities..."},
    "health": {"score": 65, "text": "Mars energy needs balance..."},
    "travel": {"score": 70, "text": "Mercury supports beneficial journeys..."}
  },
  "planetary_data": {
    "positions": {
      "Sun": {"rashi": "Gemini", "degrees_in_sign": 21.9, "longitude": 81.01},
      "Moon": {"rashi": "Scorpio", "degrees_in_sign": 18.9, "longitude": 228.89},
      // ... other planets
    },
    "strengths": {
      "Sun": "Neutral",
      "Moon": "Debilitated",
      "Venus": "Own Sign"
      // ... other planets
    },
    "aspects": [
      {"planet1": "Sun", "planet2": "Mars", "aspect": "sextile", "orb": 4.3},
      // ... other aspects
    ],
    "tithi": 12,
    "nakshatra": 18,
    "sunrise": "06:15",
    "sunset": "18:42"
  }
}
```

## Astrological Interpretation Logic

### Planetary Influences on Life Areas

- **Love & Relationships**: Primarily Venus, with Moon and Mars influences
- **Career & Success**: Sun and Jupiter positions and strength
- **Money & Finances**: Venus and Jupiter, with Saturn considerations
- **Health & Vitality**: Mars and Sun energy levels
- **Travel & Movement**: Mercury and Moon positions

### Planetary Strength Assessment

1. **Exalted**: Planet in its exaltation sign (highest strength)
2. **Own Sign**: Planet in its ruling sign (strong)
3. **Debilitated**: Planet in its debilitation sign (challenged)
4. **Neutral**: Planet in other signs (moderate strength)

### Lucky Elements Calculation

- **Lucky Color**: Based on dominant planet's traditional color
- **Lucky Number**: Calculated from sum of planetary degrees
- **Lucky Time**: Based on planetary hours and dominant planet
- **Mood**: Determined by Moon's current sign

## Comparison: Static vs Planetary Horoscopes

| Feature                | Static Horoscope | Planetary Horoscope         |
| ---------------------- | ---------------- | --------------------------- |
| **Accuracy**           | Template-based   | Astronomically accurate     |
| **Planetary Data**     | ❌ None           | ✅ Real positions & aspects  |
| **Location Specific**  | ❌ Generic        | ✅ Lat/Long/Timezone aware   |
| **Vedic Elements**     | ❌ None           | ✅ Tithi, Nakshatra included |
| **Consistency**        | 🔄 Repeatable     | 📅 Changes with time         |
| **Astrological Depth** | ⭐ Basic          | ⭐⭐⭐ Professional grade      |

## Dependencies

- **Swiss Ephemeris** (`pyswisseph`) - Astronomical calculations
- **Drik Panchanga** - Vedic calendar calculations

## Installation

```bash
pip install pyswisseph
```

## Example Output

```
=== PLANETARY DAILY HOROSCOPE ===
Sign: Scorpio
Date: 2025-07-08
Lucky Color: Silver
Lucky Number: 29
Mood: Intense (Moon in Scorpio)

Current Planetary Positions:
Sun: Gemini 21.9° (Neutral)
Moon: Scorpio 18.9° (Debilitated)
Venus: Taurus 9.5° (Own Sign)
Mars: Leo 17.6° (Neutral)
Jupiter: Gemini 12.2° (Neutral)

Active Aspects:
Moon trine Mercury (exact)
Sun sextile Mars (4° orb)
Venus sextile Saturn (2° orb)

Love: Venus in own sign brings harmony and attractiveness
Career: Steady progress through consistent efforts
Money: Balance approach to finances yields positive results
```

## Future Enhancements

- [ ] Weekly/Monthly/Yearly planetary horoscopes
- [ ] Transit analysis for major planetary movements
- [ ] Dasha (planetary periods) integration
- [ ] Muhurta (auspicious timing) calculations
- [ ] Compatibility analysis between charts

---

**Note**: This planetary horoscope engine provides professional-grade astrological calculations that rival commercial astrology software, with full Swiss Ephemeris accuracy and traditional Vedic astronomical methods.
