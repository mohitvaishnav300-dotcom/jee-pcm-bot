import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai
from collections import defaultdict # Memory dictionary manage karne ke liye

# ---- CONFIGURATION ----
TELEGRAM_TOKEN = "8683419082:AAH-7xsJbiz_ipiuut1B-H8tWJgvZv6IP6g"
API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Bot and Dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Configure Gemini AI
if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=API_KEY)
    
# Naye memory format ke liye GenerativeModel ko function mein convert karna better hai
def get_gemini_model(model_name="gemini-2.5-flash"):
    return genai.GenerativeModel(model_name)

# 🧠 Har user ki alag memory (history) track karne ke liye defaultdict
# Isse agar user_id nahi mila toh error nahi aayega, nayi history ban jayegi
user_chats_history = defaultdict(list)

# Gemini ChatSession ko restart/resume karne ka logic
def get_user_chat_session(user_id):
    model = get_gemini_model()
    # Purani history ko fetch karein, agar user naya ho toh empty list use karein
    history = user_chats_history[user_id]
    # Naya ChatSession return karein with history
    return model.start_chat(history=history)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    # /start dabate hi user ki memory clear ho jayegi (optional)
    if message.from_user.id in user_chats_history:
        del user_chats_history[message.from_user.id]
    await message.reply("👋 Hello! Main aapka PCM Doubt Solver Bot hoon, Memory ke saath! Mujhe sawaal ya photo bhejiye, main steps-wise solution doonga!")

# 📸 1. PHOTO WITH MEMORY HANDLE KARNE KE LIYE (Improved Error Handling)
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    wait_message = await message.reply("🔄 Photo mil gayi hai! Solution taiyar ho raha hai, kripya thoda sabr rakhein...")
    
    try:
        # Photo download karein
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        
        # Binary data download karein
        file_bytes = await bot.download_file(file_path)
        image_data = file_bytes.read()

        # User ki chat session nikalna
        user_id = message.from_user.id
        chat_session = get_user_chat_session(user_id)

        # Photo aur prompt ko send karna
        # Note: ChatSession mein photo seedhe send_message mein support ho sakta hai, otherwise we need to structure it differently.
        # Structured input works best.
        
        prompt = "Solve this PCM question step-by-step in Hindi and English mix language clearly."
        
        # Method 1 (Supported by recent google-generativeai versions for structured requests)
        content = [
            {"mime_type": "image/jpeg", "data": image_data},
            prompt
        ]
        
        response = chat_session.send_message(content)
        
        # Jawab process karein
        if response and response.text:
            # Memory check logic: Agar reply bohot bada hai, toh history short rehne dein
            # History mein sirf text messages store karein (photo as bytes size badha deta hai)
            user_chats_history[user_id].append({"role": "user", "parts": [prompt]})
            user_chats_history[user_id].append({"role": "model", "parts": [response.text]})
            
            await bot.edit_message_text(response.text, message.chat.id, wait_message.message_id)
        else:
            await bot.edit_message_text("❌ Maaf kijiyega, AI koi jawab nahi bana paya. Kripya doosri photo try karein.", message.chat.id, wait_message.message_id)
            
    except Exception as e:
        print(f"ERROR processing photo for user {message.from_user.id}: {e}")
        # Error handling code yahan response short kar deta hai
        await bot.edit_message_text(f"❌ Photo process karne mein galti hui! Error Detail: {str(e)[:100]}...", message.chat.id, wait_message.message_id)

# 💬 2. TEXT WITH MEMORY HANDLE KARNE KE LIYE
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_text(message: types.Message):
    wait_message = await message.reply("🔄 Aapka sawaal mil gaya hai! Soch raha hoon...")
    
    try:
        user_id = message.from_user.id
        chat_session = get_user_chat_session(user_id)
        
        prompt = message.text
        # Hindi/English mixed prompt structure if user just sends text
        if not prompt.lower().startswith("solve"):
             prompt_structured = f"Solve this PCM question step-by-step in Hindi and English mix language: {prompt}"
        else:
             prompt_structured = prompt
        
        # Gemini ko chat history ke sath message bhejna
        response = chat_session.send_message(prompt_structured)
        
        if response and response.text:
            # History track karna (text photo processing ke samay save karte hain)
            user_chats_history[user_id].append({"role": "user", "parts": [prompt_structured]})
            user_chats_history[user_id].append({"role": "model", "parts": [response.text]})
            
            await bot.edit_message_text(response.text, message.chat.id, wait_message.message_id)
        else:
            await bot.edit_message_text("❌ Maaf kijiyega, main iska jawab nahi dhoondh paya.", message.chat.id, wait_message.message_id)
            
    except Exception as e:
        print(f"ERROR processing text for user {message.from_user.id}: {e}")
        await bot.edit_message_text("❌ Sawaal ka jawab nikalne mein koi technical dikkat aayi hai.", message.chat.id, wait_message.message_id)

async def main():
    print("Bot chalu ho raha hai...")
    # Check variables before starting
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN not set!")
        return
        
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
