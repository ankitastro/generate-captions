# Varga Engine - Divisional Charts Calculator

## Overview

The Varga Engine is a comprehensive implementation of all major divisional charts (D1-D60) according to the **Brihat Parashara Hora Shastra (BPHS)** - the foundational text of Vedic astrology. This modular system provides accurate calculations for planetary positions across various divisional charts, essential for advanced astrological analysis.

## Features

### 📊 Supported Divisional Charts

| Chart | Name           | Division | Usage                     |
| ----- | -------------- | -------- | ------------------------- |
| D1    | Rashi          | 30°00'   | Main birth chart          |
| D2    | Hora           | 15°00'   | Wealth & prosperity       |
| D3    | Drekkana       | 10°00'   | Siblings & courage        |
| D4    | Chaturthamsa   | 7°30'    | Fortune & destiny         |
| D7    | Saptamsa       | 4°17'    | Children & progeny        |
| D9    | Navamsa        | 3°20'    | Marriage & spiritual path |
| D10   | Dasamsa        | 3°00'    | Career & profession       |
| D12   | Dwadasamsa     | 2°30'    | Parents & ancestry        |
| D16   | Shodasamsa     | 1°52'    | Vehicles & comforts       |
| D20   | Vimsamsa       | 1°30'    | Spirituality & devotion   |
| D24   | Chaturvimsamsa | 1°15'    | Education & learning      |
| D27   | Saptavimsamsa  | 1°07'    | Strengths & weaknesses    |
| D30   | Trimsamsa      | 1°00'    | Diseases & misfortunes    |
| D40   | Khavedamsa     | 0°45'    | Maternal heritage         |
| D45   | Akshavedamsa   | 0°40'    | Paternal heritage         |
| D60   | Shastyamsa     | 0°30'    | Karma & past life         |

### 🔧 Core Functions

#### 1. `get_varga_sign(planet_deg: float, varga: int) -> str`
- Calculates the divisional chart sign for a planet's sidereal longitude
- Implements BPHS-specific rules for each varga
- Handles even/odd sign differences and special cases

#### 2. `get_varga_chart(planet_positions: Dict[str, float], varga: int) -> Dict[str, List[str]]`
- Generates complete divisional chart for all planets
- Returns dictionary mapping signs to planet lists
- Error handling for invalid calculations

#### 3. `get_varga_summary(planet_positions: Dict[str, float], varga: int) -> Dict`
- Comprehensive analysis including:
  - Chart layout
  - Planetary strengths (exalted/debilitated/own sign)
  - Sign distribution statistics
  - Most populated signs

#### 4. `get_all_varga_charts(planet_positions: Dict[str, float], vargas: List[int]) -> Dict`
- Generates multiple divisional charts simultaneously
- Optimized for batch processing
- Configurable varga selection

## Integration with KundaliEngine

The Varga Engine is seamlessly integrated into the main `KundaliEngine` class:

```python
from kundali_engine import KundaliEngine

engine = KundaliEngine()

# Generate a complete kundali
kundali = engine.generate_kundali(birth_data)

# Generate single varga chart
navamsa_chart = engine.get_varga_chart(kundali.planets, 9)

# Generate multiple charts
all_charts = engine.get_all_varga_charts(kundali.planets, [1, 2, 3, 9, 10, 12])

# Get detailed analysis
navamsa_analysis = engine.get_varga_analysis(kundali.planets, 9)

# Complete varga summary
major_varga_summary = engine.get_major_varga_summary(kundali.planets)
```

## BPHS Implementation Details

### Special Rules Implemented

1. **Hora (D2)**: Different rules for even/odd signs
2. **Drekkana (D3)**: 1st, 5th, 9th sign progression
3. **Navamsa (D9)**: Even/odd sign variations
4. **Dasamsa (D10)**: Forward/backward counting rules
5. **Trimsamsa (D30)**: Completely different planetary ownership for odd/even signs

### Key Features

- **Accurate Calculations**: All formulas verified against classical texts
- **Edge Case Handling**: Proper handling of degree boundaries (0°, 30°, 360°)
- **Error Resilience**: Graceful fallback for invalid inputs
- **Performance Optimized**: Efficient batch processing for multiple charts

## Usage Examples

### Basic Usage

```python
from core.varga_engine import get_varga_sign, get_varga_chart

# Calculate single planet position
sun_in_navamsa = get_varga_sign(132.45, 9)  # Sun at 132.45° in D9

# Generate complete chart
planet_positions = {
    "Sun": 132.45,
    "Moon": 220.30,
    "Mars": 45.20,
    # ... more planets
}
navamsa_chart = get_varga_chart(planet_positions, 9)
```

### Advanced Analysis

```python
from core.varga_engine import get_varga_summary

# Get comprehensive analysis
analysis = get_varga_summary(planet_positions, 9)

print(f"Total planets: {analysis['total_planets']}")
print(f"Most populated signs: {analysis['most_populated_signs']}")
print(f"Planetary strengths: {analysis['planet_strengths']}")
```

## Testing

### Test Suite

Run the comprehensive test suite:

```bash
python test_varga_engine.py
```

### Example Integration

See the complete integration example:

```bash
python example_varga_usage.py
```

## Technical Implementation

### Mathematics

Each varga uses specific mathematical formulas:

- **Base calculation**: `sign_index = int(planet_deg / 30)`
- **Degree within sign**: `degree_in_sign = planet_deg % 30`
- **Division calculation**: `division = int(degree_in_sign / (30/varga))`
- **Final sign**: Depends on varga-specific rules

### Special Cases

1. **Trimsamsa (D30)**: Uses planetary ownership rules
2. **Even/Odd Signs**: Different progression patterns
3. **Boundary Handling**: Proper wrapping for 360° transitions

## Benefits

### For Astrologers

- **Professional Accuracy**: BPHS-compliant calculations
- **Comprehensive Coverage**: All major divisional charts
- **Detailed Analysis**: Strength assessment and statistics
- **Batch Processing**: Efficient multiple chart generation

### For Developers

- **Modular Design**: Easy to extend and maintain
- **Clear Documentation**: Well-commented code
- **Error Handling**: Robust error management
- **Performance**: Optimized for speed

## Future Enhancements

- **Additional Vargas**: Support for specialized divisional charts
- **Chart Visualization**: Graphical representation of charts
- **Advanced Analysis**: More sophisticated strength calculations
- **Integration**: HTML report generation with varga charts

---

## Quick Start

```python
# Import and initialize
from kundali_engine import KundaliEngine
engine = KundaliEngine()

# Generate birth chart
birth_data = KundaliRequest(...)
kundali = engine.generate_kundali(birth_data)

# Get Navamsa chart
navamsa = engine.get_varga_chart(kundali.planets, 9)

# Analyze results
for sign, planets in navamsa.items():
    if planets:
        print(f"{sign}: {', '.join(planets)}")
```

✅ **Ready to use**: The Varga Engine is fully integrated and ready for production use in your Vedic astrology applications.
