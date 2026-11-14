"""Reporting service for formatting administrative responses and bot messages."""

from datetime import datetime
from typing import Optional, Dict, Any
from database.models import AnalysisRecord


def format_start_message(admin_name: str) -> str:
    """Format welcome and setup message for /start."""
    return f"""👋 **Assalomu alaykum, {admin_name}!**

Men **Zero to Hero English — AI Channel Analyzer Bot**man.

Men kanalingizdagi postlar va foydalanuvchilar izohlarini (oxirgi 2 kunlik) yig'ib boraman hamda buyrug'ingiz bilan Gemini AI orqali tahlil qilib, **yangi, takrorlanmagan mavzular ro'yxatini** tavsiya qilaman.

🔒 **Eski botingizga mutlaqo xalaqit bermayman**:
• Post yozmayman va kanalga hech narsa joylamayman.
• Izohlarga javob bermayman.
• Faqat ma'lumotlarni o'qiyman va tahlil qilaman.
• Barcha ma'lumotlar strictly **D:\\ZeroToHero_Analyzer** papkasida saqlanadi.

📋 **Buyruqlar ro'yxati:**
• `/analyze` — Oxirgi 2 kunlik ma'lumotlarni Gemini AI bilan tahlil qilish va yangi mavzular olish
• `/status` — Oxirgi 2 kun ichida nechta post va komment yig'ilganini ko'rish
• `/topics` — Oxirgi marta AI tomonidan tavsiya qilingan mavzularni ko'rish
• `/cleanup` — 2 kundan eski ma'lumotlarni qo'lda tozalash
• `/help` — Sozlash va ishlatish bo'yicha to'liq qo'llanma
"""


def format_help_message() -> str:
    """Format detailed help and configuration instructions for /help."""
    return """📚 **Zero to Hero English Analyzer — Qo'llanma**

### 1. Telegram API orqali ma'lumot yig'ish qoidalari:
Telegram Bot API xavfsizlik arxitekturasi tufayli botlar eski yozishmalar tarixini (`getHistory`) o'qiy olmaydi. Bot qo'shilgan paytdan boshlab real vaqtda kelgan barcha yangi xabarlarni kuzatadi.

**To'g'ri ishlashi uchun 3 ta qadam:**
1. **Kanalga ulash:**
   • Ushbu botni @zerotohero_english kanalingizga **Administrator** qilib qo'shing.
   • Ruxsatlardan kamida: *Postlarni ko'rish/boshqarish* yetarli.
2. **Discussion Group (Guruh) ga ulash:**
   • Kanalga ulangan izohlar guruhiga ham ushbu botni qo'shing.
   • @BotFather da bot sozlamalariga kiring: `/setprivacy` -> Botni tanlang -> **Disable** qiling (yoki botni guruhga administrator qilib qo'shing). Shunda bot foydalanuvchilarning barcha savol va izohlarini o'qiy oladi.
3. **Tarixiy postlarni import qilish (Bonus imkoniyat):**
   • Botni endigina ishga tushirganingizda oxirgi 2 kunlik postlarni botning o'ziga shunchaki **Forward (Uzatish)** qilsangiz, bot ularni bir zumda bazaga saqlab oladi!

---

### 2. Administrator buyruqlari:
• `/analyze` — Oxirgi 2 kunlik post va kommentlarni Gemini AI ga yuboradi va 5-10 ta yangi mavzu beradi.
• `/status` — 2 kunlik statistika, DB hajmi va oxirgi post/komment vaqtlari.
• `/topics` — Oxirgi AI tahlil natijasini qayta ko'rsatadi.
• `/cleanup` — 2 kundan eski ma'lumotlarni tozalaydi (har soatda avtomatik ham tozalanadi).

📁 **Fayllar joylashuvi:**
Barcha ma'lumotlar va baza `D:\\ZeroToHero_Analyzer` papkasida joylashgan.
"""


def format_status_message(stats: Dict[str, Any], channel_id: Optional[str], group_id: Optional[str]) -> str:
    """Format status report message for /status command."""
    recent_p = stats.get("recent_posts_count", 0)
    recent_c = stats.get("recent_comments_count", 0)
    total_p = stats.get("total_posts_count", 0)
    total_c = stats.get("total_comments_count", 0)
    db_kb = stats.get("db_size_kb", 0.0)
    last_p = stats.get("latest_post_date") or "Mavjud emas"
    last_c = stats.get("latest_comment_date") or "Mavjud emas"

    ch_status = f"`{channel_id}`" if channel_id else "Sozlangan (barcha admin kanallari)"
    gr_status = f"`{group_id}`" if group_id else "Sozlangan (barcha ulangan guruhlar)"

    return f"""📊 **Zero to Hero English — Tizim holati (Oxirgi 2 kun)**

• 📝 **Oxirgi 2 kunlik postlar:** `{recent_p} ta` (Jami: `{total_p}`)
• 💬 **Oxirgi 2 kunlik izohlar:** `{recent_c} ta` (Jami: `{total_c}`)
• 🕒 **Oxirgi post sanasi:** `{last_p}`
• 🕒 **Oxirgi izoh sanasi:** `{last_c}`

💾 **Xotira va saqlash (D: Disk):**
• Baza fayli: `D:\\ZeroToHero_Analyzer\\database\\analyzer.db`
• Baza hajmi: `{db_kb} KB`
• Saqlash chegarasi: **Faqat oxirgi 2 kunlik ma'lumotlar**

📡 **Kanal va guruh holati:**
• Kanal: {ch_status}
• Discussion Group: {gr_status}

💡 *Tahlil qilish uchun `/analyze` buyrug'ini yuboring.*
"""


def format_topics_message(record: Optional[AnalysisRecord]) -> str:
    """Format the latest analyzed topics message for /topics command."""
    if not record:
        return (
            "ℹ️ **Hali hech qanday AI tahlil o'tkazilmagan.**\n\n"
            "Mavzular olish uchun `/analyze` buyrug'ini bering."
        )

    dt_str = record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "Yaqinda"
    header = (
        f"🕒 *Oxirgi tahlil vaqti:* `{dt_str}`\n"
        f"📊 *Tahlil qilingan:* `{record.posts_analyzed_count} ta post`, `{record.comments_analyzed_count} ta izoh`\n\n"
    )
    return header + record.raw_topics_text
