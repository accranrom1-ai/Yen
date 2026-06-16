import telebot
from telebot import types
import json
import os
import datetime
import time
import random
import string
import requests
from flask import Flask, render_template_string, request

# 1. CẤU HÌNH BOT TELEGRAM VÀ HỆ THỐNG
TOKEN = '8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ'
bot = telebot.TeleBot(TOKEN, threaded=False)
DATA_FILE = "users_data.json"
ADMIN_USERNAME = "leductai51"  
ADMIN_ID = 0  # Tự động nhận diện khi Admin gõ /admin
GIOI_HAN_NHIEM_VU_NGAY = 1     
LINK4M_API_KEY = "694cc66f558f587fcc15b845"
WEB_URL = "https://yen-xxch.onrender.com" 

app = Flask(__name__)

# 2. CÁC HÀM XỬ LÝ DỮ LIỆU CƠ BẢN
def doc_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def luu_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def tao_ma_ngau_nhien():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def lay_ma_he_thong():
    db = doc_data()
    if "system_config" not in db:
        db["system_config"] = {"ma_xac_nhan": tao_ma_ngau_nhien()}
        luu_data(db)
    return db["system_config"]["ma_xac_nhan"]

def lay_thong_tin_user(user_id, username=None):
    db = doc_data()
    uid = str(user_id)
    if uid not in db: db[uid] = {}
    CẤU_TRÚC_CHUẨN = {
        "balance": 0, "hoat_dong": 1, "tong_task": 0, "hoa_hong": 0, "da_moi": 0,
        "nv_hoan_thanh": 0, "state": "NONE", "lich_su_rut": [], "username": "",
        "ref_by": "", "last_task_date": "", "today_task_count": 0
    }
    for key, value in CẤU_TRÚC_CHUẨN.items():
        if key not in db[uid]: db[uid][key] = value
    if username: db[uid]["username"] = str(username).lower()
    luu_data(db)
    return db[uid]

def cap_nhat_user(user_id, key, value):
    db = doc_data()
    uid = str(user_id)
    if uid in db:
        db[uid][key] = value
        luu_data(db)

def reset_state(user_id):
    cap_nhat_user(user_id, "state", "NONE")

def la_admin(message_or_call):
    username = message_or_call.from_user.username
    uid = message_or_call.from_user.id
    if uid == ADMIN_ID or (username and username.lower() == ADMIN_USERNAME.lower()): return True
    return False

def tu_dong_tao_link_link4m(url_goc):
    try:
        api_endpoint = f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={url_goc}"
        response = requests.get(api_endpoint, timeout=10).json()
        if response.get("status") == "success": return response.get("shortenedUrl")
    except Exception as e: print(f"❌ Lỗi kết nối API Link4m: {e}")
    return None

# GIAO DIỆN MENUS
def tao_menu_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("👤 Tài khoản"), types.KeyboardButton("⛏️ Kiếm tiền"))
    markup.row(types.KeyboardButton("💸 Rút tiền"), types.KeyboardButton("✉️ Mời bạn"))
    return markup

def tao_menu_huy():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("❌ Hủy nhập mã"))
    return markup

