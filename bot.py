import os
from datetime import datetime

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# =========================
# الإعدادات
# =========================
BOT_TOKEN = "8211007927:AAHF_G-z95bcMpF5QSeklVsa2eJ3jKhvo80"
ADMIN_CHAT_ID = 1498115119
NETWORK_NAME = "VR Network"
PAYMENT_INFO = (
    "بنك فلسطين\n"
    "الاسم: محمد يوسف ابو معمر\n"
    "IBAN: PS44PALS044817049130993000000\n"
    "أرسل إشعار التحويل داخل المحادثة بعد الدفع."
)
# =========================
# الحالات
# =========================
(
    MAIN_MENU,
    FAULT_NAME,
    FAULT_AREA,
    FAULT_ROUTER,
    FAULT_DETAILS,
    CARD_RULES,
    CARD_NAME,
    CARD_AREA,
    CARD_TYPE,
    CARD_QTY,
    CARD_DELIVERY,
    CARD_RECEIPT,
) = range(12)

# =========================
# الأزرار
# =========================
main_keyboard = ReplyKeyboardMarkup(
    [
        ["🔧 تقديم شكوى أو عطل", "💳 طلب بطاقات"],
        ["ℹ️ معلومات البطاقات", "📌 شروط الطلب"],
        ["🏠 القائمة الرئيسية"],
    ],
    resize_keyboard=True,
)

rules_keyboard = ReplyKeyboardMarkup(
    [["✅ أوافق على الشروط", "❌ إلغاء"]],
    resize_keyboard=True,
)

card_type_keyboard = ReplyKeyboardMarkup(
    [
        ["1 شيكل - 8 ساعات - 2 ميجا"],
        ["2 شيكل - 10 ساعات - 3 ميجا"],
        ["❌ إلغاء"],
    ],
    resize_keyboard=True,
)

delivery_keyboard = ReplyKeyboardMarkup(
    [
        ["📄 ملف", "🖼 صورة"],
        ["❌ إلغاء"],
    ],
    resize_keyboard=True,
)

cancel_keyboard = ReplyKeyboardMarkup(
    [["❌ إلغاء"]],
    resize_keyboard=True,
)

# =========================
# أدوات مساعدة
# =========================
def is_order_time() -> bool:
    now = datetime.now()
    return 8 <= now.hour < 17


def get_card_summary(choice: str) -> str:
    if choice == "1 شيكل - 8 ساعات - 2 ميجا":
        return "1 شيكل | 8 ساعات | 2 ميجا"
    if choice == "2 شيكل - 10 ساعات - 3 ميجا":
        return "2 شيكل | 10 ساعات | 3 ميجا"
    return choice


async def send_to_admin_and_map(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user_id: int,
    text: str = None,
    photo_file_id: str = None,
    document_file_id: str = None,
    caption: str = None,
):
    """
    يرسل الرسالة للأدمن ويحفظ رقم رسالة الأدمن -> user_id
    حتى إذا الأدمن رد عليها، البوت يرد للعميل.
    """
    if "reply_map" not in context.bot_data:
        context.bot_data["reply_map"] = {}

    sent_message = None

    if text is not None:
        sent_message = await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text
        )
    elif photo_file_id is not None:
        sent_message = await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_file_id,
            caption=caption
        )
    elif document_file_id is not None:
        sent_message = await context.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=document_file_id,
            caption=caption
        )

    if sent_message:
        context.bot_data["reply_map"][sent_message.message_id] = user_id


def build_user_header(user, title: str) -> str:
    username = f"@{user.username}" if user.username else "لا يوجد"
    return (
        f"{title}\n\n"
        f"الاسم الظاهر: {user.full_name}\n"
        f"يوزر العميل: {username}\n"
        f"User ID: {user.id}\n"
    )

# =========================
# أوامر أساسية
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"أهلاً وسهلاً بك في {NETWORK_NAME} 🌐\n\n"
        "نحن هنا لخدمتك في:\n"
        "• تقديم الشكاوى والأعطال\n"
        "• طلب بطاقات الإنترنت\n"
        "• استقبال إشعارات التحويل والملفات والصور\n\n"
        "اختر الخدمة المطلوبة من القائمة التالية:"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard)
    return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "تم إلغاء العملية الحالية.",
        reply_markup=main_keyboard
    )
    return MAIN_MENU


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "تم الرجوع إلى القائمة الرئيسية.",
        reply_markup=main_keyboard
    )
    return MAIN_MENU

