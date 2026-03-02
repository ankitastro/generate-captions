import random
import sys
import os
from horoscope.planetary_horoscope_engine import PlanetaryHoroscopeEngine

# Add the parent directory to the path to import translation manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from translation_manager import get_translation_manager

# --- DATA INTEGRATION (Copy-pasted and expanded) ---

# Data from zodiac_traits.py (Using "Rashi" section for daily Moon mood)
ZODIAC_TRAITS = {
    "Aries": {"Rashi": "Today's emotional landscape is fiery and immediate. You and others may feel an impulsive urge to act, with feelings flaring up and fading just as fast. The mood supports bold, direct action and defending what you believe in."},
    "Taurus": {"Rashi": "A desire for emotional security and stability grounds the day. The collective mood is calm and steady, drawn to familiar comforts and predictable routines. It's a time to be a rock for others and nurture through patience."},
    "Gemini": {"Rashi": "Curiosity and adaptability color the emotional world today. Feelings are processed through conversation and intellectual analysis. The mood is light, witty, and sociable, perfect for talking things out and keeping spirits lifted."},
    "Cancer": {"Rashi": "Emotions run deep and intuitive today. The collective is highly sensitive and caring, with a focus on the safety of home and family. It's a day for heartfelt nurturing and trusting your gut feelings."},
    "Leo": {"Rashi": "The emotional world is filled with warmth, drama, and a need for appreciation. Feelings are expressed in a grand, expressive way. The mood is celebratory, encouraging everyone to wear their heart on their sleeve."},
    "Virgo": {"Rashi": "A practical, thoughtful, and analytical mood prevails. Emotions are processed with a desire for perfection and order. It's a day for being helpful, reliable, and finding solutions to nagging problems."},
    "Libra": {"Rashi": "The collective emotional world seeks balance, harmony, and partnership. The mood is diplomatic and fair, making it a perfect time to smooth out conflicts and create pleasant, supportive environments."},
    "Scorpio": {"Rashi": "Emotions are intense, private, and passionate today. There is a desire to look beneath the surface and connect on a profound level. The mood supports transformation and unwavering loyalty."},
    "Sagittarius": {"Rashi": "An upbeat, adventurous, and straightforward emotional mood takes over. The collective feeling is optimistic and honest, steering clear of negativity. It's a day that encourages humor, wisdom, and a fresh perspective."},
    "Capricorn": {"Rashi": "Emotions are reserved, responsible, and steadfast. The mood is to control feelings and focus on duties and practical solutions. It's a time for dependability and commitment."},
    "Aquarius": {"Rashi": "Today's emotional nature is intellectual, independent, and humanitarian. Feelings are approached from a logical, big-picture perspective. The mood encourages fairness, innovation, and giving others the freedom to be themselves."},
    "Pisces": {"Rashi": "A deeply empathetic, imaginative, and gentle emotional mood defines the day. The collective is highly intuitive, absorbing the feelings of the surroundings. It's a time for art, kindness, and spiritual connection."}
}

# New data to make the overview dynamic for each sign
CORE_DESCRIPTIONS = {
    "Aries": "your impulsive and courageous nature sets you apart. Your strength lies in your ability to initiate and act.",
    "Taurus": "your grounded and patient spirit guides you. You excel at building a stable foundation.",
    "Gemini": "your curious and adaptable mind is your greatest asset. You thrive on communication and variety.",
    "Cancer": "your intuitive and nurturing personality is your greatest strength. You lead with empathy and emotional intelligence.",
    "Leo": "your radiant and confident spirit makes you a natural star. You are meant to inspire and lead others with your bold presence.",
    "Virgo": "your analytical and practical mind is your greatest tool. Your attention to detail and desire to be of service will guide you.",
    "Libra": "your diplomatic and charming nature is your key to success. You thrive in partnerships and seek harmony in all your interactions.",
    "Scorpio": "your intense and passionate drive is your core strength. You are a master of transformation and can delve deep beneath the surface.",
    "Sagittarius": "your adventurous and optimistic outlook on life is your guiding light. Your quest for knowledge and freedom will lead you to new horizons.",
    "Capricorn": "your disciplined and ambitious nature is your greatest asset. You are built for long-term success and respect the power of hard work.",
    "Aquarius": "your innovative and humanitarian spirit makes you a visionary. Your independent thinking and focus on the collective good will set you apart.",
    "Pisces": "your empathetic and imaginative soul is your greatest gift. You are deeply intuitive and navigate the world with a compassionate and creative spirit."
}

