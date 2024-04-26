import os
import fitz
import time
import logging
import asyncio
import datetime
from PIL import Image
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv(find_dotenv())

bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise ValueError("Missing BOT_TOKEN environment variable")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=bot_token)
dp = Dispatcher(bot)

# Define the inline keyboard
keyboard = InlineKeyboardMarkup(row_width=2)
buttons = [
    InlineKeyboardButton("PDF to JPG", callback_data="pdf_to_jpg"),
    # InlineKeyboardButton("CSV to XLSX", callback_data="csv_to_xlsx"),
]
keyboard.add(*buttons)

# Define the inline keyboard for continue and stop
continue_stop_keyboard = InlineKeyboardMarkup(row_width=2)
continue_stop_buttons = [
    InlineKeyboardButton("Davom etish", callback_data="continue"),
    InlineKeyboardButton("Toxtatish", callback_data="stop"),
]
continue_stop_keyboard.add(*continue_stop_buttons)

# Create a queue to store the incoming PDF files
pdf_queue = asyncio.Queue()


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer(
        f"Salom [{message.from_user.first_name}](tg://user?id={message.from_user.id})\nQuyidagi amallarni tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@dp.callback_query_handler(lambda c: c.data == "csv_to_xlsx")
async def process_csv_to_xlsx(callback_query: types.CallbackQuery):
    # Handle the 'CSV to XLSX' button press here
    pass


@dp.callback_query_handler(lambda c: c.data == "pdf_to_jpg")
async def process_pdf_to_jpg(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id, "JPG qilish uchun PDF faylni yuboring."
    )

    @dp.message_handler(content_types=types.ContentType.DOCUMENT)
    async def pdf_to_jpg(message: types.Message):
        if message.document.mime_type == "application/pdf":
            # Add the incoming PDF file to the queue
            await pdf_queue.put(message)

            # Start the worker function
            asyncio.create_task(process_pdf_files())


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


async def process_pdf_files():
    while True:
        # Wait for a new PDF file to come in
        message = await pdf_queue.get()

        await message.answer("PDF fayl qabul qilindi. JPG formatiga o'tkazilmoqda...")

        time.sleep(1)  # Simulate a long-running task
        # Generate a unique filename for the downloaded file
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"temp_{timestamp}.pdf"
        time.sleep(1)

        # Download the file
        file = await bot.download_file_by_id(
            message.document.file_id, destination=file_path
        )
        file.close()  # Close the file after downloading

        # Open the PDF file
        doc = fitz.open(file_path)
        for i in range(len(doc)):
            # Convert each page to a pixmap object with a higher resolution
            zoom = 20.0  # Increase the zoom factor for higher resolution
            mat = fitz.Matrix(zoom, zoom)
            pix = doc.get_page_pixmap(i, matrix=mat)

            # Convert the pixmap to a PIL Image and save it
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_file_path = f"out_{timestamp}_{i}.jpg"
            img.save(img_file_path, "JPEG", quality=100)

            time.sleep(1)  # Simulate a long-running task
            # Send the image file
            with open(img_file_path, "rb") as img_file:
                await bot.send_document(message.chat.id, img_file)
                time.sleep(1)

            # Remove the image file after sending
            if os.path.exists(img_file_path):
                os.remove(img_file_path)

        # Close the fitz.Document object
        doc.close()

        # Remove the downloaded PDF file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Mark the task as done
        pdf_queue.task_done()
        await bot.send_message(
            message.chat.id,
            "Jarayon yakunlandi : )",
            reply_markup=continue_stop_keyboard,
        )


if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
