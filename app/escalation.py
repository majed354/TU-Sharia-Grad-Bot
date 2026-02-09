"""نظام التصعيد — إرسال الأسئلة غير المُجابة للمشرف"""

import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# كلمات تفعّل التصعيد الفوري
ESCALATION_KEYWORDS = [
    "أريد التحدث مع شخص",
    "تحدث مع إنسان",
    "أريد مساعدة بشرية",
    "لم أفهم",
    "مو واضح",
    "ما فهمت",
    "مسؤول",
    "إداري",
    "تواصل مع",
    "رقم هاتف",
    "رقم الجوال",
    "أريد الاتصال",
]


def should_escalate_by_keywords(message: str) -> bool:
    """فحص إذا كانت الرسالة تحتوي على طلب تصعيد صريح"""
    message_lower = message.strip()
    return any(kw in message_lower for kw in ESCALATION_KEYWORDS)


async def escalate_to_admin(
    bot: Bot,
    user_id: int,
    user_name: str,
    user_full_name: str,
    question: str,
    context: str = "",
    reason: str = "ثقة منخفضة في الإجابة",
):
    """إرسال إشعار تصعيد للمشرف"""

    message = (
        "🔔 <b>تصعيد جديد</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"👤 <b>المستخدم:</b> {user_full_name}\n"
        f"🆔 <b>المعرّف:</b> @{user_name or 'بدون'} (<code>{user_id}</code>)\n"
        f"📝 <b>السبب:</b> {reason}\n"
        "━━━━━━━━━━━━━━━\n"
        f"❓ <b>السؤال:</b>\n{question}\n"
    )

    if context:
        # اقتصار السياق على 500 حرف
        short_ctx = context[:500] + "..." if len(context) > 500 else context
        message += f"\n📋 <b>سياق إضافي:</b>\n<i>{short_ctx}</i>\n"

    message += (
        "\n━━━━━━━━━━━━━━━\n"
        "💡 للرد على المستخدم، استخدم الأمر:\n"
        f"<code>/reply {user_id} رسالتك هنا</code>"
    )

    # أزرار سريعة
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تم الرد", callback_data=f"resolved:{user_id}"),
            InlineKeyboardButton("📌 تعليق", callback_data=f"note:{user_id}"),
        ]
    ])

    try:
        await bot.send_message(
            chat_id=settings.admin_chat_id,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        logger.info(f"📤 تم تصعيد سؤال من {user_full_name} ({user_id}) للمشرف")
        return True
    except Exception as e:
        logger.error(f"❌ فشل إرسال التصعيد: {e}")
        return False


async def notify_user_escalated(bot: Bot, chat_id: int):
    """إبلاغ المستخدم أن سؤاله تم تحويله"""
    message = (
        "📨 تم تحويل سؤالك إلى المختص.\n"
        "سيتم الرد عليك في أقرب وقت إن شاء الله.\n\n"
        "يمكنك الاستمرار في طرح أسئلة أخرى في الأثناء."
    )
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logger.error(f"❌ فشل إبلاغ المستخدم: {e}")
