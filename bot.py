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

# 🧠 Simple Memory: Sirf pichla text yaad rakhne ke liye
user_text_history = {}

# 🚀 START COMMAND
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_text_history[user_id] = []
    await message.reply("👋 Hello! Main aapka PCM Tutor Bot hoon. Mujhe sawaal ki photo bhejiye ya text likhiye, main step‑by‑step solution doonga!")

# 📸 PHOTO HANDLE
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    wait_message = await message.reply("🔄 Photo mil gayi hai! me mohit se puch raha hu, thoda sabr rakhein...")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        file_bytes = await bot.download_file(file_path)
        image_data = file_bytes.read()

        # Detailed tutor style prompt
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data},
            """You are a professional PCM tutor. 
            Solve this question step-by-step in Hindi-English mix language. 
            - Explain each step clearly like a teacher.
            - Use simple words and short sentences.
            - Show formulas, substitutions, and simplifications.
            - Highlight the final answer separately.
            - If multiple options are given, check each option and explain why correct/incorrect.
            """
        ])
        
        if response.text:
            await bot.edit_message_text(response.text, message.chat.id, wait_message.message_id)
        else:
            await bot.edit_message_text("❌ Maaf kijiyega, AI koi jawab nahi bana paya.", message.chat.id, wait_message.message_id)
    except Exception as e:
        print(f"Error: {e}")
        await bot.edit_message_text("❌ Photo process karne mein galti hui! Kripya dobara try karein.", message.chat.id, wait_message.message_id)

# 💬 TEXT HANDLE
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    wait_message = await message.reply("🔄 Aapka sawaal mil gaya hai! Soch raha hoon...")
    
    try:
        if user_id not in user_text_history:
            user_text_history[user_id] = []
            
        current_prompt = message.text
        full_context = """You are a professional PCM tutor. 
        Solve the following question step-by-step in Hindi-English mix language. 
        - Explain each step clearly like a teacher.
        - Use formulas and reasoning.
        - Give hints and tips if needed.
        - Highlight the final answer neatly.
        """
        for past_text in user_text_history[user_id][-3:]:
            full_context += f"\nUser asked earlier: {past_text}"
        full_context += f"\nNow solve: {current_prompt}"

        response = model.generate_content(full_context)
        
        if response.text:
            user_text_history[user_id].append(current_prompt)
            await bot.edit_message_text(response.text, message.chat.id, wait_message.message_id)
        else:
            await bot.edit_message_text("❌ Maaf kijiyega, main iska jawab nahi dhoondh paya.", message.chat.id, wait_message.message_id)
    except Exception as e:
        print(f"Error: {e}")
        await bot.edit_message_text("❌ Sawaal ka jawab nikalne mein koi technical dikkat aayi hai.", message.chat.id, wait_message.message_id)

# MAIN FUNCTION
async def main():
    print("Bot chalu ho raha hai (Tutor Style)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