# =========================
# القائمة الرئيسية
# =========================
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🔧 تقديم شكوى أو عطل":
        await update.message.reply_text(
            "🔧 تقديم شكوى أو عطل\n\n"
            "يمكنك تقديم الشكوى في أي وقت.\n"
            "يرجى إدخال الاسم الكامل:",
            reply_markup=cancel_keyboard
        )
        return FAULT_NAME

    if text == "💳 طلب بطاقات":
        if not is_order_time():
            await update.message.reply_text(
                "⏰ استقبال طلبات البطاقات متاح فقط من الساعة 8:00 صباحًا حتى 5:00 مساءً.",
                reply_markup=main_keyboard
            )
            return MAIN_MENU

        await update.message.reply_text(
            "💳 طلب بطاقات\n\n"
            "قبل البدء، يرجى قراءة الشروط والموافقة عليها.",
            reply_markup=rules_keyboard
        )
        return CARD_RULES

    if text == "ℹ️ معلومات البطاقات":
        await update.message.reply_text(
            "ℹ️ معلومات البطاقات\n\n"
            "• 1 شيكل = 8 ساعات / 2 ميجا\n"
            "• 2 شيكل = 10 ساعات / 3 ميجا\n"
            "• أقل حد للطلب: 100 بطاقة\n"
            "• التسليم: ملف أو صورة\n"
            "• الطلب من 8 صباحًا إلى 5 مساءً",
            reply_markup=main_keyboard
        )
        return MAIN_MENU

    if text == "📌 شروط الطلب":
        await update.message.reply_text(
            "📌 شروط طلب البطاقات\n\n"
            "1) أقل حد للطلب هو 100 بطاقة.\n"
            "2) التحويل قبل الاستلام.\n"
            "3) يتم إرسال الفرخ على شكل ملف أو صورة.\n"
            "4) بعد التحويل يجب إرسال إشعار التحويل داخل المحادثة.\n"
            "5) الطلبات تستقبل من 8 صباحًا إلى 5 مساءً.",
            reply_markup=main_keyboard
        )
        return MAIN_MENU

    if text == "🏠 القائمة الرئيسية":
        return await back_to_menu(update, context)

    await update.message.reply_text(
        "اختر خدمة من الأزرار الظاهرة.",
        reply_markup=main_keyboard
    )
    return MAIN_MENU

# =========================
# قسم الشكاوى
# =========================
async def fault_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        return await cancel(update, context)

    context.user_data["fault_name"] = update.message.text
    await update.message.reply_text("يرجى إدخال المنطقة أو العنوان:", reply_markup=cancel_keyboard)
    return FAULT_AREA


async def fault_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        return await cancel(update, context)

    context.user_data["fault_area"] = update.message.text
    await update.message.reply_text("يرجى إدخال رقم الراوتر:", reply_markup=cancel_keyboard)
    return FAULT_ROUTER


async def fault_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        return await cancel(update, context)

    context.user_data["fault_router"] = update.message.text
    await update.message.reply_text("يرجى كتابة الشكوى أو وصف العطل:", reply_markup=cancel_keyboard)
    return FAULT_DETAILS


async def fault_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        return await cancel(update, context)

    context.user_data["fault_details"] = update.message.text
    user = update.effective_user

    msg = (
        "🚨 شكوى / عطل جديد\n\n"
        f"الاسم: {context.user_data['fault_name']}\n"
        f"المنطقة: {context.user_data['fault_area']}\n"
        f"رقم الراوتر: {context.user_data['fault_router']}\n"
        f"الشكوى: {context.user_data['fault_details']}\n\n"
        f"الاسم الظاهر: {user.full_name}\n"
        f"يوزر العميل: @{user.username if user.username else 'لا يوجد'}\n"
        f"User ID: {user.id}\n\n"
        "يمكنك الرد على هذه الرسالة مباشرة، والبوت سيرسل الرد للعميل."
    )

    await send_to_admin_and_map(
        context,
        user_id=user.id,
        text=msg
    )

    await update.message.reply_text(
        "✅ تم استلام الشكوى بنجاح، وسيتم مراجعتها.",
        reply_markup=main_keyboard
    )
    context.user_data.clear()
    return MAIN_MENU

