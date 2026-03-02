#!/usr/bin/env python3
"""
Compare KP System Results with AstroSage PDF
Analyzes the accuracy of our KP calculations against the reference chart
"""

import json
import sys

def main():
    print("🔍 KP System Accuracy Analysis")
    print("=" * 60)

    # Load our results
    try:
        with open('abhishek_kp_result.json', 'r') as f:
            our_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return

    print("📊 Birth Details from AstroSage PDF:")
    print("  Name: Abhishek Kumar")
    print("  Date: 23.12.1986")
    print("  Time: 0.5.0 (00:05:00)")
    print("  Place: Kanpur (26.28°N, 80.20°E)")
    print("  Lagna: Virgo")
    print("  Nakshatra: Purvaphalguni-2")
    print("  Rashi: Leo")
    print()

    # Expected planetary positions from AstroSage PDF
    astrosage_positions = {
        'Sun': {'house': 9, 'degree': '247-02-51'},
        'Moon': {'house': 5, 'degree': '138-15-10'},
        'Mars': {'house': 11, 'degree': '324-43-50'},
        'Mercury': {'house': 8, 'degree': '235-20-53'},
        'Jupiter': {'house': 11, 'degree': '322-35-48'},
        'Venus': {'house': 7, 'degree': '202-54-02'},
        'Saturn': {'house': 8, 'degree': '230-45-33'},
        'Rahu': {'house': 12, 'degree': '353-23-43'},
        'Ketu': {'house': 6, 'degree': '173-23-43'}
    }

    print("🎯 House Position Comparison:")
    print("-" * 60)

    if 'kp_system' not in our_data:
        print("❌ No KP system data found in results")
        return

    kp_data = our_data['kp_system']
    chart_layout = kp_data.get('chart_layout', {})

    matches = 0
    total_planets = len(astrosage_positions)

    for planet, expected in astrosage_positions.items():
        expected_house = expected['house']
        our_house = chart_layout.get(planet, 'Not found')

        if our_house == expected_house:
            status = "✅ MATCH"
            matches += 1
        else:
            status = "❌ DIFF"

        print(f"  {planet:<8}: Expected H{expected_house:<2} | Our H{our_house:<2} | {status}")

    accuracy = (matches / total_planets) * 100
    print("-" * 60)
    print(f"📈 Overall House Accuracy: {matches}/{total_planets} = {accuracy:.1f}%")

    # Check planets table data
    print(f"\n📋 Planetary Data Quality:")
    planets_table = kp_data.get('planets_table', [])
    print(f"  Total planets calculated: {len(planets_table)}")

    # Check for complete data
    complete_planets = 0
    for planet in planets_table:
        if all(key in planet for key in ['Planet', 'Cusp', 'Sign', 'Sign_Lord', 'Star_Lord', 'Sub_Lord']):
            complete_planets += 1

    print(f"  Planets with complete data: {complete_planets}/{len(planets_table)}")

    # Check cusps
    cusps_table = kp_data.get('cusps_table', [])
    print(f"  House cusps calculated: {len(cusps_table)}")

    # Check ruling planets
    ruling_planets = kp_data.get('ruling_planets', {})
    expected_ruling = {'Mo', 'Asc', 'Day Lord'}
    actual_ruling = set(ruling_planets.keys())
    ruling_complete = expected_ruling.issubset(actual_ruling)

    print(f"  Ruling planets: {'✅ Complete' if ruling_complete else '❌ Incomplete'}")

    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    if accuracy >= 90:
        print(f"  🌟 EXCELLENT: {accuracy:.1f}% accuracy - Production ready!")
    elif accuracy >= 75:
        print(f"  ✅ GOOD: {accuracy:.1f}% accuracy - Minor calibration needed")
    elif accuracy >= 50:
        print(f"  ⚠️  FAIR: {accuracy:.1f}% accuracy - Requires adjustment")
    else:
        print(f"  ❌ POOR: {accuracy:.1f}% accuracy - Major revision needed")

    print(f"\n📝 Key Differences Analysis:")

    # Show specific differences
    different_planets = []
    for planet, expected in astrosage_positions.items():
        our_house = chart_layout.get(planet, 'Not found')
        if our_house != expected['house']:
            different_planets.append(f"{planet}: Expected H{expected['house']}, Got H{our_house}")

    if different_planets:
        print("  Planets with house differences:")
        for diff in different_planets:
            print(f"    - {diff}")
    else:
        print("  ✅ All planetary house positions match perfectly!")

    # System info
    system_info = kp_data.get('system', 'Unknown')
    print(f"\n🔧 System: {system_info}")

if __name__ == "__main__":
    main()