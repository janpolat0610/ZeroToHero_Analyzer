# Zero to Hero English — AI Channel Analyzer Bot

**Zero to Hero English** Telegram kanali uchun maxsus ishlab chiqilgan, to'liq mustaqil ishlaydigan **AI Channel Analyzer Bot**.

Ushbu bot kanaldagi postlar va auditoriya izohlarini (faqat oxirgi 2 kunlik) yig'ib boradi va administrator `/analyze` buyrug'ini yuborganida Google Gemini AI yordamida tahlil qilib, **kamida 3 ta (odatda 5–10 ta) yangi, takrorlanmagan dars mavzularini** tavsiya qiladi.

---

## 🔒 1. Eski botdan to'liq mustaqillik va xavfsizlik kafolati

- **Eski botga mutlaqo tegmaydi:** Loyihangizdagi mavjud post joylovchi bot kodlari o'zgartirilmaydi, to'xtatilmaydi va unga xalaqit berilmaydi.
- **Alohida Bot Token:** Ushbu bot uchun `@BotFather` dan olingan yangi, alohida bot tokeni ishlatiladi.
- **Cheklovlar:** Bot hech qachon kanalga post joylamaydi, izohlarga javob yozmaydi va to'liq dars matnlarini generatsiya qilmaydi. Vazifasi faqat: **ma'lumot yig'ish + administrator so'raganda mavzular ro'yxatini berish**.
- **Natija formati:** AI faqat mavzu nomlarini beradi (hech qanday uzun dars, tushuntirish yoki keraksiz gaplarsiz).

---

## 💾 2. Disk D talablari va Fayllar joylashuvi

Kompyuteringizdagi C disk to'lib qolmasligi uchun barcha fayllar strictly **D: diskda** joylashtirilgan:

```
D:\ZeroToHero_Analyzer\
├── .venv\                      # Virtual environment (Python 3.12, D diskda)
├── .cache\                     # Pip va vaqtinchalik kesh fayllari
├── database\
│   ├── analyzer.db             # SQLite ma'lumotlar bazasi
│   ├── models.py               # Post, Comment, AnalysisRecord ma'lumot modellari
│   ├── db.py                   # aiosqlite ulanish va sxema boshqaruvi
│   └── crud.py                 # Saqlash, 2 kunlik filtr va avto-tozalash funksiyalari
├── collector\
│   ├── channel_collector.py    # Kanal postlarini real vaqtda ushlab qoluvchi
│   ├── comment_collector.py    # Discussion Group izohlarini ushlab qoluvchi
│   └── manual_importer.py      # Tarixiy postlarni forward orqali bir zumda import qilish
├── analyzer\
│   ├── gemini_analyzer.py      # Google Gemini API mijozi va parser
│   └── prompts.py              # Zero to Hero English uchun maxsus sozlangan AI prompt
├── bot\
│   ├── handlers\
│   │   └── admin_handlers.py   # /start, /analyze, /status, /topics, /cleanup, /help
│   ├── filters\
│   │   └── admin_filter.py     # Faqat administratorlar uchun ruxsat filtri
│   └── middlewares\
│       └── logging_middleware.py # Update monitoring va kontekst boshqaruvi
├── services\
│   ├── scheduler_service.py    # APScheduler orqali 2 kundan eski ma'lumotlarni avto-tozalash
│   └── reporter_service.py     # Chiroyli formatlangan hisobotlar va xabarlar
├── logs\
│   └── bot.log                 # D diskdagi to'liq tizim loglari
├── config.py                   # Sozlamalar va .env yuklovchi
├── main.py                     # Asosiy ishga tushirish fayli
├── test_system.py              # 7/7 avtomatlashtirilgan tekshiruv testi
├── requirements.txt            # Python kutubxonalari
├── .env.example                # Konfiguratsiya namunasi
├── .gitignore                  # Git uchun istisnolar
└── README.md                   # To'liq hujjat
```

