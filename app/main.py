"""نقطة الدخول الرئيسية — FastAPI + Telegram Webhook"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from telegram import Update
from app.config import get_settings
from app.bot import create_bot_app, set_bot_commands
from app.rag.engine import get_engine

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# تطبيق البوت (Telegram)
bot_app = create_bot_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """أحداث بدء وإيقاف الخادم"""
    # --- بدء التشغيل ---
    logger.info("🚀 جارٍ تشغيل الخادم...")

    # تهيئة البوت
    await bot_app.initialize()
    await bot_app.start()

    # تسجيل أوامر البوت
    await set_bot_commands(bot_app)

    # تهيئة محرك RAG
    engine = get_engine()
    count = engine.get_collection_count()
    logger.info(f"📚 قاعدة المعرفة: {count} مقطع")

    # ربط Webhook
    if settings.webhook_url:
        await bot_app.bot.set_webhook(
            url=settings.webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
        logger.info(f"🔗 Webhook: {settings.webhook_url}")
    else:
        logger.warning("⚠️ WEBHOOK_URL غير محدد — اضبطه في .env")

    logger.info("✅ الخادم جاهز!")

    yield

    # --- إيقاف التشغيل ---
    logger.info("🛑 جارٍ إيقاف الخادم...")
    engine = get_engine()
    await engine.close()
    await bot_app.stop()
    await bot_app.shutdown()


# تطبيق FastAPI
app = FastAPI(
    title="مساعد الدراسات العليا",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    """استقبال تحديثات تيليغرام"""
    try:
        data = await request.json()
        update = Update.de_json(data=data, bot=bot_app.bot)
        await bot_app.process_update(update)
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة التحديث: {e}")
    return Response(status_code=200)


@app.get("/health")
async def health_check():
    """فحص صحة الخادم"""
    engine = get_engine()
    return {
        "status": "ok",
        "knowledge_base_chunks": engine.get_collection_count(),
        "model": settings.openrouter_model,
    }


@app.get("/")
async def root():
    return {"message": "🎓 مساعد الدراسات العليا يعمل"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
    )
