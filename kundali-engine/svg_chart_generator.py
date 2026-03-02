import math
import svgwrite
from typing import Dict, Optional, Tuple, Any, List
from io import StringIO
from translation_manager import get_translation_manager

ZODIAC_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

PLANET_ABBREVIATIONS = {
    'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me', 'Jupiter': 'Ju',
    'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke',
    'Ascendant': 'Asc', 'Lagna': 'Asc', 'Asc': 'Asc'
}

# Hindi abbreviations for planets
PLANET_ABBREVIATIONS_HI = {
    'Sun': 'सू', 'Moon': 'च', 'Mars': 'मं', 'Mercury': 'बु', 'Jupiter': 'गु',
    'Venus': 'शु', 'Saturn': 'श', 'Rahu': 'रा', 'Ketu': 'के',
    'Ascendant': 'लग्', 'Lagna': 'लग्', 'Asc': 'लग्'
}

def get_planet_abbreviation(planet_name: Any, lang: str = 'en') -> str:
    """Get planet abbreviation based on language, with support for Lagna variants."""
    # If somehow a dict comes through (e.g. {'planet': 'Lagna', ...})
    if isinstance(planet_name, dict):
        planet_name = planet_name.get("planet", "")

    # Always treat it as string from here
    name = str(planet_name).strip()

    # Handle any Lagna-like names (e.g. "Navamsa Lagna", "D9 Lagna", etc.)
    lowered = name.lower()
    if "lagna" in lowered:
        key = "Lagna"
        if lang == 'hi':
            return PLANET_ABBREVIATIONS_HI.get(key, "लग्")
        return PLANET_ABBREVIATIONS.get(key, "Asc")

    # Normal behavior
    if lang == 'hi':
        return PLANET_ABBREVIATIONS_HI.get(name, name[:2] if name else "")
    return PLANET_ABBREVIATIONS.get(name, name[:2] if name else "")


# Mapping from sign names (first 3 letters) to numbers for chart display
SIGNS_TO_NUMBERS = {sign[:3]: i + 1 for i, sign in enumerate(ZODIAC_SIGNS)}

PLANET_COLORS = {
  "Sun": "red", "Moon": "blue", "Mars": "red", "Mercury": "purple",
  "Jupiter": "orange", "Venus": "black", "Saturn": "steelblue", "Rahu": "darkred",
  "Ketu": "darkgreen", "Lagna": "black"
 }



# Function to calculate the center of each house
def get_house_centers(width, height):
    # Midpoints for the diamond
    center_x = width / 2
    center_y = height / 2

    # Define the coordinates of the corners of the diamond
    top_center = (center_x, 0)
    right_center = (width, center_y)
    bottom_center = (center_x, height)
    left_center = (0, center_y)

    mid_point_tri = (height - (bottom_center[1] + center_y)/2)/2
    side_mid = (width - (right_center[0] + top_center[0]) / 2)/2
    # Centers of the four quadrants (houses)
    kendra_offset_y = 70
    o_26812_y = 40
    o_35911_y = 50

    return {
        'First_House': (center_x, (top_center[1] + center_y)/2+kendra_offset_y),
        'Second_House': ((center_x + left_center[0]) / 2, mid_point_tri+o_26812_y),
        'Third_House':  ((center_x + left_center[0]) /6 , (top_center[1] + center_y)/2+o_35911_y),
        'Fourth_House': ((left_center[0] + center_x) / 2, center_y+kendra_offset_y),
        'Fifth_House': ((center_x + left_center[0]) / 6, (bottom_center[1] + center_y)/2+o_35911_y),
        'Sixth_House': ((center_x + left_center[0]) / 2, (center_y + bottom_center[1])/2+mid_point_tri+o_26812_y),
        'Seventh_House': (center_x, (center_y + bottom_center[1])/2+kendra_offset_y),
        'Eighth_House': ((center_x + right_center[0]) / 2, (bottom_center[1] + center_y)/2 + mid_point_tri+o_26812_y),
        'Ninth_House': ((right_center[0] + top_center[0])/2+side_mid+15, (bottom_center[1] + center_y)/2+o_35911_y),
        'Tenth_House': ((right_center[0] + center_x) / 2, center_y+kendra_offset_y),
        'Eleventh_House': ((right_center[0] + top_center[0])/2+side_mid+15, (center_y + top_center[1])/2+o_35911_y),
        'Twelfth_House': ((center_x + right_center[0]) / 2, mid_point_tri+o_26812_y),

    }