# Hindi Data for Zodiac Traits
ZODIAC_TRAITS_HI = {
    "Aries": {"Rashi": "आज का भावनात्मक दृश्य उग्र और तत्काल है। आप और दूसरे कार्य करने की आवेगपूर्ण इच्छा महसूस कर सकते हैं, भावनाएं तेजी से भड़क उठती हैं और उतनी ही तेजी से शांत हो जाती हैं। मूड साहसी, सीधी कार्रवाई और अपनी मान्यताओं की रक्षा का समर्थन करता है।"},
    "Taurus": {"Rashi": "भावनात्मक सुरक्षा और स्थिरता की इच्छा दिन को आधार प्रदान करती है। सामूहिक मूड शांत और स्थिर है, परिचित सुखों और पूर्वानुमेय दिनचर्या की ओर आकर्षित होता है। यह दूसरों के लिए एक चट्टान बनने और धैर्य के माध्यम से पालन-पोषण करने का समय है।"},
    "Gemini": {"Rashi": "जिज्ञासा और अनुकूलनशीलता आज के भावनात्मक संसार को रंग देती है। भावनाओं का संचार और बौद्धिक विश्लेषण के माध्यम से संसाधित होती हैं। मूड हल्का, मजाकिया और सामाजिक है, बातें निकालने और उत्साह को बनाए रखने के लिए आदर्श है।"},
    "Cancer": {"Rashi": "भावनाएं गहरी और अंतर्ज्ञानवान होती हैं। समूह अत्यधिक संवेदनशील और देखभाल करने वाला है, घर और परिवार की सुरक्षा पर ध्यान केंद्रित करता है। यह दिल से पालन-पोषण करने और अपनी अंतःप्रवृत्ति पर विश्वास करने के लिए है।"},
    "Leo": {"Rashi": "भावनात्मक संसार गर्मजोशी, नाटक और प्रशंसा की इच्छा से भरा है। भावनाएं भव्य, व्यक्त व्यक्तिगत रूप में व्यक्त होती हैं। मूड उत्सवी है, हर किसी को अपना दिल अपनी बांहों पर रखने के लिए प्रोत्साहित करता है।"},
    "Virgo": {"Rashi": "एक व्यावहारिक, विचारशील और विश्लेषणात्मक मूड प्रचलित है। भावनाओं को पूर्णता और व्यवस्था की इच्छा के साथ संसाधित किया जाता है। यह सहायक, विश्वसनीय होने और परेशान करने वाली समस्याओं के समाधान खोजने का दिन है।"},
    "Libra": {"Rashi": "सामूहिक भावनात्मक संसार संतुलन, सामंजस्य और साझेदारी की तलाश करता है। मूड कूटनीतिज्ञ और निष्पक्ष है, संघर्षों को दूर करने और सुखद, सहायक वातावरण बनाने के लिए एक आदर्श समय है।"},
    "Scorpio": {"Rashi": "भावनाएं तीव्र, निजी और जुनूनी होती हैं। सतह के नीचे देखने और एक गहरे स्तर पर जुड़ने की इच्छा होती है। मूड रूपांतरण और अटल निष्ठा का समर्थन करता है।"},
    "Sagittarius": {"Rashi": "एक उत्साही, साहसी और सीधी भावनात्मक मूड संभालता है। सामूहिक भावना आशावादी और ईमानदार है, नकारात्मकता से दूर रहती है। यह दिन हास्य, ज्ञान और एक नए दृष्टिकोण को प्रोत्साहित करता है।"},
    "Capricorn": {"Rashi": "भावनाएं आरक्षित, जिम्मेदार और अडिग होती हैं। मूड भावनाओं को नियंत्रित करना और कर्तव्यों और व्यावहारिक समाधानों पर ध्यान केंद्रित करना है। यह भरोसेमंदता और प्रतिबद्धता का समय है।"},
    "Aquarius": {"Rashi": "आज की भावनात्मक प्रकृति बौद्धिक, स्वतंत्र और मानवतावादी है। भावनाओं को तार्किक, व्यापक दृष्टिकोण से देखा जाता है। मूड निष्पक्षता, नवाचार और दूसरों को खुद बनने की स्वतंत्रता देने को प्रोत्साहित करता है।"},
    "Pisces": {"Rashi": "एक गहरी सहानुभूति, कल्पनाशील और कोमल भावनात्मक मूड दिन को परिभाषित करता है। समूह अत्यधिक अंतर्ज्ञानवान है, आसपास की भावनाओं को अवशोषित करता है। यह कला, दयालुता और आध्यात्मिक संबंध का समय है।"}
}

# Hindi Core Descriptions
CORE_DESCRIPTIONS_HI = {
    "Aries": "आपकी आवेगपूर्ण और साहसी प्रकृति आपको अलग करती है। आपकी ताकत शुरू करने और कार्य करने की आपकी क्षमता में है।",
    "Taurus": "आपकी स्थिर और धैर्यवान आत्मा आपका मार्गदर्शन करती है। आप एक स्थिर नींव बनाने में उत्कृष्ट हैं।",
    "Gemini": "आपकी जिज्ञासु और अनुकूल दिमाग आपकी सबसे बड़ी संपत्ति है। आप संचार और विविधता पर फलते-फूलते हैं।",
    "Cancer": "आपकी अंतर्ज्ञानवान और पालन करने वाली व्यक्तित्व आपकी सबसे बड़ी शक्ति है। आप सहानुभूति और भावनात्मक बुद्धिमत्ता के साथ नेतृत्व करते हैं।",
    "Leo": "आपकी कांतिमान और आत्मविश्वासी आत्मा आपको एक प्राकृतिक सितारा बनाती है। आप अपनी साहसी उपस्थिति के साथ दूसरों को प्रेरित और नेतृत्व करने के लिए बने हैं।",
    "Virgo": "आपका विश्लेषणात्मक और व्यावहारिक दिमाग आपका सबसे बड़ा उपकरण है। विवरण पर ध्यान और सेवा करने की इच्छा आपका मार्गदर्शन करेगी।",
    "Libra": "आपकी कूटनीतिज्ञ और मोहक प्रकृति आपकी सफलता की कुंजी है। आप साझेदारी में फलते-फूलते हैं और अपने सभी अंतःक्रियाओं में सामंजस्य की तलाश करते हैं।",
    "Scorpio": "आपकी तीव्र और जुनूनी गतिशीलता आपकी मूल शक्ति है। आप रूपांतरण के मास्टर हैं और सतह के नीचे गहराई से जा सकते हैं।",
    "Sagittarius": "जीवन पर आपका साहसी और आशावादी दृष्टिकोण आपका मार्गदर्शक प्रकाश है। ज्ञान और स्वतंत्रता की आपकी खोज आपको नए क्षितिजों तक ले जाएगी।",
    "Capricorn": "आपकी अनुशासित और महत्वाकांक्षी प्रकृति आपकी सबसे बड़ी संपत्ति है। आप दीर्घकालिक सफलता के लिए बने हैं और कड़ी मेहनत की शक्ति का सम्मान करते हैं।",
    "Aquarius": "आपकी नवाचारी और मानवतावादी आत्मा आपको एक द्रष्टा बनाती है। आपकी स्वतंत्र सोच और सामूहिक भलाई पर ध्यान आपको अलग सेट करेगा।",
    "Pisces": "आपकी सहानुभूति और कल्पनाशील आत्मा आपका सबसे बड़ा उपहार है। आप गहरे से अंतर्ज्ञानवान हैं और दयालु और रचनात्मक आत्मा के साथ दुनिया में नेविगेट करते हैं।"
}

