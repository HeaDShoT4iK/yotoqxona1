# Anonim Shikoyatlar Boti

Talabalar anonim tarzda muammo/shikoyat yuboradigan, xodimlar (adminlar) guruhda
tugmalar orqali javob beradigan Telegram bot. PostgreSQL yoki Redis talab qilinmaydi —
hammasi bitta SQLite fayl (`bot.db`) va xotirada (in-memory) FSM orqali ishlaydi.

## Imkoniyatlari

- Talaba botga shaxsiy (DM) yozadi → xabar avtomatik anonim `Ticket` sifatida guruhga yuboriladi
- Guruhdagi xodim tugma bosadi (⏳ Jarayonda / ✅ Bajarildi / ❌ Rad etildi) → izoh yozadi
- Izoh yozilgach guruhdagi xabar yangilanadi va talabaga shaxsiy javob (anonim) yuboriladi
- Bir nechta xodim bir vaqtning o'zida, bir-biriga xalaqit bermay turli ticketlar bilan ishlashi mumkin
- `/admin` — faqat shaxsiy chatda, faqat super adminga ochiladigan tugmali boshqaruv paneli:
  - Xodimlar: qo'shish / o'chirish / ro'yxat
  - Guruh sozlamalari: qaysi guruhga ticketlar yuborilishini belgilash
  - Xabar tarqatish (broadcast): barcha foydalanuvchilarga xabar, flood-limitdan himoyalangan
  - Foydalanuvchilarni bloklash / blokdan chiqarish / ro'yxat
  - Statistika: ticketlar soni statuslar bo'yicha

## O'rnatish

1. Python 3.11+ o'rnatilgan bo'lishi kerak.
2. Loyihani oching va kerakli paketlarni o'rnating:

   ```bash
   pip install -r requirements.txt
   ```

3. `.env` faylidan nusxa olib `.env` yarating:

   ```bash
   cp .env .env
   ```

4. `.env` faylini to'ldiring:
   - `BOT_TOKEN` — @BotFather'dan olingan token
   - `SUPER_ADMIN_ID` — sizning (yoki bosh administratorning) Telegram ID raqamingiz
     (ID'ni bilish uchun @userinfobot ga yozing)

5. Botni ishga tushiring:

   ```bash
   python main.py
   ```

## Guruhni ulash

1. Botni kerakli guruhga **admin** sifatida qo'shing (xabarlarni o'chira olishi,
   xabar yubora olishi kerak).
2. O'sha guruhda super admin nomidan `/set_group` buyrug'ini yozing — shundan
   so'ng barcha yangi ticketlar shu guruhga tushadi.

## Xodim (admin) qo'shish

1. Botga shaxsiy yozib `/admin` buyrug'ini bering (faqat super admin uchun ishlaydi).
2. **👥 Xodimlar → ➕ Admin qo'shish** tugmasini bosing.
3. Yangi xodimning biror xabarini forward qiling yoki uning Telegram ID raqamini yuboring.

## Ishlash tartibi (flow)

```
Talaba (DM) → bot → Ticket yaratiladi → Guruhga tugmali xabar yuboriladi
Xodim tugma bosadi → bot izoh so'raydi → xodim izoh yozadi
   → guruhdagi xabar yangilanadi (status + izoh + kim bajardi)
   → talabaga shaxsiy javob yuboriladi (anonim)
```

## Loyihaning fayl strukturasi

```
anon-complaints-bot/
├── main.py                  # botni ishga tushirish
├── db.py                    # SQLite bilan ishlash (aiosqlite)
├── config.py                # BOT_TOKEN, SUPER_ADMIN_ID va h.k.
├── states.py                # barcha FSM state'lar
├── keyboards.py              # barcha inline tugmalar va matn formatlash
├── utils.py                  # anonim kod generatsiyasi, status nomlari
├── handlers/
│   ├── user.py                # talaba oqimi (DM orqali ticket yaratish)
│   ├── group.py                # guruhdagi tugmalar, status/izoh
│   └── admin_panel.py           # /admin paneli (super admin)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Kengaytirish bo'yicha eslatmalar

- Hozircha FSM holatlari `MemoryStorage`da saqlanadi — bot qayta ishga tushsa,
  "izoh kutilayotgan" holatlar tozalanadi. Agar bot bir nechta serverga
  tarqatilsa (scaling) yoki qayta ishga tushishlarda holat saqlanishi kerak
  bo'lsa, `main.py` ichida `RedisStorage`ga o'ting (kod ichida izoh qoldirilgan).
- Foydalanuvchilar soni juda katta bo'lib, SQLite yozish tezligi yetmay qolsa,
  `db.py`dagi funksiyalarni PostgreSQL + `asyncpg`/`SQLAlchemy`ga ko'chirish mumkin —
  funksiyalarning imzosi (signature) o'zgarmaydi, faqat ichki implementatsiya almashadi.
- Broadcast funksiyasida har xabardan keyin `asyncio.sleep(0.05)` qo'yilgan —
  bu Telegramning soniyasiga ~30 xabar limitidan saqlaydi.