def get_house_signs(house_data):
    house_signs = []
    for h, inf in house_data.items():
        house_signs.append(inf['sign'])
    return house_signs

# Function to fill the kundali with circles at the center of each house, with house numbers inside
def fill_kundali_with_circles(dwg, house_centers, text_color, house_data, lang: str = 'en'):
    house_map = {
     1:'First_House',
     2:'Second_House',
     3:'Third_House',
     4:'Fourth_House',
     5:'Fifth_House',
     6:'Sixth_House',
     7:'Seventh_House',
     8:'Eighth_House',
     9:'Ninth_House',
     10:'Tenth_House',
     11:'Eleventh_House',
     12:'Twelfth_House',
    }

    translation_manager = get_translation_manager() if lang != 'en' else None
    house_numbers = get_house_signs(house_data)

    for idx, (house, (x, y)) in enumerate(house_centers.items()):
        # Draw a circle at the center of each house
        #dwg.add(dwg.circle(center=(x, y), r=10, fill='none', stroke=text_color, stroke_width=2))
        # Place the house number inside the circle (translate sign name)
        sign_text = house_numbers[idx]
        if translation_manager:
            sign_text = translation_manager.translate(f'zodiac_signs.{sign_text}', lang, default=sign_text)
        dwg.add(dwg.text(sign_text, insert=(x, y + 4), text_anchor="middle", font_size="10px", fill=text_color))

        offset = len(house_data[house_map[idx+1]]['residing_planets'])*10
        for planet_idx, planet in enumerate(house_data[house_map[idx+1]]['residing_planets']):
            # Translate planet name
            planet_text = planet
            if translation_manager:
                planet_abbr = get_planet_abbreviation(planet, lang)
                planet_text = planet_abbr
            dwg.add(dwg.text(planet_text, insert=(x, (y-offset) + planet_idx*10), text_anchor="middle", font_size="10px", fill=text_color))

# Function to create SVG with kundali and fill it with circles
def create_filled_kundali_svg(house_data, filename=None, lang: str = 'en'):
    width=400
    height=400
    rx=20
    ry=20

    if filename:
        dwg = svgwrite.Drawing(filename, profile='tiny', size=(width, height))
    else:
        dwg = svgwrite.Drawing(profile='tiny', size=(width, height))

    # Get translation manager for sign names
    translation_manager = get_translation_manager() if lang != 'en' else None

    # Add cosmic background image
    #dwg.add(dwg.image(href=background_image_url, insert=(0, 0), size=(width, height)))
    dwg.add(dwg.rect(insert=(0, 0), rx=rx, ry=ry, size=(width, height), fill='ivory'))

    # Saffron color for strokes
    saffron_color = 'rgb(255, 153, 51)'  # Saffron color
    text_color = 'black'  # White color for text

    # Create a rounded rectangle with no fill (to see the background)
    dwg.add(dwg.rect((0, 0), (width, height), rx=rx, ry=ry, fill='none', stroke=saffron_color, stroke_width=3))

    # Calculate the diamond coordinates
    diamond_points = [
        (width / 2, 0),          # Top center
        (width, height / 2),     # Right center
        (width / 2, height),     # Bottom center
        (0, height / 2)          # Left center
    ]

    # Create a diamond (polygon) that touches the center of each side
    dwg.add(dwg.polygon(diamond_points, fill='none', stroke=saffron_color, stroke_width=2))

    # Create lines that pass through the center
    dwg.add(dwg.line(start=(rx/2, rx/2), end=(width - rx/2, height - rx/2), stroke=saffron_color, stroke_width=2))
    dwg.add(dwg.line(start=(rx/2, height - rx/2), end=(width - rx/2, rx/2), stroke=saffron_color, stroke_width=2))
    # Get house centers
    house_centers = get_house_centers(width, height)

    # Fill the kundali with circles at the center of each house, with house numbers inside
    fill_kundali_with_circles(dwg, house_centers, text_color, house_data, lang)
    # Save the SVG
    return dwg.tostring()