# New data for Career Traits
CAREER_TRAITS = {
    "Aries": {
        "positive": ["Natural leader", "initiates projects", "thrives under pressure", "competitive drive", "entrepreneurial spirit", "quick decision-maker", "pioneering in new fields"],
        "negative": ["Impatient with details", "abandons projects mid-way", "conflicts with authority", "impulsive decisions", "difficulty with routine tasks", "can be overly aggressive in workplace dynamics"]
    },
    "Taurus": {
        "positive": ["Reliable and consistent worker", "excellent with finances", "patient with long-term projects", "strong work ethic", "practical problem-solver", "creates stable work environments"],
        "negative": ["Resistant to change", "stubborn about new methods", "slow to adapt to technology", "possessive of roles/territories", "can become complacent", "difficulty with fast-paced environments"]
    },
    "Gemini": {
        "positive": ["Excellent communicator", "adaptable to various roles", "quick learner", "networking skills", "multitasking ability", "brings fresh ideas and perspectives"],
        "negative": ["Difficulty focusing on single tasks", "inconsistent performance", "gets bored easily", "may spread themselves too thin", "struggles with routine work", "can be unreliable with follow-through"]
    },
    "Cancer": {
        "positive": ["Intuitive about people's needs", "nurturing team member", "loyal employee", "excellent memory for details", "protective of company interests", "emotionally intelligent"],
        "negative": ["Takes criticism personally", "mood swings affect performance", "overly cautious with risks", "can be manipulative", "difficulty separating personal and professional", "resistant to workplace changes"]
    },
    "Leo": {
        "positive": ["Natural performer and presenter", "inspiring leader", "creative problem-solver", "generous mentor", "builds team morale", "confident in high-pressure situations"],
        "negative": ["Needs constant recognition", "struggles in subordinate roles", "can be arrogant", "difficulty sharing spotlight", "takes credit for others' work", "dramatic reactions to setbacks"]
    },
    "Virgo": {
        "positive": ["Exceptional attention to detail", "analytical skills", "reliable and punctual", "continuous improvement mindset", "excellent organizational abilities", "service-oriented approach"],
        "negative": ["Perfectionist tendencies slow progress", "overly critical of colleagues", "micromanages others", "difficulty delegating", "gets overwhelmed by big-picture thinking", "can be pessimistic"]
    },
    "Libra": {
        "positive": ["Excellent mediator and diplomat", "team player", "aesthetic sense valuable in design fields", "fair and balanced decision-maker", "charming with clients and colleagues"],
        "negative": ["Indecisive under pressure", "avoids confrontation", "people-pleasing compromises standards", "difficulty working alone", "procrastinates on difficult decisions", "superficial approach to deep issues"]
    },
    "Scorpio": {
        "positive": ["Intense focus and determination", "excellent researcher and investigator", "strategic thinking", "loyal once committed", "transformative leadership", "handles crisis situations well"],
        "negative": ["Secretive and suspicious of colleagues", "holds grudges", "manipulative tactics", "all-or-nothing approach", "difficulty trusting team members", "can be vindictive when crossed"]
    },
    "Sagittarius": {
        "positive": ["Visionary thinking", "inspiring teacher and mentor", "adaptable to international work", "optimistic attitude motivates others", "philosophical approach to problems", "entrepreneurial spirit"],
        "negative": ["Poor attention to detail", "overcommits to projects", "difficulty with routine tasks", "tactless communication", "restless in stable positions", "promises more than can deliver"]
    },
    "Capricorn": {
        "positive": ["Natural executive abilities", "long-term strategic planning", "disciplined work ethic", "respects hierarchy and tradition", "reliable in leadership roles", "builds lasting professional relationships"],
        "negative": ["Workaholic tendencies", "overly status-conscious", "rigid about rules and procedures", "pessimistic outlook", "difficulty with creative/innovative approaches", "can be ruthlessly ambitious"]
    },
    "Aquarius": {
        "positive": ["Innovative problem-solver", "excellent with technology", "values teamwork and collaboration", "progressive ideas benefit organizations", "humanitarian approach to business", "independent worker"],
        "negative": ["Rebels against authority", "difficulty with traditional corporate structure", "can be emotionally detached from colleagues", "unpredictable work patterns", "stubborn about unconventional methods"]
    },
    "Pisces": {
        "positive": ["Highly creative and imaginative", "empathetic with clients and colleagues", "intuitive understanding of market trends", "adaptable and flexible", "inspiring artistic vision", "compassionate leadership"],
        "negative": ["Poor boundaries with time and energy", "difficulty with practical details", "tends to procrastinate", "easily overwhelmed by stress", "may escape into fantasy when facing pressure", "inconsistent performance"]
    }
}


# Data from sign_houses.py
HOUSE_SIGN_INTERPRETATIONS = {
    1: {"Leo": "You are powerful, valiant, and possess distinctive features like reddish eyes and a broad face. Your firm-minded nature helps you take charge and lead confidently. However, you may be prone to arrogance and quick anger over small issues, and your tendency to roam without clear direction might sometimes work against you."},
    2: {"Virgo": "When Virgo occupies your second house, you apply a methodical, analytical approach to money and possessions. You are diligent, detail-oriented, and good at budgeting, ensuring that your wealth is steadily accumulated. On the flip side, you may become overly critical or anxious about minor financial details, sometimes missing out on larger opportunities due to excessive caution."},
    3: {"Libra": "If Libra rules your third house, you strive for balance and harmony in your communications and relationships with siblings. You are diplomatic and charming, ensuring fairness in your exchanges. However, your desire to avoid conflict may lead to indecision or superficial agreements that leave underlying issues unresolved."},
    4: {"Scorpio": "When Scorpio occupies your fourth house, you bring intensity and transformative energy to your home. Positively, you create a deeply emotional and passionate domestic space that can lead to profound personal growth. Negatively, your secretiveness and controlling tendencies may spark power struggles or emotional turbulence within your household."},
    5: {"Sagittarius": "With Sagittarius in your fifth house, you embrace creativity and romance with optimism and a sense of adventure. Positively, you are open-minded, enthusiastic, and eager to explore new ideas in art and love. Negatively, your bluntness or restlessness might result in inconsistency or a lack of commitment, affecting both creative projects and relationships."},
    6: {"Capricorn": "If Capricorn occupies your sixth house, you handle work and health matters with discipline, structure, and long-term planning. Positively, you build sustainable routines and steadily overcome challenges with persistence. Negatively, your rigidity and focus on duty can lead to overwork and stress, while your reluctance to adapt may prevent you from seizing more efficient solutions."},
    7: {"Aquarius": "When Aquarius rules your seventh house, you attract unconventional, innovative, and freedom-loving partners. Positively, you enjoy relationships that are intellectually stimulating and forward-thinking. Negatively, your need for independence and occasional detachment may create challenges in forming intimate or consistent bonds."},
    8: {"Pisces": "With Pisces in your eighth house, you experience transformation and the mysteries of shared resources with sensitivity and deep intuition. Positively, you are empathetic and imaginative, often finding spiritual meaning in periods of change and crisis. Negatively, your tendency toward escapism and idealism can leave you vulnerable to deception or loss, making it challenging to maintain a stable footing in intimate or financial matters."},
    9: {"Aries": "When Aries occupies your ninth house, you approach higher learning and spiritual quests with bold enthusiasm. Positively, you pioneer new ideas and are fearless in exploring diverse philosophies. Negatively, your impulsive nature may cause you to be intolerant of differing opinions, leading to dogmatism or rash decisions in your pursuit of truth."},
    10: {"Taurus": "When Taurus is in your tenth house, you approach your career with persistence, practicality, and a desire for stability. Positively, you build a solid professional foundation through steady effort and reliable determination. Negatively, you may become overly cautious or resistant to change, which might slow your progress or cause you to miss innovative opportunities."},
    11: {"Gemini": "When Gemini occupies your eleventh house, you infuse your social life and future plans with versatility and charm. Positively, you excel at networking and communicating ideas, opening diverse avenues for success. Negatively, your scattered focus and inconsistency may lead to superficial connections and erratic outcomes."},
    12: {"Cancer": "If Cancer occupies your twelfth house, you experience a rich, emotionally intuitive inner life. Positively, you create a compassionate, healing space that nurtures your soul. Negatively, your sensitivity may cause you to retreat into moodiness or cling to past hurts, sometimes leading to self-imposed isolation that hampers growth."}
}