---

## 📡 3. Telegram API imkoniyatlari va Sozlash talablari

### Telegram API texnik cheklovi:
Telegram Bot API xavfsizlik arxitekturasi tufayli botlar kanal yoki guruhlarning o'tmishdagi eski yozishmalarini (`getChatHistory`) to'g'ridan-to'g'ri so'rab ololmaydi. Bot qo'shilgan va ishga tushgan paytdan boshlab barcha xabarlarni real vaqt rejimida yozib boradi.

### Botni sozlash uchun zarur 3 ta qadam:

1. **Botni Kanalga Administrator qilish:**
   - Botni `@zerotohero_english` kanalingizga administrator qilib qo'shing.
   - Kamida **Postlarni ko'rish/boshqarish** huquqini bering.
2. **Botni Discussion Group (Guruh) ga qo'shish:**
   - Kanalga ulangan izohlar guruhiga ham ushbu yangi botni qo'shing.
   - **MUHIM:** Telegram `@BotFather` ga kiring:
     - `/mybots` -> Botingizni tanlang -> `Bot Settings` -> `Group Privacy` -> **Turn off** (Disable) qiling.
     - Yoki botni ushbu guruhga ham Administrator qiling.
     - *Nega bu kerak?* Privacy Mode o'chiq bo'lmasa, bot guruhdagi oddiy foydalanuvchilarning izohlarini ko'ra olmaydi.
3. **Oxirgi 2 kunlik tarixiy postlarni bir zumda import qilish (Bonus qulaylik):**
   - Botni endi ishga tushirganingizda 2 kun kutishingiz shart emas!
   - Kanal va guruhdagi oxirgi 2 kunlik post yoki izohlarni botning o'ziga shaxsiy yozishmada **Forward (Uzatish)** qiling.
   - Bot ularni avtomatik taniydi, sanasi va ID sini aniqlab bazaga kiritadi.

---

## 🚀 4. Windows 11 va VS Code orqali Ishga tushirish (Bosqichma-bosqich)

### 1-qadam: VS Code da ochish
1. **VS Code** dasturini oching.
2. Menyudan: **File** -> **Open Folder...** -> `D:\ZeroToHero_Analyzer` papkasini tanlang.

### 2-qadam: `.env` faylini to'ldirish
1. `D:\ZeroToHero_Analyzer\.env.example` faylidan nusxa olib, nomini `.env` ga o'zgartiring:
   ```powershell
   Copy-Item D:\ZeroToHero_Analyzer\.env.example D:\ZeroToHero_Analyzer\.env
   ```
2. `.env` faylini ochib, quyidagi ma'lumotlarni kiriting:
   ```env
   # @BotFather dan olingan yangi bot tokeni
   BOT_TOKEN=7123456789:AAH...

   # Google AI Studio dan olingan Gemini kaliti
   # Olish manzili: https://aistudio.google.com/app/apikey
   GEMINI_API_KEY=AIzaSy...

   # Model (default: gemini-2.5-flash)
   GEMINI_MODEL=gemini-2.5-flash

   # O'z Telegram ID raqamingiz (@userinfobot orqali bilib oling)
   ADMIN_IDS=123456789

   # Kanalingiz ID raqami yoki username
   CHANNEL_ID=-1001234567890

   # Kanalga ulangan Discussion Group ID raqami
   DISCUSSION_GROUP_ID=-1009876543210
   ```

### 3-qadam: VS Code da Python muhitini tanlash
1. VS Code da klaviaturadan `Ctrl + Shift + P` tugmalarini bosing.
2. Qidiruv qatoriga: `Python: Select Interpreter` deb yozing.
3. Ro'yxatdan quyidagi yo'lni tanlang (yoki **Enter interpreter path** orqali kiriting):
   `D:\ZeroToHero_Analyzer\.venv\Scripts\python.exe`