def _get_mini_chart_house_centers(width, height):
    """Calculates the 12 text positions for a single mini-chart."""
    cx = width / 2
    cy = height / 2

    vertical_nudge = 5 # As discussed, adjust if needed for your font

    return {
        # Outer Ring (Kendra & Panapara/Apoklima)
        'First_House': (cx, height * 0.16 + vertical_nudge),
        'Second_House': (width * 0.77, height * 0.25 + vertical_nudge),
        'Third_House': (width * 0.84, cy + vertical_nudge),
        'Fourth_House': (width * 0.77, height * 0.75 + vertical_nudge),
        'Fifth_House': (cx, height * 0.84 + vertical_nudge),
        'Sixth_House': (width * 0.23, height * 0.75 + vertical_nudge),
        'Seventh_House': (width * 0.16, cy + vertical_nudge),
        'Eighth_House': (width * 0.23, height * 0.25 + vertical_nudge),

        # Inner Ring (The four inner quadrilateral sections)
        'Ninth_House': (cx, height * 0.38 + vertical_nudge),
        'Tenth_House': (width * 0.62, cy + vertical_nudge),
        'Eleventh_House': (cx, height * 0.62 + vertical_nudge),
        'Twelfth_House': (width * 0.38, cy + vertical_nudge),
    }

def _draw_single_ashtakavarga_chart(dwg, chart_group, title: str, house_values: Dict, chart_size: int, title_height: int):
    """Draws a single, correctly aligned North Indian Ashtakavarga chart into a given SVG group."""
    saffron_color, text_color, bg_color = 'rgb(255, 153, 51)', '#333', 'ivory'
    base_font_size = chart_size / 12.0

    # Draw chart structure using the main 'dwg' object, then add to the group
    chart_group.add(dwg.rect((0, 0), (chart_size, chart_size), fill=bg_color, stroke=saffron_color, stroke_width=2))
    chart_group.add(dwg.line((0, 0), (chart_size, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size, 0), (0, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size/2, 0), (chart_size, chart_size/2), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size, chart_size/2), (chart_size/2, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size/2, chart_size), (0, chart_size/2), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((0, chart_size/2), (chart_size/2, 0), stroke=saffron_color, stroke_width=1.5))

    # Draw Title relative to the group's position
    chart_group.add(dwg.text(
        title,
        insert=(chart_size / 2, -title_height / 2),
        text_anchor="middle",
        font_size=f"{base_font_size * 0.9}px",
        fill=text_color,
        font_weight="bold"
    ))

    house_centers = get_north_indian_house_centers(chart_size, chart_size)
    for house_num in range(1, 13):
        x, y = house_centers.get(house_num, (0, 0))
        value = house_values.get(str(house_num), '0')

        chart_group.add(dwg.text(
            str(value),
            insert=(x, y),
            text_anchor="middle",
            dominant_baseline="middle",
            font_size=f"{base_font_size}px",
            fill="#374151",
            font_weight="bold"
        ))

def create_ashtakavarga_svg(ashtakavarga_data: Dict, lagna_sign: str) -> str:
    """Creates a single SVG image containing a grid of all Ashtakavarga charts."""
    chart_size = 200
    margin = 20
    title_height = 30
    charts_per_row = 2

    bav_data = ashtakavarga_data.get("bhinna_ashtakavarga", {})
    sav_data = ashtakavarga_data.get("sarvashtakavarga", [])
    chart_order = [
        ("SAV", sav_data), ("Sun", bav_data.get("Sun")), ("Moon", bav_data.get("Moon")),
        ("Mars", bav_data.get("Mars")), ("Mercury", bav_data.get("Mercury")),
        ("Jupiter", bav_data.get("Jupiter")), ("Venus", bav_data.get("Venus")),
        ("Saturn", bav_data.get("Saturn")),
    ]

    valid_charts = [(title, values) for title, values in chart_order if values]
    if not valid_charts:
        return '<svg viewBox="0 0 100 50"><text x="10" y="30">No Data</text></svg>'

    num_rows = math.ceil(len(valid_charts) / charts_per_row)
    total_width = charts_per_row * (chart_size + margin) - margin
    total_height = num_rows * (chart_size + title_height + margin) - margin

    viewBox = f"0 0 {total_width} {total_height}"
    dwg = svgwrite.Drawing(viewBox=viewBox)
    dwg.add(dwg.rect(insert=(0, 0), size=(total_width, total_height), fill="ivory"))

    lagna_sign_index = ZODIAC_SIGNS.index(lagna_sign)

    for i, (title, values) in enumerate(valid_charts):
        row = i // charts_per_row
        col = i % charts_per_row
        offset_x = col * (chart_size + margin)
        offset_y = row * (chart_size + title_height + margin)

        house_values = {}
        for house_num in range(1, 13):
            sign_index_for_this_house = (lagna_sign_index + house_num - 1) % 12
            score = values[sign_index_for_this_house] if sign_index_for_this_house < len(values) else 0
            house_values[str(house_num)] = score

        # Create the group and position it
        chart_group = dwg.g(transform=f"translate({offset_x}, {offset_y + title_height})")

        # --- THIS IS THE FIX ---
        # Pass the main 'dwg' object to the helper function
        _draw_single_ashtakavarga_chart(dwg, chart_group, title, house_values, chart_size, title_height)
        dwg.add(chart_group)

    return dwg.tostring()