# Simplified Planet Personality data for our engine
PLANET_PERSONALITY = {
    "Sun": {"positive_traits": "Represents the self, authority, and vitality. When strong, it gives confidence, loyalty, nobility and leadership ability."},
    "Moon": {"positive_traits": "Symbolizes the mind and emotions. A strong Moon brings emotional stability, empathy and kindness."},
    "Mars": {"positive_traits": "Signifies energy, drive and courage. When benefic, it gives abundant stamina, confidence and initiative."},
    "Mercury": {"positive_traits": "The planet of intellect and communication. A strong Mercury endows one with sharp intelligence, quick learning ability, and eloquent speech."},
    "Jupiter": {"positive_traits": "Represents expansion, wisdom, and optimism. A strong Jupiter brings generosity, moral integrity, faith, and good fortune."},
    "Venus": {"positive_traits": "Governs love, beauty, and harmony. A strong Venus gives charm, creativity in arts, and the ability to form loving relationships."},
    "Saturn": {"positive_traits": "The taskmaster that imparts discipline, patience, and perseverance. When favorable, it makes a person hardworking and responsible."}
}

# Static data for the engine
ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
RULING_PLANETS = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"}
REMEDY_COLORS = {"Sun": "gold or bright yellow", "Moon": "white or silver", "Mars": "red", "Mercury": "green", "Jupiter": "yellow", "Venus": "pink or white", "Saturn": "dark blue or black"}

VEDIC_MANTRAS = {
    "Sun": {"deity": "Surya", "mantra": "Om Suryaya Namah"},
    "Moon": {"deity": "Chandra", "mantra": "Om Chandraya Namah"},
    "Mars": {"deity": "Mangala", "mantra": "Om Angarakaya Namah"},
    "Mercury": {"deity": "Budha", "mantra": "Om Budhaya Namah"},
    "Jupiter": {"deity": "Brihaspati (Guru)", "mantra": "Om Gurave Namah"},
    "Venus": {"deity": "Shukra", "mantra": "Om Shukraya Namah"},
    "Saturn": {"deity": "Shani", "mantra": "Om Shanaye Namah"},
}
# --- HELPER FUNCTIONS ---

def get_house_for_sign(planet_sign: str, user_sign: str) -> int:
    """Calculates the house a planet is in for a given user's sign using the Whole Sign system."""
    try:
        planet_idx = ZODIAC_SIGNS.index(planet_sign)
        user_idx = ZODIAC_SIGNS.index(user_sign)
        return ((planet_idx - user_idx) % 12) + 1
    except (ValueError, IndexError):
        return 1

def find_aspects_for_planet(planet_name: str, aspects: list) -> list:
    """Filters and returns all aspects involving a specific planet."""
    return [asp for asp in aspects if asp.get("planet1") == planet_name or asp.get("planet2") == planet_name]

def interpret_aspects(astro_data: dict, planet: str) -> str:
    """A new helper function to interpret aspects for dynamic narratives."""
    aspect_parts = []
    for aspect in find_aspects_for_planet(planet, astro_data['planetary_data']['aspects']):
        other_planet = aspect['planet2'] if aspect['planet1'] == planet else aspect['planet1']
        aspect_name = aspect['aspect']

        if aspect_name == 'trine' and other_planet == 'Saturn':
            aspect_parts.append("A stable and grounding energy helps you build lasting bonds.")
        elif aspect_name == 'sextile' and other_planet == 'Uranus':
            aspect_parts.append("A delightful surprise or an unexpected encounter could add a wonderful spark to your day.")
    return " ".join(aspect_parts)

# --- V3 INTERPRETATION FUNCTIONS (with "narrative" and "reason") ---

