import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Konversatsiya holatlari
LANGUAGE, STIR = range(2)
ECOL_DOCUMENT, ECOL_DOCUMENT_TYPE = range(2, 4)

# Xabarlarni ikki tilda saqlash
MESSAGES = {
    'uz': {
        'language_prompt': "Iltimos, tilni tanlang / Пожалуйста, выберите язык:\n1. O‘zbekcha\n2. Русский",
        'invalid_language': "Noto‘g‘ri tanlov. Iltimos, quyidagi variantlardan birini tanlang.\nНеверный выбор. Пожалуйста, выберите один из вариантов ниже.",
        'start_prompt': "Salom! Iltimos, 9 xonali STIR raqamingizni kiriting:",
        'invalid_stir': "Iltimos, 9 xonali faqat raqamdan iborat STIR raqamini kiriting:",
        'stir_not_found': "Kiritilgan STIR raqamiga mos ma'lumot topilmadi.",
        'error_loading': "Ma'lumotlar bazasiga ulanishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        'operation_cancelled': "Operatsiya bekor qilindi.",
        'stir_info': (
            "**STIR:** `{STIR}`\n"
            "**Tashkilot Nomi:** `{Tashkilot_Nomi}`\n"
            "**Hudud:** `{Hudud}`\n"
            "**Manzil:** `{Manzil}`\n"
            "**OKED Raqami:** `{OKED_Raqami}`\n"
            "**OKED Nomi:** `{OKED_Nomi}`\n"
        ),
        'language_selected': "Til tanlandi: O‘zbekcha",
        'ask_ecological_documents': "Ekologik normativ hujjatlaringiz bormi? (Agar borga 'Ha' ni bosing):",
        'eco_documents_options': "Qaysi turdagi ekologik normativ hujjatlaringiz bor?\n1. AMTB – Atrof-muhitga ta'sir to'g'risidagi bayonot\n2. AМТБЛ – Atrof-muhitga ta'sir to'g'risidagi bayonot loyihasi\n3. ЭОТБ – Ekologik oqibatlar to'g'risidagi bayonot\n4. ЧЧМ – Chiqindilarning hosil bo'lishi cheklangan miqdori\n5. ТЧМ – Atmosferaga tashlamalar miqdori\n6. ОЧМ – Oqovaning yo'l qo'yiladigan cheklangan miqdori\nBir nechtasini tanlang (raqamlar bilan):",
        'eco_service_message': "eco-service.uz veb saytida Ekologik ekspertiza xulosasini olish uchun ariza yuborishingiz mumkin!",
        'thank_you_message': "E'tiboringiz uchun katta rahmat\nQo'shimcha ma'lumot uchun: Call center 71-203-00-22",
    },
    'ru': {
        'language_prompt': "Пожалуйста, выберите язык / Iltimos, tilni tanlang:\n1. O‘zbekcha\n2. Русский",
        'invalid_language': "Неверный выбор. Пожалуйста, выберите один из вариантов ниже.\nNoto‘g‘ri tanlov. Iltimos, quyidagi variantlardan birini tanlang.",
        'start_prompt': "Здравствуйте! Пожалуйста, введите ваш 9-значный номер STIR:",
        'invalid_stir': "Пожалуйста, введите действительный 9-значный числовой номер STIR:\nIltimos, 9 xonali faqat raqamdan iborat STIR raqamini kiriting:",
        'stir_not_found': "Информация по введенному номеру STIR не найдена.\nKiritilgan STIR raqamiga mos ma'lumot topilmadi.",
        'error_loading': "Произошла ошибка при доступе к базе данных. Пожалуйста, попробуйте позже.\nMa'lumotlar bazasiga ulanishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        'operation_cancelled': "Операция отменена.\nOperatsiya bekor qilindi.",
        'stir_info': (
            "**STIR:** `{STIR}`\n"
            "**Название Организации:** `{Tashkilot_Nomi}`\n"
            "**Регион:** `{Hudud}`\n"
            "**Адрес:** `{Manzil}`\n"
            "**Код OKED:** `{OKED_Raqami}`\n"
            "**Название OKED:** `{OKED_Nomi}`\n"
        ),
        'language_selected': "Выбранный язык: Русский",
        'ask_ecological_documents': "Экологический нормативный документ у вас есть? (Если есть, нажмите \"Да\")",
        'eco_documents_options': "Какой тип экологического нормативного документа у вас есть?\n1. АМТБ – Отчет об воздействии на окружающую среду\n2. АМТБЛ – Проект отчета об воздействии на окружающую среду\n3. ЭОТБ – Отчет об экологических последствиях\n4. ЧЧМ – Ограниченное количество образования отходов\n5. ТЧМ – Допустимое количество выбросов в атмосферу\n6. ОЧМ – Допустимое количество сточных вод\nВыберите несколько (по номеру):",
        'eco_service_message': "Вы можете отправить заявку на получение заключения экологической экспертизы на сайте eco-service.uz!",
        'thank_you_message': "Спасибо за ваше внимание\nДля дополнительной информации: Call center 71-203-00-22",
    }
}


