import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai

# ---- CONFIGURATION ----
TELEGRAM_TOKEN = "8683419082:AAH-7xsJbiz_ipiuut1B-H8tWJgvZv6IP6g"
API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Bot and Dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Configure Gemini AI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply("👋 Hello! Main aapka PCM Doubt Solver Bot hoon. Mujhe kisi bhi question ki photo bhejiye, main solution de doonga!")

@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    await message.reply("🔄 Photo mil gayi hai! Solution taiyar ho raha hai, kripya thoda sabr rakhein...")
    
    try:
        # Photo download karein
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        
        # Binary data download karein
        file_bytes = await bot.download_file(file_path)
        image_data = file_bytes.read()

        # Gemini 2.5 Flash ko photo aur prompt bhejein
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data},
            "Solve this PCM question step-by-step in Hindi and English mix language clearly."
        ])
        
        # Answer send karein
        if response.text:
            await message.reply(response.text)
        else:
            await message.reply("❌ Maaf kijiyega, AI koi jawab nahi bana paya. Kripya doosri photo try karein.")
            
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("❌ Galti hui! Kripya check karein ki Render par GEMINI_API_KEY sahi se set hai ya nahi.")

async def main():
    print("Bot chalu ho raha hai...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