# =========================
# قسم طلب البطاقات
# =========================
async def card_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ إلغاء":
        return await cancel(update, context)

    if text == "✅ أوافق على الشروط":
        await update.message.reply_text(
            "📌 شروط الطلب:\n\n"
            "• 1 شيكل = 8 ساعات / 2 ميجا\n"
            "• 2 شيكل = 10 ساعات / 3 ميجا\n"
            "• أقل حد للطلب 100 بطاقة\n"
            "• التحويل قبل الاستلام\n"
            "• التسليم ملف أو صورة\n\n"
            "يرجى إدخال الاسم الكامل:",
            reply_markup=ReplyKeyboardRemove()
        )
        return CARD_NAME

    await update.message.reply_text("اختر من الأزرار الظاهرة.", reply_markup=rules_keyboard)
    return CARD_RULES


async def card_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        return await cancel(update, context)

    context.user_data["card_name"] = update.message.text
    await update.message.reply_text("يرجى إدخال المنطقة أو العنوان:", reply_markup=cancel_keyboard)
    return CARD_AREA


async def card_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        return await cancel(update, context)

    context.user_data["card_area"] = update.message.text
    await update.message.reply_text(
        "اختر نوع البطاقة المطلوبة:",
        reply_markup=card_type_keyboard
    )
    return CARD_TYPE


async def card_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ إلغاء":
        return await cancel(update, context)

    valid_choices = [
        "1 شيكل - 8 ساعات - 2 ميجا",
        "2 شيكل - 10 ساعات - 3 ميجا",
    ]

    if text not in valid_choices:
        await update.message.reply_text(
            "يرجى اختيار نوع البطاقة من الأزرار.",
            reply_markup=card_type_keyboard
        )
        return CARD_TYPE

    context.user_data["card_type"] = text
    await update.message.reply_text(
        "أدخل الكمية المطلوبة (الحد الأدنى 100 بطاقة):",
        reply_markup=ReplyKeyboardRemove()
    )
    return CARD_QTY


async def card_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "❌ إلغاء":
        return await cancel(update, context)

    if not text.isdigit():
        await update.message.reply_text("يرجى إدخال رقم صحيح للكمية:")
        return CARD_QTY

    qty = int(text)
    if qty < 100:
        await update.message.reply_text("❌ أقل حد للطلب هو 100 بطاقة. أدخل كمية صحيحة:")
        return CARD_QTY

    context.user_data["card_qty"] = qty
    await update.message.reply_text(
        "اختر طريقة التسليم:",
        reply_markup=delivery_keyboard
    )
    return CARD_DELIVERY


async def card_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ إلغاء":
        return await cancel(update, context)

    if text not in ["📄 ملف", "🖼 صورة"]:
        await update.message.reply_text(
            "يرجى اختيار طريقة التسليم من الأزرار.",
            reply_markup=delivery_keyboard
        )
        return CARD_DELIVERY

    context.user_data["card_delivery"] = text

    await update.message.reply_text(
        "✅ تم استلام بيانات الطلب.\n\n"
        f"{PAYMENT_INFO}\n\n"
        "الآن أرسل إشعار التحويل داخل المحادثة:\n"
        "• صورة\n"
        "• أو ملف",
        reply_markup=main_keyboard
    )
    return CARD_RECEIPT


async def card_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    caption = (
        "💳 طلب بطاقات جديد\n\n"
        f"الاسم: {context.user_data.get('card_name', '')}\n"
        f"المنطقة: {context.user_data.get('card_area', '')}\n"
        f"نوع البطاقة: {get_card_summary(context.user_data.get('card_type', ''))}\n"
        f"الكمية: {context.user_data.get('card_qty', '')}\n"
        f"طريقة التسليم: {context.user_data.get('card_delivery', '')}\n\n"
        f"الاسم الظاهر: {user.full_name}\n"
        f"يوزر العميل: @{user.username if user.username else 'لا يوجد'}\n"
        f"User ID: {user.id}\n\n"
        "يمكنك الرد على هذه الرسالة مباشرة، والبوت سيرسل الرد للعميل."
    )

    if update.message.photo:
        await send_to_admin_and_map(
            context,
            user_id=user.id,
            photo_file_id=update.message.photo[-1].file_id,
            caption=caption
        )
    elif update.message.document:
        await send_to_admin_and_map(
            context,
            user_id=user.id,
            document_file_id=update.message.document.file_id,
            caption=caption
        )
    else:
        await update.message.reply_text("أرسل صورة أو ملف إشعار التحويل فقط.")
        return CARD_RECEIPT

    await update.message.reply_text(
        "✅ تم استلام إشعار التحويل والطلب بنجاح.\nسيتم مراجعة الطلب والتواصل معك.",
        reply_markup=main_keyboard
    )
    context.user_data.clear()
    return MAIN_MENU

