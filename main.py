import telebot
import json
import random
import re
import os
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ───────────────────────────────────────────
TOKEN = "8097779875:AAGw4kiMa0KqFVi2yh429g0TJCTpfx4aSnM"
PRIMARY_ADMIN_ID = "5399171337"  # asosiy admin (bu o'zgarmasdan qoladi)
# ───────────────────────────────────────────

bot = telebot.TeleBot(TOKEN)

TESTS_FILE = 'tests.json'
USERS_FILE = 'users.json'
ADMINS_FILE = 'admins.json'  # yangi fayl – adminlar ro'yxatini saqlash uchun

def load_data(file_name, default):
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

tests = load_data(TESTS_FILE, {})
users = load_data(USERS_FILE, {})
admins = load_data(ADMINS_FILE, [PRIMARY_ADMIN_ID])  # defaultda faqat asosiy admin

user_state = {}

def is_admin(uid):
    return str(uid) in admins

def is_valid_test_id(test_id):
    return bool(re.match(r'^\d{4,5}$', test_id))

def generate_unique_test_id():
    existing = set(tests.keys())
    while True:
        new_id = str(random.randint(10000, 99999))
        if new_id not in existing:
            return new_id

def parse_answers(answers_str):
    answers = {}
    cleaned = re.sub(r'\s+', '', answers_str.lower())

    if re.search(r'\d+[a-z]', cleaned):
        matches = re.findall(r'(\d+)([a-z])', cleaned)
        for num, letter in matches:
            answers[int(num)] = letter
    else:
        i = 1
        for char in cleaned:
            if char.isalpha():
                answers[i] = char
                i += 1

    return answers

@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = str(message.from_user.id)
    if uid in users:
        send_main_keyboard(message)
    else:
        user_state[uid] = "waiting_ism"
        bot.reply_to(message, "Xush kelibsiz! Ismingizni yozing (masalan: Erkinjon)")

@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state and user_state[str(m.from_user.id)] == "waiting_ism")
def handle_ism(message):
    uid = str(message.from_user.id)
    ism = message.text.strip()
    users[uid] = {"ism": ism, "familiya": "", "tests": {}}
    user_state[uid] = "waiting_familiya"
    bot.reply_to(message, "Familiyangizni yozing (masalan: Orziqulov)")

@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state and user_state[str(m.from_user.id)] == "waiting_familiya")
def handle_familiya(message):
    uid = str(message.from_user.id)
    familiya = message.text.strip()
    users[uid]["familiya"] = familiya
    save_data(USERS_FILE, users)
    del user_state[uid]
    bot.reply_to(message, "Registratsiya muvaffaqiyatli!")
    send_main_keyboard(message)

def send_main_keyboard(message):
    uid = str(message.from_user.id)
    ism = users.get(uid, {}).get('ism', 'Nomaʼlum')
    familiya = users.get(uid, {}).get('familiya', 'Nomaʼlum')

    text = f"""Ism: {ism}
Familiya: {familiya}

📒 Foydalanish yo'riqnomasi:
Test javobini tekshirish uchun:
1543*abcdbcda
yoki
1543*1a2b3c4d5b6c7d8a
shaklida yozing.

Yangi test yaratish (adminlar uchun):
*Matematika*abcdbcda
yoki
*Ona tili*1a2b3c4d5e"""

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Natijalarimni ko'rish", "Statistika")
    markup.add("Ism/Familiyani o'zgartirish")
    
    if is_admin(uid):
        markup.add("Test qatnashuvchilari")
        markup.add("Admin qo'shish")           # yangi tugma

    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Natijalarimni ko'rish")
def show_my_results(message):
    uid = str(message.from_user.id)
    if uid not in users or not users[uid].get('tests'):
        bot.reply_to(message, "Hali hech qanday test ishlmadingiz.")
        return

    text = "Sizning natijalaringiz:\n\n"
    for tid, res in users[uid]['tests'].items():
        text += f"Test: {tid}\n"
        text += f"To'g'ri: {res['correct']}/{res['total']}\n"
        text += f"Foiz: {res['percent']}%\n"
        text += f"Sana: {res['date']}\n\n"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text == "Statistika")
