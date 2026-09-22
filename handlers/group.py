"""
Guruhdagi xodimlar (admin/super admin) oqimi:
- ticket ostidagi tugmani bosadi (Jarayonda / Bajarildi / Rad etildi)
- bot izoh so'raydi (shu admin uchun alohida FSM holat)
- izoh kelgach: guruhdagi xabar yangilanadi va talabaga DM orqali javob yuboriladi

Muhim: aiogram'da FSM holati sukut bo'yicha (chat_id, user_id) bo'yicha ajratiladi,
shuning uchun bitta guruhda bir nechta admin bir vaqtda turli ticketlar ustida
bir-biriga xalaqit bermay ishlay oladi.
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
import keyboards as kb
from states import CommentStates
from utils import STATUS_LABELS

router = Router()

STATUS_MAP = {
    "progress": "jarayonda",
    "done": "bajarildi",
    "rejected": "rad_etildi",
}


@router.callback_query(F.data.startswith("status:"))
async def on_status_click(callback: CallbackQuery, state: FSMContext):
    staff = await db.get_staff(callback.from_user.id)
    if not staff:
        await callback.answer("⛔ Sizda ruxsat yo'q", show_alert=True)
        return

    _, status_key, ticket_id_str = callback.data.split(":")
    ticket_id = int(ticket_id_str)
    status = STATUS_MAP.get(status_key)
    if not status:
        await callback.answer()
        return

    await state.update_data(ticket_id=ticket_id, status=status)
    await state.set_state(CommentStates.waiting_comment)

    await callback.message.reply(
        f"✍️ Ticket #{ticket_id} uchun izohingizni shu xabarga javob tarzida yozing:"
    )
    await callback.answer()


@router.message(CommentStates.waiting_comment, F.chat.type.in_({"group", "supergroup"}))
async def on_comment_received(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    status = data.get("status")
    if not ticket_id or not status:
        await state.clear()
        return

    staff = await db.get_staff(message.from_user.id)
    if not staff:
        await state.clear()
        return

    comment = message.text or ""
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await state.clear()
        return

    await db.update_ticket_status(ticket_id, status, staff["id"], comment)

    if ticket["group_message_id"]:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=ticket["group_message_id"],
                text=kb.format_ticket_text(
                    ticket_id, ticket["text"], status, comment, staff["full_name"]
                ),
                reply_markup=kb.ticket_keyboard(ticket_id, disabled=(status != "jarayonda")),
            )
        except Exception:
            pass

    await message.reply(f"✅ Ticket #{ticket_id} yangilandi: {STATUS_LABELS[status]}")

    user_row = await db.get_user_by_id(ticket["user_id"])
    if user_row:
        try:
            await message.bot.send_message(
                user_row["telegram_id"],
                "📩 Sizning murojaatingiz bo'yicha javob:\n\n"
                f"Holat: {STATUS_LABELS[status]}\n"
                f"Izoh: {comment}",
            )
        except Exception:
            pass

    await state.clear()
