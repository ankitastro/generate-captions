#!/usr/bin/env python3
"""
Example: Using the Varga Engine with KundaliEngine
This demonstrates how to generate divisional charts for a birth chart
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from kundali_engine import KundaliEngine
from models import KundaliRequest

def demonstrate_varga_engine():
    """Demonstrate the Varga engine functionality"""

    # Initialize the engine
    engine = KundaliEngine()

    # Create a sample birth data
    birth_data = KundaliRequest(
        name="Sample Person",
        datetime=datetime(1990, 7, 15, 14, 30, 0),  # July 15, 1990, 2:30 PM
        timezone="Asia/Kolkata",
        latitude=28.6139,   # New Delhi
        longitude=77.2090
    )

    print("🔮 VARGA ENGINE DEMONSTRATION 🔮")
    print("=" * 60)

    # Generate the complete kundali
    print("Generating complete Kundali...")
    try:
        kundali = engine.generate_kundali(birth_data)
        print(f"✅ Kundali generated successfully for {kundali.name}")
        print(f"Birth: {birth_data.datetime.strftime('%B %d, %Y at %I:%M %p')}")
        print(f"Location: New Delhi, India")
        print(f"Coordinates: {birth_data.latitude:.4f}°N, {birth_data.longitude:.4f}°E")
        print(f"Lagna: {kundali.lagna} {kundali.lagna_degree:.2f}°")
        print()

        # Display planetary positions
        print("📍 PLANETARY POSITIONS")
        print("-" * 30)
        for planet in kundali.planets:
            print(f"{planet.planet:<8}: {planet.sign} {planet.degree:.2f}° (House {planet.house})")
        print()

        # Generate major divisional charts
        print("🌟 MAJOR DIVISIONAL CHARTS")
        print("-" * 30)

        major_vargas = [1, 2, 3, 9, 10, 12, 30]
        all_charts = engine.get_all_varga_charts(kundali.planets, major_vargas)

        for varga in major_vargas:
            chart_name = {
                1: "Rashi (D1)", 2: "Hora (D2)", 3: "Drekkana (D3)",
                9: "Navamsa (D9)", 10: "Dasamsa (D10)", 12: "Dwadasamsa (D12)",
                30: "Trimsamsa (D30)"
            }[varga]

            print(f"\n🏠 {chart_name}")
            print("-" * 20)

            chart = all_charts[varga]
            for sign, planets in chart.items():
                if planets:  # Only show signs with planets
                    print(f"{sign:<12}: {', '.join(planets)}")

        # Detailed Navamsa Analysis
        print("\n🎯 DETAILED NAVAMSA (D9) ANALYSIS")
        print("-" * 40)

        navamsa_analysis = engine.get_varga_analysis(kundali.planets, 9)

        print(f"Chart: {navamsa_analysis['varga_name']}")
        print(f"Total planets: {navamsa_analysis['total_planets']}")
        print(f"Most populated signs: {', '.join(navamsa_analysis['most_populated_signs'])}")

        print("\nPlanetary Strengths in Navamsa:")
        for planet, strength in navamsa_analysis['planet_strengths'].items():
            print(f"  {planet:<8}: {strength}")

        print("\nSign Distribution:")
        for sign, count in navamsa_analysis['sign_counts'].items():
            if count > 0:
                print(f"  {sign}: {count} planet{'s' if count > 1 else ''}")

        # Sun's journey through divisional charts
        print("\n☀️ SUN'S JOURNEY THROUGH DIVISIONAL CHARTS")
        print("-" * 50)

        sun_positions = {}
        for varga, chart in all_charts.items():
            for sign, planets in chart.items():
                if "Sun" in planets:
                    sun_positions[varga] = sign
                    break

        chart_names = {
            1: "Rashi", 2: "Hora", 3: "Drekkana", 9: "Navamsa",
            10: "Dasamsa", 12: "Dwadasamsa", 30: "Trimsamsa"
        }

        for varga in sorted(sun_positions.keys()):
            print(f"D{varga} ({chart_names[varga]}): {sun_positions[varga]}")

        # Complete Varga Summary
        print("\n📊 COMPLETE VARGA SUMMARY")
        print("-" * 30)

        # Test a few more divisional charts
        additional_vargas = [4, 7, 16, 20, 24, 27, 40, 45, 60]
        additional_charts = engine.get_all_varga_charts(kundali.planets, additional_vargas)

        print("\nAdditional Divisional Charts:")
        varga_names = {
            4: "Chaturthamsa", 7: "Saptamsa", 16: "Shodasamsa", 20: "Vimsamsa",
            24: "Chaturvimsamsa", 27: "Saptavimsamsa", 40: "Khavedamsa",
            45: "Akshavedamsa", 60: "Shastyamsa"
        }

        for varga in additional_vargas:
            print(f"\nD{varga} ({varga_names[varga]}):")
            chart = additional_charts[varga]
            occupied_signs = []
            for sign, planets in chart.items():
                if planets:
                    occupied_signs.append(f"{sign}({len(planets)})")
            print(f"  Occupied signs: {', '.join(occupied_signs[:6])}{'...' if len(occupied_signs) > 6 else ''}")

        print("\n" + "=" * 60)
        print("✅ Varga Engine demonstration completed successfully!")
        print("All major divisional charts calculated according to BPHS rules.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demonstrate_varga_engine()
