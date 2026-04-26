import os
import json
import threading
import time
import random
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

DATA_FILE = "data.json"
TIMER = {}
QUOTES = [
    "“অসাধারণ কিছুর জন্য আজ কঠিনটা করি, কাল সেটার ফল আসবেই।”",
    "“শক্ত বাতাসই উড়ানাকে চরম করে তোলে।”",
    "“প্রতিদিনের ছোট ছোট অধ্যবসায়েই সফলতা।”",
    "“ফোকাস থাকুন, আকাশ পর্যন্ত সম্ভাবনা।”",
    "“পড়াশোনা হলো নিজের ডানা মেলে দেওয়ার শুরু।”"
]

MUSIC_LINK = "https://www.youtube.com/watch?v=jfKfPfyJRdk"  # Lo-fi Girl Stream

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম ক্যাপটেন! 👨‍✈️ আপনার স্টাডি ডেক-এ আপনাকে স্বাগতম। আকাশ পরিষ্কার, আজ আমরা অনেক দূর যাবো। আপনার মিশন শুরু করতে /takeoff লিখুন।",
        reply_markup=ReplyKeyboardMarkup(
            [["/takeoff", "/plan"], ["/fuel", "/stats", "/music"]],
            resize_keyboard=True
        )
    )

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await update.message.reply_text("✈️ আজকের ফ্লাইট প্ল্যান (To-Do) পাঠান (এক লাইনেই লিখুন):")
    TIMER[user_id] = {'await_plan': True}

async def plan_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in TIMER and TIMER[user_id].get('await_plan'):
        data = load_data()
        if user_id not in data:
            data[user_id] = {}
        data[user_id]['plan'] = update.message.text
        save_data(data)
        TIMER[user_id]['await_plan'] = False
        await update.message.reply_text(f"✅ আপনার ফ্লাইট প্ল্যান সেট হয়েছে: {update.message.text}")

async def takeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    start_time = datetime.now().isoformat()
    if user_id not in data:
        data[user_id] = {}
    data[user_id]['flight'] = {'start': start_time, 'running': True}
    save_data(data)
    await update.message.reply_text(
        "ইঞ্জিন স্টার্ট হচ্ছে... 🚀 আপনার ২৫ মিনিটের স্টাডি ফ্লাইট শুরু হলো। মোবাইল থেকে দূরে থাকুন এবং ফোকাস করুন। শুভ যাত্রা!"
    )
    threading.Thread(target=mission_timer, args=(context, user_id), daemon=True).start()

def mission_timer(context, user_id):
    time.sleep(25*60)
    data = load_data()
    info = data.get(user_id, {}).get('flight')
    if info and info.get('running'):
        context.application.create_task(
            context.bot.send_message(
                chat_id=int(user_id),
                text="অভিনন্দন পাইলট! 🛬 আমরা সফলভাবে ল্যান্ড করেছি। এখন ৫ মিনিটের 'রিফুয়েলিং' (বিরতি) নিন। আবার উড়তে চাইলে আমাদের জানান।"
            )
        )
        start = datetime.fromisoformat(info['start'])
        mins = 25
        data[user_id]['flight']['running'] = False
        sess = {'start': info['start'], 'duration': mins}
        if 'history' not in data[user_id]:
            data[user_id]['history'] = []
        data[user_id]['history'].append(sess)
        save_data(data)

async def landing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    info = data.get(user_id, {}).get('flight')
    if info and info.get('running'):
        start = datetime.fromisoformat(info['start'])
        end = datetime.now()
        mins = int((end - start).total_seconds()//60)
        data[user_id]['flight']['running'] = False
        sess = {'start': info['start'], 'duration': mins}
        if 'history' not in data[user_id]:
            data[user_id]['history'] = []
        data[user_id]['history'].append(sess)
        save_data(data)
        await update.message.reply_text(f"🛬 সফল ল্যান্ডিং! আপনি {mins} মিনিট পড়েছেন।")
    else:
        await update.message.reply_text("কোন চলমান ফ্লাইট নেই!")

async def fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(QUOTES)
    await update.message.reply_text(f"⛽️ Fuel Station:\n\n{quote}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    total = 0
    today = datetime.now().date()
    for sess in data.get(user_id, {}).get('history', []):
        dt = datetime.fromisoformat(sess['start'])
        if dt.date() == today:
            total += sess.get('duration',0)
    await update.message.reply_text(f"📊 আজকের ল্যান্ডিং রিপোর্ট:\nআপনি মোট {total} মিনিট আকাশে ছিলেন (পড়েছেন)!")

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎧 Cockpit Music:\n{MUSIC_LINK}")

async def abort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    info = data.get(user_id, {}).get('flight')
    if info and info.get('running'):
        data[user_id]['flight']['running'] = False
        save_data(data)
        await update.message.reply_text("⚠️ জরুরি অবতরণ (Break)! আপনার সেশন বাতিল করা হয়েছে।")
    else:
        await update.message.reply_text("কোন ফ্লাইট রানিং নেই!")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("⚠️ টেলিগ্রাম বট টোকেন সেট করুন!")
        return
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("takeoff", takeoff))
    app.add_handler(CommandHandler("landing", landing))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("fuel", fuel))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("abort", abort))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), plan_msg))

    app.run_polling()

if __name__ == "__main__":
    main()