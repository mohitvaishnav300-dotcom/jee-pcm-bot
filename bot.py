import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai

# ---- CONFIGURATION ----
# Token aur Key yahan direct dal sakte hain ya Server settings me environment variable bana sakte hain
TELEGRAM_TOKEN = "8683419082:AAH-7xsJbiz_ipiuut1B-H8tWJgvZv6IP6g"
GEMINI_API_KEY = "AIzaSyCBLHf6D5o3BBwoalhfF4sNIoC9z50D9cg"

# Initialize Bot and Dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ---- BOT COMMANDS ----
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply(
        "👋 Hello! Main aapka **IIT-JEE PCM Solver Bot** hoon.\n\n"
        "📸 Mujhe Physics, Chemistry, ya Maths ke question ki **Image (Photo)** bhejiye, "
        "main aapko step-by-step solution dunga!"
    )

# ---- IMAGE HANDLER (CRASH PROOF) ----
@dp.message(lambda message: message.photo)
async def process_question_image(message: types.Message):
    status_message = await message.reply("⏳ Aapka question mil gaya hai. Sahi solution generate ho raha hai, kripya thoda intezar karein...")
    
    try:
        # 1. Image download karein
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_success = await bot.download_file(file_info.file_path)
        
        # 2. Image ko bytes me convert karein AI ke liye
        image_bytes = file_success.read()
        
        # 3. AI Prompts set karein taaki IIT-JEE level ka answer mile
        prompt = (
            "Aap ek expert IIT-JEE teacher hain. Is image mein diye gaye Physics/Chemistry/Maths "
            "ke question ko dhyan se padhein aur samajhein. Phir uska bilkul sahi aur step-by-step "
            "solution Hindi aur English (Hinglish) mix language mein dein taaki student ko acche se samajh aaye."
        )
        
        # 4. Gemini AI se answer lein
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        # 5. Answer user ko bhein (Agar answer bada ho toh crash na ho isliye chunking)
        answer_text = response.text
        if len(answer_text) > 4000:
            for i in range(0, len(answer_text), 4000):
                await message.reply(answer_text[i:i+4000], parse_mode="Markdown")
        else:
            await message.reply(answer_text, parse_mode="Markdown")
            
    except Exception as e:
        # Agar koi error aaye toh bot crash nahi hoga, bas ye message dikha dega
        print(f"Error occurred: {e}")
        await message.reply("❌ Maaf kijiyega, is photo ko samajhne mein dikkat hui. Kripya clear photo kheencho ya thodi der baad try karein.")
    
    finally:
        # Status message delete karna
        await bot.delete_message(chat_id=message.chat.id, message_id=status_message.message_id)

# ---- MAIN RUNNER ----
async def main():
    print("Bot start ho raha hai... Bina kisi crash ke chalne ke liye taiyar!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())