def get_north_indian_house_centers(width, height):
    """Calculates center coordinates for a North Indian (diamond) chart."""
    w, h = width, height
    return {
        1: (w * 0.5, h * 0.25), 2: (w * 0.25, h * 0.125), 3: (w * 0.125, h * 0.25),
        4: (w * 0.25, h * 0.5), 5: (w * 0.125, h * 0.75), 6: (w * 0.25, h * 0.875),
        7: (w * 0.5, h * 0.75), 8: (w * 0.75, h * 0.875), 9: (w * 0.875, h * 0.75),
        10: (w * 0.75, h * 0.5), 11: (w * 0.875, h * 0.25), 12: (w * 0.75, h * 0.125)
    }



def _draw_single_north_indian_chart(dwg, title: str, house_data: Dict, chart_size: int, title_height: int, lang: str = 'en'):
    """
    Draws a single, complete North Indian style chart with corrected element placement.
    - Sign numbers are placed inside the corners of their house blocks.
    - Planets are stacked correctly in the center of their house.
    """
    # --- 1. SETUP & CONFIGURATION ---
    base_font_size = chart_size / 25.0

    saffron_color, text_color, bg_color = 'rgb(255, 153, 51)', '#333', '#f7f7f7'
    planet_line_height = base_font_size * 1.1

    # --- THE FIX IS HERE ---
    # Reduced the offset to keep numbers inside the chart.
    # You can tweak this value (e.g., 8.0, 8.5, 9.0) to get the perfect placement.
    sign_offset_distance = chart_size / 10.0

    sign_offset_map = {
        1: (0, -1), 2: (-1, -1), 3: (-1, -1), 4: (-1, 0),
        5: (-1, 1), 6: (-1, 1), 7: (0, 1), 8: (1, 1),
        9: (1, 1), 10: (1, 0), 11: (1, -1), 12: (1, -1)
    }

    # --- 2. INITIALIZE SVG GROUPS & DRAW STRUCTURE ---
    chart_group = dwg.g()
    dwg.add(dwg.text(title, insert=(chart_size / 2, title_height / 2), text_anchor="middle",
                     dominant_baseline="middle", font_size=f"{base_font_size * 0.9}px", fill=text_color, font_weight="bold"))

    chart_group.attribs['transform'] = f'translate(0, {title_height})'

    chart_group.add(dwg.rect((0, 0), (chart_size, chart_size), fill=bg_color, stroke=saffron_color, stroke_width=2))
    chart_group.add(dwg.line((0, 0), (chart_size, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size, 0), (0, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size/2, 0), (chart_size, chart_size/2), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size, chart_size/2), (chart_size/2, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size/2, chart_size), (0, chart_size/2), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((0, chart_size/2), (chart_size/2, 0), stroke=saffron_color, stroke_width=1.5))

    house_centers = get_north_indian_house_centers(chart_size, chart_size)

    # --- 3. DRAW CHART CONTENTS IN TWO PASSES ---

    # == PASS 1: Draw all the SIGN NUMBERS inside the corners ==
    for house_num in range(1, 13):
        x_center, y_center = house_centers.get(house_num, (0, 0))
        sign_num = house_data.get(str(house_num), {}).get("sign_num", "")

        x_mult, y_mult = sign_offset_map.get(house_num, (0, 0))

        sign_x = x_center + (x_mult * sign_offset_distance)
        sign_y = y_center + (y_mult * sign_offset_distance)

        chart_group.add(dwg.text(
            str(sign_num), insert=(sign_x, sign_y),
            text_anchor="middle", dominant_baseline="middle",
            font_size=f"{base_font_size * 0.7}px", fill="#555"
        ))

    # == PASS 2: Draw all the PLANETS stacked in the center ==
    for house_num in range(1, 13):
        x_center, y_center = house_centers.get(house_num, (0, 0))
        planets_list = house_data.get(str(house_num), {}).get("planets", [])
        num_planets = len(planets_list)

        if num_planets == 0:
            continue

        column_threshold = 4

        if num_planets < column_threshold:
            start_y = y_center - ((num_planets - 1) * planet_line_height / 2)
            for i, planet_info in enumerate(planets_list):
                chart_group.add(dwg.text(
                    planet_info["text"], insert=(x_center, start_y + i * planet_line_height),
                    text_anchor="middle", dominant_baseline="middle",
                    font_size=f"{base_font_size * 0.65}px", fill=planet_info["color"]
                ))
        else:
            col1_count = math.ceil(num_planets / 2)
            col1 = planets_list[:col1_count]
            col2 = planets_list[col1_count:]
            x_offset_col = chart_size / 12

            start_y1 = y_center - ((len(col1) - 1) * planet_line_height / 2)
            for i, planet_info in enumerate(col1):
                chart_group.add(dwg.text(
                    planet_info["text"], insert=(x_center - x_offset_col, start_y1 + i * planet_line_height),
                    text_anchor="middle", dominant_baseline="middle",
                    font_size=f"{base_font_size * 0.65}px", fill=planet_info["color"]
                ))

            start_y2 = y_center - ((len(col2) - 1) * planet_line_height / 2)
            for i, planet_info in enumerate(col2):
                chart_group.add(dwg.text(
                    planet_info["text"], insert=(x_center + x_offset_col, start_y2 + i * planet_line_height),
                    text_anchor="middle", dominant_baseline="middle",
                    font_size=f"{base_font_size * 0.65}px", fill=planet_info["color"]
                ))

    dwg.add(chart_group)