# Excel faylini o'qish va tekshirish
def load_data():
    try:
        df = pd.read_excel('data.xlsx', dtype={'STIR': str})

        # Ustunlarni tekshirish
        required_columns = ['STIR', 'Ташкилот номи', 'OKED', 'OKED_NAME', 'вилоят', 'туман']
        for column in required_columns:
            if column not in df.columns:
                print(f"Ustun topilmadi: {column}")
                return None

        # Har bir ustun uchun qiymatlarning yo'qligini tekshirish
        for column in required_columns:
            if df[column].isnull().any():
                print(f"Ustunda bo'sh qiymatlar mavjud: {column}")
                return None

        return df
    except Exception as e:
        print(f"Excel faylini o'qishda xatolik: {e}")
        return None


# Tilni tanlash uchun funksiya
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        MESSAGES['uz']['language_prompt'],
        reply_markup=ReplyKeyboardMarkup(
            [['O‘zbekcha', 'Русский']], one_time_keyboard=True, resize_keyboard=True
        )
    )
    return LANGUAGE


# Til tanlanganida ishlaydigan funksiya
async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text.strip().lower()
    if user_choice in ['o‘zbekcha', 'uzbekcha', 'uz']:
        context.user_data['lang'] = 'uz'
        await update.message.reply_text(
            MESSAGES['uz']['language_selected'],
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text(MESSAGES['uz']['start_prompt'])
        return STIR
    elif user_choice in ['rus', 'русский', 'рус']:
        context.user_data['lang'] = 'ru'
        await update.message.reply_text(
            MESSAGES['ru']['language_selected'],
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text(MESSAGES['ru']['start_prompt'])
        return STIR
    else:
        await update.message.reply_text(MESSAGES['uz']['invalid_language'])
        return LANGUAGE


# /start komandasi uchun funksiya
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await choose_language(update, context)


# STIR raqamini qabul qilish va tekshirish
async def get_stir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'uz')
    stir_input = update.message.text.strip()

    if not stir_input.isdigit() or len(stir_input) != 9:
        await update.message.reply_text(MESSAGES[lang]['invalid_stir'])
        return STIR

    # Foydalanuvchini kutish holatiga o'zgartirish
    await update.message.reply_text("⌛️")

    # Excel faylini yuklash
    df = load_data()
    if df is None:
        await update.message.reply_text(MESSAGES[lang]['error_loading'])
        return ConversationHandler.END

    # STIR raqamini tekshirish
    result = df.loc[df['STIR'] == stir_input]

    if result.empty:
        await update.message.reply_text(MESSAGES[lang]['stir_not_found'])
        return ConversationHandler.END

    # STIR ma'lumotlarini tayyorlash
    stir_info = result.iloc[0]
    stir_details = MESSAGES[lang]['stir_info'].format(
        STIR=stir_input,
        Tashkilot_Nomi=stir_info['Ташкилот номи'],
        Hudud=stir_info['вилоят'],
        Manzil=stir_info['туман'],
        OKED_Raqami=stir_info['OKED'],
        OKED_Nomi=stir_info['OKED_NAME']
    )

    await update.message.reply_text(stir_details)

    # Ekologik hujjatlar so'rovini yuborish
    await update.message.reply_text(MESSAGES[lang]['ask_ecological_documents'], reply_markup=ReplyKeyboardMarkup(
        [['Ha', 'Yo\'q']], one_time_keyboard=True, resize_keyboard=True
    ))
    return ECOL_DOCUMENT


# Ekologik hujjatlarni so'rash
async def ask_ecological_documents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'uz')
    user_choice = update.message.text.strip().lower()

    if user_choice == 'ha':
        await update.message.reply_text(MESSAGES[lang]['eco_documents_options'])
        return ECOL_DOCUMENT_TYPE
    else:
        await update.message.reply_text(MESSAGES[lang]['eco_service_message'])
        await update.message.reply_text(MESSAGES[lang]['thank_you_message'])
        return ConversationHandler.END


# Ekologik hujjatlarni turlari uchun funksiya
async def eco_documents_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'uz')
    user_choice = update.message.text.strip()

    # Ekologik hujjatlarni turlarini olish
    eco_documents = user_choice.split(',')


    await update.message.reply_text(MESSAGES[lang]['thank_you_message'])
    return ConversationHandler.END


# Botni ishga tushirish
def main():
    application = ApplicationBuilder().token("7650230873:AAFWGZnbpaM9DYn4KAMO0bJjf5THUa7sgMw").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_selected)],
            STIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stir)],
            ECOL_DOCUMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ecological_documents)],
            ECOL_DOCUMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, eco_documents_type)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
