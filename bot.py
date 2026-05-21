import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai

# ---- कॉन्फ़िगरेशन ----
TELEGRAM_TOKEN = "8683419082:AAH-7xsJbiz_ipiuut1B-H8tWJgvZv6IP6g"   # अपना BotFather टोकन डालें
API_KEY = os.environ.get("GEMINI_API_KEY")   # Render/GitHub में GEMINI_API_KEY सेट करें

# Bot और Dispatcher शुरू करें
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Gemini AI कॉन्फ़िगर करें
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# 🧠 साधारण मेमोरी: पिछले 3 सवाल याद रखेगा
user_text_history = {}

# 🚀 START कमांड
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user_text_history[user_id] = []
    await message.reply("👋 नमस्ते! मैं आपका Class 11 PCM Tutor Bot हूँ। Physics, Chemistry, Math के JEE सवाल भेजिए, मैं स्टेप‑बाय‑स्टेप हल दूँगा।")

# 📸 फोटो हैंडल करना
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    wait_message = await message.reply("🔄 फोटो मिल गई है! हल तैयार हो रहा है, कृपया थोड़ा इंतज़ार करें...")
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        file_bytes = await bot.download_file(file_path)
        image_data = file_bytes.read()

        # Tutor स्टाइल प्रॉम्प्ट
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data},
            """आप एक प्रोफेशनल JEE PCM Tutor हैं।
            - केवल Class 11 Physics, Chemistry और Math के सवाल हल करें।
            - स्टेप‑बाय‑स्टेप हल दीजिए।
            - हिंदी‑English मिक्स भाषा में समझाइए।
            - हर स्टेप में फ़ॉर्मूला और कारण बताइए।
            - अंतिम उत्तर को साफ़ तरीके से अलग दिखाइए।
            """
        ])
        
        if response.text:
            await bot.edit_message_text(response.text, message.chat.id, wait_message.message_id)
        else:
            await bot.edit_message_text("❌ माफ़ कीजिए, AI कोई हल नहीं बना पाया।", message.chat.id, wait_message.message_id)
    except Exception as e:
        print(f"Error: {e}")
        await bot.edit_message_text("❌ फोटो प्रोसेस करने में समस्या हुई, कृपया दोबारा कोशिश करें।", message.chat.id, wait_message.message_id)

# 💬 टेक्स्ट हैंडल करना
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text.lower()

    # अगर यूज़र casual greeting करे
    if user_input in ["hi", "hii", "hyy", "hello", "hey", "namaste"]:
        await message.reply("👋 नमस्ते! मैं आपका JEE Class 11 PCM Tutor हूँ. "
                            "मैं आपकी तैयारी में किस तरह मदद कर सकता हूँ?")
        return

    wait_message = await message.reply("🔄 आपका सवाल मिल गया है! सोच रहा हूँ...")

    try:
        if user_id not in user_text_history:
            user_text_history[user_id] = []
            
        current_prompt = message.text
        full_context = """आप एक प्रोफेशनल JEE PCM Tutor हैं।
        - केवल Class 11 Physics, Chemistry और Math के सवाल हल करें।
        - स्टेप‑बाय‑स्टेप हल दीजिए।
        - हिंदी‑English मिक्स भाषा में समझाइए।
        - हर स्टेप में फ़ॉर्मूला और कारण बताइए।
        - अंतिम उत्तर को साफ़ तरीके से अलग दिखाइए।
        """
        for past_text in user_text_history[user_id][-3:]:
            full_context += f"\nपहले पूछा गया सवाल: {past_text}"
        full_context += f"\nअब हल करें: {current_prompt}"

        response = model.generate_content(full_context)

        if response.text:
            user_text_history[user_id].append(current_prompt)
            await bot.edit_message_text(response.text, message.chat.id, wait_message.message_id)
        else:
            await bot.edit_message_text("❌ माफ़ कीजिए, मैं इसका हल नहीं ढूँढ पाया।", message.chat.id, wait_message.message_id)
    except Exception as e:
        print(f"Error: {e}")
        await bot.edit_message_text("❌ सवाल का हल निकालने में तकनीकी समस्या हुई।", message.chat.id, wait_message.message_id)

# MAIN FUNCTION
async def main():
    print("Bot चालू हो रहा है (Class 11 PCM Tutor)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
