#!/usr/bin/env python3
"""
KP System API Endpoint Testing Script
Tests all KP-related endpoints to ensure they're working correctly
"""

import requests
import json
import sys
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:9090"
API_PREFIX = "/api/v1/kundali"

# Test data
TEST_DATA = {
    "name": "Test User",
    "date_of_birth": "13/09/2024",
    "time_of_birth": "16:18",
    "place_of_birth": "New Delhi, India",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata"
}

def test_endpoint(endpoint, description):
    """Test an API endpoint and return results"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"

    print(f"\n🧪 Testing: {description}")
    print(f"   URL: {url}")

    try:
        response = requests.post(url, json=TEST_DATA, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: SUCCESS (200)")

            # Check for expected keys based on endpoint
            expected_keys = []
            if "kp-system" in endpoint:
                expected_keys = ["kp_system", "birth_details"]
            elif "bhava-chalit" in endpoint:
                expected_keys = ["bhava_chalit", "birth_details"]
            elif "kp-bhava-combined" in endpoint:
                expected_keys = ["kp_system", "bhava_chalit", "birth_details"]

            missing_keys = [key for key in expected_keys if key not in data]
            if missing_keys:
                print(f"   ⚠️  Missing keys: {missing_keys}")
            else:
                print(f"   ✅ Data structure: VALID")

            # Check KP data quality if present
            if "kp_system" in data:
                kp_data = data["kp_system"]
                planets_count = len(kp_data.get("planets_table", []))
                cusps_count = len(kp_data.get("cusps_table", []))
                print(f"   📊 KP Data: {planets_count} planets, {cusps_count} cusps")

                # Check for AstroSage compatibility
                chart_layout = kp_data.get("chart_layout", {})
                expected_positions = {
                    "Moon": 7, "Mars": 11, "Jupiter": 11,
                    "Venus": 11, "Rahu": 12, "Ketu": 2
                }

                matches = 0
                for planet, expected_house in expected_positions.items():
                    actual_house = chart_layout.get(planet)
                    if actual_house == expected_house:
                        matches += 1

                compatibility = (matches / len(expected_positions)) * 100
                print(f"   🎯 AstroSage compatibility: {compatibility:.1f}%")

            return True, len(json.dumps(data))

        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_detail)
            except:
                error_detail = response.text[:100]

            print(f"   ❌ Status: FAILED ({response.status_code})")
            print(f"   💥 Error: {error_detail}")
            return False, 0

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Status: CONNECTION ERROR")
        print(f"   💥 Error: {str(e)}")
        return False, 0
    except Exception as e:
        print(f"   ❌ Status: UNEXPECTED ERROR")
        print(f"   💥 Error: {str(e)}")
        return False, 0

def main():
    """Run all KP endpoint tests"""
    print("🚀 KP System API Endpoint Testing")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Define test cases
    test_cases = [
        ("/api/kp-system", "KP System Analysis"),
        ("/api/bhava-chalit", "Bhava Chalit Chart"),
        ("/api/kp-bhava-combined", "Combined KP & Bhava Chalit"),
    ]

    results = []
    total_data_size = 0

    for endpoint, description in test_cases:
        success, data_size = test_endpoint(endpoint, description)
        results.append((endpoint, description, success, data_size))
        total_data_size += data_size

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    successful = sum(1 for _, _, success, _ in results if success)
    total_tests = len(results)
    success_rate = (successful / total_tests) * 100

    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful}")
    print(f"Failed: {total_tests - successful}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Data Size: {total_data_size:,} bytes")

    # Detailed results
    print(f"\nDetailed Results:")
    for endpoint, description, success, data_size in results:
        status = "✅ PASS" if success else "❌ FAIL"
        size_info = f"({data_size:,} bytes)" if success else ""
        print(f"  {status} {description} {size_info}")

    # Final status
    if success_rate == 100:
        print(f"\n🎉 ALL TESTS PASSED! KP System is fully operational.")
        sys.exit(0)
    elif success_rate >= 66:
        print(f"\n⚠️  PARTIAL SUCCESS: {successful}/{total_tests} endpoints working.")
        sys.exit(1)
    else:
        print(f"\n💥 CRITICAL FAILURE: Most endpoints not working.")
        sys.exit(2)

if __name__ == "__main__":
    main()