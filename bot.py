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

# 🧠 Har user ki alag memory (history) track karne ke liye dictionary
user_chats = {}

def get_user_chat(user_id):
    """Agar user naya hai toh nayi chat session shuru karega, nahi toh purani chalayega"""
    if user_id not in user_chats:
        # Bot ko ek personal assistant aur PCM expert ki tarah treat karne ka system instruction
        user_chats[user_id] = model.start_chat(history=[])
    return user_chats[user_id]

@dp.message(Command("start"))
async def start_command(message: types.Message):
    # /start dabate hi purani memory refresh ho jayegi
    if message.from_user.id in user_chats:
        del user_chats[message.from_user.id]
    await message.reply("👋 Hello! Main aapka PCM Doubt Solver Bot hoon, aur ab mujhe aapki saari baatein yaad rahengi! Mujhe koi bhi sawaal likh kar ya photo kheench kar bhejiye.")

# 📸 1. PHOTO WITH MEMORY HANDLE KARNE KE LIYE
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    await message.reply("🔄 Photo mil gayi hai! Solution taiyar ho raha hai...")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        file_bytes = await bot.download_file(file_path)
        image_data = file_bytes.read()

        # User ki chat history nikalna
        chat = get_user_chat(message.from_user.id)

        # Photo aur text prompt ko history mein bhejkar jawab lena
        response = chat.send_message([
            {"mime_type": "image/jpeg", "data": image_data},
            "Solve this PCM question step-by-step in Hindi and English mix language clearly."
        ])
        
        if response.text:
            await message.reply(response.text)
        else:
            await message.reply("❌ Maaf kijiyega, AI koi jawab nahi bana paya.")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("❌ Photo process karne mein galti hui!")

# 💬 2. TEXT WITH MEMORY HANDLE KARNE KE LIYE
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_text(message: types.Message):
    try:
        # User ki chat history nikalna
        chat = get_user_chat(message.from_user.id)
        
        # Gemini ko chat history ke sath message bhejna
        response = chat.send_message(message.text)
        
        if response.text:
            await message.reply(response.text)
        else:
            await message.reply("❌ Maaf kijiyega, main iska jawab nahi dhoondh paya.")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("❌ Sawaal ka jawab nikalne mein koi technical dikkat aayi hai.")

async def main():
    print("Bot chalu ho raha hai...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