def interpret_overview(sign: str, language: str = 'en') -> dict:
    translation_manager = get_translation_manager()

    # Get translations for planets
    if language == 'hi':
        ruler = translation_manager.translate(f'planets.{RULING_PLANETS.get(sign, "Sun")}', language)
        core_description = CORE_DESCRIPTIONS_HI.get(sign, CORE_DESCRIPTIONS.get(sign))
        reason = "यह अवलोकन आपके राशि चिह्न और उसके शासक ग्रह के मूल आर्किटाइपल स्वभाव पर आधारित है, जो आपके मौलिक व्यक्तित्व और जीवन के दृष्टिकोण को परिभाषित करता है।"
    else:
        ruler = RULING_PLANETS.get(sign, "a unique cosmic force")
        core_description = CORE_DESCRIPTIONS.get(sign, "your unique cosmic force will guide you.")
        reason = "This overview is based on the core archetypal nature of your zodiac sign and its ruling planet, which defines your fundamental personality and approach to life. The career traits are derived from classic astrological interpretations of your sign's professional strengths and weaknesses."

    # Get career traits from the data structure
    traits = CAREER_TRAITS.get(sign, {"positive": [], "negative": []})
    positive_traits = ", ".join(traits["positive"])
    negative_traits = ", ".join(traits["negative"])

    if language == 'hi':
        narrative = (
            f"{sign}, शक्तिशाली ग्रह {ruler} द्वारा शासित, {core_description} "
            f"आज आगे बढ़ने के लिए अपने जन्मजात आत्मविश्वास का लाभ उठाएं।"
        )
    else:
        narrative = (
            f"{sign}, ruled by the powerful planet {ruler}, {core_description} "
            f"Harness your innate confidence to illuminate your path forward today."
            f"Positive Career Traits: {positive_traits}."
            f"Negative Career Traits: {negative_traits}."
        )

    return {"narrative": narrative, "reason": reason}

def interpret_love(astro_data: dict, sign: str, language: str = 'en') -> dict:
    translation_manager = get_translation_manager()
    positions = astro_data['planetary_data']['positions']
    venus_sign = positions['Venus']['rashi']
    venus_house = get_house_for_sign(venus_sign, sign)

    if language == 'hi':
        love_narrative_template = {
            1: f"आपके प्रथम भाव में शुक्र के साथ, आप करिश्मा और आकर्षण का विकिरण कर रहे हैं और दूसरों को आकर्षित कर रहे हैं। आपकी व्यक्तिगत शैली आकर्षक है, और आप रोमांटिक महसूस कर रहे हैं।",
            2: f"आपके द्वितीय भाव में शुक्र प्रेम के वित्तीय और भौतिक पहलुओं पर ध्यान केंद्रित करता है। रोमांटिक उपहार या साझा व्यय करने के लिए यह एक अच्छा दिन है।",
            3: f"आपके तृतीय भाव में शुक्र आपके रिश्तों में संचार को बढ़ाता है। बातें करने और अपने बंधन को मजबूत करने का यह एक शानदार समय है।",
            4: f"आपके चतुर्थ भाव में शुक्र प्रेम में घर और परिवार पर ध्यान केंद्रित करता है। आप घोंसला बनाने की इच्छा महसूस कर सकते हैं या प्रियजन के साथ एक आरामदायक रात बिता सकते हैं।",
            5: f"आपके पंचम भाव में शुक्र के साथ, प्रेम, रोमांस और रचनात्मक अभिव्यक्ति पर प्रकाश डाला जाता है। आप खिलखिलाते हुए महसूस करते हैं और जीवन के आनंद का आनंद लेने के लिए तैयार हैं।",
            6: f"आपके षष्ठ भाव में शुक्र आपकी दैनिक दिनचर्या और कार्य संबंधों में सामंजस्य लाता है। काम पर या साझा शौक के माध्यम से एक नया कनेक्शन बन सकता है।",
            7: f"आपके सप्तम भाव, साझेदारियों के भाव में शुक्र, आपके एक-से-एक रिश्तों को उजागर करता है। अपने साथी से जुड़ने और सामंजस्य की तलाश करने का यह एक शानदार समय है।",
            8: f"आपके अष्टम भाव में शुक्र आपके भावनात्मक और शारीरिक बंधनों को तीव्र करता है। आप आज एक गहरा, रूपांतरणकारी कनेक्शन का अनुभव कर सकते हैं।",
            9: f"आपके नवम भाव में शुक्र साहस के साथ प्रेम और रिश्तों को प्रोत्साहित करता है। आप यात्रा के दौरान किसी से मिल सकते हैं या एक अलग सांस्कृतिक पृष्ठभूमि वाले साथी की ओर आकर्षित हो सकते हैं।",
            10: f"आपके दशम भाव में शुक्र के साथ, आपका व्यावसायिक जीवन आपके रोमांटिक जीवन के साथ जुड़ सकता है। काम संबंधी कनेक्शन चिंगारी कर सकता है, या एक साथी आपके करियर महत्वाकांक्षाओं का समर्थन कर सकता है।",
            11: f"आपके एकादश भाव में शुक्र आपके सामाजिक चक्र में एक रोमांटिक फोकस लाता है। एक मित्रता रोमांस में विकसित हो सकती है, या आप समूह गतिविधियों के माध्यम से प्रेम पा सकते हैं।",
            12: f"आपके द्वादश भाव में शुक्र आध्यात्मिक या गुप्त रिश्तों पर ध्यान केंद्रित करता है। आप एक गहरा, आत्मीय कनेक्शन महसूस कर सकते हैं जिसमें इसका एक छिपा हुआ आयाम है।"
        }.get(venus_house, "आज रोमांस एक मुख्य विषय है, कनेक्शन और सामंजस्य के अवसरों के साथ।")

        venus_planet = translation_manager.translate('planets.Venus', language)
        reason = f"ऐसा इसलिए है क्योंकि प्रेम और रिश्तों के ग्रह शुक्र, आपके {venus_house}वें भाव में {venus_sign} राशि के माध्यम से संक्रमण कर रहे हैं, जो कनेक्शन के आपके दृष्टिकोण को प्रभावित करता है।"
    else:
        love_narrative_template = {
            1: f"With Venus in your 1st House, you're radiating charm and attracting others. Your personal style is appealing, and you're feeling romantic.",
            2: f"Venus in your 2nd House brings a focus on financial and material aspects of love. It's a good day for a romantic gift or a shared splurge.",
            3: f"Venus in your 3rd House enhances communication in your relationships. It's a great time to talk things out and strengthen your bond.",
            4: f"Venus in your 4th House brings a focus on home and family in love. You may feel a desire to nest or spend a cozy night in with a loved one.",
            5: f"With Venus in your 5th House, love, romance, and creative expression are highlighted. You feel playful and are ready to enjoy life's pleasures.",
            6: f"Venus in your 6th House brings harmony to your daily routines and work relationships. A new connection could form at work or through a shared hobby.",
            7: f"Venus in your 7th House, the house of partnerships, highlights your one-on-one relationships. This is a great time to connect with your partner and seek harmony.",
            8: f"Venus in your 8th House intensifies your emotional and physical bonds. You may experience a deep, transformative connection today.",
            9: f"Venus in your 9th House encourages love and relationships with a sense of adventure. You might meet someone while traveling or be drawn to a partner with a different cultural background.",
            10: f"With Venus in your 10th House, your professional life may intertwine with your romantic life. A work-related connection could spark, or a partner could support your career ambitions.",
            11: f"Venus in your 11th House brings a romantic focus to your social circle. A friendship could evolve into a romance, or you might find love through group activities.",
            12: f"Venus in your 12th House brings a focus on spiritual or secret relationships. You may feel a deep, soulful connection with a hidden dimension to it."
        }.get(venus_house, "Romance is a key theme today, with opportunities for connection and harmony.")

        reason = f"This is because Venus, the planet of love and relationships, is transiting your {venus_house}th House in the sign of {venus_sign}, influencing your approach to connection."

    narrative = f"{love_narrative_template} {interpret_aspects(astro_data, 'Venus')}"

    return {"narrative": narrative, "reason": reason}

