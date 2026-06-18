import telebot, math, re, time, os
from flask import Flask, request

TOKEN = '8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ'
WEB_URL = "https://yen-xxch.onrender.com"
ADMIN_USER = 'leductai51'

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

USER_FILE = "users.txt"
if not os.path.exists(USER_FILE): open(USER_FILE, "w").close()
with open(USER_FILE, "r") as f:
    users_set = set(line.strip() for line in f if line.strip())

def save_user(uid):
    uid_str = str(uid)
    if uid_str not in users_set:
        users_set.add(uid_str)
        with open(USER_FILE, "a") as f: f.write(uid_str + "\n")

def process_matrix(h):
    n = [int(c, 16) for c in h]
    length = len(h)
    rows = length // 8
    m_sum = sum(n[r * 8 + (r % 8)] for r in range(rows))
    a_sum = sum(n[r * 8 + ((7 - r) % 8)] for r in range(rows))
    score = (1.5 if m_sum % 2 == 0 else -1.5) + (1.2 if a_sum % 2 == 0 else -1.2)
    fwd, bwd = 0xABCDE123, 0x321EDCBA
    for i in range(length):
        fwd = (fwd ^ (n[i] << (i % 7))) & 0xFFFFFFFF
        fwd = (fwd >> 1) | ((fwd & 1) << 31)
        bwd = (bwd ^ (n[length - 1 - i] << (i % 7))) & 0xFFFFFFFF
        bwd = (bwd >> 1) | ((bwd & 1) << 31)
    score += 2.0 if ((fwd ^ bwd) & 1) == 0 else -2.0
    edge = sum(n[c] + n[(rows - 1) * 8 + c] for c in range(8))
    score += 1.3 if edge % 2 == 0 else -1.3
    choice = "TÀI" if score > 0 else "XỈU" if score < 0 else "BỎ QUA"
    rate = 50 + (49.6 / (1 + math.exp(-0.5 * (abs(score) - 2))))
    return choice, rate, "MD5" if length == 32 else "SHA-256"

@app.route('/')
def home(): return "OK", 200

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if m.from_user.username != ADMIN_USER: return
    bot.send_message(m.chat.id, f"👑 <b>ADMIN PANEL</b>\n📊 Users: <b>{len(users_set)}</b>\n📢 Gửi thông báo: <code>/thongbao [Nội dung]</code>", parse_mode="HTML")

@bot.message_handler(commands=['thongbao'])
def broadcast(m):
    if m.from_user.username != ADMIN_USER: return
    msg = m.text.replace("/thongbao", "").strip()
    if not msg: return
    s, f = 0, 0
    for uid in list(users_set):
        try:
            bot.send_message(int(uid), msg, parse_mode="HTML")
            s += 1
        except: f += 1
    bot.send_message(m.chat.id, f"✅ Thành công: {s} | ❌ Lỗi: {f}")

@bot.message_handler(commands=['start', 'help'])
def start(m):
    save_user(m.chat.id)
    bot.send_message(m.chat.id, "🤖 <b>NEURAL HASH MATRIX</b>\n👉 Gửi chuỗi MD5 hoặc SHA-256 để phân tích.", parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def analyze(m):
    save_user(m.chat.id)
    h = m.text.strip().lower().replace(" ", "")
    if not re.match(r"^[a-f0-9]{32}$|^[a-f0-9]{64}$", h): return
    choice, rate, t = process_matrix(h)
    icon = "🔴" if choice == "TÀI" else "🟢" if choice == "XỈU" else "⚪"
    bot.send_message(m.chat.id, f"🔮 <b>{t} RESULT</b>\n🔹 Gợi ý: {icon} <b>{choice}</b>\n🔹 Tỷ lệ: <b>{rate:.1f}%</b>", parse_mode="HTML")

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(0.2)
    bot.set_webhook(url=f"{WEB_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
