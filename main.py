import telebot
from telebot import types
import json
import os
import datetime
import time
import random
import string
import threading
import requests
from flask import Flask, render_template_string

# 1. CẤU HÌNH BOT TELEGRAM
TOKEN = '8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ'
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_data.json"

# ⭐ TỰ ĐỘNG NHẬN DIỆN ADMIN QUA USERNAME TELEGRAM ⭐
ADMIN_USERNAME = "leductai51"  
ADMIN_ID = 0                   

# 2. CẤU HÌNH GIỚI HẠN NHIỆM VỤ / NGÀY
GIOI_HAN_NHIEM_VU_NGAY = 1     

# 3. CẤU HÌNH API LINK4M
LINK4M_API_KEY = "694cc66f558f587fcc15b845"

# 4. ĐỊA CHỈ WEB SERVER RENDER CỦA BẠN
WEB_URL = "https://yen-xxch.onrender.com" 

app = Flask(__name__)

# --- HÀM KIỂM TRA QUYỀN ADMIN ---
def la_admin(message_or_call):
    username = message_or_call.from_user.username
    uid = message_or_call.from_user.id
    if uid == ADMIN_ID:
        return True
    if username and username.lower() == ADMIN_USERNAME.lower():
        return True
    return False

# --- HÀM TỰ ĐỘNG RÚT GỌN LINK ---
def tu_dong_tao_link_link4m(url_goc):
    try:
        api_endpoint = f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={url_goc}"
        response = requests.get(api_endpoint, timeout=10).json()
        if response.get("status") == "success":
            return response.get("shortenedUrl")
    except Exception as e:
        print(f"❌ Lỗi kết nối API Link4m: {e}")
    return None

# --- GIAO DIỆN WEB XÁC MINH ---
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

def tao_menu_huy():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("❌ Hủy nhập mã"))
    return markup

@app.route('/')
def web_trang_chu():
    return render_template_string(HTML_TRANG_DICH, ma_so=lay_ma_he_thong())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    lay_thong_tin_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, "👋 Chào mừng bạn đến với Bot kiếm tiền!", reply_markup=tao_menu_chinh())


# =======================================================
# ⭐ PANEL ADMIN & HỆ THỐNG DUYỆT LỆNH RÚT TIỀN ⭐
# =======================================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not la_admin(message): return
    global ADMIN_ID
    ADMIN_ID = message.from_user.id 
    
    db = doc_data()
    LOAI_TRU = ["system_config", "withdrawal_requests"]
    total_users = sum(1 for key in db.keys() if key not in LOAI_TRU)
    total_balance = sum(db[key].get("balance", 0) for key in db.keys() if key not in LOAI_TRU)
    
    msg = (f"👑 <b>PANEL QUẢN TRỊ ADMIN</b>\n"
           f"──────────────────\n"
           f"👥 Tổng thành viên: <b>{total_users} người</b>\n"
           f"💰 Tổng quỹ số dư: <b>{total_balance:,} VNĐ</b>\n\n"
           f"💡 <b>Lệnh nhanh:</b> <code>/check [ID]</code> | <code>/cong [ID] [Tiền]</code> | <code>/thongbao [Nội dung]</code>\n\n"
           f"📝 <b>DANH SÁCH LỆNH RÚT ĐANG CHỜ DUYỆT:</b>\n"
           f"──────────────────\n")
    
    tickets = db.get("withdrawal_requests", {})
    pending_tickets = {tid: t for tid, t in tickets.items() if t.get("status") == "PENDING"}
    
    if not pending_tickets:
        msg += "🎉 <i>Hiện tại không có lệnh rút tiền nào đang chờ xử lý!</i>"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, msg, parse_mode="HTML")
        for tid, ticket in pending_tickets.items():
            ticket_msg = (f"⏳ <b>Mã lệnh rút: {tid}</b>\n"
                          f"👤 Thành viên: @{ticket.get('username')} (ID: <code>{ticket.get('user_id')}</code>)\n"
                          f"💵 Số tiền rút: <b>{ticket.get('amount', 0):,} VNĐ</b>\n"
                          f"🏦 Thông tin nhận: <code>{ticket.get('info')}</code>\n"
                          f"📅 Thời gian tạo: <i>{ticket.get('date')}</i>")
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton(f"✅ Duyệt {tid}", callback_data=f"apprut_{tid}"),
                types.InlineKeyboardButton(f"❌ Từ Chối", callback_data=f"rejrut_{tid}")
            )
            bot.send_message(message.chat.id, ticket_msg, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("apprut_") or call.data.startswith("rejrut_"))
