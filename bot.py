import random
import string
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from pytube import YouTube
from pytube.exceptions import VideoUnavailable

# Состояния
WAITING_FOR_LENGTH = 1
WAITING_FOR_YOUTUBE_LINK = 2

# Функция для генерации случайного пароля
def generate_password(length: int) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Стартовая команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["/gen_pass", "/download"]]  # Кнопки для генерации пароля и скачивания видео
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать! Вы можете:\n"
        "- Сгенерировать пароль, нажав на /gen_pass\n"
        "- Скачать видео с YouTube, нажав на /download",
        reply_markup=reply_markup
    )

# Команда /gen_pass
async def start_gen_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите длину пароля:")
    return WAITING_FOR_LENGTH

# Получение длины пароля от пользователя
async def get_password_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        length = int(update.message.text)
        if length < 1:
            await update.message.reply_text("Длина пароля должна быть больше 0. Попробуйте снова:")
            return WAITING_FOR_LENGTH

        password = generate_password(length)
        await update.message.reply_text(
            f"Ваш пароль: `{password}`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число:")
        return WAITING_FOR_LENGTH

# Команда /download
async def start_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отправьте ссылку на видео с YouTube:")
    return WAITING_FOR_YOUTUBE_LINK

# Обработка ссылки на YouTube
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text
    try:
        # Загружаем видео в минимальном разрешении
        yt = YouTube(url)
        stream = yt.streams.get_lowest_resolution()
        file_path = stream.download()

        # Отправляем файл пользователю
        await update.message.reply_text(f"Скачиваю видео: {yt.title}")
        await update.message.reply_video(video=open(file_path, 'rb'))

        # Удаляем локальный файл после отправки
        os.remove(file_path)

        return ConversationHandler.END
    except VideoUnavailable:
        await update.message.reply_text("Видео недоступно. Проверьте ссылку и попробуйте снова.")
        return WAITING_FOR_YOUTUBE_LINK
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при загрузке видео: {e}")
        return WAITING_FOR_YOUTUBE_LINK

# Команда для отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Основная функция
def main():
    # Токен вашего бота
    TOKEN = '8194298232:AAGHFRrwWI3ngH8Ril_o8eVOuIQnpKakt3g'

    # Создаем приложение Telegram
    application = Application.builder().token(TOKEN).build()

    # ConversationHandler для генерации пароля
    password_handler = ConversationHandler(
        entry_points=[CommandHandler("gen_pass", start_gen_pass)],
        states={
            WAITING_FOR_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password_length)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler для загрузки видео
    download_handler = ConversationHandler(
        entry_points=[CommandHandler("download", start_download)],
        states={
            WAITING_FOR_YOUTUBE_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, download_video)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(password_handler)
    application.add_handler(download_handler)

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
