from typing import Dict, List, Tuple

def calculate_mangal_dosha(
    planet_houses: Dict[str, int],
    planet_signs: Dict[str, str],
    planet_degrees: Dict[str, float], # Added for more precise calculations
    lagna_house: int = 1, # Assuming Lagna is typically house 1 for calculations
    aspects: Dict[str, List[Tuple[str, int]]] = None # For aspects, if available
) -> Dict:
    """
    Checks for Mangal Dosha (Manglik) from the Lagna and includes detailed calculations
    for presence, cancellation, and percentages.
    
    Args:
        planet_houses: A dictionary mapping planet names to their house numbers.
        planet_signs: A dictionary mapping planet names to their zodiac signs.
        planet_degrees: A dictionary mapping planet names to their longitudes (degrees).
        lagna_house: The house number of the Lagna (Ascendant). Default is 1.
        aspects: Optional. A dictionary where keys are planet names and values are
                 lists of tuples (other_planet, aspect_strength).
                 e.g., {'Jupiter': [('Mars', 0.8)]} for Jupiter's aspect on Mars.
    """
    
    if aspects is None:
        aspects = {} # Initialize empty if not provided

    if 'Mars' not in planet_houses:
        return {
            "is_present": False,
            "is_cancelled": False,
            "report": "Mars not found in chart.",
            "manglik_present_rule": {"based_on_aspect": [], "based_on_house": []},
            "manglik_cancel_rule": [],
            "is_mars_manglik_cancelled": False,
            "manglik_status": "Not Manglik",
            "percentage_manglik_present": 0.0,
            "percentage_manglik_after_cancellation": 0.0,
            "manglik_report": "Mars not found in the chart, so Mangal Dosha is not applicable."
        }

    mars_house = planet_houses['Mars']
    mars_sign = planet_signs['Mars']
    
    # --- 1. Mangal Dosha Presence Rules ---
    # Houses where Mars causes Dosha (from Lagna, Moon, and Venus)
    # This example focuses on Lagna, but can be extended.
    dosha_houses = [1, 2, 4, 7, 8, 12] # Lagna, 2nd, 4th, 7th, 8th, 12th houses

    is_present_from_lagna = mars_house in dosha_houses
    
    # You'd need Moon and Venus positions here for comprehensive check
    # For simplicity, let's assume this function currently only checks from Lagna
    # is_present_from_moon = planet_houses.get('Moon') and ((mars_house - planet_houses['Moon'] + 12) % 12 + 1) in dosha_houses
    # is_present_from_venus = planet_houses.get('Venus') and ((mars_house - planet_houses['Venus'] + 12) % 12 + 1) in dosha_houses

    # For now, let's stick to the core logic as per your original code
    is_present = is_present_from_lagna # You can expand this to OR with Moon/Venus based checks
    
    present_rules_house: List[str] = []
    if is_present_from_lagna:
        present_rules_house.append(f"Mars in {mars_house}th house from Lagna.")
    # Add rules based on Moon/Venus if you implement them

    # --- 2. Mangal Dosha Cancellation Rules ---
    cancellation_rules: List[str] = []
    is_cancelled_flag = False # Will be true if *any* major cancellation applies

    # Rule 1: Mars in own sign (Aries, Scorpio)
    if mars_sign in ['Aries', 'Scorpio']:
        is_cancelled_flag = True
        cancellation_rules.append("Mars is in its own sign (Aries or Scorpio).")
            
    # Rule 2: Mars in exaltation sign (Capricorn)
    if mars_sign == 'Capricorn':
        is_cancelled_flag = True
        cancellation_rules.append("Mars is in its exaltation sign (Capricorn).")
        
    # Rule 3: Mars in a friendly sign (Leo, Cancer, Sagittarius, Pisces)
    if mars_sign in ['Cancer', 'Leo', 'Sagittarius', 'Pisces']: # Example friendly signs
        # This rule might be considered a milder cancellation or reduction, not full cancellation
        # Depending on tradition, this might just reduce intensity. Let's make it a cancellation for this example.
        # is_cancelled_flag = True # Decide if this fully cancels or just mitigates
        # cancellation_rules.append(f"Mars is in a friendly sign ({mars_sign}).")
        pass # For strict cancellation, avoid this if it's just mitigation

    # Rule 4: Mars aspected by a benefic planet (e.g., Jupiter)
    # This requires more advanced aspect calculation. Assuming you have 'aspects' data.
    if 'Jupiter' in aspects:
        for aspecting_planet, strength in aspects['Jupiter']:
            if aspecting_planet == 'Mars' and strength > 0.5: # Example: strong aspect
                is_cancelled_flag = True
                cancellation_rules.append("Mars is aspected by benefic Jupiter.")
                break

    # Rule 5: Mars in certain houses in certain signs (e.g., Mars in 2nd house of Gemini/Virgo, Mars in 7th house of Cancer/Capricorn)
    # This requires detailed astrological rules. Example:
    if mars_house == 2 and mars_sign in ['Gemini', 'Virgo']:
        is_cancelled_flag = True
        cancellation_rules.append(f"Mars in 2nd house in {mars_sign}.")
    if mars_house == 4 and mars_sign in ['Taurus', 'Libra']:
         is_cancelled_flag = True
         cancellation_rules.append(f"Mars in 4th house in {mars_sign}.")
    # Add more such specific rules

    # Rule 6: Lagna Lord in Kendra/Trikona (can reduce general doshas) - More general
    # Rule 7: Strong Jupiter/Venus in Lagna/Kendra - General benefic influence

    # Determine final cancellation status
    is_mars_manglik_cancelled = is_cancelled_flag

    # --- 3. Percentage Calculations (Illustrative - often subjective) ---
    # These percentages are highly interpretive and not universally standardized.
    # You'd need a robust astrological model to assign weights to each rule.
    # This is a very simplistic example.
    
    base_manglik_strength = 100.0 if is_present else 0.0
    
    # Apply cancellation effects to percentage
    percentage_after_cancellation = base_manglik_strength
    if is_present:
        if is_mars_manglik_cancelled:
            # Each cancellation rule could reduce the percentage
            # For simplicity, if cancelled, it's significantly reduced or negated
            percentage_after_cancellation = 10.0 # Example: Reduced to 10% if cancelled
        # More nuanced: reduction based on number/strength of cancellation rules
        # percentage_reduction_per_cancellation_rule = 15.0 # Example
        # percentage_after_cancellation = max(0, base_manglik_strength - len(cancellation_rules) * percentage_reduction_per_cancellation_rule)

    # --- 4. Manglik Status and Report ---
    manglik_status = "Manglik"
    if not is_present:
        manglik_status = "Not Manglik"
    elif is_mars_manglik_cancelled:
        manglik_status = "Manglik (Cancelled)"
    
    manglik_report = f"Mangal Dosha is {'present' if is_present else 'not present'}. "
    if is_present:
        manglik_report += f"Mars is located in the {mars_house}th house. "
    if is_mars_manglik_cancelled and cancellation_rules:
        manglik_report += "However, it is cancelled due to the following reasons: " + "; ".join(cancellation_rules) + "."
    elif is_present and not is_mars_manglik_cancelled:
         manglik_report += "No major cancellation rules are observed."
    
    return {
        "is_present": is_present,
        "is_cancelled": is_mars_manglik_cancelled, # This aligns with your original output
        "report": manglik_report, # This aligns with your original output, could be shorter
        "manglik_present_rule": {
            "based_on_house": present_rules_house,
            "based_on_aspect": [] # Populate if you implement aspect-based presence rules
        },
        "manglik_cancel_rule": cancellation_rules,
        "is_mars_manglik_cancelled": is_mars_manglik_cancelled,
        "manglik_status": manglik_status,
        "percentage_manglik_present": base_manglik_strength,
        "percentage_manglik_after_cancellation": percentage_after_cancellation,
        "manglik_report": manglik_report # More detailed report
    }