def handle_admin_withdrawal_buttons(call):
    if not la_admin(call):
        bot.answer_callback_query(call.id, "❌ Bạn không có quyền quản trị!", show_alert=True)
        return
        
    action = "approve" if call.data.startswith("apprut_") else "reject"
    tid = call.data.split("_")[1]
    
    db = doc_data()
    if "withdrawal_requests" not in db or tid not in db["withdrawal_requests"]:
        bot.answer_callback_query(call.id, "❌ Lệnh không tồn tại hoặc dữ liệu lỗi.", show_alert=True)
        return
        
    ticket = db["withdrawal_requests"][tid]
    if ticket["status"] != "PENDING":
        bot.answer_callback_query(call.id, "⚠️ Lệnh này đã được xử lý từ trước rồi!", show_alert=True)
        return
        
    target_uid = ticket["user_id"]
    amount = ticket["amount"]
    
    if action == "approve":
        db["withdrawal_requests"][tid]["status"] = "APPROVED"
        if target_uid in db and "lich_su_rut" in db[target_uid]:
            for x in db[target_uid]["lich_su_rut"]:
                if x.get("ticket_id") == tid: x["status"] = "APPROVED"
        luu_data(db)
        
        bot.answer_callback_query(call.id, "✅ Đã phê duyệt lệnh thành công!")
        bot.edit_message_text(f"🟢 <b>ĐÃ DUYỆT RÚT TIỀN</b>\n🆔 Mã lệnh: {tid}\n💰 Số tiền: {amount:,}đ\n👤 Tài khoản nhận: @{ticket.get('username')}", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        
        try:
            bot.send_message(int(target_uid), f"🎉 <b>RÚT TIỀN THÀNH CÔNG!</b>\n────────────────\n🆔 Mã lệnh <code>{tid}</code> của bạn đã được Admin **PHÊ DUYỆT**.\n💵 Số tiền <b>{amount:,} VNĐ</b> đã được chuyển về ví của bạn!", parse_mode="HTML")
        except: pass
        
    elif action == "reject":
        db["withdrawal_requests"][tid]["status"] = "REJECTED"
        if target_uid in db:
            db[target_uid]["balance"] = db[target_uid].get("balance", 0) + amount
            if "lich_su_rut" in db[target_uid]:
                for x in db[target_uid]["lich_su_rut"]:
                    if x.get("ticket_id") == tid: x["status"] = "REJECTED"
        luu_data(db)
        
        bot.answer_callback_query(call.id, "❌ Đã hủy lệnh và hoàn tiền cho thành viên!")
        bot.edit_message_text(f"🔴 <b>ĐÃ TỪ CHỐI LỆNH RÚT</b>\n🆔 Mã lệnh: {tid}\n💰 Đã hoàn trả lại {amount:,}đ vào số dư của @{ticket.get('username')}", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        
        try:
            bot.send_message(int(target_uid), f"🛑 <b>LỆNH RÚT TIỀN BỊ TỪ CHỐI</b>\n────────────────\n🆔 Mã lệnh <code>{tid}</code> đã bị từ chối.\n💵 Số tiền <b>{amount:,} VNĐ</b> đã được **hoàn trả tự động** về số dư tài khoản của bạn.", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['check'])
def admin_check_user(message):
    if not la_admin(message): return
    args = message.text.split()
    if len(args) < 2: return
    uid = args[1]
    db = doc_data()
    if uid not in db: return
    user = db[uid]
    msg = (f"🔍 <b>THÔNG TIN THÀNH VIÊN</b>\n🆔 ID: <code>{uid}</code>\n👤 Username: @{user.get('username', 'Không có')}\n💰 Số dư: <b>{user.get('balance', 0):,} VNĐ</b>\n⚡ Hôm nay: <b>{user.get('today_task_count', 0)} lượt</b>")
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(commands=['cong', 'tru'])
def admin_modify_balance(message):
    if not la_admin(message): return
    command = message.text.split()[0]
    args = message.text.split()
    if len(args) < 3: return
    uid, amount_str = args[1], args[2]
    try: amount = int(amount_str)
    except: return
    db = doc_data()
    if uid not in db: return
    if command == "/cong":
        db[uid]["balance"] = db[uid].get("balance", 0) + amount
    else:
        db[uid]["balance"] = max(0, db[uid].get("balance", 0) - amount)
    luu_data(db)
    bot.reply_to(message, "✅ Đã thực thi thay đổi số dư thành công.")

@bot.message_handler(commands=['thongbao'])
def admin_broadcast(message):
    if not la_admin(message): return
    text_split = message.text.split(' ', 1)
    if len(text_split) < 2: return
    noi_dung = text_split[1]
    db = doc_data()
    for uid in db.keys():
        if uid not in ["system_config", "withdrawal_requests"]:
            try: bot.send_message(int(uid), f"📢 <b>THÔNG BÁO TỪ ADMIN:</b>\n\n{noi_dung}", parse_mode="HTML")
            except: continue


# =======================================================
# XỬ LÝ CÁC CHỨC NĂNG DÀNH CHO THÀNH VIÊN THƯỜNG
# =======================================================

@bot.message_handler(func=lambda message: message.text == "👤 Tài khoản")
def handle_tai_khoan(message):
    user = lay_thong_tin_user(message.from_user.id, message.from_user.username)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    luot_hom_nay = user['today_task_count'] if user['last_task_date'] == today else 0
    
    bot.send_message(
        message.chat.id, 
        f"👤 <b>THÔNG TIN TÀI KHOẢN</b>\n"
        f"────────────────────────\n"
        f"🆔 ID của bạn: <code>{message.from_user.id}</code>\n"
        f"💰 Số dư của bạn: <b>{user['balance']:,} VNĐ</b>\n"
        f"⚡ Đã làm hôm nay: <b>{luot_hom_nay}/{GIOI_HAN_NHIEM_VU_NGAY}</b> lượt", 
        parse_mode="HTML", 
        reply_markup=tao_menu_chinh()
    )

@bot.message_handler(func=lambda message: message.text == "💸 Rút tiền")
def handle_rut_tien(message):
    user_id = message.from_user.id
    user = lay_thong_tin_user(user_id)
    
    if user['balance'] < 10000:
        bot.send_message(
            message.chat.id, 
            f"💸 <b>RÚT TIỀN VỀ VÍ</b>\n"
            f"────────────────────────\n"
            f"💵 Số dư hiện tại: <b>{user['balance']:,} VNĐ</b>\n"
            f"📌 Hạn mức rút tối thiểu: <b>10,000 VNĐ</b>\n\n"
            f"❌ Số dư của bạn chưa đủ 10,000đ để thực hiện rút tiền.", 
            parse_mode="HTML", 
            reply_markup=tao_menu_chinh()
        )
        return

    # Chuyển trạng thái sang nhập thông tin
    cap_nhat_user(user_id, "state", "NHAP_THONG_TIN_RUT")
    
    # ⭐ ĐÃ CẬP NHẬT ĐỊNH DẠNG: NGÂN HÀNG STK TÊNTK THEO YÊU CẦU ⭐
    bot.send_message(
        message.chat.id,
        f"💸 <b>KHỞI TẠO LỆNH RÚT TIỀN</b>\n"
        f"────────────────────────\n"
        f"💰 Số tiền rút toàn bộ: <b>{user['balance']:,} VNĐ</b>\n\n"
        f"👉 <b>Vui lòng nhập thông tin nhận tiền theo mẫu:</b>\n"
        f"<code>NGÂN HÀNG STK TÊNTK</code>\n\n"
        f"📌 <i>Ví dụ: MBBANK 1903456789 NGUYEN VAN A</i>\n\n"
        f"⚠️ Nhập <code>HUY</code> để hủy bỏ lệnh rút.",
        parse_mode="HTML",
        reply_markup=tao_menu_huy()
    )

@bot.message_handler(func=lambda message: message.text == "✉️ Mời bạn")
def handle_moi_ban(message):
    bot.send_message(
        message.chat.id, 
        f"✉️ <b>GIỚI THIỆU BẠN BÈ</b>\n"
        f"────────────────────────\n"
        f"🤝 Chia sẻ Bot cho bạn bè cùng làm nhiệm vụ để nhận ngay 10% hoa hồng trên mỗi lượt vượt link thành công!", 
        parse_mode="HTML", 
        reply_markup=tao_menu_chinh()
    )

@bot.message_handler(func=lambda message: message.text == "⛏️ Kiếm tiền")
def handle_kiem_tien(message):
    user_id = message.from_user.id
    user = lay_thong_tin_user(user_id)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if user["last_task_date"] != today:
        cap_nhat_user(user_id, "last_task_date", today)
        cap_nhat_user(user_id, "today_task_count", 0)
        user["today_task_count"] = 0

    if user["today_task_count"] >= GIOI_HAN_NHIEM_VU_NGAY:
        bot.send_message(
            message.chat.id, 
            f"❌ <b>Đạt giới hạn!</b>\n"
            f"Mỗi ngày bạn chỉ được làm tối đa <b>{GIOI_HAN_NHIEM_VU_NGAY}</b> nhiệm vụ.\n"
            f"Vui lòng quay lại vào ngày mai nhé!", 
            parse_mode="HTML"
        )
        return

    bot.send_message(message.chat.id, "⏳ <i>Hệ thống đang khởi tạo liên kết nhiệm vụ riêng cho bạn, vui lòng đợi vài giây...</i>", parse_mode="HTML")
    
    url_dich_thuc_te = f"{WEB_URL}/?t={int(time.time())}"
    link_rut_gon_tu_dong = tu_dong_tao_link_link4m(url_dich_thuc_te)
    
    if not link_rut_gon_tu_dong:
        bot.send_message(message.chat.id, "❌ Hệ thống tạo link đang bận, vui lòng thử lại sau!")
        return

    cap_nhat_user(user_id, "state", "NHAP_MA_XAC_NHAN")
    
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    markup_inline.add(types.InlineKeyboardButton("🔗 BẤM VÀO ĐÂY ĐỂ VƯỢT LINK", url=link_rut_gon_tu_dong))
    
    bot.send_message(
        message.chat.id, 
        f"<b>Nhiệm vụ vượt link kiếm tiền (400đ)</b>\n"
        f"────────────────────────\n"
        f"👉 <b>Bước 1:</b> Bấm vào nút liên kết bên dưới.\n"
        f"👉 <b>Bước 2:</b> Vượt link quảng cáo thành công để lấy mã.\n"
        f"👉 <b>Bước 3:</b> Copy mã đó dán gửi vào đây để nhận tiền.\n\n"
        f"📊 Lượt làm hôm nay của bạn: <b>{user['today_task_count']}/{GIOI_HAN_NHIEM_VU_NGAY}</b>", 
        reply_markup=markup_inline, 
        parse_mode="HTML"
    )
    
    bot.send_message(
        message.chat.id,
        f"📝 <b>Ghi chú:</b> Nhập <code>HUY</code> hoặc bấm nút bên dưới để hủy nhập mã vượt link.",
        parse_mode="HTML",
        reply_markup=tao_menu_huy()
    )

# --- XỬ LÝ NHẬN TIN NHẮN CHUNG VÀ PHÂN CHIA TRẠNG THÁI ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user = lay_thong_tin_user(user_id)
    text = message.text.strip()

    # TRƯỜNG HỢP 1: USER ĐANG TRONG TRẠNG THÁI NHẬP MÃ KIẾM TIỀN
    if user["state"] == "NHAP_MA_XAC_NHAN":
        if text.upper() in ["HUY", "HỦY", "❌ HỦY NHẬP MÃ"]:
            cap_nhat_user(user_id, "state", "NONE")
            bot.send_message(message.chat.id, "🛑 Đã hủy trạng thái nhập mã thành công!", reply_markup=tao_menu_chinh())
            return
            
        ma_chuan = lay_ma_he_thong()
        if text.upper() != ma_chuan:
            bot.send_message(message.chat.id, "❌ <b>Mã sai!</b> Vui lòng kiểm tra lại.\n👉 Nhập <code>HUY</code> để hủy bỏ.", parse_mode="HTML")
            return
            
        db = doc_data()
        uid_str = str(user_id)
        db[uid_str]["balance"] = db[uid_str].get("balance", 0) + 400
        db[uid_str]["today_task_count"] = db[uid_str].get("today_task_count", 0) + 1
        db[uid_str]["state"] = "NONE"
        db["system_config"]["ma_xac_nhan"] = tao_ma_ngau_nhien() 
        luu_data(db)
        
        bot.send_message(message.chat.id, f"🎉 <b>Chính xác!</b> Bạn đã nhận được +400đ vào tài khoản.\n📊 Tiến độ hôm nay: <b>{db[uid_str]['today_task_count']}/{GIOI_HAN_NHIEM_VU_NGAY}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        return

    # TRƯỜNG HỢP 2: USER ĐANG TRONG TRẠNG THÁI NHẬP THÔNG TIN RÚT TIỀN
    elif user["state"] == "NHAP_THONG_TIN_RUT":
        if text.upper() in ["HUY", "HỦY", "❌ HỦY NHẬP MÃ"]:
            cap_nhat_user(user_id, "state", "NONE")
            bot.send_message(message.chat.id, "🛑 Đã hủy yêu cầu rút tiền thành công!", reply_markup=tao_menu_chinh())
            return
            
        db = doc_data()
        uid_str = str(user_id)
        so_tien_rut = db[uid_str]["balance"]
        
        if so_tien_rut < 10000:
            db[uid_str]["state"] = "NONE"
            luu_data(db)
            bot.send_message(message.chat.id, "❌ Lỗi: Số dư không đủ hạn mức tối thiểu.", reply_markup=tao_menu_chinh())
            return
            
        ticket_id = "".join(random.choice(string.digits) for _ in range(5))
        ngay_tao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if "withdrawal_requests" not in db: db["withdrawal_requests"] = {}
        if "lich_su_rut" not in db[uid_str]: db[uid_str]["lich_su_rut"] = []
        
        db[uid_str]["balance"] = 0
        db[uid_str]["state"] = "NONE"
        
        gói_lệnh = {
            "user_id": uid_str,
            "username": user.get("username", "Không có"),
            "amount": so_tien_rut,
            "info": text,
            "status": "PENDING",
            "date": ngay_tao
        }
        
        db["withdrawal_requests"][ticket_id] = gói_lệnh
        db[uid_str]["lich_su_rut"].append({"ticket_id": ticket_id, "a
