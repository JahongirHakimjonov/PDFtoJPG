import asyncio
import datetime
import os
import time

import fitz
from PIL import Image

pdf_queue = asyncio.Queue()


async def process_pdf_files(bot, continue_stop_keyboard):
    while True:
        message = await pdf_queue.get()

        await message.answer("PDF fayl qabul qilindi. JPG formatiga o'tkazilmoqda...")

        time.sleep(1)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"temp_{timestamp}.pdf"
        time.sleep(1)

        file = await bot.download_file_by_id(
            message.document.file_id, destination=file_path
        )
        file.close()

        doc = fitz.open(file_path)
        for i in range(len(doc)):
            zoom = 10.0
            mat = fitz.Matrix(zoom, zoom)
            pix = doc.get_page_pixmap(i, matrix=mat)

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_file_path = f"out_{timestamp}_{i}.jpg"
            img.save(img_file_path, "JPEG", quality=100)

            time.sleep(1)
            with open(img_file_path, "rb") as img_file:
                await bot.send_document(message.chat.id, img_file)
                time.sleep(1)

            if os.path.exists(img_file_path):
                os.remove(img_file_path)

        doc.close()

        if os.path.exists(file_path):
            os.remove(file_path)

        pdf_queue.task_done()
        await bot.send_message(
            message.chat.id,
            "Jarayon yakunlandi : )",
            reply_markup=continue_stop_keyboard,
        )