# =========================
# دعم المحادثة العامة بين العميل والأدمن
# =========================
async def user_general_media_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    أي رسالة عامة من العميل خارج النماذج:
    نص / صورة / ملف
    يتم إرسالها للأدمن مع حفظ الربط للرد.
    """
    if update.effective_user.id == ADMIN_CHAT_ID:
        return

    user = update.effective_user
    header = build_user_header(user, "📨 رسالة جديدة من العميل")

    if update.message.text:
        full_text = (
            f"{header}\n"
            f"الرسالة:\n{update.message.text}\n\n"
            "يمكنك الرد على هذه الرسالة مباشرة."
        )
        await send_to_admin_and_map(
            context,
            user_id=user.id,
            text=full_text
        )
        await update.message.reply_text("تم إرسال رسالتك للإدارة ✅", reply_markup=main_keyboard)
        return

    if update.message.photo:
        caption = (
            f"{header}\n"
            "أرسل العميل صورة.\n\n"
            "يمكنك الرد على هذه الرسالة مباشرة."
        )
        await send_to_admin_and_map(
            context,
            user_id=user.id,
            photo_file_id=update.message.photo[-1].file_id,
            caption=caption
        )
        await update.message.reply_text("تم إرسال الصورة للإدارة ✅", reply_markup=main_keyboard)
        return

    if update.message.document:
        caption = (
            f"{header}\n"
            f"أرسل العميل ملفًا: {update.message.document.file_name or 'بدون اسم'}\n\n"
            "يمكنك الرد على هذه الرسالة مباشرة."
        )
        await send_to_admin_and_map(
            context,
            user_id=user.id,
            document_file_id=update.message.document.file_id,
            caption=caption
        )
        await update.message.reply_text("تم إرسال الملف للإدارة ✅", reply_markup=main_keyboard)
        return


async def admin_reply_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    إذا الأدمن رد على رسالة كان البوت أرسلها له، البوت يعيد توجيه الرد للعميل.
    """
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if not update.message.reply_to_message:
        return

    reply_map = context.bot_data.get("reply_map", {})
    replied_message_id = update.message.reply_to_message.message_id
    target_user_id = reply_map.get(replied_message_id)

    if not target_user_id:
        return

    try:
        if update.message.text:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📩 رد من الإدارة:\n\n{update.message.text}"
            )
            await update.message.reply_text("تم إرسال الرد للعميل ✅")
            return

        if update.message.photo:
            caption = update.message.caption or "📩 صورة من الإدارة"
            await context.bot.send_photo(
                chat_id=target_user_id,
                photo=update.message.photo[-1].file_id,
                caption=caption
            )
            await update.message.reply_text("تم إرسال الصورة للعميل ✅")
            return

        if update.message.document:
            caption = update.message.caption or "📩 ملف من الإدارة"
            await context.bot.send_document(
                chat_id=target_user_id,
                document=update.message.document.file_id,
                caption=caption
            )
            await update.message.reply_text("تم إرسال الملف للعميل ✅")
            return

    except Exception as e:
        await update.message.reply_text(f"تعذر إرسال الرد: {e}")

# =========================
# التشغيل
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler),
            ],
            FAULT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fault_name),
            ],
            FAULT_AREA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fault_area),
            ],
            FAULT_ROUTER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fault_router),
            ],
            FAULT_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fault_details),
            ],
            CARD_RULES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, card_rules),
            ],
            CARD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, card_name),
            ],
            CARD_AREA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, card_area),
            ],
            CARD_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, card_type),
            ],
            CARD_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, card_qty),
            ],
            CARD_DELIVERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, card_delivery),
            ],
            CARD_RECEIPT: [
                MessageHandler((filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, card_receipt),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^🏠 القائمة الرئيسية$"), back_to_menu),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    # رد الأدمن على الرسائل المحولة
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
            admin_reply_router
        ),
        group=0
    )

    # استقبال أي رسالة عامة من العميل خارج النماذج
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
            user_general_media_or_text
        ),
        group=1
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