def create_single_chart_svg(title: str, house_data: Dict, chart_size: int = 400, lang: str = 'en') -> str:
    """Creates a single, scalable SVG for any chart (Rasi, Navamsa, or Varga)."""
    title_height = 40
    viewBox = f"0 0 {chart_size} {chart_size + title_height}"

    # Create a drawing with a viewBox for responsiveness, NOT a fixed size
    dwg = svgwrite.Drawing(viewBox=viewBox)

    # Call the universal drawing function
    _draw_single_north_indian_chart(dwg, title, house_data, chart_size, title_height, lang)

    return dwg.tostring()

# --- Your Varga Grid Generator (Updated to use the new unified function) ---
def create_all_varga_svgs(
    all_varga_data: Dict[int, Any],
    varga_names: Dict[int, str],
    degree_map: Dict[str, float],
    lang: str = 'en'
) -> Dict[str, str]:
    """Generates a dictionary of individual, scalable SVG strings for each Varga chart."""
    # Get translation manager for chart title translations
    translation_manager = get_translation_manager()

    svg_dict = {}
    for varga_num, chart_raw in all_varga_data.items():
        title = varga_names.get(varga_num, f"D{varga_num}")

        # Translate chart title if language is not English
        if lang and lang != 'en':
            title = translation_manager.translate(f'charts.{title}', lang, default=title)

        # Data preparation logic for this specific varga
        varga_lagna_sign = next((sign for sign, planets in chart_raw.items() if 'Lagna' in planets), ZODIAC_SIGNS[0])
        lagna_idx = ZODIAC_SIGNS.index(varga_lagna_sign)
        north_indian_house_data = {str(h): {"sign_num": "", "planets": []} for h in range(1, 13)}

        for house_num in range(1, 13):
            sign_index = (lagna_idx + house_num - 1) % 12
            north_indian_house_data[str(house_num)]["sign_num"] = sign_index + 1

        for sign, planets in chart_raw.items():
            s_idx = ZODIAC_SIGNS.index(sign)
            house_num = ((s_idx - lagna_idx) % 12) + 1
            for planet_name in planets:
                abbr = get_planet_abbreviation(planet_name, lang)
                degree = degree_map.get(planet_name, 0.0)
                display_text = f"{abbr} {degree:.2f}°"
                planet_info = {"text": display_text, "color": PLANET_COLORS.get(planet_name, "#333")}
                north_indian_house_data[str(house_num)]["planets"].append(planet_info)

        # Use the unified SVG generator
        svg_dict[title] = create_single_chart_svg(title, north_indian_house_data, lang=lang)

    return svg_dict


