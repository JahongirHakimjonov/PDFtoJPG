import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv, find_dotenv

from CSVtoXLSX import process_csv
from PDFtoJPG import process_pdf_files

load_dotenv('env/.env')

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise ValueError("Missing BOT_TOKEN environment variable")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

keyboard = InlineKeyboardMarkup(row_width=2)
buttons = [
    InlineKeyboardButton("PDF to JPG", callback_data="pdf_to_jpg"),
    InlineKeyboardButton("CSV to XLSX", callback_data="csv_to_xlsx"),
]
keyboard.add(*buttons)

continue_stop_keyboard = InlineKeyboardMarkup(row_width=2)
continue_stop_buttons = [
    InlineKeyboardButton("Davom etish", callback_data="continue"),
    InlineKeyboardButton("Toxtatish", callback_data="stop"),
]
continue_stop_keyboard.add(*continue_stop_buttons)

pdf_queue = asyncio.Queue()
csv_queue = asyncio.Queue()


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer(
        f"Salom [{message.from_user.first_name}](tg://user?id={message.from_user.id})\nQuyidagi amallarni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@dp.callback_query_handler(lambda c: c.data == "csv_to_xlsx")
async def process_csv_to_xlsx(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, "CSV faylni yuboring. XLSX formatiga o'tkazilmoqda."
    )

    @dp.message_handler(content_types=types.ContentType.DOCUMENT)
    async def csv_to_xlsx(message: types.Message):
        if message.document.mime_type == "text/csv":
            await csv_queue.put(message)

            asyncio.create_task(process_csv(bot, message))


@dp.callback_query_handler(lambda c: c.data == "pdf_to_jpg")
async def process_pdf_to_jpg(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, "JPG qilish uchun PDF faylni yuboring."
    )

    @dp.message_handler(content_types=types.ContentType.DOCUMENT)
    async def pdf_to_jpg(message: types.Message):
        if message.document.mime_type == "application/pdf":
            await pdf_queue.put(message)

            asyncio.create_task(process_pdf_files(bot, continue_stop_keyboard))


@dp.callback_query_handler(lambda c: c.data == "continue")
async def process_continue(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, "Keyingi amalni tanlang:", reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data == "stop")
async def process_stop(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.delete_message(
        callback_query.from_user.id, callback_query.message.message_id
    )
    await bot.send_message(
        callback_query.from_user.id, "Xizmatlarimizdan foydalanganingiz uchun rahmat!"
    )


if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
