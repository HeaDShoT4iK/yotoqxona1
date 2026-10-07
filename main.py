```python
import asyncio
import logging
import os

from aiohttp import web, ClientSession, ClientTimeout

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import db
from config import BOT_TOKEN, SUPER_ADMIN_ID
from handlers import admin_panel, group, user


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# WEB SERVER
# =========================================================

async def handle(request: web.Request):
    return web.Response(
        text="Bot is running!"
    )


async def health(request: web.Request):
    return web.Response(
        text="OK"
    )


async def start_web_server():
    app = web.Application()

    # Asosiy URL
    app.router.add_get(
        "/",
        handle
    )

    # Health check
    app.router.add_get(
        "/health",
        health
    )

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    logger.info(
        f"🌐 Web server ishga tushdi: 0.0.0.0:{port}"
    )


# =========================================================
# SELF PING
# =========================================================

async def self_ping_task():

    # Render avtomatik bergan URL
    # yoki qo'lda berilgan SELF_URL
    base_url = (
        os.environ.get("RENDER_EXTERNAL_URL")
        or os.environ.get("SELF_URL")
    )

    if not base_url:

        logger.warning(
            "⚠️ Self-ping o'chirilgan."
        )

        logger.warning(
            "RENDER_EXTERNAL_URL yoki "
            "SELF_URL topilmadi."
        )

        return

    # URL oxiridagi / belgini olib tashlaymiz
    base_url = base_url.rstrip("/")

    # Health endpoint
    url = f"{base_url}/health"

    logger.info(
        f"🔄 Self-ping URL: {url}"
    )

    # Web server ishga tushishi uchun kutamiz
    await asyncio.sleep(30)

    timeout = ClientTimeout(
        total=15
    )

    async with ClientSession(
        timeout=timeout
    ) as session:

        while True:

            try:

                async with session.get(
                    url
                ) as response:

                    logger.info(
                        f"🔄 Self-ping: "
                        f"HTTP {response.status}"
                    )

            except asyncio.CancelledError:

                logger.info(
                    "🛑 Self-ping task to'xtatildi."
                )

                raise

            except Exception as e:

                logger.warning(
                    f"⚠️ Self-ping xatosi: {e}"
                )

            # 5 daqiqada bir
            await asyncio.sleep(300)


# =========================================================
# MAIN
# =========================================================

async def main():

    logger.info(
        "🚀 Bot ishga tushmoqda..."
    )

    # =====================================================
    # DATABASE
    # =====================================================

    logger.info(
        "🗄️ Database ishga tushirilmoqda..."
    )

    await db.init_db()

    logger.info(
        "✅ Database tayyor."
    )

    # =====================================================
    # BOT
    # =====================================================

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    # =====================================================
    # DISPATCHER
    # =====================================================

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    # =====================================================
    # ROUTERS
    # =====================================================

    dp.include_router(
        admin_panel.router
    )

    dp.include_router(
        group.router
    )

    dp.include_router(
        user.router
    )

    logger.info(
        "✅ Barcha routerlar yuklandi."
    )

    # =====================================================
    # SUPER ADMIN
    # =====================================================

    if SUPER_ADMIN_ID:

        try:

            chat = await bot.get_chat(
                SUPER_ADMIN_ID
            )

            await db.ensure_super_admin(
                SUPER_ADMIN_ID,
                chat.full_name or "Super Admin"
            )

            logger.info(
                f"✅ Super admin bootstrap qilindi: "
                f"{SUPER_ADMIN_ID}"
            )

        except Exception as e:

            logger.warning(
                f"⚠️ Super adminni avtomatik "
                f"qo'shib bo'lmadi: {e}"
            )

            logger.warning(
                "Botga /start yuborib ko'ring."
            )

    else:

        logger.warning(
            "⚠️ SUPER_ADMIN_ID belgilanmagan."
        )

    # =====================================================
    # WEBHOOK
    # =====================================================

    try:

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        logger.info(
            "✅ Telegram webhook o'chirildi."
        )

    except Exception as e:

        logger.warning(
            f"⚠️ Webhookni o'chirishda xato: {e}"
        )

    # =====================================================
    # WEB SERVER TASK
    # =====================================================

    web_task = asyncio.create_task(
        start_web_server()
    )

    # =====================================================
    # SELF PING TASK
    # =====================================================

    ping_task = asyncio.create_task(
        self_ping_task()
    )

    # =====================================================
    # BOT POLLING
    # =====================================================

    logger.info(
        "🤖 Bot ishga tushdi (polling)..."
    )

    try:

        await dp.start_polling(
            bot
        )

    except Exception as e:

        logger.exception(
            f"❌ Bot ishlashida xato: {e}"
        )

    finally:

        logger.info(
            "🛑 Bot to'xtatilmoqda..."
        )

        # Self-ping taskni to'xtatish
        ping_task.cancel()

        # Web server taskni to'xtatish
        web_task.cancel()

        try:
            await ping_task
        except asyncio.CancelledError:
            pass

        try:
            await web_task
        except asyncio.CancelledError:
            pass

        # Bot sessionni yopish
        await bot.session.close()

        logger.info(
            "✅ Bot to'xtatildi."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "🛑 Dastur foydalanuvchi tomonidan to'xtatildi."
        )
```
