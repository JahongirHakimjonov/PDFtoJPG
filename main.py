import asyncio
import datetime
import logging
import os

import fitz
from PIL import Image
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv("env/.env")

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise ValueError("Missing BOT_TOKEN environment variable")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

keyboard = InlineKeyboardMarkup(row_width=2)
buttons = [
    InlineKeyboardButton("PDF to JPG", callback_data="pdf_to_jpg"),
]
keyboard.add(*buttons)

continue_stop_keyboard = InlineKeyboardMarkup(row_width=2)
continue_stop_buttons = [
    InlineKeyboardButton("Davom etish", callback_data="continue"),
    InlineKeyboardButton("Toxtatish", callback_data="stop"),
]
continue_stop_keyboard.add(*continue_stop_buttons)

pdf_queue = asyncio.Queue()


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer(
        f"Salom [{message.from_user.first_name}](tg://user?id={message.from_user.id})\nQuyidagi amallarni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


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


async def process_pdf_files():
    while True:
        message = await pdf_queue.get()

        await message.answer("PDF fayl qabul qilindi. JPG formatiga o'tkazilmoqda...")

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"temp_{timestamp}.pdf"

        file = await bot.download_file_by_id(
            message.document.file_id, destination=file_path
        )
        file.close()

        try:
            doc = fitz.open(file_path)
            for i in range(len(doc)):
                zoom = 10.0
                mat = fitz.Matrix(zoom, zoom)
                pix = doc.get_page_pixmap(i, matrix=mat)

                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_file_path = f"out_{timestamp}_{i}.jpg"
                img.save(img_file_path, "JPEG", quality=100)

                with open(img_file_path, "rb") as img_file:
                    await bot.send_document(message.chat.id, img_file)

                os.remove(img_file_path)

            doc.close()

        finally:
            os.remove(file_path)

        pdf_queue.task_done()
        await bot.send_message(
            message.chat.id,
            "Jarayon yakunlandi : )",
            reply_markup=continue_stop_keyboard,
        )


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
    Bot.set_current(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(process_pdf_files())
    executor.start_polling(dp, skip_updates=True)