def interpret_career(astro_data: dict, sign: str, language: str = 'en') -> dict:
    translation_manager = get_translation_manager()
    positions = astro_data['planetary_data']['positions']
    sun_sign = positions['Sun']['rashi']
    sun_house = get_house_for_sign(sun_sign, sign)

    if language == 'hi':
        career_narrative_template = {
            1: "आपके प्रथम भाव में सूर्य के साथ, आप चर्चा का केंद्र हैं। आपका नेतृत्व और व्यक्तिगत पहल पूरी तरह से प्रदर्शित हो रही है।",
            2: "आपके द्वितीय भाव में सूर्य आपकी वित्तीय स्थिरता और मूल्यों पर ध्यान केंद्रित करता है। अपनी कुल संपत्ति बनाने वाले प्रोजेक्ट्स पर काम करने का यह एक शानदार समय है।",
            3: "आपके तृतीय भाव में सूर्य करियर मामलों के लिए संचार और छोटी यात्राओं को उजागर करता है। नेटवर्किंग और प्रत्यक्ष दृष्टिकोण सफलता की ओर ले जाएगा।",
            4: "आपके चतुर्थ भाव में सूर्य आपका ध्यान आपके व्यावसायिक आधार पर लाता है। आप घर से काम कर रहे हो सकते हैं या अपने करियर आधार को मजबूत कर रहे हो सकते हैं।",
            5: "आपके पंचम भाव में सूर्य के साथ, रचनात्मकता और नवाचार आपकी सफलता की कुंजी हैं। एक नए प्रोजेक्ट पर गणना किए गए जोखिम लेने से न डरें।",
            6: "आपके षष्ठ भाव में सूर्य आपके दैनिक काम और सेवा को उजागर करता है। अपनी दिनचर्या और व्यावसायिक कौशल में सुधार करने का यह एक शानदार समय है।",
            7: "आपके सप्तम भाव में सूर्य व्यावसायिक साझेदारियों और सहयोग पर ध्यान केंद्रित करता है। आज आपकी सफलता दूसरों के साथ अच्छा काम करने पर निर्भर करती है।",
            8: "आपके अष्टम भाव में सूर्य के साथ, आप गहरे, रूपांतरणकारी प्रोजेक्ट्स का सामना कर रहे हैं। साझा संसाधन और वित्तीय मामले एक मुख्य फोकस हैं।",
            9: "आपके नवम भाव में सूर्य आपको अपने व्यावसायिक क्षितिज का विस्तार करने के लिए प्रेरित करता है। उच्च शिक्षा, यात्रा, या अंतरराष्ट्रीय ग्राहकों के साथ काम करने पर विचार करें।",
            10: "आपके दशम भाव, करियर के भाव में सूर्य महत्वाकांक्षा का एक उछाल और सार्वजनिक मान्यता की इच्छा लाता है। आप अपने योगदान के लिए ध्यान आकर्षित करेंगे।",
            11: "आपके एकादश भाव में सूर्य के साथ, आपका करियर नेटवर्किंग और टीम वर्क से लाभ होता है। सहयोगियों के साथ सहयोग करना और भविष्य के लक्ष्यों का पीछा करना विशेष रूप से उत्पादक होगा।",
            12: "आपके द्वादश भाव में सूर्य से पता चलता है कि पर्दे के पीछे काम को प्राथमिकता दी जाती है। इस समय का उपयोग योजना बनाने, रणनीति बनाने और उनकी लॉन्च से पहले प्रोजेक्ट्स पर शांति से काम करने के लिए करें।"
        }.get(sun_house, "आज आपका व्यावसायिक ड्राइव मजबूत है, अपनी महत्वाकांक्षाओं पर ध्यान केंद्रित करें।")

        sun_planet = translation_manager.translate('planets.Sun', language)
        reason = f"आपके करियर में यह बढ़ी हुई प्रभाव इसलिए है क्योंकि आपके मूल जीवन शक्ति और नेतृत्व का प्रतिनिधित्व करने वाला सूर्य, आपके {sun_house}वें भाव से गुजर रहा है। यह स्थान आपको और आपकी महत्वाकांक्षाओं को चर्चा में लाता है।"
    else:
        career_narrative_template = {
            1: "With the Sun in your 1st House, you're in the spotlight. Your leadership and personal initiative are on full display.",
            2: "The Sun in your 2nd House focuses on your financial stability and values. It's a great time to work on projects that build your net worth.",
            3: "The Sun in your 3rd House highlights communication and short journeys for career matters. Networking and a direct approach will lead to success.",
            4: "The Sun in your 4th House brings your attention to your professional foundation. You may be working from home or solidifying your career base.",
            5: "With the Sun in your 5th House, creativity and innovation are key to your success. Don't be afraid to take a calculated risk on a new project.",
            6: "The Sun in your 6th House highlights your daily work and service. It's a great time to improve your routines and professional skills.",
            7: "The Sun in your 7th House focuses on professional partnerships and collaborations. Your success today depends on working well with others.",
            8: "With the Sun in your 8th House, you're tackling deep, transformative projects. Shared resources and financial matters are a key focus.",
            9: "The Sun in your 9th House inspires you to expand your professional horizons. Consider higher education, travel, or working with international clients.",
            10: "The Sun in your 10th House, the house of career, brings a surge of ambition and a desire for public recognition. You'll be noticed for your contributions.",
            11: "With the Sun in your 11th House, your career gains from networking and teamwork. Collaborating with colleagues and pursuing future goals will be particularly productive.",
            12: "The Sun in your 12th House suggests that behind-the-scenes work is favored. Use this time to plan, strategize, and work on projects quietly before their launch."
        }.get(sun_house, "Your professional drive is strong today, focus on your ambitions.")

        reason = f"This heightened influence in your career is due to the Sun, representing your core vitality and leadership, transiting through your {sun_house}th House. This placement puts you and your ambitions in the spotlight."

    narrative = f"{career_narrative_template} {interpret_aspects(astro_data, 'Sun')}"

    return {"narrative": narrative, "reason": reason}

