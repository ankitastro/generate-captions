"""
Calculator endpoints - Rashi, Sun Sign, Nakshatra, Numerology
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from models import KundaliRequest, MinimalKundliInput
from api.input_normalizer import minimal_to_kundali_request
from api.services.kundli_service import get_engine
from api.utils.constants import RASHI_DETAILS, SUN_SIGN_DETAILS

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/calculators/rashi")
async def calculate_rashi_only(req: MinimalKundliInput):
    """
    Calculate Rashi (Moon Sign) using accurate Vedic astrology

    This endpoint calculates the Moon's position at birth to determine the Rashi (Moon Sign).
    Requires: name, date_of_birth, time_of_birth, place_of_birth for accurate calculation.

    Returns:
        - Rashi name and details
        - Moon's nakshatra, pada, and lord
        - Element, quality, and lucky gem
    """
    try:
        kundali_engine = get_engine()
        # Convert minimal input to full KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info(f"Calculating Rashi for {req.name}")

        # Calculate Julian Day
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

        # Get Moon's nakshatra (which determines Rashi)
        moon_nakshatra = kundali_engine._get_moon_nakshatra(jd)

        # Get Moon's position from planetary calculations
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)
        moon_data = planets.get('Moon')

        if not moon_data:
            raise HTTPException(status_code=500, detail="Could not calculate Moon position")

        rashi = moon_data.sign
        details = RASHI_DETAILS.get(rashi, {})

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth,
            },
            "rashi": {
                "sign": rashi,
                "sanskrit_name": details.get('sanskrit', rashi),
                "rashi_lord": details.get('lord', ''),
                "element": details.get('element', ''),
                "quality": details.get('quality', ''),
                "lucky_gem": details.get('lucky_gem', ''),
                "moon_degree": round(moon_data.degree, 2),
                "moon_degree_dms": moon_data.degree_dms,
            },
            "nakshatra": {
                "name": moon_nakshatra.name,
                "pada": moon_nakshatra.pada,
                "lord": moon_nakshatra.lord,
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Rashi: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Rashi: {str(e)}")


@router.post("/api/calculators/sun-sign")
async def calculate_sun_sign_only(req: MinimalKundliInput):
    """
    Calculate Sun Sign (Western/Tropical Zodiac) using accurate astronomical data

    This endpoint calculates the Sun's position at birth to determine the Sun Sign.
    Requires: name, date_of_birth, time_of_birth, place_of_birth for accurate calculation.

    Returns:
        - Sun sign name and symbol
        - Element, quality, and ruling planet
        - Lucky color and number
        - Key personality traits
    """
    try:
        kundali_engine = get_engine()
        # Convert minimal input to full KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info(f"Calculating Sun Sign for {req.name}")

        # Get Sun's position from planetary calculations
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)
        sun_data = planets.get('Sun')

        if not sun_data:
            raise HTTPException(status_code=500, detail="Could not calculate Sun position")

        sun_sign = sun_data.sign
        details = SUN_SIGN_DETAILS.get(sun_sign, {})

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth,
            },
            "sun_sign": {
                "sign": sun_sign,
                "symbol": details.get('symbol', ''),
                "element": details.get('element', ''),
                "quality": details.get('quality', ''),
                "ruling_planet": details.get('ruling_planet', ''),
                "lucky_color": details.get('lucky_color', ''),
                "lucky_number": details.get('lucky_number', 0),
                "traits": details.get('traits', []),
                "sun_degree": round(sun_data.degree, 2),
                "sun_degree_dms": sun_data.degree_dms,
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Sun Sign: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Sun Sign: {str(e)}")


# Comprehensive nakshatra details
NAKSHATRA_DETAILS = {
    'Ashwini': {
        'symbol': 'Horse Head', 'deity': 'Ashwini Kumaras', 'gana': 'Deva (Divine)',
        'element': 'Earth', 'lucky_color': 'Red',
        'characteristics': ['Quick', 'Healing', 'Pioneering', 'Enthusiastic', 'Independent']
    },
    'Bharani': {
        'symbol': 'Yoni (Womb)', 'deity': 'Yama', 'gana': 'Manushya (Human)',
        'element': 'Earth', 'lucky_color': 'Red',
        'characteristics': ['Creative', 'Passionate', 'Responsible', 'Determined', 'Nurturing']
    },
    'Krittika': {
        'symbol': 'Razor/Flame', 'deity': 'Agni', 'gana': 'Rakshasa (Demon)',
        'element': 'Earth', 'lucky_color': 'White',
        'characteristics': ['Sharp', 'Determined', 'Ambitious', 'Purifying', 'Direct']
    },
    'Rohini': {
        'symbol': 'Cart/Chariot', 'deity': 'Brahma', 'gana': 'Manushya (Human)',
        'element': 'Earth', 'lucky_color': 'White',
        'characteristics': ['Beautiful', 'Creative', 'Sensual', 'Materialistic', 'Growth']
    },
    'Mrigashira': {
        'symbol': 'Deer Head', 'deity': 'Soma', 'gana': 'Deva (Divine)',
        'element': 'Earth', 'lucky_color': 'Silver',
        'characteristics': ['Curious', 'Searching', 'Gentle', 'Suspicious', 'Restless']
    },
    'Ardra': {
        'symbol': 'Teardrop/Diamond', 'deity': 'Rudra', 'gana': 'Manushya (Human)',
        'element': 'Air', 'lucky_color': 'Green',
        'characteristics': ['Transformative', 'Intense', 'Emotional', 'Destructive', 'Renewal']
    },
    'Punarvasu': {
        'symbol': 'Bow and Quiver', 'deity': 'Aditi', 'gana': 'Deva (Divine)',
        'element': 'Air', 'lucky_color': 'Yellow',
        'characteristics': ['Optimistic', 'Repetitive', 'Philosophical', 'Protective', 'Generous']
    },
    'Pushya': {
        'symbol': 'Cow Udder/Lotus', 'deity': 'Brihaspati', 'gana': 'Deva (Divine)',
        'element': 'Water', 'lucky_color': 'Orange',
        'characteristics': ['Nurturing', 'Spiritual', 'Disciplined', 'Conservative', 'Devoted']
    },
    'Ashlesha': {
        'symbol': 'Coiled Serpent', 'deity': 'Nagas', 'gana': 'Rakshasa (Demon)',
        'element': 'Water', 'lucky_color': 'Red',
        'characteristics': ['Mystical', 'Secretive', 'Intuitive', 'Cunning', 'Powerful']
    },
    'Magha': {
        'symbol': 'Royal Throne', 'deity': 'Pitris (Ancestors)', 'gana': 'Rakshasa (Demon)',
        'element': 'Water', 'lucky_color': 'Ivory',
        'characteristics': ['Royal', 'Authoritative', 'Proud', 'Traditional', 'Respectful']
    },
    'Purva Phalguni': {
        'symbol': 'Front Legs of Bed', 'deity': 'Bhaga', 'gana': 'Manushya (Human)',
        'element': 'Water', 'lucky_color': 'Light Brown',
        'characteristics': ['Creative', 'Pleasure-loving', 'Artistic', 'Relaxing', 'Generous']
    },
    'Uttara Phalguni': {
        'symbol': 'Back Legs of Bed', 'deity': 'Aryaman', 'gana': 'Manushya (Human)',
        'element': 'Fire', 'lucky_color': 'Bright Blue',
        'characteristics': ['Generous', 'Friendly', 'Responsible', 'Leadership', 'Helpful']
    },
    'Hasta': {
        'symbol': 'Hand/Fist', 'deity': 'Savitar', 'gana': 'Deva (Divine)',
        'element': 'Fire', 'lucky_color': 'Light Green',
        'characteristics': ['Skillful', 'Hardworking', 'Clever', 'Humorous', 'Dexterous']
    },
    'Chitra': {
        'symbol': 'Bright Jewel/Pearl', 'deity': 'Tvashtar', 'gana': 'Rakshasa (Demon)',
        'element': 'Fire', 'lucky_color': 'Black',
        'characteristics': ['Creative', 'Charismatic', 'Artistic', 'Ambitious', 'Bright']
    },
    'Swati': {
        'symbol': 'Young Sprout/Coral', 'deity': 'Vayu', 'gana': 'Deva (Divine)',
        'element': 'Fire', 'lucky_color': 'Black',
        'characteristics': ['Independent', 'Flexible', 'Business-minded', 'Diplomatic', 'Restless']
    },
    'Vishakha': {
        'symbol': 'Triumphal Archway', 'deity': 'Indra-Agni', 'gana': 'Rakshasa (Demon)',
        'element': 'Fire', 'lucky_color': 'Gold',
        'characteristics': ['Determined', 'Goal-oriented', 'Ambitious', 'Powerful', 'Patient']
    },
    'Anuradha': {
        'symbol': 'Lotus/Triumphal Archway', 'deity': 'Mitra', 'gana': 'Deva (Divine)',
        'element': 'Fire', 'lucky_color': 'Reddish Brown',
        'characteristics': ['Devoted', 'Balanced', 'Friendly', 'Spiritual', 'Disciplined']
    },
    'Jyeshtha': {
        'symbol': 'Circular Amulet/Earring', 'deity': 'Indra', 'gana': 'Rakshasa (Demon)',
        'element': 'Air', 'lucky_color': 'Cream',
        'characteristics': ['Authoritative', 'Protective', 'Responsible', 'Generous', 'Mature']
    },
    'Mula': {
        'symbol': 'Tied Roots/Elephant Goad', 'deity': 'Nirriti', 'gana': 'Rakshasa (Demon)',
        'element': 'Air', 'lucky_color': 'Brown',
        'characteristics': ['Investigative', 'Transformative', 'Philosophical', 'Destructive', 'Rooted']
    },
    'Purva Ashadha': {
        'symbol': 'Elephant Tusk/Fan', 'deity': 'Apas', 'gana': 'Manushya (Human)',
        'element': 'Air', 'lucky_color': 'Black',
        'characteristics': ['Invincible', 'Proud', 'Philosophical', 'Purifying', 'Ambitious']
    },
    'Uttara Ashadha': {
        'symbol': 'Elephant Tusk/Planks of Bed', 'deity': 'Vishvadevas', 'gana': 'Manushya (Human)',
        'element': 'Air', 'lucky_color': 'Copper',
        'characteristics': ['Righteous', 'Leadership', 'Ambitious', 'Grateful', 'Principled']
    },
    'Shravana': {
        'symbol': 'Three Footprints/Ear', 'deity': 'Vishnu', 'gana': 'Deva (Divine)',
        'element': 'Air', 'lucky_color': 'Light Blue',
        'characteristics': ['Listening', 'Learning', 'Communicative', 'Thoughtful', 'Organized']
    },
    'Dhanishta': {
        'symbol': 'Drum/Flute', 'deity': 'Eight Vasus', 'gana': 'Rakshasa (Demon)',
        'element': 'Ether', 'lucky_color': 'Silver Grey',
        'characteristics': ['Musical', 'Wealthy', 'Charitable', 'Bold', 'Adaptable']
    },
    'Shatabhisha': {
        'symbol': 'Empty Circle/1000 Flowers', 'deity': 'Varuna', 'gana': 'Rakshasa (Demon)',
        'element': 'Ether', 'lucky_color': 'Blue Green',
        'characteristics': ['Healing', 'Secretive', 'Scientific', 'Mystical', 'Independent']
    },
    'Purva Bhadrapada': {
        'symbol': 'Front Legs of Funeral Cot/Two Faced Man', 'deity': 'Aja Ekapada', 'gana': 'Manushya (Human)',
        'element': 'Ether', 'lucky_color': 'Silver Grey',
        'characteristics': ['Intense', 'Passionate', 'Transformative', 'Mystical', 'Dualistic']
    },
    'Uttara Bhadrapada': {
        'symbol': 'Back Legs of Funeral Cot/Twins', 'deity': 'Ahir Budhnya', 'gana': 'Manushya (Human)',
        'element': 'Ether', 'lucky_color': 'Purple',
        'characteristics': ['Wise', 'Spiritual', 'Patient', 'Calm', 'Mystical']
    },
    'Revati': {
        'symbol': 'Fish/Drum', 'deity': 'Pushan', 'gana': 'Deva (Divine)',
        'element': 'Ether', 'lucky_color': 'Brown',
        'characteristics': ['Nurturing', 'Protective', 'Compassionate', 'Wealthy', 'Journey']
    },
}


@router.post("/api/calculators/nakshatra")
async def calculate_nakshatra_only(req: MinimalKundliInput):
    """
    Calculate Nakshatra (Lunar Mansion) using accurate Vedic astrology

    This endpoint calculates the Moon's nakshatra at birth with detailed information.
    Requires: name, date_of_birth, time_of_birth, place_of_birth for accurate calculation.

    Returns:
        - Nakshatra name, lord, and pada
        - Symbol, deity, and gana
        - Characteristics and element
        - Lucky color
    """
    try:
        kundali_engine = get_engine()
        # Convert minimal input to full KundaliRequest
        kr: KundaliRequest = minimal_to_kundali_request(req)
        logger.info(f"Calculating Nakshatra for {req.name}")

        # Calculate Julian Day
        jd = kundali_engine._datetime_to_jd(kr.datetime, kr.timezone)

        # Get Moon's nakshatra
        moon_nakshatra = kundali_engine._get_moon_nakshatra(jd)

        # Get Moon's position for additional details
        planets, lagna_info, person = kundali_engine._calculate_positions_with_kerykeion(kr)
        moon_data = planets.get('Moon')

        nakshatra_name = moon_nakshatra.name
        details = NAKSHATRA_DETAILS.get(nakshatra_name, {})

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
                "time_of_birth": req.time_of_birth,
                "place_of_birth": req.place_of_birth,
            },
            "nakshatra": {
                "name": nakshatra_name,
                "pada": moon_nakshatra.pada,
                "lord": moon_nakshatra.lord,
                "symbol": details.get('symbol', ''),
                "deity": details.get('deity', ''),
                "gana": details.get('gana', ''),
                "element": details.get('element', ''),
                "lucky_color": details.get('lucky_color', ''),
                "characteristics": details.get('characteristics', []),
            },
            "moon_position": {
                "sign": moon_data.sign if moon_data else '',
                "degree": round(moon_data.degree, 2) if moon_data else 0,
                "degree_dms": moon_data.degree_dms if moon_data else '',
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Nakshatra: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Nakshatra: {str(e)}")


@router.post("/api/calculators/numerology")
async def calculate_numerology(req: MinimalKundliInput):
    """
    Calculate comprehensive Numerology analysis

    This endpoint calculates multiple numerology numbers from birth date and name.
    Requires: name, date_of_birth for accurate calculation.

    Returns:
        - Life Path Number with meaning
        - Destiny Number (from name)
        - Soul Urge Number (from vowels)
        - Personality Number (from consonants)
        - Lucky Numbers
    """
    try:
        logger.info(f"Calculating Numerology for {req.name}")

        # Parse date of birth
        from api.input_normalizer import _parse_date
        year, month, day = _parse_date(req.date_of_birth)

        # Helper functions for numerology calculations
        def reduce_to_single_digit(num: int) -> int:
            """Reduce a number to single digit, keeping master numbers 11, 22, 33"""
            if num in [11, 22, 33]:
                return num
            while num > 9:
                num = sum(int(digit) for digit in str(num))
            return num

        def get_letter_value(letter: str) -> int:
            """Get numerology value of a letter (A=1, B=2, ... Z=8)"""
            values = {
                'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
                'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
                's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8,
            }
            return values.get(letter.lower(), 0)

        def get_name_value(name: str) -> int:
            """Calculate total value of a name"""
            clean_name = ''.join(c.lower() for c in name if c.isalpha())
            return sum(get_letter_value(char) for char in clean_name)

        # Number meanings
        life_path_meanings = {
            1: "The Leader - Independent, ambitious, and pioneering. Natural leader with strong willpower.",
            2: "The Peacemaker - Diplomatic, cooperative, and sensitive. Excel in partnerships and teamwork.",
            3: "The Creative - Expressive, optimistic, and social. Gift for communication and creativity.",
            4: "The Builder - Practical, disciplined, and hardworking. Create solid foundations and value stability.",
            5: "The Freedom Seeker - Adventurous, versatile, and energetic. Love freedom and new experiences.",
            6: "The Nurturer - Responsible, caring, and harmonious. Devoted to family and community service.",
            7: "The Seeker - Analytical, spiritual, and introspective. Seek knowledge and deeper understanding.",
            8: "The Powerhouse - Ambitious, authoritative, and success-oriented. Strong business acumen.",
            9: "The Humanitarian - Compassionate, generous, and idealistic. Devoted to making the world better.",
            11: "The Visionary - Intuitive, inspirational, and enlightened. Master number with spiritual insights.",
            22: "The Master Builder - Practical visionary who can turn dreams into reality on a large scale.",
            33: "The Master Teacher - Devoted to uplifting humanity through selfless service and guidance.",
        }

        destiny_meanings = {
            1: "Destined to be a leader and pioneer, breaking new ground and inspiring others.",
            2: "Destiny involves diplomacy, partnership, and bringing people together in harmony.",
            3: "Meant to express yourself creatively and bring joy to others through your talents.",
            4: "Destiny is to build lasting structures and provide stability for yourself and others.",
            5: "Destined for a life of adventure, change, and helping others embrace freedom.",
            6: "Destiny involves nurturing, teaching, and creating harmony in your community.",
            7: "Meant to seek and share wisdom, pursuing spiritual and intellectual growth.",
            8: "Destiny involves achieving material success and using it to benefit others.",
            9: "Destined to serve humanity and make significant contributions to society.",
            11: "Destiny is to inspire and enlighten others with your spiritual insights.",
            22: "Meant to turn grand visions into tangible reality that benefits many.",
            33: "Destiny is to teach and uplift humanity through compassionate service.",
        }

        soul_urge_meanings = {
            1: "Deep desire for independence, leadership, and individual achievement.",
            2: "Inner need for harmony, partnership, and peaceful relationships.",
            3: "Soul craves creative expression, joy, and social interaction.",
            4: "Inner desire for stability, order, and building something lasting.",
            5: "Soul seeks freedom, adventure, and variety in life experiences.",
            6: "Deep need to nurture, serve, and create harmony for others.",
            7: "Inner desire for knowledge, spirituality, and understanding life's mysteries.",
            8: "Soul craves success, power, and material achievement.",
            9: "Deep desire to serve humanity and make a positive difference.",
            11: "Soul seeks spiritual enlightenment and inspiring others.",
            22: "Inner need to build something grand that benefits humanity.",
            33: "Deep desire to teach and heal through compassionate service.",
        }

        personality_meanings = {
            1: "Appear confident, independent, and strong-willed to others.",
            2: "Come across as gentle, diplomatic, and approachable.",
            3: "Appear creative, charming, and socially engaging.",
            4: "Come across as practical, reliable, and hardworking.",
            5: "Appear adventurous, energetic, and freedom-loving.",
            6: "Come across as caring, responsible, and harmonious.",
            7: "Appear mysterious, introspective, and intellectual.",
            8: "Come across as powerful, ambitious, and authoritative.",
            9: "Appear compassionate, generous, and idealistic.",
            11: "Come across as inspiring, intuitive, and enlightened.",
            22: "Appear as a visionary builder with grand plans.",
            33: "Come across as a compassionate teacher and healer.",
        }

        # 1. Calculate Life Path Number
        reduced_day = reduce_to_single_digit(day)
        reduced_month = reduce_to_single_digit(month)
        reduced_year = reduce_to_single_digit(year)
        life_path_number = reduce_to_single_digit(reduced_day + reduced_month + reduced_year)

        # 2. Calculate Destiny Number (from full name)
        name_value = get_name_value(req.name)
        destiny_number = reduce_to_single_digit(name_value)

        # 3. Calculate Soul Urge Number (from vowels in name)
        vowels = 'aeiou'
        vowel_value = sum(
            get_letter_value(char)
            for char in req.name.lower()
            if char in vowels
        )
        soul_urge_number = reduce_to_single_digit(vowel_value)

        # 4. Calculate Personality Number (from consonants in name)
        consonant_value = sum(
            get_letter_value(char)
            for char in req.name.lower()
            if char.isalpha() and char not in vowels
        )
        personality_number = reduce_to_single_digit(consonant_value)

        # 5. Calculate Lucky Numbers
        lucky_numbers = list(set([
            life_path_number,
            reduce_to_single_digit(day),
            reduce_to_single_digit(month),
            reduce_to_single_digit(day + month),
            reduce_to_single_digit(life_path_number * 2) if reduce_to_single_digit(life_path_number * 2) <= 9 else reduce_to_single_digit(life_path_number + 1)
        ]))
        lucky_numbers.sort()

        return {
            "success": True,
            "name": req.name,
            "birth_info": {
                "date_of_birth": req.date_of_birth,
            },
            "numerology": {
                "life_path_number": {
                    "number": life_path_number,
                    "meaning": life_path_meanings.get(life_path_number, "Unique path with special significance."),
                    "calculation": f"{day} + {month} + {year} = {reduced_day} + {reduced_month} + {reduced_year} = {life_path_number}"
                },
                "destiny_number": {
                    "number": destiny_number,
                    "meaning": destiny_meanings.get(destiny_number, "You have a unique destiny path."),
                    "calculation": f"Name value: {name_value} → {destiny_number}"
                },
                "soul_urge_number": {
                    "number": soul_urge_number,
                    "meaning": soul_urge_meanings.get(soul_urge_number, "Unique inner desires."),
                    "calculation": f"Vowel value: {vowel_value} → {soul_urge_number}"
                },
                "personality_number": {
                    "number": personality_number,
                    "meaning": personality_meanings.get(personality_number, "Unique outer personality."),
                    "calculation": f"Consonant value: {consonant_value} → {personality_number}"
                },
                "lucky_numbers": lucky_numbers,
                "master_number": life_path_number in [11, 22, 33] or destiny_number in [11, 22, 33]
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error calculating Numerology: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Numerology: {str(e)}")
