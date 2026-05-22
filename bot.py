import io
import os
import telebot
from PIL import Image
import google.generativeai as genai

# API Keys (इन्हें अपने क्रेडेंशियल्स के साथ बदलें या एनवायरनमेंट वेरिएबल्स का उपयोग करें)
TELEGRAM_BOT_TOKEN = "8683419082:AAH-7xsJbiz_ipiuut1B-H8tWJgvZv6IP6g"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# Gemini API कॉन्फ़िगरेशन
genai.configure(api_key=GEMINI_API_KEY)

# JEE Mentor AI के लिए विस्तृत System Instruction
SYSTEM_INSTRUCTION = """
You are "JEE Mentor AI", an advanced Hindi AI teacher made only for JEE aspirants.
Your main goal is to help students in Physics, Chemistry, and Mathematics for JEE Main and Advanced.

IMPORTANT LANGUAGE RULES:
- You must ALWAYS reply ONLY in Hindi language.
- Use simple and natural Hindi.
- English words can be used only for PCM terms like: Physics, Chemistry, Maths, Formula, Equation, Chapter, Revision, concept, solution, preparation etc.
- Never reply fully in English.

MAIN RULES:
1. You ONLY talk about: Physics, Chemistry, Mathematics, JEE preparation, Study motivation, Revision strategy, Time management, PYQ practice, Mock tests, NCERT, Doubt solving, and Career guidance related to PCM.
2. If user asks unrelated things like movies, hacking, politics, adult content, general chat etc., reply ONLY:
"मैं केवल JEE PCM पढ़ाई में मदद करने वाला AI Mentor हूँ 😊"
3. Personality: Friendly, smart, supportive, patient, and motivational. Avoid overconfident or bragging language. Be humble.
4. If student feels stressed, reply in a motivational style:
"JEE मुश्किल जरूर है, लेकिन रोज़ की consistency तुम्हें बहुत आगे ले जाएगी 💪"
5. Doubt Solving Method:
- Recognize the subject (Physics, Chemistry, Maths).
- Explain step-by-step in simple language.
- Explain the Formula and key concept first, then provide the solution and clearly state the final answer.
6. If student says "समझ नहीं आया", explain in even simpler terms with a real-life example or a small trick.
7. If student says "Short trick बताओ", provide a fast JEE-solving trick or time-saving method.
8. If student asks for a timetable, ask them for: Class, Target percentile/rank, Weak subjects, and Daily study hours.
9. If unsure about an answer, say: "इस question को carefully recheck करते हैं।"
10. formatting: Clean answers, bullet points, headings, and proper equations.
"""

# Gemini 2.5 Flash मॉडल को सिस्टम इंस्ट्रक्शन के साथ इनिशियलाइज़ करना
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
)

# Telegram Bot इनिशियलाइज़ करना
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# चैट हिस्ट्री स्टोर करने के लिए डिक्शनरी (यह प्रत्येक यूज़र के लिए अलग चैट सेशन रखेगा)
# नोट: प्रोडक्शन के लिए डेटाबेस का उपयोग करना बेहतर होता है।
chat_sessions = {}

def get_chat_session(chat_id):
    """यूज़र के लिए पुराना चैट सेशन प्राप्त करें या नया शुरू करें"""
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
    return chat_sessions[chat_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "नमस्ते! मैं हूँ आपका **JEE Mentor AI** 🎓\n\n"
        "मैं यहाँ Physics, Chemistry, और Mathematics की तैयारी में आपकी मदद करने के लिए हूँ।\n"
        "आप मुझसे:\n"
        "🔹 PCM के डाउट्स पूछ सकते हैं\n"
        "🔹 Numericals और Formulae समझ सकते हैं\n"
        "🔹 Revision Strategy और Timetable बना सकते हैं\n"
        "🔹 किसी सवाल का फोटो भेजकर भी हल पा सकते हैं\n\n"
        "अपनी पढ़ाई से जुड़ा कोई भी सवाल यहाँ पूछें!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    chat_id = message.chat.id
    user_text = message.text

    try:
        # यूज़र का चैट सेशन प्राप्त करें
        chat = get_chat_session(chat_id)
        
        # Gemini API से रिस्पॉन्स प्राप्त करें
        response = chat.send_message(user_text)
        
        # उत्तर भेजें
        bot.reply_to(message, response.text, parse_mode="Markdown")
    except Exception as e:
        print(f"Error handling text: {e}")
        bot.reply_to(message, "क्षमा करें, कुछ तकनीकी समस्या आ रही है। कृपया पुनः प्रयास करें।")

@bot.message_handler(content_types=['photo'])
def handle_image_message(message):
    chat_id = message.chat.id
    
    try:
        # बोट को 'typing' ऐक्शन दिखाने के लिए
        bot.send_chat_action(chat_id, 'upload_photo')
        
        # टेलीग्राम से इमेज फाइल डाउनलोड करना
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # इमेज को PIL प्रारूप में खोलना
        image = Image.open(io.BytesIO(downloaded_file))
        
        # यदि यूज़र ने इमेज के साथ कोई टेक्स्ट (कैप्शन) भी भेजा है
        prompt = message.caption if message.caption else "इस इमेज में दिए गए JEE सवाल को पहचानें और इसे step-by-step हल करें।"
        
        # सिस्टम इंस्ट्रक्शन का संदर्भ देने के लिए प्रॉम्ट को मॉडिफाई करना
        final_prompt = f"{prompt}\n\nNote: Follow your standard JEE guidelines, explain steps, formulas, and respond in natural Hindi."
        
        # इमेज इनपुट के लिए सीधे मॉडल का उपयोग (मल्टीमॉडल रिस्पॉन्स)
        response = model.generate_content([final_prompt, image])
        
        bot.reply_to(message, response.text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error handling image: {e}")
        bot.reply_to(message, "कृपया थोड़ा clear photo भेजो 😊")

if __name__ == "__main__":
    print("JEE Mentor AI Bot सक्रिय है और संदेशों की प्रतीक्षा कर रहा है...")
    # बोट को पोलिंग मोड में चालू करना
    bot.infinity_polling()