def show_statistika(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        bot.reply_to(message, "Bu funksiya faqat admin uchun.")
        return
    text = f"Foydalanuvchilar: {len(users)}\nTestlar: {len(tests)}\nAdminlar: {len(admins)}"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text == "Ism/Familiyani o'zgartirish")
def change_name(message):
    uid = str(message.from_user.id)
    if uid not in users:
        bot.reply_to(message, "Avval /start buyrug'ini bering.")
        return
    user_state[uid] = "changing_ism"
    bot.reply_to(message, "Yangi ismingizni yozing:")

@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state and user_state[str(m.from_user.id)] == "changing_ism")
def change_ism(message):
    uid = str(message.from_user.id)
    users[uid]["ism"] = message.text.strip()
    user_state[uid] = "changing_familiya"
    bot.reply_to(message, "Yangi familiyangizni yozing:")

@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state and user_state[str(m.from_user.id)] == "changing_familiya")
def change_familiya(message):
    uid = str(message.from_user.id)
    users[uid]["familiya"] = message.text.strip()
    save_data(USERS_FILE, users)
    del user_state[uid]
    bot.reply_to(message, "Ma'lumotlar yangilandi!")
    send_main_keyboard(message)

# ─── Yangi: Admin qo'shish ───
@bot.message_handler(func=lambda m: m.text == "Admin qo'shish")
def ask_new_admin_id(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        bot.reply_to(message, "Faqat adminlar yangi admin qo'sha oladi.")
        return
    
    user_state[uid] = "waiting_new_admin_id"
    bot.reply_to(message, "Yangi adminning Telegram ID sini yuboring (raqam sifatida):")

@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state and user_state[str(m.from_user.id)] == "waiting_new_admin_id")
def add_new_admin(message):
    uid = str(message.from_user.id)
    new_admin_id = message.text.strip()

    if not new_admin_id.isdigit():
        bot.reply_to(message, "ID faqat raqamlardan iborat bo'lishi kerak.")
        del user_state[uid]
        return

    if new_admin_id in admins:
        bot.reply_to(message, f"{new_admin_id} allaqachon admin.")
        del user_state[uid]
        return

    admins.append(new_admin_id)
    save_data(ADMINS_FILE, admins)
    del user_state[uid]

    bot.reply_to(message, f"✅ {new_admin_id} endi admin qilib qo'shildi!")
    # yangi adminni xabardor qilish (ixtiyoriy)
    try:
        bot.send_message(new_admin_id, "Sizga admin huquqlari berildi! /start buyrug'ini bosing.")
    except:
        pass  # agar bot bilan boshlamagan bo'lsa xato chiqmaydi

@bot.message_handler(func=lambda m: m.text == "Test qatnashuvchilari")
def ask_test_id_for_participants(message):
    uid = str(message.from_user.id)
    if not is_admin(uid):
        bot.reply_to(message, "Faqat admin uchun.")
        return
    user_state[uid] = "waiting_test_id_participants"
    bot.reply_to(message, "Test kodini kiriting (masalan: 57991):")