def calculate_kalasarpa_dosha(
    planet_longitudes: Dict[str, float],
    planet_houses: Dict[str, int] # Needed for house_id in report
) -> Dict:
    """
    Checks for Kalasarpa Dosha and determines its type.
    
    Args:
        planet_longitudes: A dictionary mapping planet names to their longitudes (degrees).
        planet_houses: A dictionary mapping planet names to their house numbers.
    """
    
    if 'Rahu' not in planet_longitudes or 'Ketu' not in planet_longitudes:
        return {
            "is_present": False,
            "report": "Rahu or Ketu not found in chart.",
            "present": False,
            "type": "N/A",
            "one_line": "Kalasarpa Dosha is not applicable as Rahu/Ketu data is missing.",
            "name": "N/A",
            "report": {"house_id": 0, "report": "Kalasarpa Dosha not applicable."}
        }

    rahu_lon = planet_longitudes['Rahu']
    ketu_lon = planet_longitudes['Ketu'] # Ketu is always 180 degrees from Rahu
    
    planets_to_check = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    planets_hemmed_rahu_ketu_axis = True
    planets_hemmed_ketu_rahu_axis = True
    
    # Determine the "direction" of the axis based on Rahu's position
    # If Rahu is 0-180 and Ketu 180-360, axis 1 is Rahu to Ketu (0 to 180)
    # If Rahu is 180-360 and Ketu 0-180, axis 2 is Rahu to Ketu (180 to 360)
    
    # Normalize longitudes to be between 0 and 360
    rahu_lon_norm = rahu_lon % 360
    ketu_lon_norm = ketu_lon % 360

    # Calculate the span of the Rahu-Ketu axis in both directions
    # Axis 1: Rahu (start) to Ketu (end)
    span1_start = rahu_lon_norm
    span1_end = ketu_lon_norm
    if span1_end < span1_start:
        span1_end += 360 # Wrap around
    
    # Axis 2: Ketu (start) to Rahu (end)
    span2_start = ketu_lon_norm
    span2_end = rahu_lon_norm
    if span2_end < span2_start:
        span2_end += 360 # Wrap around

    # Check if all planets are within the first axis (Rahu -> Ketu)
    for planet in planets_to_check:
        planet_lon = planet_longitudes.get(planet)
        if planet_lon is None:
            planets_hemmed_rahu_ketu_axis = False
            planets_hemmed_ketu_rahu_axis = False
            break
        
        plon_norm = planet_lon % 360
        
        # Check for span 1 (Rahu to Ketu)
        if span1_start <= span1_end:
            if not (span1_start <= plon_norm <= span1_end):
                planets_hemmed_rahu_ketu_axis = False
        else: # Span wraps around 0/360
            if not (plon_norm >= span1_start or plon_norm <= span1_end - 360):
                planets_hemmed_rahu_ketu_axis = False

        # Check for span 2 (Ketu to Rahu)
        if span2_start <= span2_end:
            if not (span2_start <= plon_norm <= span2_end):
                planets_hemmed_ketu_rahu_axis = False
        else: # Span wraps around 0/360
            if not (plon_norm >= span2_start or plon_norm <= span2_end - 360):
                planets_hemmed_ketu_rahu_axis = False

    is_present = planets_hemmed_rahu_ketu_axis or planets_hemmed_ketu_rahu_axis
    
    dosha_type = "N/A"
    dosha_name = "N/A"
    one_line_summary = "Kalasarpa Dosha is not present."
    detailed_report = {"house_id": 0, "report": "Kalasarpa Dosha is not present."}
    
    if is_present:
        # Determine type based on which side the planets are hemmed
        if planets_hemmed_rahu_ketu_axis:
            dosha_type = "Purva Ardh Kalasarpa Yoga (Planets between Rahu and Ketu)"
            # Names of Kalasarpa types are specific to houses Rahu/Ketu occupy
            # You'd need a mapping for Rahu's house to the specific Kalasarpa name
            # Example: Rahu in 1st house -> Anant Kalasarpa Yoga
            # Rahu in 2nd house -> Kulik Kalasarpa Yoga
            rahu_house = planet_houses.get('Rahu', 0)
            
            # This mapping is illustrative, you need to verify exact names
            kalasarpa_names = {
                1: "Anant Kalasarpa Yoga",
                2: "Kulik Kalasarpa Yoga",
                3: "Vasuki Kalasarpa Yoga",
                4: "Shankhpal Kalasarpa Yoga",
                5: "Padma Kalasarpa Yoga",
                6: "Mahapadma Kalasarpa Yoga",
                7: "Takshak Kalasarpa Yoga",
                8: "Karkotak Kalasarpa Yoga",
                9: "Shankhnad Kalasarpa Yoga",
                10: "Ghatak Kalasarpa Yoga",
                11: "Vishdhar Kalasarpa Yoga",
                12: "Sheshnag Kalasarpa Yoga",
            }
            dosha_name = kalasarpa_names.get(rahu_house, "Unknown Kalasarpa Yoga")
            one_line_summary = f"Kalasarpa Dosha ({dosha_name}) is present as all planets are hemmed between Rahu and Ketu."
            detailed_report = {
                "house_id": rahu_house,
                "report": f"{dosha_name} is formed when all planets are situated between Rahu and Ketu. "
                          f"Rahu is in the {rahu_house}th house. This formation can lead to..." # Add more effects based on type
            }
        else: # planets_hemmed_ketu_rahu_axis
            dosha_type = "Paschima Ardh Kalasarpa Yoga (Planets between Ketu and Rahu)"
            # Names would typically follow the Ketu's house from Lagna in this case
            ketu_house = planet_houses.get('Ketu', 0)
            kalasarpa_names_ketu = {
                1: "Sheshnag Kalasarpa Yoga", # If Ketu in 1st, Rahu in 7th
                # ... other mappings if they differ for Ketu-start
            }
            dosha_name = kalasarpa_names_ketu.get(ketu_house, "Unknown Kalasarpa Yoga (Ketu-start)")
            one_line_summary = f"Kalasarpa Dosha ({dosha_name}) is present as all planets are hemmed between Ketu and Rahu."
            detailed_report = {
                "house_id": ketu_house,
                "report": f"{dosha_name} is formed when all planets are situated between Ketu and Rahu. "
                          f"Ketu is in the {ketu_house}th house. This formation can lead to..." # Add more effects based on type
            }

    return {
        "is_present": is_present,
        "one_line_summary_text": detailed_report["report"], # Matches your original 'report'
        "present": is_present, # Matches the 'present' key in your desired output
        "type": dosha_type,
        "one_line": one_line_summary,
        "name": dosha_name,
        "report": detailed_report # More structured report
    }
