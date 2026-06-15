import telebot
from telebot import types
import json
import os
import datetime
import time
import random
import string
import threading
import requests # Thêm thư viện để gọi API Link4m
from flask import Flask, render_template_string

# 1. CẤU HÌNH BOT TELEGRAM
TOKEN = '8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ'
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"
BOT_USERNAME = "bot_kiem_tien"

# 2. CẤU HÌNH API LINK4M (LẤY TỪ ẢNH CỦA BẠN)
LINK4M_API_KEY = "694cc66f558f587fcc15b845"

# 3. ĐỊA CHỈ WEB SERVER CỦA BẠN (Thay bằng IP VPS hoặc Tên miền của bạn)
# Ví dụ: "http://123.45.67.89:5000" hoặc "https://tenwebcuaban.com"
WEB_URL = "http:// THAY_IP_VPS_HOAC_DOMAIN_CỦA_BẠN_VÀO_ĐÂY :5000" 

app = Flask(__name__)

# --- HÀM TỰ ĐỘNG RÚT GỌN LINK QUA API LINK4M ---
def tu_dong_tao_link_link4m(url_goc):
    try:
        # Gọi API theo đúng cấu trúc trong ảnh của bạn
        api_endpoint = f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={url_goc}"
        response = requests.get(api_endpoint, timeout=10).json()
        
        if response.get("status") == "success":
            return response.get("shortenedUrl") # Trả về link đã rút gọn thành công
    except Exception as e:
        print(f"❌ Lỗi kết nối API Link4m: {e}")
    return None

# --- GIAO DIỆN WEB ---
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
        .btn-copy:hover { background: #2980b9; }
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

# --- CÁC HÀM XỬ LÝ DỮ LIỆU JSON ---
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

def tao_menu_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("👤 Tài khoản"), types.KeyboardButton("⛏️ Kiếm tiền"))
    markup.row(types.KeyboardButton("💸 Rút tiền"), types.KeyboardButton("✉️ Mời bạn"))
    return markup

@app.route('/')
def web_trang_chu():
    return render_template_string(HTML_TRANG_DICH, ma_so=lay_ma_he_thong())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    lay_thong_tin_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, "👋 Chào mừng bạn đến với Bot kiếm tiền!", reply_markup=tao_menu_chinh())

# --- XỬ LÝ KHI BẤM NÚT KIẾM TIỀN (GỌI API TỰ ĐỘNG) ---
@bot.message_handler(func=lambda message: message.text == "⛏️ Kiếm tiền")
def handle_kiem_tien(message):
    user_id = message.from_user.id
    
    bot.send_message(message.chat.id, "⏳ <i>Hệ thống đang khởi tạo liên kết nhiệm vụ riêng cho bạn, vui lòng đợi vài giây...</i>", parse_mode="HTML")
    
    # Tạo một link đích ngẫu nhiên theo thời gian để Link4m không bắt trùng lặp
    url_dich_thuc_te = f"{WEB_URL}/?t={int(time.time())}"
    
    # Gọi API Link4m tự động rút gọn
    link_rut_gon_tu_dong = tu_dong_tao_link_link4m(url_dich_thuc_te)
    
    if not link_rut_gon_tu_dong:
        # Nếu Link4m bị lỗi API, dùng link dự phòng hoặc thông báo thử lại
        bot.send_message(message.chat.id, "❌ Hệ thống tạo link Link4m đang bận, vui lòng thử lại sau ít phút!")
        return

    cap_nhat_user(user_id, "state", "NHAP_MA_XAC_NHAN")
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔗 BẤM VÀO ĐÂY ĐỂ VƯỢT LINK", url=link_rut_gon_tu_dong))
    
    bot.send_message(
        message.chat.id, 
        "<b>Nhiệm vụ vượt link kiếm tiền (400đ)</b>\n"
        "────────────────────────\n"
        "👉 <b>Bước 1:</b> Bấm vào nút liên kết bên dưới.\n"
        "👉 <b>Bước 2:</b> Vượt link quảng cáo thành công để lấy mã.\n"
        "👉 <b>Bước 3:</b> Copy mã đó dán gửi vào đây để nhận tiền.", 
        reply_markup=markup, 
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user = lay_thong_tin_user(user_id)
    text = message.text

    if text == "👤 Tài khoản":
        bot.send_message(message.chat.id, f"💰 Số dư của bạn: <b>{user['balance']:,} VNĐ</b>", parse_mode="HTML")
        
    elif user["state"] == "NHAP_MA_XAC_NHAN":
        ma_chuan = lay_ma_he_thong()
        if text.strip().upper() != ma_chuan:
            bot.send_message(message.chat.id, "❌ <b>Mã sai!</b> Vui lòng kiểm tra lại mã trên web.", parse_mode="HTML")
            return
            
        db = doc_data()
        uid_str = str(user_id)
        
        # Cộng tiền và reset mã ngẫu nhiên mới
        db[uid_str]["balance"] = db[uid_str].get("balance", 0) + 400
        db[uid_str]["state"] = "NONE"
        db["system_config"]["ma_xac_nhan"] = tao_ma_ngau_nhien() # Web tự động nhận mã mới
        luu_data(db)
        
        bot.send_message(message.chat.id, "🎉 <b>Chính xác!</b> Bạn được cộng +400đ vào tài khoản.", reply_markup=tao_menu_chinh(), parse_mode="HTML")

def khoi_chay_web():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    try: bot.delete_webhook(drop_pending_updates=True)
    except: pass
    
    t = threading.Thread(target=khoi_chay_web)
    t.daemon = True
    t.start()
    
    bot.infinity_polling()
  
