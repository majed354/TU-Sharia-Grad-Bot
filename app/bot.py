"""معالجات بوت تيليغرام"""

import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from app.config import get_settings
from app.rag.engine import get_engine
from app.escalation import (
    should_escalate_by_keywords,
    escalate_to_admin,
    notify_user_escalated,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ══════════════════════════════════════
#  أوامر البوت
# ══════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}! 👋\n\n"
        "أنا مساعد الدراسات العليا الذكي 🎓\n\n"
        "يمكنك سؤالي عن:\n"
        "• شروط القبول والتسجيل\n"
        "• المواعيد والجداول الزمنية\n"
        "• الرسوم والمنح الدراسية\n"
        "• البرامج والتخصصات المتاحة\n"
        "• أي استفسار آخر متعلق بالدراسات العليا\n\n"
        "💬 اكتب سؤالك مباشرة وسأبحث لك في قاعدة المعرفة.\n\n"
        "📨 إذا لم أستطع مساعدتك، سأحوّلك للمختص مباشرة.",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    await update.message.reply_text(
        "📋 <b>الأوامر المتاحة:</b>\n\n"
        "/start — بدء المحادثة\n"
        "/help — عرض المساعدة\n"
        "/human — طلب التحدث مع المختص\n"
        "/status — حالة البوت\n\n"
        "💡 أو اكتب سؤالك مباشرة!",
        parse_mode="HTML",
    )


async def cmd_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /human — طلب تواصل مع المشرف"""
    user = update.effective_user
    await escalate_to_admin(
        bot=context.bot,
        user_id=user.id,
        user_name=user.username,
        user_full_name=user.full_name,
        question="(طلب تواصل مباشر مع المختص)",
        reason="طلب صريح من المستخدم",
    )
    await notify_user_escalated(context.bot, update.effective_chat.id)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /status — حالة البوت"""
    engine = get_engine()
    count = engine.get_collection_count()
    await update.message.reply_text(
        "🤖 <b>حالة البوت:</b>\n\n"
        f"📚 المقاطع في قاعدة المعرفة: <b>{count}</b>\n"
        f"🧠 نموذج التوليد: <b>Kimi 2.5</b>\n"
        f"📐 نموذج الـ Embedding: <b>{settings.embedding_model}</b>\n"
        f"✅ البوت يعمل بشكل طبيعي",
        parse_mode="HTML",
    )


# ══════════════════════════════════════
#  أمر الرد من المشرف
# ══════════════════════════════════════

async def cmd_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /reply — رد المشرف على مستخدم"""
    if update.effective_user.id != settings.admin_chat_id:
        return  # فقط المشرف يمكنه استخدام هذا الأمر

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ الاستخدام:\n<code>/reply USER_ID رسالتك</code>",
            parse_mode="HTML",
        )
        return

    try:
        target_user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ معرّف المستخدم غير صحيح")
        return

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"💬 <b>رد من المختص:</b>\n\n{reply_text}",
            parse_mode="HTML",
        )
        await update.message.reply_text("✅ تم إرسال الرد بنجاح")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل الإرسال: {e}")


# ══════════════════════════════════════
#  معالجة الرسائل النصية (السؤال الرئيسي)
# ══════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أي رسالة نصية — القلب النابض للبوت"""
    user = update.effective_user
    message_text = update.message.text.strip()

    if not message_text:
        return

    logger.info(f"📩 سؤال من {user.full_name} ({user.id}): {message_text[:80]}")

    # --- 1. فحص التصعيد بالكلمات المفتاحية ---
    if should_escalate_by_keywords(message_text):
        await escalate_to_admin(
            bot=context.bot,
            user_id=user.id,
            user_name=user.username,
            user_full_name=user.full_name,
            question=message_text,
            reason="كلمة مفتاحية للتصعيد",
        )
        await notify_user_escalated(context.bot, update.effective_chat.id)
        return

    # --- 2. عرض مؤشر الكتابة ---
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    # --- 3. تشغيل RAG ---
    engine = get_engine()
    result = await engine.query(message_text)

    # --- 4. تقييم النتيجة ---
    if result.needs_escalation:
        # إرسال ما وُجد (إن وُجد) ثم تصعيد
        if result.answer and result.confidence == "medium":
            await update.message.reply_text(
                f"{result.answer}\n\n"
                "⚠️ <i>هذه الإجابة قد تكون غير مكتملة. "
                "سأحوّل سؤالك للمختص للتأكد.</i>",
                parse_mode="HTML",
            )

        await escalate_to_admin(
            bot=context.bot,
            user_id=user.id,
            user_name=user.username,
            user_full_name=user.full_name,
            question=message_text,
            context=result.answer if result.answer else "",
            reason=f"ثقة: {result.confidence} | أعلى تشابه: {max(result.similarity_scores) if result.similarity_scores else 0:.2f}",
        )
        await notify_user_escalated(context.bot, update.effective_chat.id)
    else:
        # إجابة واثقة — إرسال مباشر
        await update.message.reply_text(result.answer)

    logger.info(
        f"✅ رد على {user.full_name} | ثقة: {result.confidence} | "
        f"تصعيد: {result.needs_escalation}"
    )


# ══════════════════════════════════════
#  Callback للأزرار
# ══════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات الأزرار"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("resolved:"):
        user_id = data.split(":")[1]
        await query.edit_message_text(
            query.message.text + "\n\n✅ <b>تم الرد والإغلاق</b>",
            parse_mode="HTML",
        )
    elif data.startswith("note:"):
        user_id = data.split(":")[1]
        await query.edit_message_text(
            query.message.text + "\n\n📌 <b>تم التعليق — بانتظار المتابعة</b>",
            parse_mode="HTML",
        )


# ══════════════════════════════════════
#  بناء التطبيق
# ══════════════════════════════════════

def create_bot_app() -> Application:
    """إنشاء تطبيق البوت مع جميع المعالجات"""
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # أوامر
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("human", cmd_human))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("reply", cmd_reply))

    # أزرار
    app.add_handler(CallbackQueryHandler(handle_callback))

    # رسائل نصية (آخر شيء — catch-all)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app


async def set_bot_commands(app: Application):
    """تسجيل قائمة الأوامر في تيليغرام"""
    commands = [
        BotCommand("start", "بدء المحادثة"),
        BotCommand("help", "عرض المساعدة"),
        BotCommand("human", "التحدث مع المختص"),
        BotCommand("status", "حالة البوت"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("📋 تم تسجيل أوامر البوت")