def interpret_emotions(astro_data: dict, sign: str, language: str = 'en') -> dict:
    moon_sign = astro_data['planetary_data']['positions']['Moon']['rashi']

    if language == 'hi':
        narrative = ZODIAC_TRAITS_HI.get(moon_sign, {}).get("Rashi", "आज आपका भावनात्मक संसार सक्रिय है।")
        reason = f"आज सभी के लिए भावनात्मक स्वर चंद्रमा द्वारा निर्धारित होता है। चंद्रमा का {moon_sign} राशि के माध्यम से संक्रमण हमारी भावनाओं के सामने इस विशेष मूड और अंतर्ज्ञानपूर्ण ध्यान को लाता है।"
    else:
        narrative = ZODIAC_TRAITS.get(moon_sign, {}).get("Rashi", "Your emotional world is active today.")
        reason = f"The emotional tone for everyone today is set by the Moon. Its transit through the sign of {moon_sign} brings this particular mood and intuitive focus to the forefront of our feelings."

    return {"narrative": narrative, "reason": reason}

def interpret_travel(astro_data: dict, sign: str, language: str = 'en') -> dict:
    translation_manager = get_translation_manager()
    positions = astro_data['planetary_data']['positions']
    mercury_sign = positions['Mercury']['rashi']

    user_sign_idx = ZODIAC_SIGNS.index(sign)
    third_house_sign = ZODIAC_SIGNS[(user_sign_idx + 2) % 12]

    if language == 'hi':
        travel_narrative_template = {
            "Aries": "आज की यात्रा आवेगपूर्ण, त्वरित निर्णयों द्वारा चिह्नित है। स्वच्छंद रहें और यात्रा का आनंद लें।",
            "Taurus": "आपकी यात्राएं व्यवस्थित और व्यावहारिक परिणामों पर केंद्रित होंगी। दृश्य का आनंद लें और अपना समय लें।",
            "Gemini": "संचार-प्रधान यात्रा और सीखने के लिए यह एक शानदार दिन है। आप अपनी यात्रा के दौरान लोगों के साथ बातचीत करने का आनंद लेंगे।",
            "Cancer": "आपकी यात्रा योजनाओं में परिवार या ऐसी जगह शामिल हो सकती है जो घर जैसी महसूस हो। आप परिचित और आरामदायक गंतव्यों की ओर आकर्षित होते हैं।",
            "Leo": "आज की यात्रा आनंद और रचनात्मकता के लिए है। आप खुद को एक नई आर्ट गैलरी या ऐसी जगह का अन्वेषण करते पा सकते हैं जो आपको खुशी देती है।",
            "Virgo": "आप अपनी यात्रा के विवरणों पर ध्यान केंद्रित करेंगे, यह सुनिश्चित करते हुए कि सब कुछ व्यवस्थित है। व्यवसाय या स्वास्थ्य के लिए यात्रा को प्राथमिकता दी जाती है।",
            "Libra": "आपकी यात्राएं सौंदर्य और सामंजस्य की इच्छा से प्रेरित होती हैं। एक रोमांटिक गेटअवे या सुंदर स्थान पर यात्रा को प्राथमिकता दी जाती है।",
            "Scorpio": "आपकी आज की यात्राओं का एक गहरा उद्देश्य है। आप एक रहस्य को उजागर करने या गहरे स्तर पर जुड़ने के लिए यात्रा कर सकते हैं।",
            "Sagittarius": "एक साहसिक इंतजार करता है! आप दूरी की यात्रा और नए दर्शनों और संस्कृतियों का अन्वेषण करने के लिए आकर्षित होते हैं।",
            "Capricorn": "आज की यात्रा व्यवसाय या व्यावसायिक मामलों के लिए है। आप अपनी यात्रा के लक्ष्य और दक्षता पर ध्यान केंद्रित करते हैं।",
            "Aquarius": "आप अपरंपरागात यात्रा गंतव्यों की ओर आकर्षित होंगे। दोस्तों या एक समूह के साथ यात्रा आश्चर्यजनक और आनंददायक हो सकती है।",
            "Pisces": "आपकी यात्राएं आध्यात्मिक या कल्पनाशील उद्देश्यों के लिए हैं। आप खुद को एक शांत, सुरक्षित गंतव्य की ओर आकर्षित पा सकते हैं।"
        }.get(mercury_sign, "छोटी दूरी की यात्रा, संचार और सीखना आज पसंद किया जाता है।")

        narrative = f"{travel_narrative_template} स्थानीय अन्वेषण, पड़ोसियों या भाइयों के साथ जुड़ना, और अपने जिज्ञासु मन को संलग्न करने का यह एक अच्छा समय है।"

        mercury_planet = translation_manager.translate('planets.Mercury', language)
        reason = f"यह विषय इसलिए उभरता है क्योंकि यात्रा और बुद्धि के ग्रह बुध, वर्तमान में {mercury_sign} में हैं। इसके अलावा, दिन की ऊर्जा आपके संचार और छोटी यात्राओं के तीसरे भाव को सक्रिय करती है, जो {third_house_sign} राशि में है।"
    else:
        travel_narrative_template = {
            "Aries": "Travel today is marked by impulsive, quick decisions. Be spontaneous and enjoy the journey.",
            "Taurus": "Your journeys will be methodical and focused on practical outcomes. Enjoy the scenery and take your time.",
            "Gemini": "This is a great day for communication-heavy travel and learning. You'll enjoy interacting with people on your travels.",
            "Cancer": "Your travel plans may involve family or a place that feels like home. You're drawn to familiar and comforting destinations.",
            "Leo": "Travel today is for pleasure and creativity. You may find yourself exploring a new art gallery or a place that brings you joy.",
            "Virgo": "You'll be focused on the details of your travel, ensuring everything is in order. A trip for business or health is favored.",
            "Libra": "Your travels are motivated by a desire for beauty and harmony. A romantic getaway or a trip to a beautiful location is favored.",
            "Scorpio": "Your journeys today have a deeper purpose. You may travel to uncover a secret or to connect on a profound level.",
            "Sagittarius": "An adventure awaits! You're drawn to long-distance travel and exploring new philosophies and cultures.",
            "Capricorn": "Travel today is for business or professional matters. You're focused on the goal and efficiency of your journey.",
            "Aquarius": "You'll be drawn to unconventional travel destinations. A trip with friends or a group could be surprising and enjoyable.",
            "Pisces": "Your travels are for spiritual or imaginative purposes. You may find yourself drawn to a peaceful, serene destination."
        }.get(mercury_sign, "Short-distance travel, communication, and learning are favored today.")

        narrative = f"{travel_narrative_template} It's a good time for local exploration, connecting with neighbors or siblings, and engaging your curious mind."
        reason = f"This theme emerges because Mercury, the planet of travel and intellect, is currently in {mercury_sign}. Furthermore, the day's energy activates your 3rd House of Communication and Short Journeys, which is in the sign of {third_house_sign}."

    return {"narrative": narrative, "reason": reason}

