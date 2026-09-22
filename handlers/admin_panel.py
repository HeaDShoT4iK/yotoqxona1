"""
/admin — faqat shaxsiy chatda, faqat super admin uchun tugmali boshqaruv paneli.
"""
import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
import keyboards as kb
from states import StaffStates, BroadcastStates, BlockStates
from utils import STATUS_LABELS

router = Router()


async def _is_super(telegram_id: int) -> bool:
    return await db.is_super_admin(telegram_id)


# ---------------- ENTRY / MAIN MENU ----------------

@router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return
    if not await _is_super(message.from_user.id):
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return
    await state.clear()
    await message.answer("🛠 Admin panel", reply_markup=kb.main_admin_menu())


@router.callback_query(F.data == "adm:back")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 Admin panel", reply_markup=kb.main_admin_menu())
    await callback.answer()


# ---------------- STAFF ----------------

@router.callback_query(F.data == "adm:staff")
async def staff_menu(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text("👥 Xodimlar bo'limi", reply_markup=kb.staff_menu())
    await callback.answer()


@router.callback_query(F.data == "adm:staff:add")
async def ask_new_admin(callback: CallbackQuery, state: FSMContext):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "Yangi adminning xabarini forward qiling yoki Telegram ID raqamini yuboring:",
        reply_markup=kb.cancel_menu("adm:staff"),
    )
    await state.set_state(StaffStates.waiting_new_admin)
    await callback.answer()


@router.message(StaffStates.waiting_new_admin, F.chat.type == "private")
async def save_new_admin(message: Message, state: FSMContext):
    if not await _is_super(message.from_user.id):
        await state.clear()
        return

    new_id = None
    name = "Noma'lum"
    if message.forward_from:
        new_id = message.forward_from.id
        name = message.forward_from.full_name
    elif message.text and message.text.strip().lstrip("-").isdigit():
        new_id = int(message.text.strip())
    else:
        await message.answer(
            "⚠️ Noto'g'ri format. Telegram ID raqam bo'lishi yoki xabar forward qilinishi kerak."
        )
        return

    await db.add_staff(new_id, name, "admin", added_by=message.from_user.id)
    await message.answer(f"✅ Admin qo'shildi: {name} ({new_id})", reply_markup=kb.main_admin_menu())
    await state.clear()


@router.callback_query(F.data == "adm:staff:remove")
async def ask_remove_admin(callback: CallbackQuery, state: FSMContext):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "O'chirmoqchi bo'lgan adminning Telegram ID raqamini yuboring:",
        reply_markup=kb.cancel_menu("adm:staff"),
    )
    await state.set_state(StaffStates.waiting_remove_admin)
    await callback.answer()


@router.message(StaffStates.waiting_remove_admin, F.chat.type == "private")
async def remove_admin(message: Message, state: FSMContext):
    if not await _is_super(message.from_user.id):
        await state.clear()
        return
    if not (message.text and message.text.strip().lstrip("-").isdigit()):
        await message.answer("⚠️ Telegram ID raqam bo'lishi kerak.")
        return
    target_id = int(message.text.strip())
    ok = await db.deactivate_staff(target_id)
    if ok:
        await message.answer(f"✅ Admin ({target_id}) o'chirildi.", reply_markup=kb.main_admin_menu())
    else:
        await message.answer(
            "⚠️ Bunday admin topilmadi yoki u super admin (o'chirib bo'lmaydi).",
            reply_markup=kb.main_admin_menu(),
        )
    await state.clear()


@router.callback_query(F.data == "adm:staff:list")
async def list_admins(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    staff = await db.list_staff()
    if not staff:
        text = "Adminlar mavjud emas."
    else:
        lines = ["👥 Adminlar ro'yxati:\n"]
        for s in staff:
            role = "👑 Super admin" if s["role"] == "super_admin" else "🛡 Admin"
            lines.append(f"• {s['full_name']} ({s['telegram_id']}) — {role}")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=kb.staff_menu())
    await callback.answer()


# ---------------- GROUP SETTINGS ----------------

