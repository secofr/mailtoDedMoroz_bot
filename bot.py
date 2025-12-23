import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN"  # Замените на ваш токен
EMAIL_ADDRESS = "yourname@gmail.com"
EMAIL_PASSWORD = "ВАШ_EMAIL_PАРОЛЬ_ИЛИ_APP_PASSWORD"  # Для Gmail нужен App Password

# Этапы разговора
NAME, AGE, GOOD_DEEDS, GIFT, CONFIRMATION = range(5)

# Клавиатура для подтверждения
confirmation_keyboard = ReplyKeyboardMarkup(
    [["Да, отправить письмо", "Нет, заполнить заново"]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Начало разговора
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает разговор и спрашивает имя."""
    await update.message.reply_text(
        "Привет! Я помогу тебе написать письмо Деду Морозу! 🎅\n\n"
        "Для начала расскажи, как тебя зовут?"
    )
    return NAME

# Получение имени
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['name'] = update.message.text
    logger.info(f"Пользователь {user.first_name} указал имя: {update.message.text}")
    
    await update.message.reply_text(
        f"Приятно познакомиться, {update.message.text}! 🎄\n\n"
        "Сколько тебе лет?"
    )
    return AGE

# Получение возраста
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['age'] = update.message.text
    logger.info(f"Пользователь {user.first_name} указал возраст: {update.message.text}")
    
    await update.message.reply_text(
        "Замечательно! 🌟\n\n"
        "Расскажи, что хорошего ты сделал в уходящем году?\n"
        "(Можно перечислить несколько хороших дел)"
    )
    return GOOD_DEEDS

# Получение хороших дел
async def get_good_deeds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['good_deeds'] = update.message.text
    logger.info(f"Пользователь {user.first_name} рассказал о хороших делах")
    
    await update.message.reply_text(
        "Молодец! Дед Мороз обязательно оценит твои добрые дела! ❤️\n\n"
        "Теперь самый важный вопрос:\n"
        "Какой подарок ты бы хотел получить на Новый год? 🎁"
    )
    return GIFT

# Получение желаемого подарка
async def get_gift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    context.user_data['gift'] = update.message.text
    context.user_data['telegram_username'] = user.username
    context.user_data['telegram_name'] = user.full_name
    
    logger.info(f"Пользователь {user.first_name} хочет подарок: {update.message.text}")
    
    # Формируем сводку ответов
    summary = format_summary(context.user_data)
    
    await update.message.reply_text(
        f"Отлично! Давай проверим твое письмо Деду Морозу:\n\n{summary}\n"
        "Всё верно? Отправляем письмо?",
        reply_markup=confirmation_keyboard
    )
    return CONFIRMATION

# Форматирование сводки
def format_summary(user_data: dict) -> str:
    return (
        f"📝 Письмо Деду Морозу:\n\n"
        f"👤 Имя: {user_data.get('name', 'Не указано')}\n"
        f"🎂 Возраст: {user_data.get('age', 'Не указано')}\n"
        f"🌟 Хорошие дела: {user_data.get('good_deeds', 'Не указано')}\n"
        f"🎁 Желаемый подарок: {user_data.get('gift', 'Не указано')}\n"
        f"📱 От: {user_data.get('telegram_name', 'Не указано')}"
        f" (@{user_data.get('telegram_username', 'Не указано')})"
    )

# Отправка email
def send_email(user_data: dict) -> bool:
    """Отправляет письмо на email."""
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['Subject'] = f"Письмо Деду Морозу от {user_data.get('name', 'Аноним')}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        
        # Текст письма
        body = f"""
        📨 Новое письмо Деду Морозу!
        
        📋 Информация о ребенке:
        👤 Имя: {user_data.get('name', 'Не указано')}
        🎂 Возраст: {user_data.get('age', 'Не указано')}
        📱 Telegram: {user_data.get('telegram_name', 'Не указано')} (@{user_data.get('telegram_username', 'Не указано')})
        
        🌟 Хорошие дела в уходящем году:
        {user_data.get('good_deeds', 'Не указано')}
        
        🎁 Желаемый подарок:
        {user_data.get('gift', 'Не указано')}
        
        ---
        Письмо отправлено через Telegram-бот "Письмо Деду Морозу"
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Отправка через SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Письмо успешно отправлено для пользователя {user_data.get('name')}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
        return False

# Подтверждение и отправка
async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_choice = update.message.text
    
    if user_choice == "Да, отправить письмо":
        # Отправляем email
        success = send_email(context.user_data)
        
        if success:
            await update.message.reply_text(
                "🎉 Поздравляю! Твое письмо успешно отправлено Деду Морозу! 🎅\n\n"
                "Он уже получил его и обязательно прочитает. \n"
                "Не забывай вести себя хорошо и готовиться к празднику! 🎄✨\n\n"
                "С наступающим Новым Годом! 🎁",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"Пользователь {user.first_name} успешно отправил письмо")
        else:
            await update.message.reply_text(
                "К сожалению, произошла ошибка при отправке письма. 😔\n"
                "Попробуй еще раз немного позже или свяжись с организаторами.",
                reply_markup=ReplyKeyboardRemove()
            )
        
        # Очищаем данные пользователя
        context.user_data.clear()
        return ConversationHandler.END
        
    else:
        # Начинаем заново
        await update.message.reply_text(
            "Хорошо, давай заполним письмо заново! 🔄\n\n"
            "Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return NAME

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} отменил разговор.")
    
    await update.message.reply_text(
        "Жаль, что ты передумал писать письмо Деду Морозу. 😔\n"
        "Если захочешь написать - просто нажми /start\n"
        "С наступающим Новым Годом! 🎄",
        reply_markup=ReplyKeyboardRemove()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# Основная функция
def main() -> None:
    """Запуск бота."""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GOOD_DEEDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_good_deeds)],
            GIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gift)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Добавляем обработчик
    application.add_handler(conv_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