HTML_TRANG_DICH = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XÁC MINH HOÀN THÀNH</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 90%; }
        h2 { color: #2ecc71; margin-bottom: 10px; }
        p { color: #666; font-size: 14px; margin-bottom: 25px; }
        .code-box { background: #f8f9fa; border: 2px dashed #cbd5e1; padding: 15px; font-size: 24px; font-weight: bold; color: #1e293b; border-radius: 8px; margin-bottom: 20px; }
        .btn-copy { background: #3498db; color: white; border: none; padding: 12px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;}
    </style>
</head>
<body>
    <div class="container">
        <h2>🎉 Vượt Link Thành Công!</h2>
        <p>Hãy sao chép mã bên dưới và gửi vào Bot Telegram để nhận thưởng.</p>
        <div class="code-box" id="auth-code">{{ ma_so }}</div>
        <button class="btn-copy" onclick="copyCode()">📋 SAO CHÉP MÃ</button>
    </div>
    <script>
        function copyCode() {
            var codeText = document.getElementById("auth-code").innerText;
            navigator.clipboard.writeText(codeText).then(function() {
                alert("Đã sao chép: " + codeText + "\\nQuay lại Bot và dán vào ô chat nhé!");
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def web_trang_chu(): return render_template_string(HTML_TRANG_DICH, ma_so=lay_ma_he_thong())

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    lay_thong_tin_user(message.from_user.id, message.from_user.username)
    reset_state(message.from_user.id)
    bot.send_message(message.chat.id, "👋 Chào mừng bạn đến với Bot kiếm tiền!", reply_markup=tao_menu_chinh())

@bot.message_handler(func=lambda message: message.text in ["👤 Tài khoản", "💸 Rút tiền", "✉️ Mời bạn", "⛏️ Kiếm tiền"])
def handle_menu_navigation(message):
    user_id = message.from_user.id
    reset_state(user_id)
    if message.text == "👤 Tài khoản":
        user = lay_thong_tin_user(user_id, message.from_user.username)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        luot_hom_nay = user['today_task_count'] if user['last_task_date'] == today else 0
        bot.send_message(message.chat.id, f"👤 <b>THÔNG TIN TÀI KHOẢN</b>\n────────────────────────\n🆔 ID: <code>{user_id}</code>\n💰 Số dư: <b>{user['balance']:,} VNĐ</b>\n⚡ Nhiệm vụ hôm nay: <b>{luot_hom_nay}/{GIOI_HAN_NHIEM_VU_NGAY}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif message.text == "💸 Rút tiền":
        user = lay_thong_tin_user(user_id)
        if user['balance'] < 10000:
            bot.send_message(message.chat.id, f"❌ Số dư chưa đủ hạn mức tối thiểu (10,000 VNĐ). Hiện tại: <b>{user['balance']:,}đ</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
            return
        cap_nhat_user(user_id, "state", "NHAP_THONG_TIN_RUT")
        bot.send_message(message.chat.id, f"💸 <b>NHẬP THÔNG TIN RÚT TIỀN</b>\n────────────────────────\n💰 Rút toàn bộ: <b>{user['balance']:,}đ</b>\n👉 Nhập theo mẫu: <code>NGÂN HÀNG STK TÊNTK</code>\n📌 Ví dụ: <i>MBBANK 1903456789 NGUYEN VAN A</i>", reply_markup=tao_menu_huy(), parse_mode="HTML")
    elif message.text == "✉️ Mời bạn":
        bot.send_message(message.chat.id, "✉️ <b>GIỚI THIỆU BẠN BÈ</b>\n────────────────────────\n🤝 Nhận 10% hoa hồng khi bạn bè vượt link thành công!", reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif message.text == "⛏️ Kiếm tiền":
        user = lay_thong_tin_user(user_id)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if user["last_task_date"] != today:
            cap_nhat_user(user_id, "last_task_date", today)
            cap_nhat_user(user_id, "today_task_count", 0)
            user["today_task_count"] = 0
        if user["today_task_count"] >= GIOI_HAN_NHIEM_VU_NGAY:
            bot.send_message(message.chat.id, f"❌ Hôm nay bạn đã hết lượt làm nhiệm vụ ({GIOI_HAN_NHIEM_VU_NGAY}/{GIOI_HAN_NHIEM_VU_NGAY}).")
            return
        bot.send_message(message.chat.id, "⏳ <i>Đang khởi tạo link nhiệm vụ...</i>", parse_mode="HTML")
        url_dich = f"{WEB_URL}/?t={int(time.time())}"
        link_rut_gon = tu_dong_tao_link_link4m(url_dich)
        if not link_rut_gon:
            bot.send_message(message.chat.id, "❌ Hệ thống bận, vui lòng bấm lại nút!")
            return
        cap_nhat_user(user_id, "state", "NHAP_MA_XAC_NHAN")
        markup_inline = types.InlineKeyboardMarkup()
        markup_inline.add(types.InlineKeyboardButton("🔗 BẤM VÀO ĐÂY ĐỂ VƯỢT LINK", url=link_rut_gon))
        bot.send_message(message.chat.id, f"<b>Nhiệm vụ vượt link kiếm tiền (400đ)</b>\n────────────────────────\n👉 Hãy vượt link lấy mã rồi dán vào đây.", reply_markup=markup_inline, parse_mode="HTML")
        bot.send_message(message.chat.id, "📝 Nhập <code>HUY</code> để hủy bỏ.", reply_markup=tao_menu_huy(), parse_mode="HTML")
                                  # --- PANEL QUẢN TRỊ ADMIN VÀ LỆNH QUẢN TRỊ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not la_admin(message): return
    global ADMIN_ID
    ADMIN_ID = message.from_user.id 
    db = doc_data()
    LOAI_TRU = ["system_config", "withdrawal_requests"]
    total_users = sum(1 for key in db.keys() if key not in LOAI_TRU)
    total_balance = sum(db[key].get("balance", 0) for key in db.keys() if key not in LOAI_TRU)
    msg = f"👑 <b>PANEL ADMIN</b>\n👥 Thành viên: <b>{total_users}</b>\n💰 Tổng quỹ: <b>{total_balance:,} VNĐ</b>\n\n"
    tickets = db.get("withdrawal_requests", {})
    pending_tickets = {tid: t for tid, t in tickets.items() if t.get("status") == "PENDING"}
    if not pending_tickets:
        msg += "🎉 <i>Không có lệnh rút nào chờ duyệt!</i>"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
        for tid, ticket in pending_tickets.items():
            ticket_msg = f"⏳ <b>Mã: {tid}</b>\n👤 User: @{ticket.get('username')}\n💵 Rút: <b>{ticket.get('amount', 0):,}đ</b>\n🏦 STK: <code>{ticket.get('info')}</code>"
            markup_admin = types.InlineKeyboardMarkup()
            markup_admin.row(types.InlineKeyboardButton(f"✅ Duyệt {tid}", callback_data=f"apprut_{tid}"), types.InlineKeyboardButton(f"❌ Từ Chối", callback_data=f"rejrut_{tid}"))
            bot.send_message(message.chat.id, ticket_msg, parse_mode="HTML", reply_markup=markup_admin)

@bot.callback_query_handler(func=lambda call: call.data.startswith("apprut_") or call.data.startswith("rejrut_"))
def handle_admin_buttons(call):
    if not la_admin(call): return
    action = "approve" if call.data.startswith("apprut_") else "reject"
    tid = call.data.split("_")[1]
    db = doc_data()
    if "withdrawal_requests" not in db or tid not in db["withdrawal_requests"]: return
    ticket = db["withdrawal_requests"][tid]
    if ticket["status"] != "PENDING": return
    target_uid = ticket["user_id"]
    amount = ticket["amount"]
    if action == "approve":
        db["withdrawal_requests"][tid]["status"] = "APPROVED"
        luu_data(db)
        bot.edit_message_text(f"🟢 <b>ĐÃ DUYỆT RÚT TIỀN</b>\n🆔 Mã: {tid}\n💰 Số tiền: {amount:,}đ", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        try: bot.send_message(int(target_uid), f"🎉 Lệnh rút <code>{tid}</code> trị giá <b>{amount:,}đ</b> đã được duyệt!", parse_mode="HTML")
        except: pass
    elif action == "reject":
        db["withdrawal_requests"][tid]["status"] = "REJECTED"
        if target_uid in db: db[target_uid]["balance"] = db[target_uid].get("balance", 0) + amount
        luu_data(db)
        bot.edit_message_text(f"🔴 <b>ĐÃ TỪ CHỐI</b>\n🆔 Mã: {tid}\n💰 Đã hoàn trả {amount:,}đ", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        try: bot.send_message(int(target_uid), f"🛑 Lệnh rút <code>{tid}</code> bị từ chối, tiền đã trả lại số dư.", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['check'])
def admin_check_user(message):
    if not la_admin(message): return
    args = message.text.split()
    if len(args) < 2: return
    uid = args[1]
    db = doc_data()
    if uid in db:
        user = db[uid]
        bot.send_message(message.chat.id, f"🔍 <b>USER {uid}</b>\n💰 Số dư: <b>{user.get('balance', 0):,}đ</b>\n⚡ Hôm nay: {user.get('today_task_count', 0)} lượt", parse_mode="HTML")

@bot.message_handler(commands=['cong'])
def admin_modify_balance(message):
    if not la_admin(message): return
    args = message.text.split()
    if len(args) < 3: return
    uid, amount_str = args[1], args[2]
    try: amount = int(amount_str)
    except: return
    db = doc_data()
    if uid in db:
        db[uid]["balance"] = db[uid].get("balance", 0) + amount
        luu_data(db)
        bot.reply_to(message, f"✅ Đã cộng {amount:,}đ cho ID {uid}")

# --- PHÂN LUỒNG XỬ LÝ TRẠNG THÁI CHUNG ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user = lay_thong_tin_user(user_id)
    text = message.text.strip()
    if text.upper() in ["HUY", "HỦY", "❌ HỦY NHẬP MÃ"]:
        reset_state(user_id)
        bot.send_message(message.chat.id, "🛑 Đã hủy trạng thái!", reply_markup=tao_menu_chinh())
        return
    current_state = user.get("state", "NONE")
    if current_state == "NHAP_MA_XAC_NHAN":
        ma_chuan = lay_ma_he_thong()
        if text.upper() != ma_chuan:
            bot.send_message(message.chat.id, "❌ <b>Mã sai!</b> Gõ <code>HUY</code> để thoát.", parse_mode="HTML")
            return
        db = doc_data()
        uid_str = str(user_id)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if db[uid_str].get("last_task_date") != today:
            db[uid_str]["last_task_date"] = today
            db[uid_str]["today_task_count"] = 0
        db[uid_str]["balance"] = db[uid_str].get("balance", 0) + 400
        db[uid_str]["today_task_count"] = db[uid_str].get("today_task_count", 0) + 1
        db[uid_str]["state"] = "NONE"
        db["system_config"]["ma_xac_nhan"] = tao_ma_ngau_nhien() 
        luu_data(db)
        bot.send_message(message.chat.id, f"🎉 <b>Chính xác!</b> Bạn được +400đ.\n📊 Tiến độ: <b>{db[uid_str]['today_task_count']}/{GIOI_HAN_NHIEM_VU_NGAY}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif current_state == "NHAP_THONG_TIN_RUT":
        db = doc_data()
        uid_str = str(user_id)
        so_tien_rut = db[uid_str]["balance"]
        if so_tien_rut < 10000:
            db[uid_str]["state"] = "NONE"
            luu_data(db)
            bot.send_message(message.chat.id, "❌ Lỗi: Số dư không đủ.", reply_markup=tao_menu_chinh())
            return
        ticket_id = "".join(random.choice(string.digits) for _ in range(5))
        ngay_tao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "withdrawal_requests" not in db: db["withdrawal_requests"] = {}
        if "lich_su_rut" not in db[uid_str]: db[uid_str]["lich_su_rut"] = []
        db[uid_str]["balance"] = 0
        db[uid_str]["state"] = "NONE"
        gói_lệnh = {"user_id": uid_str, "username": user.get("username", "Không có"), "amount": so_tien_rut, "info": text, "status": "PENDING", "date": ngay_tao}
        db["withdrawal_requests"][ticket_id] = gói_lệnh
        db[uid_str]["lich_su_rut"].append({"ticket_id": ticket_id, "amount": so_tien_rut, "info": text, "status": "PENDING", "date": ngay_tao})
        luu_data(db)
        bot.send_message(message.chat.id, f"✅ Tạo yêu cầu rút tiền thành công!\n🆔 Mã lệnh: <code>{ticket_id}</code>\n💰 Số tiền: <b>{so_tien_rut:,} VNĐ</b>\nVui lòng chờ Admin duyệt!", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        try:
            markup_admin = types.InlineKeyboardMarkup()
            markup_admin.row(types.InlineKeyboardButton(f"✅ Duyệt {ticket_id}", callback_data=f"apprut_{ticket_id}"), types.InlineKeyboardButton(f"❌ Từ Chối", callback_data=f"rejrut_{ticket_id}"))
            bot.send_message(ADMIN_ID if ADMIN_ID != 0 else user_id, f"🔔 <b>RÚT TIỀN MỚI</b>\n🆔 Mã: {ticket_id}\n💵 Số tiền: <b>{so_tien_rut:,}đ</b>\n🏦 STK: `{text}`", reply_markup=markup_admin, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(message.chat.id, "🤖 Vui lòng chọn một tính năng từ menu bên dưới.", reply_markup=tao_menu_chinh())

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(0.5)
    bot.set_webhook(url=f"{WEB_URL}/{TOKEN}")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
        