@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state and user_state[str(m.from_user.id)] == "waiting_test_id_participants")
def show_test_participants(message):
    uid = str(message.from_user.id)
    test_id = message.text.strip()

    if not is_valid_test_id(test_id):
        bot.reply_to(message, "Test kodi 4 yoki 5 raqamli bo'lishi kerak.")
        del user_state[uid]
        return

    if test_id not in tests:
        bot.reply_to(message, f"Test topilmadi: {test_id}")
        del user_state[uid]
        return

    data = tests[test_id]
    participants = data.get("participants", [])

    if not participants:
        bot.reply_to(message, "Bu testga hali hech kim javob bermagan.")
        del user_state[uid]
        return

    results = []
    for pid in participants:
        if pid in users and test_id in users[pid]['tests']:
            res = users[pid]['tests'][test_id]
            name = f"{users[pid]['ism']} {users[pid]['familiya']}"
            results.append((name, res['correct'], res['total']))

    results.sort(key=lambda x: -x[1])

    text = f"Test {test_id} qatnashuvchilari:\n\n"
    for i, (name, correct, total) in enumerate(results, 1):
        text += f"{i}) {name} — {correct}/{total}\n"

    bot.reply_to(message, text)
    del user_state[uid]

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    text = message.text.strip()
    uid = str(message.from_user.id)

    if uid not in users:
        bot.reply_to(message, "Avval /start buyrug'ini bering va ro'yxatdan o'ting.")
        return

    ism = users[uid]["ism"]
    familiya = users[uid]["familiya"]

    # ─── Admin: yangi test yaratish ───
    if is_admin(uid) and text.startswith('*') and text.count('*') >= 2:
        try:
            _, mavzu, javoblar = text.split('*', 2)
            mavzu = mavzu.strip()
            correct_str = javoblar.strip().lower().replace(" ", "")

            if not correct_str:
                bot.reply_to(message, "Javoblar qismi bo'sh.")
                return

            correct_dict = parse_answers(correct_str)
            total = len(correct_dict)

            if total == 0 or max(correct_dict.keys()) != total or min(correct_dict.keys()) != 1:
                bot.reply_to(message, "Javoblar 1 dan boshlab ketma-ket va to'liq bo'lishi kerak.")
                return

            new_id = generate_unique_test_id()
            tests[new_id] = {
                "correct": correct_str,
                "total": total,
                "mavzu": mavzu or "Noma'lum",
                "status": "faol",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "participants": []
            }
            save_data(TESTS_FILE, tests)

            bot.reply_to(message, f"✅ Yangi test yaratildi!\nKod: {new_id}\nMavzu: {mavzu}\nSavollar: {total}\n\nJavob yuborish misoli:\n{new_id}*abcdabcd\nyoki\n{new_id}*1a2b3c4d")
            return
        except Exception as e:
            bot.reply_to(message, f"Xato: {str(e)}\nFormat: *Mavzu*Javoblar")
            return

    # ─── Oddiy foydalanuvchi: test javobini tekshirish ───
    if '*' not in text:
        bot.reply_to(message, "Javobni quyidagicha yuboring:\nKOD*javoblar\nMisol: 7108*abcdabcd")
        return

    parts = text.split('*', 1)
    if len(parts) != 2:
        bot.reply_to(message, "Format xato: KOD*javoblar")
        return

    test_id, user_ans = parts[0].strip(), parts[1].strip()

    if not is_valid_test_id(test_id):
        bot.reply_to(message, "Test kodi 4 yoki 5 raqamli bo'lishi kerak.")
        return

    if test_id not in tests:
        bot.reply_to(message, f"Test topilmadi: {test_id}")
        return

    data = tests[test_id]
    if data.get("status") != "faol":
        bot.reply_to(message, f"Test {test_id} faol emas.")
        return

    correct_str = data["correct"]
    total = data["total"]
    correct_dict = parse_answers(correct_str)
    user_dict = parse_answers(user_ans)

    if not user_dict:
        bot.reply_to(message, "Javob formati noto'g'ri.")
        return

    marks = []
    correct_count = 0

    for q in range(1, total + 1):
        ua = user_dict.get(q)
        ca = correct_dict.get(q)
        if ua == ca and ua is not None:
            marks.append(f"{q}-✅")
            correct_count += 1
        else:
            marks.append(f"{q}-❌")

    percent = round((correct_count / total) * 100) if total > 0 else 0

    reply = f"""👤 {ism} {familiya}
📖 Test: {test_id}
✏️ Savollar: {total} ta
✅ To'g'ri: {correct_count} ta
"""

    for i in range(0, len(marks), 4):
        reply += " ".join(marks[i:i+4]) + "\n"

    reply += f"🔣 Foiz: {percent}%\n"
    reply += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    reply += "Javoblar qabul qilindi!"

    bot.reply_to(message, reply)

    # Natijani saqlash
    users[uid]['tests'][test_id] = {
        "correct": correct_count,
        "total": total,
        "percent": percent,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    }
    save_data(USERS_FILE, users)

    # Participant qo'shish
    if uid not in data["participants"]:
        data["participants"].append(uid)
        save_data(TESTS_FILE, tests)

print("Bot ishga tushdi...")
bot.infinity_polling()