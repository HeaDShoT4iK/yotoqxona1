from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import STATUS_LABELS


def ticket_keyboard(ticket_id: int, disabled: bool = False):
    """disabled=True bo'lsa tugmalar olib tashlanadi (ticket allaqachon yopilgan)."""
    if disabled:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data=f"status:progress:{ticket_id}"),
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"status:done:{ticket_id}"),
        ],
        [
            InlineKeyboardButton(text="❌ Rad etildi", callback_data=f"status:rejected:{ticket_id}"),
        ],
    ])


def format_ticket_text(ticket_id: int, text: str, status: str, comment: str = "", handled_by_name: str = "") -> str:
    parts = [f"🆔 Ticket #{ticket_id}", f"📝 {text}", "", f"Holat: {STATUS_LABELS[status]}"]
    if handled_by_name:
        parts.append(f"👤 Bajardi: {handled_by_name}")
    if comment:
        parts.append(f"💬 Izoh: {comment}")
    return "\n".join(parts)


def main_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Xodimlar", callback_data="adm:staff")],
        [InlineKeyboardButton(text="💬 Guruh sozlamalari", callback_data="adm:group")],
        [InlineKeyboardButton(text="📢 Xabar tarqatish", callback_data="adm:broadcast")],
        [InlineKeyboardButton(text="🚫 Foydalanuvchilar", callback_data="adm:users")],
        [InlineKeyboardButton(text="📈 Statistika", callback_data="adm:stats")],
    ])


def _back_button(target: str = "adm:back"):
    return InlineKeyboardButton(text="⬅️ Orqaga", callback_data=target)


def staff_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="adm:staff:add")],
        [InlineKeyboardButton(text="➖ Adminni o'chirish", callback_data="adm:staff:remove")],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="adm:staff:list")],
        [_back_button()],
    ])


def group_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Guruhni belgilash", callback_data="adm:group:set")],
        [InlineKeyboardButton(text="ℹ️ Joriy guruh haqida", callback_data="adm:group:info")],
        [_back_button()],
    ])


def broadcast_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Yangi xabar yuborish", callback_data="adm:broadcast:new")],
        [InlineKeyboardButton(text="📊 Tarqatish tarixi", callback_data="adm:broadcast:history")],
        [_back_button()],
    ])


def users_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔒 Bloklash", callback_data="adm:users:block")],
        [InlineKeyboardButton(text="🔓 Blokdan chiqarish", callback_data="adm:users:unblock")],
        [InlineKeyboardButton(text="📋 Bloklanganlar ro'yxati", callback_data="adm:users:list")],
        [_back_button()],
    ])


def confirm_broadcast_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="adm:broadcast:confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:broadcast:cancel"),
        ],
    ])


def cancel_menu(target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_back_button(target)]])
