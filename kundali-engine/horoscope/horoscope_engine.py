"""
Horoscope Generation Engine

This module provides functionality to generate horoscopes for all 12 zodiac signs
across 4 time scopes: daily, weekly, monthly, and yearly.
Supports multi-lingual output (English and Hindi).
"""

import random
import datetime
from typing import Dict, List, Any
import hashlib
import sys
import os

# Add the parent directory to the path to import translation manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from translation_manager import get_translation_manager

# Valid zodiac signs
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Valid scopes
VALID_SCOPES = ["daily", "weekly", "monthly", "yearly"]

class HoroscopeEngine:
    """Main horoscope generation engine"""

    def __init__(self):
        self.translation_manager = get_translation_manager()

        # English colors
        self.colors_en = {
            "Aries": ["Red", "Orange", "Golden Yellow"],
            "Taurus": ["Green", "Pink", "Blue"],
            "Gemini": ["Yellow", "Silver", "Grey"],
            "Cancer": ["White", "Silver", "Sea Green"],
            "Leo": ["Gold", "Orange", "Red"],
            "Virgo": ["Navy Blue", "Grey", "Brown"],
            "Libra": ["Blue", "Green", "White"],
            "Scorpio": ["Crimson Red", "Black", "Dark Red"],
            "Sagittarius": ["Purple", "Turquoise", "Orange"],
            "Capricorn": ["Black", "Brown", "Dark Green"],
            "Aquarius": ["Blue", "Violet", "Grey"],
            "Pisces": ["Sea Green", "Blue", "Purple"]
        }

        # Hindi colors
        self.colors_hi = {
            "Aries": ["लाल", "नारंगी", "सुनहरा पीला"],
            "Taurus": ["हरा", "गुलाबी", "नीला"],
            "Gemini": ["पीला", "चांदी", "धूसर"],
            "Cancer": ["सफेद", "चांदी", "समुद्री हरा"],
            "Leo": ["सोना", "नारंगी", "लाल"],
            "Virgo": ["गहरा नीला", "धूसर", "भूरा"],
            "Libra": ["नीला", "हरा", "सफेद"],
            "Scorpio": ["गहरा लाल", "काला", "गहरा लाल"],
            "Sagittarius": ["बैंगनी", "फिरोजी", "नारंगी"],
            "Capricorn": ["काला", "भूरा", "गहरा हरा"],
            "Aquarius": ["नीला", "जामुनी", "धूसर"],
            "Pisces": ["समुद्री हरा", "नीला", "बैंगनी"]
        }

        # English moods
        self.moods_en = {
            "Aries": ["Energetic", "Confident", "Impulsive"],
            "Taurus": ["Steady", "Practical", "Determined"],
            "Gemini": ["Curious", "Adaptable", "Communicative"],
            "Cancer": ["Nurturing", "Intuitive", "Emotional"],
            "Leo": ["Radiant", "Generous", "Dramatic"],
            "Virgo": ["Analytical", "Meticulous", "Helpful"],
            "Libra": ["Harmonious", "Diplomatic", "Balanced"],
            "Scorpio": ["Intense", "Passionate", "Resilient"],
            "Sagittarius": ["Adventurous", "Optimistic", "Philosophical"],
            "Capricorn": ["Ambitious", "Disciplined", "Practical"],
            "Aquarius": ["Independent", "Innovative", "Humanitarian"],
            "Pisces": ["Dreamy", "Compassionate", "Intuitive"]
        }

        # Hindi moods
        self.moods_hi = {
            "Aries": ["ऊर्जावान", "आत्मविश्वासी", "आवेगपूर्ण"],
            "Taurus": ["स्थिर", "व्यावहारिक", "दृढ़संकल्प"],
            "Gemini": ["जिज्ञासु", "अनुकूल", "संचारी"],
            "Cancer": ["पालक", "अंतर्ज्ञानवान", "भावनात्मक"],
            "Leo": ["कांतिमान", "उदार", "नाटकीय"],
            "Virgo": ["विश्लेषणात्मक", "सूक्ष्म", "सहायक"],
            "Libra": ["सामंजस्यपूर्ण", "कूटनीतिज्ञ", "संतुलित"],
            "Scorpio": ["तीव्र", "उत्साही", "लचीला"],
            "Sagittarius": ["साहसी", "आशावादी", "दार्शनिक"],
            "Capricorn": ["महत्वाकांक्षी", "अनुशासित", "व्यावहारिक"],
            "Aquarius": ["स्वतंत्र", "नवाचारी", "मानवतावादी"],
            "Pisces": ["सपनालुलित", "दयालु", "अंतर्ज्ञानवान"]
        }

    def _get_language_data(self, language: str):
        """Get language-specific data"""
        if language == 'hi':
            return {
                'colors': self.colors_hi,
                'moods': self.moods_hi,
                'categories': self._get_hindi_category_texts(),
                'category_names': {
                    'love': self.translation_manager.translate('horoscope.love', 'hi'),
                    'career': self.translation_manager.translate('horoscope.career', 'hi'),
                    'money': self.translation_manager.translate('horoscope.money', 'hi'),
                    'health': self.translation_manager.translate('horoscope.health', 'hi'),
                    'travel': self.translation_manager.translate('horoscope.travel', 'hi'),
                    'overall': self.translation_manager.translate('horoscope.overall', 'hi')
                }
            }
        else:
            return {
                'colors': self.colors_en,
                'moods': self.moods_en,
                'categories': self._get_daily_category_texts,
                'category_names': {
                    'love': 'love',
                    'career': 'career',
                    'money': 'money',
                    'health': 'health',
                    'travel': 'travel',
                    'overall': 'overall'
                }
            }

    def _get_hindi_category_texts(self):
        """Get Hindi category texts"""
        return {
            'love': [
                "आज प्रेम संबंध मधुर रहेंगे। अपने साथी के साथ समय बिताएं।",
                "रोमांटिक मौसम है, प्यार के इजहार करने का समय।",
                "अपने प्रियजन के प्रति स्नेह और देखभाल दिखाएं।",
                "प्रेम में ईमानदारी सफलता लाएगी।",
                "अपने रिश्तों को मजबूत बनाएं।"
            ],
            'career': [
                "करियर में नई अवसर मिलेंगे। तैयार रहें।",
                "काम पर ध्यान केंद्रित करें, सफलता मिलेगी।",
                "आपकी मेहनत के परिणाम दिखाई देंगे।",
                "नए प्रोजेक्ट के लिए अच्छा समय है।",
                "आपकी क्षमताओं को पहचाना जाएगा।"
            ],
            'money': [
                "वित्तीय स्थिति में सुधार होगा।",
                "निवेश के अच्छे अवसर मिलेंगे।",
                "बचत करना महत्वपूर्ण है।",
                "आय के नए स्रोत विकसित होंगे।",
                "धन का प्रबंधन करें।"
            ],
            'health': [
                "स्वास्थ्य अच्छा रहेगा।",
                "नियमित व्यायाम करें।",
                "संतुलित आहार लें।",
                "आराम करना महत्वपूर्ण है।",
                " तनाव से बचें।"
            ],
            'travel': [
                "यात्रा शुभकारी होगी।",
                "नए स्थानों की यात्रा करें।",
                "सुरक्षित यात्रा के लिए तैयार रहें।",
                "यात्रा से ज्ञान मिलेगा।",
                "यात्रा का आनंद लें।"
            ]
        }

    def _get_seed(self, sign: str, scope: str, date_str: str) -> int:
        """Generate a consistent seed for reproducible results"""
        seed_string = f"{sign}_{scope}_{date_str}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)

    def _generate_daily(self, sign: str, language: str = 'en') -> Dict[str, Any]:
        """Generate daily horoscope for a given sign"""
        today = datetime.date.today()
        seed = self._get_seed(sign, "daily", today.strftime("%Y-%m-%d"))
        random.seed(seed)

        # Get language-specific data
        lang_data = self._get_language_data(language)

        # Lucky elements
        lucky_color = random.choice(lang_data['colors'][sign])
        lucky_number = random.randint(1, 99)

        # Generate time range
        hour = random.randint(6, 22)
        minute = random.choice([0, 15, 30, 45])
        end_hour = hour + random.randint(1, 3)
        end_minute = random.choice([0, 15, 30, 45])

        if end_hour > 23:
            end_hour = 23
            end_minute = 59

        lucky_time = f"{hour:02d}:{minute:02d} {'AM' if hour < 12 else 'PM'} – {end_hour:02d}:{end_minute:02d} {'AM' if end_hour < 12 else 'PM'}"

        mood = random.choice(lang_data['moods'][sign])

        # Generate scores and texts
        categories = {}

        if language == 'hi':
            category_texts = lang_data['categories']
        else:
            category_texts = self._get_daily_category_texts(sign, seed)

        for category in ["love", "career", "money", "health", "travel"]:
            score = random.randint(45, 85)
            text = random.choice(category_texts[category])

            # Use translated category name for the response
            category_key = lang_data['category_names'][category]
            categories[category_key] = {"score": score, "text": text}

        return {
            "date": today.strftime("%Y-%m-%d"),
            "sign": sign,
            "language": language,
            "categories": {
                self.translation_manager.translate('horoscope.lucky_color', language, default='lucky_color'): lucky_color,
                self.translation_manager.translate('horoscope.lucky_number', language, default='lucky_number'): lucky_number,
                self.translation_manager.translate('horoscope.lucky_time', language, default='lucky_time'): lucky_time,
                self.translation_manager.translate('horoscope.mood', language, default='mood'): mood,
                **categories
            }
        }

    def _get_daily_category_texts(self, sign: str, seed: int) -> Dict[str, List[str]]:
        """Get category-specific texts for daily horoscope"""
        texts = {
            "love": [
                "Great day to express your feelings to someone special.",
                "Your charm will be irresistible today.",
                "Perfect time for romantic gestures and deep conversations.",
                "Single? Keep your heart open to new possibilities.",
                "Strengthen bonds with loved ones through quality time."
            ],
            "career": [
                "Stay focused on your core goals and priorities.",
                "Your leadership qualities will shine through today.",
                "Perfect time to network and build professional relationships.",
                "Creative solutions will help you overcome challenges.",
                "Recognition for your hard work may come unexpectedly."
            ],
            "money": [
                "Be cautious with impulsive spending decisions.",
                "Good day for financial planning and budgeting.",
                "Investment opportunities may present themselves.",
                "Avoid lending money to others today.",
                "Review your expenses and cut unnecessary costs."
            ],
            "health": [
                "Maintain hydration and follow proper rest cycles.",
                "Light exercise will boost your energy levels.",
                "Pay attention to your body's signals today.",
                "Stress management techniques will be beneficial.",
                "Focus on nutritious meals and adequate sleep."
            ],
            "travel": [
                "Short trips may prove useful for your goals.",
                "Travel plans should be made with extra care.",
                "Local exploration might bring unexpected joy.",
                "Avoid unnecessary journeys during peak hours.",
                "Business travel could lead to profitable connections."
            ]
        }

        return texts

    def _generate_weekly(self, sign: str, language: str = 'en') -> Dict[str, Any]:
        """Generate weekly horoscope for a given sign"""
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)

        seed = self._get_seed(sign, "weekly", start_of_week.strftime("%Y-%m-%d"))
        random.seed(seed)

        themes = self._get_weekly_themes(sign)
        theme = random.choice(themes)

        insights = self._get_weekly_insights(sign, seed)

        return {
            "sign": sign,
            "scope": "weekly",
            "date_range": f"{start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}",
            "theme": theme,
            "insights": insights
        }

    def _get_weekly_themes(self, sign: str) -> List[str]:
        """Get weekly themes for each sign"""
        themes = {
            "Aries": ["Leadership Through Action", "Pioneering New Paths", "Energy and Initiative"],
            "Taurus": ["Building Solid Foundations", "Patience and Persistence", "Material Security"],
            "Gemini": ["Communication and Learning", "Adaptability in Change", "Mental Agility"],
            "Cancer": ["Nurturing and Protection", "Emotional Depth", "Home and Family"],
            "Leo": ["Creative Expression", "Leadership and Recognition", "Confidence and Charisma"],
            "Virgo": ["Attention to Detail", "Service and Improvement", "Practical Solutions"],
            "Libra": ["Balance and Harmony", "Relationships and Partnerships", "Justice and Fairness"],
            "Scorpio": ["Transformation and Renewal", "Depth and Intensity", "Empowerment Through Clarity"],
            "Sagittarius": ["Adventure and Exploration", "Higher Learning", "Freedom and Expansion"],
            "Capricorn": ["Ambition and Achievement", "Structure and Discipline", "Long-term Goals"],
            "Aquarius": ["Innovation and Progress", "Humanitarian Ideals", "Independence and Originality"],
            "Pisces": ["Intuition and Spirituality", "Compassion and Empathy", "Dreams and Imagination"]
        }
        return themes[sign]

    def _get_weekly_insights(self, sign: str, seed: int) -> Dict[str, str]:
        """Generate weekly insights for a sign"""
        # Base insights template that gets customized per sign
        insights_templates = self._get_insights_templates(sign)

        insights = {}
        for category, templates in insights_templates.items():
            insights[category] = random.choice(templates)

        return insights

    def _get_insights_templates(self, sign: str) -> Dict[str, List[str]]:
        """Get insights templates for weekly/monthly/yearly horoscopes"""
        # This would be expanded with sign-specific templates
        base_templates = {
            "summary": [
                f"This week brings significant opportunities for {sign} natives to showcase their natural talents and abilities. The cosmic energies align favorably, creating a supportive environment for personal growth and achievement. You'll find yourself more confident and ready to tackle challenges that once seemed insurmountable.",
                f"A transformative week awaits {sign} individuals, filled with moments of clarity and decisive action. The universe conspires to bring you closer to your goals, while unexpected encounters may open doors to new possibilities. Trust your instincts and remain open to change.",
                f"For {sign} natives, this week emphasizes the importance of balance between ambition and patience. While opportunities abound, the key to success lies in strategic planning and thoughtful execution. Your natural wisdom will guide you through any complexity."
            ],
            "personal": [
                "Your personal magnetism reaches new heights this week, drawing people and opportunities toward you effortlessly. This is an excellent time for self-reflection and understanding your deeper motivations. Embrace your authentic self and let your genuine nature shine through in all interactions.",
                "A period of personal renaissance unfolds, encouraging you to explore new facets of your personality and capabilities. You may discover hidden talents or develop existing skills to new levels. The confidence you gain from these discoveries will positively impact all areas of your life.",
                "This week emphasizes personal growth through meaningful connections and experiences. You'll find yourself more empathetic and understanding, which strengthens your relationships and broadens your perspective on life. Trust in your ability to navigate complex emotional landscapes."
            ],
            "travel": [
                "Travel plans, whether for business or pleasure, receive favorable cosmic support this week. Short journeys may prove particularly beneficial, offering fresh perspectives and valuable connections. If planning a trip, mid-week timing shows the most promise for smooth experiences.",
                "Movement and change of scenery feature prominently in your week ahead. Even local excursions or changes in your daily routine can bring refreshing energy and new insights. Stay flexible with travel plans as spontaneous opportunities may arise.",
                "The urge to explore new places grows stronger, and the universe supports your wanderlust. Whether it's a weekend getaway or a business trip, travel experiences this week will be enriching and memorable. Pack your curiosity along with your essentials."
            ],
            "luck": [
                "Fortune smiles upon your efforts this week, particularly in endeavors that require creativity and innovation. Your natural intuition is heightened, helping you make decisions that lead to positive outcomes. Trust those sudden insights and gut feelings that guide you toward success.",
                "This week brings a series of fortunate coincidences and timely opportunities. Your ability to recognize and seize these moments will determine the extent of your success. Stay alert to signs and synchronicities that point toward your next breakthrough.",
                "Lucky breaks come through your social connections and collaborative efforts. The energy you've invested in building relationships now pays dividends in unexpected ways. Your generosity and positive attitude attract equally positive responses from others."
            ],
            "profession": [
                "Your professional life takes on new dimensions this week as innovative ideas and strategic thinking propel you forward. Colleagues and superiors take notice of your contributions, possibly leading to new responsibilities or recognition. This is an excellent time to showcase your leadership abilities.",
                "Career matters gain momentum through your persistent efforts and professional networking. A project or proposal you've been working on may finally receive the attention it deserves. Your expertise and dedication set you apart from the competition.",
                "The workplace becomes a stage for your talents to shine, with opportunities for advancement or new projects coming your way. Your ability to collaborate effectively while maintaining your unique perspective makes you an invaluable team member. Embrace leadership opportunities that arise."
            ],
            "health": [
                "Your vitality and energy levels receive a significant boost this week, making it an ideal time to establish new health routines or intensify existing ones. Listen to your body's signals and provide it with the nutrition and rest it needs. Mental health benefits from creative outlets and social connections.",
                "A holistic approach to wellness serves you well this week, with particular emphasis on the mind-body connection. Stress management techniques and relaxation practices will prove especially beneficial. Consider incorporating meditation or gentle exercise into your daily routine.",
                "Your body's natural healing capabilities are enhanced this week, making it an opportune time to address any nagging health concerns. Preventive care and regular check-ups are favored. Energy levels remain stable, supporting both physical activities and mental challenges."
            ],
            "emotion": [
                "Emotional clarity and stability characterize this week, allowing you to process recent experiences and prepare for future challenges. Your empathy and understanding deepen, improving your relationships and your ability to help others. This emotional growth strengthens your overall resilience.",
                "A week of emotional healing and renewal unfolds, bringing closure to past hurts and opening your heart to new possibilities. Your emotional intelligence guides you through complex situations with grace and wisdom. Trust in your ability to navigate any emotional challenges that arise.",
                "Your emotional world becomes more balanced and harmonious this week, creating space for joy and contentment to flourish. Relationships benefit from your increased emotional availability and authentic expression. This is an excellent time for heart-to-heart conversations and emotional bonding."
            ],
            "remedy": [
                "To maximize this week's positive energy, spend time in nature and practice gratitude for the abundance in your life. Meditation or quiet reflection in the early morning hours will help you stay centered and focused. Consider wearing your lucky colors to enhance your natural magnetism.",
                "Enhance your week's potential by maintaining regular sleep patterns and staying hydrated. Engage in activities that bring you joy and connect you with your creative side. A small act of service to others will multiply your own blessings and create positive karma.",
                "This week benefits from clear communication and honest expression of your thoughts and feelings. Keep a journal to track insights and synchronicities that occur. Surrounding yourself with positive, supportive people will amplify the week's beneficial influences."
            ]
        }

        return base_templates

    def _generate_monthly(self, sign: str, language: str = 'en') -> Dict[str, Any]:
        """Generate monthly horoscope for a given sign"""
        today = datetime.date.today()
        start_of_month = today.replace(day=1)

        # Calculate end of month
        if today.month == 12:
            end_of_month = datetime.date(today.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_of_month = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)

        seed = self._get_seed(sign, "monthly", start_of_month.strftime("%Y-%m"))
        random.seed(seed)

        themes = self._get_monthly_themes(sign)
        theme = random.choice(themes)

        insights = self._get_monthly_insights(sign, seed)

        return {
            "sign": sign,
            "scope": "monthly",
            "date_range": f"{start_of_month.strftime('%Y-%m-%d')} to {end_of_month.strftime('%Y-%m-%d')}",
            "theme": theme,
            "insights": insights
        }

    def _get_monthly_themes(self, sign: str) -> List[str]:
        """Get monthly themes for each sign"""
        themes = {
            "Aries": ["Dynamic Growth and Leadership", "Breaking New Ground", "Courage in Transformation"],
            "Taurus": ["Steady Progress and Stability", "Building Lasting Foundations", "Patience Rewarded"],
            "Gemini": ["Intellectual Expansion", "Communication Mastery", "Versatile Adaptation"],
            "Cancer": ["Emotional Fulfillment", "Nurturing Growth", "Home and Heart"],
            "Leo": ["Creative Brilliance", "Recognition and Honor", "Generous Leadership"],
            "Virgo": ["Perfection Through Service", "Analytical Breakthrough", "Practical Wisdom"],
            "Libra": ["Harmony and Balance", "Partnership Success", "Aesthetic Achievement"],
            "Scorpio": ["Deep Transformation", "Intense Renewal", "Phoenix Rising"],
            "Sagittarius": ["Expansive Horizons", "Philosophical Growth", "Adventure Awaits"],
            "Capricorn": ["Ambitious Achievement", "Structured Success", "Mountain Climbing"],
            "Aquarius": ["Revolutionary Innovation", "Humanitarian Vision", "Future Focused"],
            "Pisces": ["Spiritual Awakening", "Compassionate Service", "Intuitive Flow"]
        }
        return themes[sign]

    def _get_monthly_insights(self, sign: str, seed: int) -> Dict[str, str]:
        """Generate monthly insights for a sign"""
        # Extended insights for monthly scope
        insights_templates = self._get_monthly_insights_templates(sign)

        insights = {}
        for category, templates in insights_templates.items():
            insights[category] = random.choice(templates)

        return insights

    def _get_monthly_insights_templates(self, sign: str) -> Dict[str, List[str]]:
        """Get monthly insights templates"""
        # These would be longer, more detailed templates for monthly scope
        monthly_templates = {
            "summary": [
                f"This month marks a significant turning point for {sign} natives, as planetary alignments create a powerful cosmic backdrop for personal and professional transformation. The energy builds gradually through the weeks, culminating in opportunities that have been months in the making. Your natural abilities find new expression, and doors that seemed closed begin to open. This is a time to embrace your authentic self and trust in the journey ahead.",
                f"A month of profound growth awaits {sign} individuals, characterized by both challenges that strengthen your resolve and opportunities that expand your horizons. The cosmic influences encourage you to step outside your comfort zone and embrace new possibilities. Your intuition is particularly sharp during this period, guiding you toward decisions that align with your highest good. Trust the process and remain open to unexpected developments.",
                f"For {sign} natives, this month emphasizes the importance of balance between action and reflection, ambition and patience. The universe provides multiple pathways to success, but the key lies in choosing the route that resonates with your deeper purpose. Your natural wisdom and accumulated experience serve as valuable guides through any complexity or uncertainty that may arise."
            ],
            "personal": [
                "Your personal evolution accelerates this month, bringing increased self-awareness and confidence in your unique gifts and abilities. This is an excellent time for self-improvement projects, whether they involve developing new skills, breaking old habits, or exploring different aspects of your personality. The insights you gain about yourself will positively impact all areas of your life and strengthen your relationships with others.",
                "A period of personal renaissance unfolds throughout the month, encouraging you to explore new facets of your identity and capabilities. You may find yourself drawn to activities, people, or experiences that previously held little interest, only to discover they open up entirely new dimensions of your being. This expansion of self-understanding brings greater authenticity and joy to your daily experience.",
                "This month emphasizes personal growth through meaningful connections and transformative experiences. Your empathy and understanding deepen significantly, allowing you to navigate complex emotional landscapes with grace and wisdom. The confidence you gain from these personal discoveries will create a positive ripple effect in your relationships, career, and overall life satisfaction."
            ],
            "travel": [
                "Travel features prominently in your month ahead, whether for business, pleasure, or personal growth. Long-distance journeys may prove particularly transformative, offering fresh perspectives and valuable connections that influence your future direction. If planning international travel, the middle weeks of the month show the most promise for smooth experiences and meaningful encounters.",
                "The urge to explore new places and expand your horizons grows stronger throughout the month, supported by favorable cosmic influences. Even local excursions or changes in your daily routine can bring refreshing energy and unexpected insights. Stay flexible with travel plans, as spontaneous opportunities may arise that prove more rewarding than carefully laid plans.",
                "Movement and change of scenery play important roles in your personal development this month. Whether it's a business trip that opens new professional doors or a vacation that provides much-needed rest and inspiration, travel experiences will be enriching and memorable. Your openness to new cultures and perspectives enhances the value of any journey you undertake."
            ],
            "luck": [
                "Fortune builds momentum throughout the month, particularly favoring endeavors that require creativity, innovation, and collaborative effort. Your natural intuition is heightened, helping you recognize and seize opportunities that others might overlook. The first and last weeks of the month show especially strong potential for fortunate developments and positive surprises.",
                "This month brings a series of fortunate coincidences and timely opportunities that seem to arrive just when you need them most. Your ability to recognize these moments and act upon them with confidence will determine the extent of your success. Stay alert to signs and synchronicities that point toward your next breakthrough or major opportunity.",
                "Lucky breaks come through your social connections, professional network, and collaborative efforts. The energy and goodwill you've invested in building relationships now pay dividends in unexpected ways. Your generosity and positive attitude attract equally positive responses from others, creating a cycle of mutual benefit and shared success."
            ],
            "profession": [
                "Your professional life undergoes significant positive transformation this month, as innovative ideas and strategic thinking propel you toward new levels of success. Colleagues and superiors take notice of your contributions, possibly leading to new responsibilities, recognition, or advancement opportunities. This is an excellent time to showcase your leadership abilities and propose new initiatives or solutions.",
                "Career matters gain substantial momentum through your persistent efforts and professional networking. A project or proposal you've been developing may finally receive the attention and support it deserves. Your expertise and dedication set you apart from the competition, while your ability to collaborate effectively makes you an invaluable team member and potential leader.",
                "The workplace becomes a stage for your talents to shine, with multiple opportunities for advancement, new projects, or professional recognition coming your way. Your unique perspective and problem-solving abilities are particularly valued during this period. Embrace leadership opportunities that arise, as they will likely lead to long-term career benefits and personal satisfaction."
            ],
            "health": [
                "Your vitality and energy levels receive a significant boost this month, making it an ideal time to establish new health routines or intensify existing wellness practices. Listen carefully to your body's signals and provide it with the nutrition, exercise, and rest it needs. Mental health benefits greatly from creative outlets, social connections, and stress-reduction techniques.",
                "A holistic approach to wellness serves you exceptionally well this month, with particular emphasis on the mind-body connection and preventive care. Stress management techniques, regular exercise, and proper nutrition combine to create a strong foundation for overall health. Consider incorporating meditation, yoga, or other mindfulness practices into your daily routine.",
                "Your body's natural healing capabilities are enhanced throughout the month, making it an opportune time to address any ongoing health concerns or focus on preventive care. Regular check-ups and health screenings are favored, as are lifestyle changes that support long-term wellness. Energy levels remain stable and strong, supporting both physical activities and mental challenges."
            ],
            "emotion": [
                "Emotional clarity and stability characterize this month, allowing you to process recent experiences and prepare confidently for future challenges. Your empathy and understanding deepen significantly, improving your relationships and your ability to help others through difficult times. This emotional growth strengthens your overall resilience and life satisfaction.",
                "A month of emotional healing and renewal unfolds, bringing closure to past hurts and opening your heart to new possibilities and deeper connections. Your emotional intelligence reaches new heights, guiding you through complex situations with grace and wisdom. Trust in your ability to navigate any emotional challenges that arise with maturity and compassion.",
                "Your emotional world becomes more balanced and harmonious throughout the month, creating space for joy, contentment, and meaningful connections to flourish. Relationships benefit from your increased emotional availability and authentic expression. This is an excellent time for heart-to-heart conversations, emotional bonding, and deepening important relationships."
            ],
            "remedy": [
                "To maximize this month's positive energy, maintain regular spiritual or meditative practices that keep you centered and focused on your highest goals. Spend time in nature, practice gratitude for the abundance in your life, and engage in activities that bring you joy and connect you with your creative side. Wearing your lucky colors and carrying small crystals or talismans can enhance your natural magnetism and intuitive abilities.",
                "Enhance your month's potential by maintaining regular sleep patterns, staying well-hydrated, and eating nutritious foods that support your energy levels. Engage in physical activities that you enjoy, whether it's walking, swimming, dancing, or yoga. A small act of service to others each week will multiply your own blessings and create positive karma that benefits all areas of your life.",
                "This month benefits from clear communication and honest expression of your thoughts and feelings in all relationships. Keep a journal to track insights, synchronicities, and personal growth that occurs throughout the month. Surrounding yourself with positive, supportive people will amplify the month's beneficial influences and help you achieve your goals more easily."
            ]
        }

        return monthly_templates

    def _generate_yearly(self, sign: str, language: str = 'en') -> Dict[str, Any]:
        """Generate yearly horoscope for a given sign"""
        today = datetime.date.today()
        start_of_year = datetime.date(today.year, 1, 1)
        end_of_year = datetime.date(today.year, 12, 31)

        seed = self._get_seed(sign, "yearly", str(today.year))
        random.seed(seed)

        themes = self._get_yearly_themes(sign)
        theme = random.choice(themes)

        insights = self._get_yearly_insights(sign, seed)

        return {
            "sign": sign,
            "scope": "yearly",
            "date_range": f"{start_of_year.strftime('%Y-%m-%d')} to {end_of_year.strftime('%Y-%m-%d')}",
            "theme": theme,
            "insights": insights
        }

    def _get_yearly_themes(self, sign: str) -> List[str]:
        """Get yearly themes for each sign"""
        themes = {
            "Aries": ["Year of Bold Beginnings", "Leadership Revolution", "Pioneering Spirit Unleashed"],
            "Taurus": ["Foundation Year", "Steady Prosperity", "Building Lasting Success"],
            "Gemini": ["Communication Mastery", "Intellectual Renaissance", "Versatile Expansion"],
            "Cancer": ["Emotional Mastery", "Nurturing Success", "Home and Heart Harmony"],
            "Leo": ["Creative Sovereignty", "Recognition and Glory", "Generous Leadership"],
            "Virgo": ["Perfection and Service", "Analytical Mastery", "Practical Wisdom"],
            "Libra": ["Harmony and Partnership", "Balanced Success", "Aesthetic Achievement"],
            "Scorpio": ["Transformation Mastery", "Phoenix Rising", "Deep Renewal"],
            "Sagittarius": ["Expansion and Adventure", "Philosophical Growth", "Boundless Horizons"],
            "Capricorn": ["Achievement and Authority", "Structured Success", "Mountain Peak"],
            "Aquarius": ["Innovation and Revolution", "Humanitarian Vision", "Future Creating"],
            "Pisces": ["Spiritual Awakening", "Compassionate Service", "Intuitive Mastery"]
        }
        return themes[sign]

    def _get_yearly_insights(self, sign: str, seed: int) -> Dict[str, str]:
        """Generate yearly insights for a sign"""
        # Extended insights for yearly scope
        insights_templates = self._get_yearly_insights_templates(sign)

        insights = {}
        for category, templates in insights_templates.items():
            insights[category] = random.choice(templates)

        return insights

    def _get_yearly_insights_templates(self, sign: str) -> Dict[str, List[str]]:
        """Get yearly insights templates"""
        # These would be comprehensive, detailed templates for yearly scope
        yearly_templates = {
            "summary": [
                f"This year represents a watershed moment for {sign} natives, as major planetary cycles converge to create unprecedented opportunities for growth, transformation, and achievement. The cosmic energies build throughout the year, creating a powerful backdrop for personal and professional evolution. Multiple cycles of expansion and consolidation will help you integrate new experiences and wisdom into your life structure. This is a year to embrace your authentic self, trust in your journey, and prepare for the significant developments that lie ahead.",
                f"A year of profound transformation awaits {sign} individuals, characterized by both challenges that forge your character and opportunities that expand your horizons beyond current imagination. The cosmic influences encourage you to step boldly outside your comfort zone and embrace new possibilities with confidence and enthusiasm. Your intuition reaches new heights during this period, guiding you toward decisions that align with your highest potential and deepest purpose. Trust the unfolding process and remain open to unexpected developments that reshape your understanding of what's possible.",
                f"For {sign} natives, this year emphasizes the crucial balance between visionary thinking and practical implementation, between ambitious goals and patient persistence. The universe provides multiple pathways to success, but the key lies in choosing the route that resonates with your deeper purpose and authentic nature. Your accumulated wisdom and life experience serve as invaluable guides through any complexity or uncertainty that may arise. This is a year of both harvesting past efforts and planting seeds for future abundance."
            ],
            "personal": [
                "Your personal evolution accelerates dramatically this year, bringing unprecedented self-awareness and confidence in your unique gifts and abilities. This is an exceptional time for comprehensive self-improvement projects, whether they involve developing new skills, breaking limiting patterns, or exploring entirely different aspects of your personality and potential. The insights you gain about yourself will create positive ripple effects in all areas of your life, strengthening relationships, enhancing career prospects, and deepening your sense of purpose and fulfillment.",
                "A year of personal renaissance unfolds, encouraging you to explore new facets of your identity and capabilities with courage and curiosity. You may find yourself drawn to activities, people, or experiences that previously held little interest, only to discover they open up entirely new dimensions of your being and potential. This expansion of self-understanding brings greater authenticity, joy, and effectiveness to your daily experience, while also inspiring others through your example of growth and transformation.",
                "This year emphasizes personal growth through meaningful connections and transformative experiences that challenge your assumptions and expand your worldview. Your empathy and understanding deepen significantly, allowing you to navigate complex emotional landscapes with grace, wisdom, and compassion. The confidence you gain from these personal discoveries will create a positive influence in your relationships, career advancement, and overall life satisfaction, while positioning you as a source of inspiration and guidance for others."
            ],
            "travel": [
                "Travel features prominently throughout your year, whether for business expansion, personal growth, or spiritual exploration. Long-distance journeys prove particularly transformative, offering fresh perspectives and valuable connections that significantly influence your future direction and opportunities. International travel during the middle months shows exceptional promise for smooth experiences and meaningful encounters that could reshape your understanding of the world and your place in it.",
                "The urge to explore new places and expand your horizons grows stronger throughout the year, supported by exceptionally favorable cosmic influences that seem to clear obstacles and create opportunities. Even local excursions or changes in your daily routine can bring refreshing energy and unexpected insights that contribute to your overall growth and development. Stay flexible with travel plans, as spontaneous opportunities may arise that prove more rewarding and significant than carefully laid plans.",
                "Movement and change of scenery play crucial roles in your personal development this year, with each journey contributing to your expanding understanding of yourself and the world. Whether it's business trips that open new professional doors or vacations that provide much-needed rest and inspiration, travel experiences will be enriching, memorable, and transformative. Your openness to new cultures and perspectives enhances the value of any journey you undertake, creating lasting memories and meaningful connections."
            ],
            "luck": [
                "Fortune builds substantial momentum throughout the year, particularly favoring endeavors that require creativity, innovation, and collaborative effort with like-minded individuals. Your natural intuition is significantly heightened, helping you recognize and seize opportunities that others might overlook or dismiss. The spring and autumn months show especially strong potential for fortunate developments and positive surprises that exceed your expectations and open new possibilities.",
                "This year brings a remarkable series of fortunate coincidences and timely opportunities that seem to arrive precisely when you need them most. Your ability to recognize these moments and act upon them with confidence and decisiveness will determine the extent of your success and fulfillment. Stay alert to signs and synchronicities that point toward your next breakthrough or major opportunity, as they will be more frequent and significant than usual.",
                "Lucky breaks come consistently through your social connections, professional network, and collaborative efforts with others who share your vision and values. The energy and goodwill you've invested in building relationships now pay substantial dividends in unexpected ways throughout the year. Your generosity and consistently positive attitude attract equally positive responses from others, creating a beneficial cycle of mutual support and shared success that amplifies everyone's achievements."
            ],
            "profession": [
                "Your professional life undergoes significant positive transformation this year, as innovative ideas and strategic thinking propel you toward new levels of success and recognition. Colleagues and superiors take notice of your contributions, leading to new responsibilities, advancement opportunities, and increased influence within your field. This is an exceptional year to showcase your leadership abilities, propose new initiatives, and position yourself as a thought leader and problem-solver in your industry.",
                "Career matters gain substantial momentum through your persistent efforts and expanded professional networking. Projects or proposals you've been developing may finally receive the attention and support they deserve, while new opportunities emerge that align perfectly with your skills and aspirations. Your expertise and dedication set you apart from the competition, while your ability to collaborate effectively makes you an invaluable team member and natural leader.",
                "The workplace becomes a stage for your talents to shine brilliantly, with multiple opportunities for advancement, new projects, and professional recognition coming your way throughout the year. Your unique perspective and innovative problem-solving abilities are particularly valued during this period of industry evolution and change. Embrace leadership opportunities that arise, as they will likely lead to long-term career benefits and personal satisfaction that extend far beyond immediate gains."
            ],
            "health": [
                "Your vitality and energy levels receive a significant boost this year, making it an ideal time to establish comprehensive health routines or intensify existing wellness practices. Listen carefully to your body's signals and provide it with the nutrition, exercise, and rest it needs to support your ambitious goals and active lifestyle. Mental health benefits greatly from creative outlets, social connections, and stress-reduction techniques that you can maintain consistently throughout the year.",
                "A holistic approach to wellness serves you exceptionally well this year, with particular emphasis on the mind-body connection and preventive care that supports long-term health and vitality. Stress management techniques, regular exercise, and proper nutrition combine to create a strong foundation for overall health that can support your increased activities and responsibilities. Consider incorporating meditation, yoga, or other mindfulness practices into your daily routine for optimal results.",
                "Your body's natural healing capabilities are enhanced throughout the year, making it an opportune time to address any ongoing health concerns or focus on preventive care that supports your long-term wellbeing. Regular check-ups and health screenings are favored, as are lifestyle changes that support sustained wellness and energy. Your energy levels remain stable and strong, supporting both physical activities and mental challenges while maintaining balance and avoiding burnout."
            ],
            "emotion": [
                "Emotional clarity and stability characterize this year, allowing you to process recent experiences and prepare confidently for future challenges and opportunities. Your empathy and understanding deepen significantly, improving your relationships and your ability to help others through difficult times while maintaining your own emotional balance. This emotional growth strengthens your overall resilience and life satisfaction while positioning you as a source of wisdom and support for others.",
                "A year of emotional healing and renewal unfolds, bringing closure to past hurts and opening your heart to new possibilities and deeper connections with others. Your emotional intelligence reaches new heights, guiding you through complex situations with grace and wisdom while maintaining your authenticity and compassion. Trust in your ability to navigate any emotional challenges that arise with maturity and understanding, knowing that each experience contributes to your growth.",
                "Your emotional world becomes more balanced and harmonious throughout the year, creating space for joy, contentment, and meaningful connections to flourish in all areas of your life. Relationships benefit from your increased emotional availability and authentic expression, while your ability to understand and support others deepens significantly. This is an excellent year for heart-to-heart conversations, emotional bonding, and deepening important relationships that will support your continued growth and happiness."
            ],
            "remedy": [
                "To maximize this year's positive energy, maintain regular spiritual or meditative practices that keep you centered and focused on your highest goals and aspirations. Spend time in nature regularly, practice gratitude for the abundance in your life, and engage in activities that bring you joy and connect you with your creative side. Wearing your lucky colors and carrying small crystals or talismans can enhance your natural magnetism and intuitive abilities throughout the year.",
                "Enhance your year's potential by maintaining regular sleep patterns, staying well-hydrated, and eating nutritious foods that support your energy levels and overall health. Engage in physical activities that you enjoy, whether it's walking, swimming, dancing, or yoga, and make them a consistent part of your routine. A small act of service to others each week will multiply your own blessings and create positive karma that benefits all areas of your life.",
                "This year benefits from clear communication and honest expression of your thoughts and feelings in all relationships, both personal and professional. Keep a journal to track insights, synchronicities, and personal growth that occurs throughout the year, as patterns will emerge that guide your future decisions. Surrounding yourself with positive, supportive people will amplify the year's beneficial influences and help you achieve your goals more easily while maintaining balance and joy in your life."
            ]
        }

        return yearly_templates