### 4-qadam: Tizim testini o'tkazish
Loyihada 7 ta avtomatlashtirilgan test mavjud. Terminalda quyidagi buyruqni bering:
```powershell
& "D:\ZeroToHero_Analyzer\.venv\Scripts\python.exe" D:\ZeroToHero_Analyzer\test_system.py
```
Natija: `ALL TESTS PASSED SUCCESSFULLY! (7/7)` chiqadi.

### 5-qadam: Botni ishga tushirish
VS Code terminalida quyidagi buyruqni bering:
```powershell
& "D:\ZeroToHero_Analyzer\.venv\Scripts\python.exe" D:\ZeroToHero_Analyzer\main.py
```
Terminalda bot muvaffaqiyatli ulanganligi haqida xabar chiqadi:
```
[INFO] Bot connected successfully as: @ZeroToHero_Analyzer_bot
[INFO] Bot is now listening for channel posts, discussion comments, and /analyze...
```

---

## 🤖 5. Telegram Buyruqlari (Faqat Administrator uchun)

| Buyruq | Tavsif |
| :--- | :--- |
| `/start` | Bot haqida ma'lumot, holati va qisqa qo'llanma. |
| `/analyze` | **Oxirgi 2 kunlik post va izohlarni Gemini AI orqali tahlil qilish va yangi mavzular olish.** |
| `/status` | Oxirgi 2 kunda nechta post va izoh to'plangani, baza hajmi va so'nggi faollik vaqti. |
| `/topics` | Oxirgi o'tkazilgan AI tahlilida tavsiya etilgan mavzular ro'yxatini qayta ko'rish. |
| `/cleanup` | 2 kundan eski ma'lumotlarni qo'lda darhol tozalash (har soatda avtomatik ham tozalanadi). |
| `/help` | To'liq qo'llanma va sozlash ko'rsatmalari. |

---

## 🔄 6. `/analyze` jarayoni qanday kechadi?

Administrator `/analyze` buyrug'ini yuborganida bot 4 bosqichli real-vaqt holatini ko'rsatadi:

1. ⏳ **[1/4] Ma'lumotlar tekshirilmoqda...** *(SQLite bazadan oxirgi 2 kunlik yozuvlar saralanadi)*
2. ⏳ **[2/4] Post va kommentlar tayyorlanmoqda...** *(Topilgan postlar va savollar AI uchun optimallashtiriladi)*
3. ⏳ **[3/4] Gemini AI tahlil qilmoqda...** *(Gemini 2.5 Flash tahlili)*
4. ✅ **[4/4] Mavzular tayyor!**

### AI Natijasi namunasi (Strikly faqat mavzular ro'yxati):

```markdown
**Zero to Hero English — Tavsiya etilgan mavzular**

1. Was / Were: O'tgan zamonda to be fe'lining ishlatilishi va amaliy mashqlar
2. Present Perfect vs Past Simple: Qachon qaysi birini ishlatish kerak?
3. 20 ta eng ko'p ishlatiladigan phrasal verbs (Look, Take, Get)
4. Modal Verbs — Must, Have to, Should: Majburiyat va maslahat farqlari
5. How to improve English listening? Yangi boshlovchilar uchun 5 ta oltin qoida
```

---

## 🧹 7. Ma'lumotlarni yig'ish chegarasi va Xotira tejamkorligi

- **2 kunlik chegara:** Baza faqat oxirgi 2 kunlik ma'lumotlarni saqlaydi.
- **Avtomatik tozalash:** `APScheduler` har soatda avtomatik ravishda 2 kundan eski post va izohlarni bazadan o'chiradi.
- **Deduplikatsiya:** Bir xil post yoki izoh bazaga qayta kiritilmaydi (`ON CONFLICT` himoyasi).
- **C disk daxlsizligi:** Hech qanday ma'lumot C diskka yozilmaydi. Barcha sqlite, kesh, log va virtual muhit fayllari strictly D: diskda saqlanadi.