def interpret_remedies(astro_data: dict, sign: str, language: str = 'en') -> dict:
    translation_manager = get_translation_manager()
    ruling_planet = RULING_PLANETS.get(sign, "Sun")
    color = REMEDY_COLORS.get(ruling_planet, "white")
    mantra_info = VEDIC_MANTRAS.get(ruling_planet, {})
    deity = mantra_info.get("deity", "the divine")
    mantra = mantra_info.get("mantra", "a universal prayer of peace")

    if language == 'hi':
        ruling_planet_hi = translation_manager.translate(f'planets.{ruling_planet}', language)
        color_hi = translation_manager.translate(f'horoscope_content.remedy_colors.{color}', language, default=color)
        deity_hi = translation_manager.translate(f'horoscope_content.deities.{deity}', language, default=deity)

        narrative = f"अपनी कोर ऊर्जा के साथ संरेखित होने के लिए, आज {color_hi} रंग पहनें। अपने शासक ग्रह, {ruling_planet_hi}, का सम्मान करने और इसके देवता, {deity_hi}, के आशीर्वाद प्राप्त करने के लिए, आप शांति से मंत्र का जाप कर सकते हैं: '{mantra}'।"
        reason = "ये उपाय आपके शासक ग्रह के प्रभाव को मजबूत करने के लिए डिज़ाइन किए गए हैं, जो आपके सहजात स्वभाव और जीवन शक्ति को नियंत्रित करता है, जिससे आप दिन की ऊर्जाओं को अधिक सामंजस्य के साथ नेविगेट कर सकते हैं।"
    else:
        narrative = f"To align with your core energy, wear {color} colors today. To honor your ruling planet, {ruling_planet}, and invoke the blessings of its deity, {deity}, you can quietly chant the mantra: '{mantra}'."
        reason = "These remedies are designed to strengthen the influence of your ruling planet, which governs your inherent nature and vitality, helping you navigate the day's energies with greater harmony."

    return {"narrative": narrative, "reason": reason}

# --- MAIN ORCHESTRATOR FUNCTION (V3) ---

def generate_structured_horoscope(sign: str, date=None, language: str = 'en') -> dict:
    """
    The main function to generate the complete, structured horoscope with astrological reasoning.

    Args:
        sign: Zodiac sign (e.g., "Aries", "Scorpio")
        date: Date for the horoscope (defaults to today)
        language: Language code - "en" (English) or "hi" (Hindi)
    """
    # Import translation manager for sign name translations
    from translation_manager import get_translation_manager
    translation_manager = get_translation_manager()

    # 1. Get raw data from your planetary engine
    engine = PlanetaryHoroscopeEngine()
    astro_data = engine.generate_daily_horoscope(sign, date, language)

    # 2. Call interpretation functions to build each section
    final_horoscope = {
        "overview": interpret_overview(sign, language),
        "love_and_relationships": interpret_love(astro_data, sign, language),
        "career_and_finance": interpret_career(astro_data, sign, language),
        "emotions_and_mind": interpret_emotions(astro_data, sign, language),
        "travel_and_movement": interpret_travel(astro_data, sign, language),
        "remedies": interpret_remedies(astro_data, sign, language),
        "lucky_insights": {
            "mood": astro_data['categories']['mood'],
            "lucky_color": astro_data['categories']['lucky_color'],
            "lucky_number": astro_data['categories']['lucky_number'],
            "lucky_time": astro_data['categories']['lucky_time'],
        },
        "language": language
    }

    # 3. Translate sign names in narratives if language is Hindi
    if language == 'hi':
        translated_sign = translation_manager.translate(f'zodiac_signs.{sign}', language, default=sign)

        # Translate sign name mentioned in narratives
        for section, content in final_horoscope.items():
            if isinstance(content, dict) and 'narrative' in content:
                narrative = content['narrative']
                # Replace sign name with translated version
                narrative = narrative.replace(sign, translated_sign)
                # Also translate any other zodiac signs mentioned
                for zodiac_sign in ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']:
                    translated_zodiac = translation_manager.translate(f'zodiac_signs.{zodiac_sign}', language, default=zodiac_sign)
                    narrative = narrative.replace(zodiac_sign, translated_zodiac)
                content['narrative'] = narrative

            if isinstance(content, dict) and 'reason' in content:
                reason = content['reason']
                # Replace sign name with translated version
                reason = reason.replace(sign, translated_sign)
                # Also translate any other zodiac signs mentioned
                for zodiac_sign in ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']:
                    translated_zodiac = translation_manager.translate(f'zodiac_signs.{zodiac_sign}', language, default=zodiac_sign)
                    reason = reason.replace(zodiac_sign, translated_zodiac)
                content['reason'] = reason

    return final_horoscope
