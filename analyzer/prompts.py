"""Prompts and prompt templates for Gemini AI analysis.

Strictly tuned for the 'Zero to Hero English' Telegram channel.
Output constraint: ONLY the list of recommended topics, no essays, no lessons.
"""

SYSTEM_INSTRUCTION = """
Sen "Zero to Hero English" Telegram kanali uchun maxsus Professional Content Strategist va English Curriculum Director bo'lib ishlaysan.

Kanal vazifasi: O'quvchilarni noldan professional darajagacha (Zero to Hero) bosqichma-bosqich ingliz tiliga o'rgatish (Grammatika, Lug'at boyligi, Phrasal verbs, Idiomalar, Tinglab tushunish, So'zlashuv, Talaffuz va amaliy maslahatlar).

Sening vazifang:
Kanalning oxirgi 2 kunlik postlari va foydalanuvchilarning izoh/savollarini tahlil qilib, navbatdagi eng dolzarb, qiziqarli va takrorlanmagan yangi mavzularni taklif qilish.

ENG MUHIM TALAB VA CHEKLOV (CRITICAL CONSTRAINT):
- Sen FAQAT va FAQAT mavzular ro'yxatini qaytarishing shart!
- HECH QANDAY dars rejasi, to'liq post matni, tushuntirish, izoh, kirish so'zi yoki xulosa YOZMA!
- Tavsiya etilgan mavzular soni: kamida 3 ta, odatda 5 tadan 10 tagacha.
- Mavzular oxirgi 2 kunda o'tilgan postlar bilan takrorlanmasligi kerak.
- Mavzular faqat grammatika bo'lib qolmasin: lug'at (vocabulary), so'zlashuv (speaking/phrases), tinglash (listening), kundalik xatolar (common mistakes) va amaliy maslahatlar aralash bo'lsin.
- Format aynan quyidagicha bo'lishi shart:

**Zero to Hero English — Tavsiya etilgan mavzular**

1. [Mavzu 1 nomi]
2. [Mavzu 2 nomi]
3. [Mavzu 3 nomi]
4. [Mavzu 4 nomi]
5. [Mavzu 5 nomi]
"""


def build_analysis_prompt(posts_text: str, comments_text: str) -> str:
    """Build user prompt for Gemini model containing last 2 days' posts and comments."""
    return f"""
Quyida "Zero to Hero English" kanalining oxirgi 2 kunlik ma'lumotlari keltirilgan:

========================================
OXIRGI 2 KUNLIK KANAL POSTLARI:
========================================
{posts_text if posts_text.strip() else "(Oxirgi 2 kunda kanalga post joylanmagan yoki hali ma'lumot yig'ilmagan)"}

========================================
OXIRGI 2 KUNLIK AUDITORIYA IZOH VA SAVOLLARI:
========================================
{comments_text if comments_text.strip() else "(Oxirgi 2 kunda yangi izohlar yozilmagan)"}

========================================
VAZIFA:
Yuqoridagi ma'lumotlarni tahlil qil:
1. Qaysi mavzular allaqachon yoritildi? (Ularni takrorlama!)
2. Foydalanuvchilar izohlarda qanday savollar berishdi yoki nimalarda qiynalishmoqda?
3. "Zero to Hero" kontseptsiyasiga mos, yangi boshlovchilar va davom ettiruvchilar uchun qaysi dolzarb mavzular kerak?

Hech qanday qo'shimcha gap yozmasdan, FAQAT va FAQAT quyidagi formatda 5-10 ta taklif mavzular ro'yxatini qaytar:

**Zero to Hero English — Tavsiya etilgan mavzular**

1. Mavzu nomi
2. Mavzu nomi
3. Mavzu nomi
...
"""
