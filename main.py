import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import db
from config import BOT_TOKEN, SUPER_ADMIN_ID
from handlers import admin_panel, group, user

logging.basicConfig(level=logging.INFO)


async def main():
    await db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Eslatma: bot bir nechta instansiyada (scaling) ishlashi kerak bo'lsa yoki
    # qayta ishga tushganda FSM holatlari saqlanishi kerak bo'lsa, MemoryStorage
    # o'rniga RedisStorage ishlating:
    #   from aiogram.fsm.storage.redis import RedisStorage
    #   storage = RedisStorage.from_url("redis://localhost:6379/0")
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin_panel.router)
    dp.include_router(group.router)
    dp.include_router(user.router)

    if SUPER_ADMIN_ID:
        try:
            chat = await bot.get_chat(SUPER_ADMIN_ID)
            await db.ensure_super_admin(SUPER_ADMIN_ID, chat.full_name or "Super Admin")
            logging.info(f"Super admin bootstrap qilindi: {SUPER_ADMIN_ID}")
        except Exception as e:
            logging.warning(
                f"Super adminni avtomatik qo'shib bo'lmadi ({e}). "
                "Botga /start bosgandan so'ng birinchi bo'lib ishga tushiring."
            )

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot ishga tushdi (polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
