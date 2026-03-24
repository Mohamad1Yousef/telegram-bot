from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime

BOT_TOKEN = "8211007927:AAHF_G-z95bcMpF5QSeklVsa2eJ3jKhvo80"
ADMIN_CHAT_ID = 1498115119
NETWORK_NAME = "VR Network"
PAYMENT_INFO = "التحويل قبل الاستلام باسم: محمد يوسف ابو معمر\nIBAN: PS44PALS044817049130993000000\nيرجى إرسال إشعار التحويل داخل المحادثة بعد الدفع."

MAIN_MENU = 0
FAULT_NAME, FAULT_AREA, FAULT_ROUTER, FAULT_DETAILS = range(1, 5)
CARD_RULES, CARD_NAME, CARD_AREA, CARD_PRICE, CARD_QTY, CARD_DELIVERY = range(5, 11)

main_keyboard = ReplyKeyboardMarkup(
    [
        ["🔧 شكوى", "💳 طلب بطاقات"],
        ["🏠 القائمة الرئيسية"],
    ],
    resize_keyboard=True
)

rules_keyboard = ReplyKeyboardMarkup(
    [["✅ موافق", "❌ إلغاء"]],
    resize_keyboard=True
)

price_keyboard = ReplyKeyboardMarkup(
    [["1 شيكل", "2 شيكل"], ["❌ إلغاء"]],
    resize_keyboard=True
)

delivery_keyboard = ReplyKeyboardMarkup(
    [["📄 ملف", "🖼 صورة"], ["❌ إلغاء"]],
    resize_keyboard=True
)

def is_order_time():
    return 8 <= datetime.now().hour < 17

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"أهلاً بك في {NETWORK_NAME}\n\nاختر الخدمة:",
        reply_markup=main_keyboard
    )
    return MAIN_MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🔧 شكوى":
        await update.message.reply_text("اكتب اسمك:")
        return FAULT_NAME

    elif text == "💳 طلب بطاقات":
        if not is_order_time():
            await update.message.reply_text("الطلبات من 8 صباحًا إلى 5 مساءً فقط", reply_markup=main_keyboard)
            return MAIN_MENU

        await update.message.reply_text(
            "شروط طلب البطاقات:\n"
            "- البطاقات المتوفرة: 1 شيكل و2 شيكل\n"
            "- أقل طلب: 100 بطاقة\n"
            "- التحويل قبل الاستلام\n"
            "- التسليم على شكل ملف أو صورة\n"
            "- بعد التحويل أرسل إشعار التحويل داخل المحادثة\n\n"
            "اضغط موافق للمتابعة",
            reply_markup=rules_keyboard
        )
        return CARD_RULES

    elif text == "🏠 القائمة الرئيسية":
        await update.message.reply_text("تم الرجوع للقائمة الرئيسية", reply_markup=main_keyboard)
        return MAIN_MENU

    await update.message.reply_text("اختر من الأزرار الظاهرة", reply_markup=main_keyboard)
    return MAIN_MENU

async def fault_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("اكتب منطقتك:")
    return FAULT_AREA

async def fault_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["area"] = update.message.text
    await update.message.reply_text("اكتب رقم الراوتر:")
    return FAULT_ROUTER

async def fault_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["router"] = update.message.text
    await update.message.reply_text("اكتب الشكوى:")
    return FAULT_DETAILS

async def fault_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["problem"] = update.message.text
    user = update.effective_user

    msg = (
        "🚨 شكوى جديدة\n\n"
        f"الاسم: {context.user_data['name']}\n"
        f"المنطقة: {context.user_data['area']}\n"
        f"رقم الراوتر: {context.user_data['router']}\n"
        f"الشكوى: {context.user_data['problem']}\n\n"
        f"يوزر العميل: @{user.username if user.username else 'لا يوجد'}\n"
        f"User ID: {user.id}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
    await update.message.reply_text("تم استلام الشكوى ✅", reply_markup=main_keyboard)
    context.user_data.clear()
    return MAIN_MENU

async def card_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "✅ موافق":
        await update.message.reply_text("اكتب اسمك:", reply_markup=ReplyKeyboardRemove())
        return CARD_NAME

    await update.message.reply_text("تم إلغاء الطلب", reply_markup=main_keyboard)
    return MAIN_MENU

async def card_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("اكتب منطقتك:")
    return CARD_AREA

async def card_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["area"] = update.message.text
    await update.message.reply_text("اختر نوع البطاقة:", reply_markup=price_keyboard)
    return CARD_PRICE

async def card_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text not in ["1 شيكل", "2 شيكل"]:
        await update.message.reply_text("اختر من الأزرار", reply_markup=price_keyboard)
        return CARD_PRICE

    context.user_data["price"] = update.message.text
    await update.message.reply_text("اكتب الكمية المطلوبة:")
    return CARD_QTY

async def card_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("اكتب رقم صحيح للكمية")
        return CARD_QTY

    qty = int(text)
    if qty < 100:
        await update.message.reply_text("أقل طلب 100 بطاقة")
        return CARD_QTY

    context.user_data["qty"] = qty
    await update.message.reply_text("اختر طريقة التسليم:", reply_markup=delivery_keyboard)
    return CARD_DELIVERY

async def card_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text not in ["📄 ملف", "🖼 صورة"]:
        await update.message.reply_text("اختر من الأزرار", reply_markup=delivery_keyboard)
        return CARD_DELIVERY

    context.user_data["delivery"] = update.message.text
    user = update.effective_user

    msg = (
        "💳 طلب بطاقات جديد\n\n"
        f"الاسم: {context.user_data['name']}\n"
        f"المنطقة: {context.user_data['area']}\n"
        f"نوع البطاقة: {context.user_data['price']}\n"
        f"الكمية: {context.user_data['qty']}\n"
        f"طريقة التسليم: {context.user_data['delivery']}\n\n"
        f"يوزر العميل: @{user.username if user.username else 'لا يوجد'}\n"
        f"User ID: {user.id}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
    await update.message.reply_text(
        f"تم تسجيل الطلب ✅\n\n{PAYMENT_INFO}",
        reply_markup=main_keyboard
    )
    context.user_data.clear()
    return MAIN_MENU

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            FAULT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fault_name)],
            FAULT_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fault_area)],
            FAULT_ROUTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, fault_router)],
            FAULT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, fault_details)],
            CARD_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_rules)],
            CARD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_name)],
            CARD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_area)],
            CARD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_price)],
            CARD_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_qty)],
            CARD_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_delivery)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