def create_bhava_chalit_svg(
    title: str,
    bhava_chart: Dict[str, list],
    ascendant_longitude: float,
    chart_size: int = 400,
    lang: str = 'en'
) -> str:
    """
    Create Bhava Chalit chart SVG (North Indian style)

    IMPORTANT: This SVG generator now supports Vedic Bhava Chalit (Equal House System):
    - Planets are placed based on Vedic equal 30° houses (Lagna at center of House 1)
    - This matches AstroTalk & AstroSage implementation
    - House 1 is ALWAYS at top-center (Lagna's house)
    - Houses flow anti-clockwise from House 1

    Args:
        title: Chart title
        bhava_chart: Dictionary with house numbers as keys and planet lists as values
                    Format: {'1': ['Lagna', 'Sun'], '2': ['Moon'], ...}
        ascendant_longitude: Lagna degree in sidereal (not used for layout, kept for compatibility)
        chart_size: Size of the SVG chart
        lang: Language code ('en' or 'hi')
    """
    translation_manager = get_translation_manager() if lang != 'en' else None

    title_height = 40
    viewBox = f"0 0 {chart_size} {chart_size + title_height}"

    dwg = svgwrite.Drawing(viewBox=viewBox)

    # --- SETUP & CONFIGURATION (same as rasi chart) ---
    base_font_size = chart_size / 25.0
    saffron_color, text_color, bg_color = 'rgb(255, 153, 51)', '#333', '#f7f7f7'
    planet_line_height = base_font_size * 1.1

    # Sign offset distance for placing Bhava numbers in corners
    sign_offset_distance = chart_size / 10.0

    sign_offset_map = {
        1: (0, -1), 2: (-1, -1), 3: (-1, -1), 4: (-1, 0),
        5: (-1, 1), 6: (-1, 1), 7: (0, 1), 8: (1, 1),
        9: (1, 1), 10: (1, 0), 11: (1, -1), 12: (1, -1)
    }

    # --- DRAW TITLE ---
    chart_title = translation_manager.translate(f'charts.{title}', lang, default=title) if translation_manager else title
    dwg.add(dwg.text(
        chart_title,
        insert=(chart_size / 2, title_height / 2),
        text_anchor="middle",
        dominant_baseline="middle",
        font_size=f"{base_font_size * 0.9}px",
        fill=text_color,
        font_weight="bold"
    ))

    # --- CREATE CHART GROUP ---
    chart_group = dwg.g()
    chart_group.attribs['transform'] = f'translate(0, {title_height})'

    # --- DRAW CHART STRUCTURE (same as rasi chart) ---
    chart_group.add(dwg.rect((0, 0), (chart_size, chart_size), fill=bg_color, stroke=saffron_color, stroke_width=2))
    chart_group.add(dwg.line((0, 0), (chart_size, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size, 0), (0, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size/2, 0), (chart_size, chart_size/2), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size, chart_size/2), (chart_size/2, chart_size), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((chart_size/2, chart_size), (0, chart_size/2), stroke=saffron_color, stroke_width=1.5))
    chart_group.add(dwg.line((0, chart_size/2), (chart_size/2, 0), stroke=saffron_color, stroke_width=1.5))

    house_centers = get_north_indian_house_centers(chart_size, chart_size)

    # --- PASS 1: Draw Bhava house numbers in corners ---
    for house_num in range(1, 13):
        x_center, y_center = house_centers.get(house_num, (0, 0))

        x_mult, y_mult = sign_offset_map.get(house_num, (0, 0))
        sign_x = x_center + (x_mult * sign_offset_distance)
        sign_y = y_center + (y_mult * sign_offset_distance)

        chart_group.add(dwg.text(
            str(house_num), insert=(sign_x, sign_y),
            text_anchor="middle", dominant_baseline="middle",
            font_size=f"{base_font_size * 0.7}px", fill="#555"
        ))

    # --- PASS 2: Draw planets stacked in center ---
    for house_num in range(1, 13):
        x_center, y_center = house_centers.get(house_num, (0, 0))
        planets_list = bhava_chart.get(str(house_num), [])
        num_planets = len(planets_list)

        if num_planets == 0:
            continue

        # Prepare planet info list with abbreviations and colors
        planet_info_list = []
        for planet_name in planets_list:
            abbr = get_planet_abbreviation(planet_name, lang)
            color = PLANET_COLORS.get(planet_name, "#333")
            planet_info_list.append({"text": abbr, "color": color})

        column_threshold = 4

        if num_planets < column_threshold:
            # Single column layout
            start_y = y_center - ((num_planets - 1) * planet_line_height / 2)
            for i, planet_info in enumerate(planet_info_list):
                chart_group.add(dwg.text(
                    planet_info["text"], insert=(x_center, start_y + i * planet_line_height),
                    text_anchor="middle", dominant_baseline="middle",
                    font_size=f"{base_font_size * 0.65}px", fill=planet_info["color"]
                ))
        else:
            # Two column layout for many planets
            col1_count = math.ceil(num_planets / 2)
            col1 = planet_info_list[:col1_count]
            col2 = planet_info_list[col1_count:]
            x_offset_col = chart_size / 12

            start_y1 = y_center - ((len(col1) - 1) * planet_line_height / 2)
            for i, planet_info in enumerate(col1):
                chart_group.add(dwg.text(
                    planet_info["text"], insert=(x_center - x_offset_col, start_y1 + i * planet_line_height),
                    text_anchor="middle", dominant_baseline="middle",
                    font_size=f"{base_font_size * 0.65}px", fill=planet_info["color"]
                ))

            start_y2 = y_center - ((len(col2) - 1) * planet_line_height / 2)
            for i, planet_info in enumerate(col2):
                chart_group.add(dwg.text(
                    planet_info["text"], insert=(x_center + x_offset_col, start_y2 + i * planet_line_height),
                    text_anchor="middle", dominant_baseline="middle",
                    font_size=f"{base_font_size * 0.65}px", fill=planet_info["color"]
                ))

    dwg.add(chart_group)
    return dwg.tostring()