def generate_horoscope(sign: str, scope: str = "daily", language: str = 'en') -> Dict[str, Any]:
    """
    Generate horoscope for a given zodiac sign and time scope with multi-lingual support.

    Args:
        sign: Zodiac sign (e.g., "Aries", "Scorpio")
        scope: Time scope - "daily", "weekly", "monthly", or "yearly"
        language: Language code - "en" (English) or "hi" (Hindi)

    Returns:
        Dictionary containing horoscope data

    Raises:
        ValueError: If sign or scope is invalid
    """
    if sign not in ZODIAC_SIGNS:
        raise ValueError(f"Invalid zodiac sign: {sign}. Must be one of: {', '.join(ZODIAC_SIGNS)}")

    if scope not in VALID_SCOPES:
        raise ValueError(f"Invalid scope: {scope}. Must be one of: {', '.join(VALID_SCOPES)}")

    engine = HoroscopeEngine()

    if scope == "daily":
        return engine._generate_daily(sign, language)
    elif scope == "weekly":
        return engine._generate_weekly(sign, language)
    elif scope == "monthly":
        return engine._generate_monthly(sign, language)
    elif scope == "yearly":
        return engine._generate_yearly(sign, language)


# Example usage
if __name__ == "__main__":
    # Test the horoscope generation
    print("=== Daily Horoscope Example ===")
    daily = generate_horoscope("Scorpio", "daily")
    print(f"Sign: {daily['sign']}")
    print(f"Date: {daily['date']}")
    print(f"Lucky Color: {daily['categories']['lucky_color']}")
    print(f"Mood: {daily['categories']['mood']}")
    print(f"Love Score: {daily['categories']['love']['score']}")
    print(f"Love Text: {daily['categories']['love']['text']}")

    print("\n=== Weekly Horoscope Example ===")
    weekly = generate_horoscope("Scorpio", "weekly")
    print(f"Sign: {weekly['sign']}")
    print(f"Scope: {weekly['scope']}")
    print(f"Date Range: {weekly['date_range']}")
    print(f"Theme: {weekly['theme']}")
    print(f"Summary: {weekly['insights']['summary'][:100]}...")
