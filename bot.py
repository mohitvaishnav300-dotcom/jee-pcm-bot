import asyncio
import io
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from sympy import sympify, solve
from PIL import Image, ImageDraw, ImageFont
import pytesseract

# 🔑 Replace with your own keys
TELEGRAM_TOKEN = "8683419082:AAH-7xsJbiz_ipiuut1B-H8tWJgvZv6IP6g"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Function: Solve math expression
def solve_math(expression):
    try:
        expr = sympify(expression)
        solution = solve(expr)
        return f"Math Answer: {solution}"
    except Exception:
        return None

# Function: Generate AI response
def ai_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {e}"

# Function: Generate answer image
def generate_image(answer_text):
    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((20, 120), answer_text, fill="black", font=font)

    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output

# Function: OCR for photo questions
def extract_text_from_photo(photo_path):
    try:
        text = pytesseract.image_to_string(Image.open(photo_path))
        return text.strip()
    except Exception as e:
        return f"OCR Error: {e}"

# Start command
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Hello 👋, I am your AI Study Bot!\nSend me a math problem, study question, or even a photo.")

# Text handler
@dp.message(lambda msg: msg.text)
async def text_handler(message: Message):
    user_text = message.text.strip()

    # Try math solver first
    math_answer = solve_math(user_text)
    if math_answer:
        answer_text = math_answer
    else:
        # If not math, use AI
        answer_text = ai_response(user_text)

    # Send image answer
    img = generate_image(answer_text)
    await message.answer_photo(img)

# Photo handler
@dp.message(lambda msg: msg.photo)
async def photo_handler(message: Message):
    photo = message.photo[-1]
    photo_path = f"photo_{message.message_id}.jpg"
    await photo.download(destination_file=photo_path)

    # OCR extract
    extracted_text = extract_text_from_photo(photo_path)

    # Try math solver
    math_answer = solve_math(extracted_text)
    if math_answer:
        answer_text = math_answer
    else:
        answer_text = ai_response(extracted_text)

    # Send image answer
    img = generate_image(answer_text)
    await message.answer_photo(img)

# Main entry
async def main():
    print("🤖 Extended Bot with OCR + Multi-subject is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