def create_transit_chart_svg(title: str, house_data: Dict, chart_size: int = 400, lang: str = 'en') -> str:
    """
    Creates a Gochar (Transit) chart SVG with color coding by transit nature.

    The chart shows:
    - Moon sign as House 1 (Lagna for transit)
    - Transit planets in their respective houses
    - Color coding by nature (green=good, red=challenging)
    - Legend showing transit nature meanings
    """
    title_height = 40
    legend_height = 60  # Extra space for legend
    total_height = chart_size + title_height + legend_height

    viewBox = f"0 0 {chart_size} {total_height}"
    dwg = svgwrite.Drawing(viewBox=viewBox)

    # Transit nature colors and labels
    NATURE_COLORS = {
        'excellent': ('#22c55e', 'Excellent'),
        'good': ('#86efac', 'Good'),
        'neutral': ('#94a3b8', 'Neutral'),
        'challenging': ('#f97316', 'Challenging'),
        'bad': ('#dc2626', 'Bad')
    }

    translation_manager = get_translation_manager() if lang != 'en' else None

    # Translate title
    chart_title = translation_manager.translate(f'charts.{title}', lang, default=title) if translation_manager else title

    # Add title
    dwg.add(dwg.text(
        chart_title,
        insert=(chart_size / 2, title_height / 2),
        text_anchor="middle",
        dominant_baseline="middle",
        font_size=f"{chart_size / 22}px",
        fill="#333",
        font_weight="bold"
    ))

    # Draw the main chart
    chart_group = dwg.g()
    chart_group.attribs['transform'] = f'translate(0, {title_height})'

    _draw_single_north_indian_chart(dwg, chart_title, house_data, chart_size, 0, lang)

    # Add legend below the chart
    legend_y = title_height + chart_size + 10
    legend_start_x = 30
    legend_spacing = 70

    legend_title = "Transit Nature:" if lang == 'en' else "गोचर की प्रकृति:"
    dwg.add(dwg.text(
        legend_title,
        insert=(legend_start_x, legend_y),
        text_anchor="start",
        font_size=f"{chart_size / 25}px",
        fill="#333",
        font_weight="bold"
    ))

    # Draw legend items
    for i, (nature, (color, label)) in enumerate(NATURE_COLORS.items()):
        legend_x = legend_start_x + (i * legend_spacing)
        legend_y_circle = legend_y + 20

        # Color circle
        dwg.add(dwg.circle(
            center=(legend_x, legend_y_circle),
            r=chart_size / 80,
            fill=color,
            stroke="#333",
            stroke_width=1
        ))

        # Label
        dwg.add(dwg.text(
            label,
            insert=(legend_x, legend_y_circle + chart_size / 30),
            text_anchor="middle",
            font_size=f"{chart_size / 35}px",
            fill="#333"
        ))

    return dwg.tostring()
