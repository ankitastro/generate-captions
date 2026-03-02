"""
Constants shared across API modules
"""

# Zodiac sign names
SIGN_NAMES = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# Varga chart divisions (degree divisions for each varga)
VARGA_DIVISIONS = {
    "D2": "15°00'", "D3": "10°00'", "D4": "7°30'", "D7": "4°17'",
    "D9": "3°20'", "D10": "3°00'", "D12": "2°30'", "D16": "1°52'",
    "D20": "1°30'", "D24": "1°15'", "D27": "1°07'", "D30": "1°00'",
    "D40": "0°45'", "D45": "0°40'", "D60": "0°30'"
}

# Major vargas for calculation
MAJOR_VARGAS = [2, 3, 4, 7, 9, 10, 12, 16, 20, 24]
ADDITIONAL_VARGAS = [27, 30, 40, 45, 60]
ALL_VARGAS = MAJOR_VARGAS + ADDITIONAL_VARGAS

# Rashi (Moon Sign) details
RASHI_DETAILS = {
    'Aries': {'sanskrit': 'Mesha', 'lord': 'Mars (Mangal)', 'element': 'Fire', 'quality': 'Movable', 'lucky_gem': 'Red Coral'},
    'Taurus': {'sanskrit': 'Vrishabha', 'lord': 'Venus (Shukra)', 'element': 'Earth', 'quality': 'Fixed', 'lucky_gem': 'Diamond'},
    'Gemini': {'sanskrit': 'Mithuna', 'lord': 'Mercury (Budh)', 'element': 'Air', 'quality': 'Dual', 'lucky_gem': 'Emerald'},
    'Cancer': {'sanskrit': 'Karka', 'lord': 'Moon (Chandra)', 'element': 'Water', 'quality': 'Movable', 'lucky_gem': 'Pearl'},
    'Leo': {'sanskrit': 'Simha', 'lord': 'Sun (Surya)', 'element': 'Fire', 'quality': 'Fixed', 'lucky_gem': 'Ruby'},
    'Virgo': {'sanskrit': 'Kanya', 'lord': 'Mercury (Budh)', 'element': 'Earth', 'quality': 'Dual', 'lucky_gem': 'Emerald'},
    'Libra': {'sanskrit': 'Tula', 'lord': 'Venus (Shukra)', 'element': 'Air', 'quality': 'Movable', 'lucky_gem': 'Diamond'},
    'Scorpio': {'sanskrit': 'Vrishchika', 'lord': 'Mars (Mangal)', 'element': 'Water', 'quality': 'Fixed', 'lucky_gem': 'Red Coral'},
    'Sagittarius': {'sanskrit': 'Dhanu', 'lord': 'Jupiter (Guru)', 'element': 'Fire', 'quality': 'Dual', 'lucky_gem': 'Yellow Sapphire'},
    'Capricorn': {'sanskrit': 'Makara', 'lord': 'Saturn (Shani)', 'element': 'Earth', 'quality': 'Movable', 'lucky_gem': 'Blue Sapphire'},
    'Aquarius': {'sanskrit': 'Kumbha', 'lord': 'Saturn (Shani)', 'element': 'Air', 'quality': 'Fixed', 'lucky_gem': 'Blue Sapphire'},
    'Pisces': {'sanskrit': 'Meena', 'lord': 'Jupiter (Guru)', 'element': 'Water', 'quality': 'Dual', 'lucky_gem': 'Yellow Sapphire'},
}

# Sun sign details with traits
SUN_SIGN_DETAILS = {
    'Aries': {
        'symbol': '♈', 'element': 'Fire', 'quality': 'Cardinal', 'ruling_planet': 'Mars',
        'lucky_color': 'Red', 'lucky_number': 9,
        'traits': ['Courageous', 'Passionate', 'Confident', 'Direct', 'Independent']
    },
    'Taurus': {
        'symbol': '♉', 'element': 'Earth', 'quality': 'Fixed', 'ruling_planet': 'Venus',
        'lucky_color': 'Green', 'lucky_number': 6,
        'traits': ['Practical', 'Loyal', 'Sensual', 'Determined', 'Stable']
    },
    'Gemini': {
        'symbol': '♊', 'element': 'Air', 'quality': 'Mutable', 'ruling_planet': 'Mercury',
        'lucky_color': 'Yellow', 'lucky_number': 5,
        'traits': ['Versatile', 'Witty', 'Social', 'Quick-thinking', 'Expressive']
    },
    'Cancer': {
        'symbol': '♋', 'element': 'Water', 'quality': 'Cardinal', 'ruling_planet': 'Moon',
        'lucky_color': 'Silver', 'lucky_number': 2,
        'traits': ['Caring', 'Protective', 'Emotional', 'Intuitive', 'Loyal']
    },
    'Leo': {
        'symbol': '♌', 'element': 'Fire', 'quality': 'Fixed', 'ruling_planet': 'Sun',
        'lucky_color': 'Gold', 'lucky_number': 1,
        'traits': ['Creative', 'Passionate', 'Generous', 'Warm-hearted', 'Cheerful']
    },
    'Virgo': {
        'symbol': '♍', 'element': 'Earth', 'quality': 'Mutable', 'ruling_planet': 'Mercury',
        'lucky_color': 'Navy Blue', 'lucky_number': 5,
        'traits': ['Detail-oriented', 'Practical', 'Hardworking', 'Reliable', 'Kind']
    },
    'Libra': {
        'symbol': '♎', 'element': 'Air', 'quality': 'Cardinal', 'ruling_planet': 'Venus',
        'lucky_color': 'Pink', 'lucky_number': 6,
        'traits': ['Balanced', 'Diplomatic', 'Social', 'Fair-minded', 'Gracious']
    },
    'Scorpio': {
        'symbol': '♏', 'element': 'Water', 'quality': 'Fixed', 'ruling_planet': 'Mars/Pluto',
        'lucky_color': 'Maroon', 'lucky_number': 9,
        'traits': ['Passionate', 'Brave', 'Resourceful', 'Stubborn', 'Loyal']
    },
    'Sagittarius': {
        'symbol': '♐', 'element': 'Fire', 'quality': 'Mutable', 'ruling_planet': 'Jupiter',
        'lucky_color': 'Purple', 'lucky_number': 3,
        'traits': ['Adventurous', 'Optimistic', 'Honest', 'Independent', 'Philosophical']
    },
    'Capricorn': {
        'symbol': '♑', 'element': 'Earth', 'quality': 'Cardinal', 'ruling_planet': 'Saturn',
        'lucky_color': 'Brown', 'lucky_number': 8,
        'traits': ['Responsible', 'Disciplined', 'Self-controlled', 'Ambitious', 'Patient']
    },
    'Aquarius': {
        'symbol': '♒', 'element': 'Air', 'quality': 'Fixed', 'ruling_planet': 'Saturn/Uranus',
        'lucky_color': 'Electric Blue', 'lucky_number': 4,
        'traits': ['Independent', 'Progressive', 'Original', 'Humanitarian', 'Intellectual']
    },
    'Pisces': {
        'symbol': '♓', 'element': 'Water', 'quality': 'Mutable', 'ruling_planet': 'Jupiter/Neptune',
        'lucky_color': 'Sea Green', 'lucky_number': 7,
        'traits': ['Compassionate', 'Artistic', 'Intuitive', 'Gentle', 'Wise']
    },
}
