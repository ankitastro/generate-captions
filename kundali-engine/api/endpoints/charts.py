"""
Charts and Varga endpoints - Rasi, Navamsa, and divisional charts
"""

import logging
import traceback
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional

from models import KundaliRequest, MinimalKundliInput
from api.input_normalizer import minimal_to_kundali_request
from api.services.kundli_service import get_engine, get_translation_mgr
from core.varga_engine import get_all_varga_charts, get_all_varga_charts_detailed, VARGA_NAMES
from api.utils.constants import SIGN_NAMES
import svg_chart_generator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/charts")
def charts(
    min_req: MinimalKundliInput,
    svg: bool = Query(False, description="Include SVG charts in response")
):
    """
    Get all charts including Rasi, Navamsa, and Varga charts

    Args:
        min_req: Minimal kundli input with birth details
        svg: If True, includes SVG charts in response. Default is False.

    Returns:
        - Rasi chart (SVG if svg=True)
        - Navamsa chart (SVG if svg=True)
        - All Varga charts with data and SVGs (if svg=True)
    """
    try:
        kundali_engine = get_engine()
        translation_manager = get_translation_mgr()

        # For charts endpoint, we need planetary positions but can optimize by not running full engine
        kr: KundaliRequest = minimal_to_kundali_request(min_req)
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)

        # Generate basic charts needed for this endpoint
        rasi_chart = kundali_engine._generate_rasi_chart(planets, lagna_info['sign'])

        # Update planetary positions with house information (needed for SVG)
        updated_planets = kundali_engine._update_planetary_houses(planets, lagna_info['sign'])

        # Generate SVGs using the same method as original
        chart_lang = kr.language if kr.language else 'en'

        # Initialize SVG variables
        rasi_chart_svg = None
        navamsa_chart_svg = None
        varga_svg_dictionary = None

        # Only generate SVGs if svg flag is True
        if svg:
            # Rasi chart SVG
            rasi_chart_title = translation_manager.translate('charts.Rasi Chart', chart_lang, default="Rasi (D1)")
            rasi_svg_data = kundali_engine._prepare_rasi_data_for_svg(updated_planets, lagna_info, lang=chart_lang)
            rasi_chart_svg = svg_chart_generator.create_single_chart_svg(rasi_chart_title, rasi_svg_data, lang=chart_lang)

            # Navamsa chart SVG
            navamsa_chart = kundali_engine.divisional_charts.get_navamsa_chart(planets, lagna_info)
            navamsa_degree_map = {p.planet: p.degree for p in updated_planets}
            navamsa_degree_map['Lagna'] = lagna_info['degree']
            for p_name, p_info in navamsa_chart['navamsa_positions'].items():
                navamsa_degree_map[p_name] = p_info['degree']

            navamsa_chart_title = translation_manager.translate('charts.Navamsa Chart', chart_lang, default="Navamsa (D9)")
            navamsa_svg_data = kundali_engine._prepare_navamsa_data_for_svg(
                navamsa_chart['navamsa_chart'],
                navamsa_chart['navamsa_lagna'],
                navamsa_degree_map,
                lang=chart_lang
            )
            navamsa_chart_svg = svg_chart_generator.create_single_chart_svg(navamsa_chart_title, navamsa_svg_data, lang=chart_lang)

        # Convert planets to format needed for varga calculations
        planet_degrees = {}
        for planet_name, planet_data in planets.items():
            sign_idx = SIGN_NAMES.index(planet_data.sign) if planet_data.sign in SIGN_NAMES else 0
            planet_degrees[planet_name] = sign_idx * 30 + planet_data.degree
        planet_degrees['Lagna'] = lagna_info['abs_longitude']

        # Prepare degree map for SVG
        degree_map_for_svg = {planet_name: planet_data.degree for planet_name, planet_data in planets.items()}
        degree_map_for_svg['Lagna'] = lagna_info['degree']

        # Calculate all Varga charts
        vargas_to_calc = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 60]
        all_varga_charts = get_all_varga_charts(planet_degrees, vargas_to_calc)

        # Calculate detailed varga charts with planet positions
        all_varga_charts_detailed = get_all_varga_charts_detailed(planet_degrees, vargas_to_calc)

        # Generate the dictionary of individual SVGs only if svg flag is True
        if svg:
            varga_svg_dictionary = svg_chart_generator.create_all_varga_svgs(
                all_varga_data=all_varga_charts,
                varga_names=VARGA_NAMES,
                degree_map=degree_map_for_svg,
                lang=min_req.language if min_req.language else 'en'
            )

        # The JSON for the raw data
        major_varga_charts = {
           VARGA_NAMES.get(v, f"D{v}"): chart
           for v, chart in all_varga_charts.items()
        }

        # Translate major varga charts if language is not English
        if min_req.language and min_req.language != 'en':
            translated_major_varga_charts = {}
            for chart_name, chart_data in major_varga_charts.items():
                translated_chart = {}
                for sign, planets_list in chart_data.items():
                    # Translate sign name
                    translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', min_req.language, default=sign)

                    # Translate planet names
                    translated_planets = []
                    for planet_name in planets_list:
                        translated_planet = translation_manager.translate(f'planets.{planet_name}', min_req.language, default=planet_name)
                        translated_planets.append(translated_planet)

                    translated_chart[translated_sign] = translated_planets
                # Translate chart name
                translated_chart_name = translation_manager.translate(f'charts.{chart_name}', min_req.language, default=chart_name)
                translated_major_varga_charts[translated_chart_name] = translated_chart
            major_varga_charts_named = translated_major_varga_charts
        else:
            major_varga_charts_named = major_varga_charts

        # Detailed varga charts with planet info
        detailed_varga_charts_named = {}
        for v, chart in all_varga_charts_detailed.items():
            chart_name = VARGA_NAMES.get(v, f"D{v}")
            chart_data = {"chart_name": chart_name, "chart_number": v, **chart}

            # Translate if needed
            if min_req.language and min_req.language != 'en':
                translated_chart = {}
                for sign, planets_list in chart.items():
                    translated_planets = []
                    for planet_info in planets_list:
                        if isinstance(planet_info, dict):
                            translated_planet = planet_info.copy()
                            if 'planet' in translated_planet:
                                translated_planet['planet'] = translation_manager.translate(
                                    f'planets.{planet_info["planet"]}', min_req.language
                                )
                            if 'sign' in translated_planet:
                                translated_planet['sign'] = translation_manager.translate(
                                    f'zodiac_signs.{planet_info["sign"]}', min_req.language,
                                    default=planet_info["sign"]
                                )
                            translated_planets.append(translated_planet)
                        else:
                            translated_planets.append(
                                translation_manager.translate(f'planets.{planet_info}', min_req.language)
                            )
                    # Translate sign name
                    translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', min_req.language)
                    translated_chart[translated_sign] = translated_planets

                # Translate chart name
                translated_chart_name = translation_manager.translate(f'charts.{chart_name}', min_req.language, default=chart_name)
                chart_data = {"chart_name": translated_chart_name, "chart_number": v, **translated_chart}
            else:
                chart_data = {"chart_name": chart_name, "chart_number": v, **chart}

            if min_req.language and min_req.language != 'en':
                detailed_varga_charts_named[translated_chart_name] = chart_data
            else:
                detailed_varga_charts_named[chart_name] = chart_data

        # Build response with or without SVGs based on svg flag
        response = {
            "major_varga_charts": major_varga_charts_named,
            "detailed_varga_charts": detailed_varga_charts_named
        }

        # Only include SVGs in response if svg flag is True
        if svg:
            response["rasi_chart_svg"] = rasi_chart_svg
            response["navamsa_chart_svg"] = navamsa_chart_svg
            response["varga_charts_svgs"] = varga_svg_dictionary

        return response
    except Exception as e:
        logger.error(f"Error in /charts endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
