import os

import pandas as pd
from aiogram import types


async def process_csv(bot, message: types.Message):
    document = message.document
    if document.mime_type == "text/csv":
        await document.download(destination_file="input.csv")  # CSV faylini yuklab olish
        df = pd.read_csv("input.csv")  # CSV faylini o'qish
        output_file = "output.xlsx"
        df.to_excel(output_file, index=False)  # XLSX fayliga o'zgartirish
        await bot.send_document(
            message.chat.id, types.InputFile(output_file)
        )  # XLSX faylini yuborish
        os.remove("input.csv")  # Faylni o'chirish
        os.remove(output_file)  # Faylni o'chirish
    else:
        await message.reply("Faqat CSV fayllarni qabul qilamiz.")
    return True