@router.callback_query(F.data == "adm:group")
async def group_menu_handler(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text("💬 Guruh sozlamalari", reply_markup=kb.group_menu())
    await callback.answer()


@router.callback_query(F.data == "adm:group:set")
async def ask_group_set(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "Botni kerakli guruhga admin sifatida qo'shing, so'ng o'sha guruhning ichida "
        "/set_group buyrug'ini yozing.",
        reply_markup=kb.group_menu(),
    )
    await callback.answer()


@router.message(Command("set_group"), F.chat.type.in_({"group", "supergroup"}))
async def set_group_cmd(message: Message):
    if not await _is_super(message.from_user.id):
        await message.reply("⛔ Sizda ruxsat yo'q.")
        return
    await db.set_setting("target_group_id", str(message.chat.id))
    await message.reply(f"✅ Shu guruh («{message.chat.title}») murojaatlar guruhi sifatida belgilandi.")


@router.callback_query(F.data == "adm:group:info")
async def group_info(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    group_id = await db.get_setting("target_group_id")
    text = f"Joriy guruh ID: {group_id}" if group_id else "⚠️ Guruh hali belgilanmagan."
    await callback.message.edit_text(text, reply_markup=kb.group_menu())
    await callback.answer()


# ---------------- BROADCAST ----------------

@router.callback_query(F.data == "adm:broadcast")
async def broadcast_menu_handler(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text("📢 Xabar tarqatish", reply_markup=kb.broadcast_menu())
    await callback.answer()


@router.callback_query(F.data == "adm:broadcast:new")
async def ask_broadcast_text(callback: CallbackQuery, state: FSMContext):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "Tarqatmoqchi bo'lgan xabar matnini yuboring:",
        reply_markup=kb.cancel_menu("adm:broadcast"),
    )
    await state.set_state(BroadcastStates.waiting_text)
    await callback.answer()


@router.message(BroadcastStates.waiting_text, F.chat.type == "private")
async def preview_broadcast(message: Message, state: FSMContext):
    if not await _is_super(message.from_user.id):
        await state.clear()
        return
    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastStates.waiting_confirm)
    await message.answer(
        f"Quyidagi xabar barcha foydalanuvchilarga yuboriladi:\n\n{message.text}",
        reply_markup=kb.confirm_broadcast_menu(),
    )


@router.callback_query(BroadcastStates.waiting_confirm, F.data == "adm:broadcast:confirm")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await callback.message.edit_text("⏳ Xabar tarqatilmoqda...")

    user_ids = await db.get_all_user_telegram_ids()
    sent = 0
    for uid in user_ids:
        try:
            await callback.bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
        # Telegram flood-limitidan saqlanish uchun sekinlashtirish
        await asyncio.sleep(0.05)

    await db.log_broadcast(text, callback.from_user.id, sent)
    await callback.message.edit_text(
        f"✅ Xabar {sent}/{len(user_ids)} foydalanuvchiga yuborildi.",
        reply_markup=kb.main_admin_menu(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "adm:broadcast:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.", reply_markup=kb.broadcast_menu())
    await callback.answer()


@router.callback_query(F.data == "adm:broadcast:history")
async def broadcast_history(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    items = await db.list_broadcasts()
    if not items:
        text = "Tarqatishlar tarixi bo'sh."
    else:
        lines = ["📊 Oxirgi tarqatishlar:\n"]
        for b in items:
            preview = (b["text"] or "")[:40]
            lines.append(f"#{b['id']} — {b['total_sent']} ta — {preview}...")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=kb.broadcast_menu())
    await callback.answer()


# ---------------- USERS (BLOCK/UNBLOCK) ----------------

@router.callback_query(F.data == "adm:users")
async def users_menu_handler(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text("🚫 Foydalanuvchilar", reply_markup=kb.users_menu())
    await callback.answer()


@router.callback_query(F.data == "adm:users:block")
async def ask_block(callback: CallbackQuery, state: FSMContext):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "Bloklamoqchi bo'lgan foydalanuvchining anonim kodini yuboring (masalan T-8F2A1):",
        reply_markup=kb.cancel_menu("adm:users"),
    )
    await state.set_state(BlockStates.waiting_block_code)
    await callback.answer()


@router.message(BlockStates.waiting_block_code, F.chat.type == "private")
async def do_block(message: Message, state: FSMContext):
    if not await _is_super(message.from_user.id):
        await state.clear()
        return
    code = (message.text or "").strip().upper()
    ok = await db.set_user_blocked(code, True)
    if ok:
        await message.answer(f"✅ {code} bloklandi.", reply_markup=kb.main_admin_menu())
    else:
        await message.answer("⚠️ Bunday kod topilmadi.", reply_markup=kb.main_admin_menu())
    await state.clear()


@router.callback_query(F.data == "adm:users:unblock")
async def ask_unblock(callback: CallbackQuery, state: FSMContext):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    await callback.message.edit_text(
        "Blokdan chiqarmoqchi bo'lgan foydalanuvchining anonim kodini yuboring:",
        reply_markup=kb.cancel_menu("adm:users"),
    )
    await state.set_state(BlockStates.waiting_unblock_code)
    await callback.answer()


@router.message(BlockStates.waiting_unblock_code, F.chat.type == "private")
async def do_unblock(message: Message, state: FSMContext):
    if not await _is_super(message.from_user.id):
        await state.clear()
        return
    code = (message.text or "").strip().upper()
    ok = await db.set_user_blocked(code, False)
    if ok:
        await message.answer(f"✅ {code} blokdan chiqarildi.", reply_markup=kb.main_admin_menu())
    else:
        await message.answer("⚠️ Bunday kod topilmadi.", reply_markup=kb.main_admin_menu())
    await state.clear()


@router.callback_query(F.data == "adm:users:list")
async def list_blocked(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    blocked = await db.list_blocked_users()
    if not blocked:
        text = "Bloklangan foydalanuvchilar yo'q."
    else:
        lines = ["📋 Bloklanganlar:\n"] + [f"• {u['anon_code']}" for u in blocked]
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=kb.users_menu())
    await callback.answer()


# ---------------- STATS ----------------

@router.callback_query(F.data == "adm:stats")
async def stats(callback: CallbackQuery):
    if not await _is_super(callback.from_user.id):
        return await callback.answer("⛔ Ruxsat yo'q", show_alert=True)
    s = await db.get_stats()
    lines = ["📈 Statistika:\n", f"Jami murojaatlar: {s.get('jami', 0)}"]
    for key, label in STATUS_LABELS.items():
        lines.append(f"{label}: {s.get(key, 0)}")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.main_admin_menu())
    await callback.answer()
