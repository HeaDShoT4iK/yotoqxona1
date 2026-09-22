"""
Talaba (oddiy foydalanuvchi) oqimi:
- /start bosadi
- shaxsiy chatga (DM) muammo matnini yozadi
- bot uni bazaga saqlaydi va guruhga (tugmalar bilan) yuboradi
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message

import db
import keyboards as kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type != "private":
        return
    user = await db.get_or_create_user(message.from_user.id)
    if user["is_blocked"]:
        await message.answer("⛔ Siz botdan foydalanish huquqidan mahrum qilingansiz.")
        return
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "Bu bot orqali muammoingizni anonim tarzda ma'muriyatga yetkazishingiz mumkin.\n"
        "Xabaringizni shunchaki yozib yuboring."
    )


@router.message(
    F.chat.type == "private",
    StateFilter(default_state),
    F.text,
    ~F.text.startswith("/"),
)
async def receive_ticket(message: Message):
    user = await db.get_or_create_user(message.from_user.id)
    if user["is_blocked"]:
        await message.answer("⛔ Siz botdan foydalanish huquqidan mahrum qilingansiz.")
        return

    group_id = await db.get_setting("target_group_id")
    if not group_id:
        await message.answer(
            "⚠️ Hozircha bot ma'muriyat tomonidan sozlanmagan. Birozdan so'ng qayta urinib ko'ring."
        )
        return

    ticket_id = await db.create_ticket(user["id"], message.text)

    sent = await message.bot.send_message(
        int(group_id),
        kb.format_ticket_text(ticket_id, message.text, "yangi"),
        reply_markup=kb.ticket_keyboard(ticket_id),
    )
    await db.set_ticket_group_message(ticket_id, sent.message_id)

    await message.answer(
        "✅ Xabaringiz qabul qilindi va anonim tarzda yuborildi.\n"
        "Javob shu yerga (shaxsiy chatga) keladi."
    )
