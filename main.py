import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import db
from config import BOT_TOKEN, SUPER_ADMIN_ID
from handlers import admin_panel, group, user

logging.basicConfig(level=logging.INFO)


async def handle(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    logging.info(f"🌐 Web server started on port {port}")


async def self_ping_task():
    url = (
        os.environ.get("RENDER_EXTERNAL_URL")
        or os.environ.get("SELF_URL")
    )

    if not url:
        logging.warning(
            "⚠️ Self-ping o'chirilgan: "
            "RENDER_EXTERNAL_URL yoki SELF_URL topilmadi."
        )
        return

    import aiohttp

    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(600)

            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    logging.info(
                        f"🔄 Self-ping: {resp.status}"
                    )

            except Exception as e:
                logging.warning(
                    f"⚠️ Self-ping xatosi: {e}"
                )


async def main():
    await db.init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    dp.include_router(admin_panel.router)
    dp.include_router(group.router)
    dp.include_router(user.router)

    if SUPER_ADMIN_ID:
        try:
            chat = await bot.get_chat(SUPER_ADMIN_ID)
            await db.ensure_super_admin(
                SUPER_ADMIN_ID,
                chat.full_name or "Super Admin"
            )
            logging.info(
                f"Super admin bootstrap qilindi: {SUPER_ADMIN_ID}"
            )
        except Exception as e:
            logging.warning(
                f"Super adminni avtomatik qo'shib bo'lmadi ({e}). "
                "Botga /start bosgandan so'ng birinchi bo'lib ishga tushiring."
            )

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    asyncio.create_task(
        start_web_server()
    )

    asyncio.create_task(
        self_ping_task()
    )

    logging.info("Bot ishga tushdi (polling)...")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
