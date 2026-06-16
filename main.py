import telebot, json, os, datetime, time, random, string, requests
from telebot import types
from flask import Flask, render_template_string, request

# CẤU HÌNH HỆ THỐNG
TOKEN = '8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ'
bot = telebot.TeleBot(TOKEN, threaded=False)
DATA_FILE = "users_data.json"
ADMIN_USERNAME = "leductai51"
ADMIN_ID = 0
GIOI_HAN_NHIEM_VU_NGAY = 1
LINK4M_API_KEY = "694cc66f558f587fcc15b845"
WEB_URL = "https://yen-xxch.onrender.com"
app = Flask(__name__)

BOT_USERNAME = "Bot"
try: BOT_USERNAME = bot.get_me().username
except: pass

# HÀM XỬ LÝ DỮ LIỆU CƠ BẢN
def doc_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def luu_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def tao_ma_ngau_nhien(): return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

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
        "ref_by": "", "last_task_date": "", "today_task_count": 0,
        "weekly_task_count": 0, "last_task_week": ""
    }
    for key, value in CẤU_TRÚC_CHUẨN.items():
        if key not in db[uid]: db[uid][key] = value
    if username: db[uid]["username"] = str(username).lower()
    luu_data(db)
    return db[uid]

def cap_nhat_user(user_id, key, value):
    db = doc_data()
    if str(user_id) in db: db[str(user_id)][key] = value; luu_data(db)

def reset_state(user_id): cap_nhat_user(user_id, "state", "NONE")

def la_admin(m):
    u = m.from_user.username
    uid = m.from_user.id
    return uid == ADMIN_ID or (u and u.lower() == ADMIN_USERNAME.lower())

def tu_dong_tao_link_link4m(url):
    try:
        res = requests.get(f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={url}", timeout=10).json()
        if res.get("status") == "success": return res.get("shortenedUrl")
    except: pass
    return None

def tao_menu_chinh():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("👤 Tài khoản"), types.KeyboardButton("⛏️ Kiếm tiền"))
    m.row(types.KeyboardButton("💸 Rút tiền"), types.KeyboardButton("✉️ Mời bạn"))
    m.row(types.KeyboardButton("🏆 BXH Tuần"))
    return m

def tao_menu_huy():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row(types.KeyboardButton("❌ Hủy nhập mã"))
    return m

# CẤU HÌNH WEBHOOK FLASK
HTML_TRANG_DICH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>XÁC MINH</title><style>body{font-family:'Segoe UI',sans-serif;background:#f4f6f9;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.container{background:white;padding:30px;border-radius:15px;box-shadow:0 10px 25px rgba(0,0,0,0.1);text-align:center;max-width:400px;width:90%}h2{color:#2ecc71}p{color:#666;font-size:14px}.code-box{background:#f8f9fa;border:2px dashed #cbd5e1;padding:15px;font-size:24px;font-weight:bold;color:#1e293b;border-radius:8px;margin:20px 0}.btn-copy{background:#3498db;color:white;border:none;padding:12px;font-size:14px;border-radius:5px;cursor:pointer;width:100%;font-weight:bold}</style></head><body><div class="container"><h2>🎉 Vượt Link Thành Công!</h2><p>Sao chép mã gửi vào Bot.</p><div class="code-box" id="auth-code">{{ma_so}}</div><button class="btn-copy" onclick="navigator.clipboard.writeText(document.getElementById('auth-code').innerText).then(()=>{alert('Đã sao chép!');})">📋 SAO CHÉP MÃ</button></div></body></html>"""

@app.route('/')
def web_trang_chu(): return render_template_string(HTML_TRANG_DICH, ma_so=lay_ma_he_thong())

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

# ĐIỀU HƯỚNG BOT TELEGRAM
@bot.message_handler(commands=['start'])
def send_welcome(m):
    uid = m.from_user.id
    db = doc_data()
    la_user_moi = str(uid) not in db
    lay_thong_tin_user(uid, m.from_user.username)
    reset_state(uid)
    
    args = m.text.split()
    if la_user_moi and len(args) > 1:
        ref_id = args[1]
        if ref_id.isdigit() and ref_id != str(uid):
            db = doc_data()
            if ref_id in db:
                db[str(uid)]["ref_by"] = ref_id
                db[ref_id]["da_moi"] = db[ref_id].get("da_moi", 0) + 1
                luu_data(db)
                try: bot.send_message(int(ref_id), f"✨ Bạn có thành viên mới đăng ký qua link giới thiệu!")
                except: pass

    bot.send_message(m.chat.id, "👋 Chào mừng bạn!", reply_markup=tao_menu_chinh())

@bot.message_handler(func=lambda m: m.text in ["👤 Tài khoản", "💸 Rút tiền", "✉️ Mời bạn", "⛏️ Kiếm tiền", "🏆 BXH Tuần"])
def handle_menu_navigation(m):
    uid = m.from_user.id
    reset_state(uid)
    if m.text == "👤 Tài khoản":
        u = lay_thong_tin_user(uid, m.from_user.username)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        done = u['today_task_count'] if u['last_task_date'] == today else 0
        bot.send_message(m.chat.id, f"👤 <b>THÔNG TIN TÀI KHOẢN</b>\n────────────────────────\n🆔 ID của bạn: <code>{uid}</code>\n💰 Số dư: <b>{u['balance']:,} VNĐ</b>\n👥 Số người đã mời: <b>{u.get('da_moi', 0)} người</b>\n🎁 Tiền mời bạn nhận được: <b>{u.get('hoa_hong', 0):,} VNĐ</b>\n⚡ Nhiệm vụ đã làm hôm nay: <b>{done}/{GIOI_HAN_NHIEM_VU_NGAY}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif m.text == "💸 Rút tiền":
        u = lay_thong_tin_user(uid)
        if u['balance'] < 20000:
            bot.send_message(m.chat.id, f"❌ Tối thiểu 20,000 VNĐ. Hiện tại: <b>{u['balance']:,} VNĐ</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
            return
        cap_nhat_user(uid, "state", "NHAP_THONG_TIN_RUT")
        bot.send_message(m.chat.id, f"💸 <b>RÚT TIỀN</b>\n────────────────────────\n💰 Số tiền: <b>{u['balance']:,} VNĐ</b>\n👉 Nhập mẫu: <code>TÊN NGÂN HÀNG - STK - TÊN NGƯỜI NHẬN</code>", reply_markup=tao_menu_huy(), parse_mode="HTML")
    elif m.text == "✉️ Mời bạn":
        u = lay_thong_tin_user(uid)
        link_moi = f"https://t.me/{BOT_USERNAME}?start={uid}"
        bot.send_message(m.chat.id, f"✉️ <b>GIỚI THIỆU BẠN BÈ</b>\n────────────────────────\n🤝 Mời bạn bè tham gia nhận ngay 10% số tiền của nhiệm vụ bạn bè làm!\n\n👥 Số người đã mời: <b>{u.get('da_moi', 0)} người</b>\n💰 Số tiền nhận từ người mời: <b>{u.get('hoa_hong', 0):,} VNĐ</b>\n\n🔗 Link giới thiệu của bạn:\n<code>{link_moi}</code>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif m.text == "🏆 BXH Tuần":
        db = doc_data()
        this_week = datetime.datetime.now().strftime("%Y-%W")
        ex = ["system_config", "withdrawal_requests"]
        bxh = []
        for k, v in db.items():
            if k in ex: continue
            w_count = v.get("weekly_task_count", 0)
            if v.get("last_task_week") != this_week:
                w_count = 0
            if w_count > 0:
                name = v.get("username", "").strip()
                if not name: name = f"User {k[:5]}..."
                else: name = f"@{name}"
                bxh.append((name, w_count))
        bxh.sort(key=lambda x: x[1], reverse=True)
        msg = "🏆 <b>BẢNG XẾP HẠNG VƯỢT LINK TUẦN</b>\n────────────────────────\n"
        if not bxh:
            msg += "<i>Chưa có dữ liệu tuần này!</i>"
        else:
            for i, (name, count) in enumerate(bxh[:10], 1):
                icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<code>{i}.</code>"
                msg += f"{icon} {name} — <b>{count}</b> lượt\n"
        bot.send_message(m.chat.id, msg, reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif m.text == "⛏️ Kiếm tiền":
        u = lay_thong_tin_user(uid)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if u["last_task_date"] != today:
            cap_nhat_user(uid, "last_task_date", today)
            cap_nhat_user(uid, "today_task_count", 0)
            u["today_task_count"] = 0
        if u["today_task_count"] >= GIOI_HAN_NHIEM_VU_NGAY:
            bot.send_message(m.chat.id, f"❌ Đã hết lượt hôm nay ({GIOI_HAN_NHIEM_VU_NGAY}/{GIOI_HAN_NHIEM_VU_NGAY}).")
            return
        bot.send_message(m.chat.id, "⏳ <i>Đang khởi tạo...</i>", parse_mode="HTML")
        link = tu_dong_tao_link_link4m(f"{WEB_URL}/?t={int(time.time())}")
        if not link:
            bot.send_message(m.chat.id, "❌ Lỗi, thử lại!")
            return
        cap_nhat_user(uid, "state", "NHAP_MA_XAC_NHAN")
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔗 BẤM VÀO ĐÂY ĐỂ VƯỢT LINK", url=link))
        bot.send_message(m.chat.id, f"<b>Nhiệm vụ vượt link (400đ)</b>\n────────────────────────\n👉 Vượt link lấy mã dán vào đây.", reply_markup=mk, parse_mode="HTML")
        bot.send_message(m.chat.id, "📝 Nhập <code>HUY</code> để hủy.", reply_markup=tao_menu_huy(), parse_mode="HTML")

# HỆ THỐNG QUẢN TRỊ ADMIN
@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if not la_admin(m): return
    global ADMIN_ID
    ADMIN_ID = m.from_user.id 
    db = doc_data()
    ex = ["system_config", "withdrawal_requests"]
    total_users = sum(1 for k in db.keys() if k not in ex)
    total_balance = sum(db[k].get("balance", 0) for k in db.keys() if k not in ex)
    msg = f"👑 <b>PANEL ADMIN</b>\n👥 Users: <b>{total_users}</b>\n💰 Quỹ: <b>{total_balance:,}đ</b>\n\n"
    tkts = db.get("withdrawal_requests", {})
    p_tkts = {tid: t for tid, t in tkts.items() if t.get("status") == "PENDING"}
    if not p_tkts:
        msg += "🎉 <i>Không có lệnh chờ!</i>"
        bot.send_message(m.chat.id, msg, parse_mode="HTML")
    else:
        bot.send_message(m.chat.id, msg, parse_mode="HTML")
        for tid, t in p_tkts.items():
            t_msg = f"⏳ <b>Mã: {tid}</b>\n👤 User: @{t.get('username')}\n💵 Rút: <b>{t.get('amount', 0):,}đ</b>\n🏦 STK: <code>{t.get('info')}</code>"
            mk = types.InlineKeyboardMarkup()
            mk.row(types.InlineKeyboardButton(f"✅ Duyệt {tid}", callback_data=f"apprut_{tid}"), types.InlineKeyboardButton(f"❌ Từ Chối", callback_data=f"rejrut_{tid}"))
            bot.send_message(m.chat.id, t_msg, parse_mode="HTML", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("apprut_") or c.data.startswith("rejrut_"))
def handle_admin_buttons(c):
    if not la_admin(c): return
    action = "approve" if c.data.startswith("apprut_") else "reject"
    tid = c.data.split("_")[1]
    db = doc_data()
    if "withdrawal_requests" not in db or tid not in db["withdrawal_requests"]: return
    t = db["withdrawal_requests"][tid]
    if t["status"] != "PENDING": return
    t_uid, amt = t["user_id"], t["amount"]
    if action == "approve":
        db["withdrawal_requests"][tid]["status"] = "APPROVED"; luu_data(db)
        bot.edit_message_text(f"🟢 <b>ĐÃ DUYỆT</b>\n🆔 Mã: {tid}\n💰 Tiền: {amt:,}đ", c.message.chat.id, c.message.message_id, parse_mode="HTML")
        try: bot.send_message(int(t_uid), f"🎉 Lệnh rút <code>{tid}</code> trị giá <b>{amt:,}đ</b> đã được duyệt!", parse_mode="HTML")
        except: pass
    elif action == "reject":
        db["withdrawal_requests"][tid]["status"] = "REJECTED"
        if t_uid in db: db[t_uid]["balance"] = db[t_uid].get("balance", 0) + amt
        luu_data(db)
        bot.edit_message_text(f"🔴 <b>TỪ CHỐI</b>\n🆔 Mã: {tid}\n💰 Đã hoàn {amt:,}đ", c.message.chat.id, c.message.message_id, parse_mode="HTML")
        try: bot.send_message(int(t_uid), f"🛑 Lệnh rút <code>{tid}</code> bị từ chối, tiền đã trả lại.", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['check'])
def admin_check_user(m):
    if not la_admin(m): return
    args = m.text.split()
    if len(args) < 2: return
    uid = args[1]
    db = doc_data()
    if uid in db:
        u = db[uid]
        bot.send_message(m.chat.id, f"🔍 <b>USER {uid}</b>\n💰 Số dư: <b>{u.get('balance', 0):,}đ</b>\n⚡ Hôm nay: {u.get('today_task_count', 0)} lượt", parse_mode="HTML")

@bot.message_handler(commands=['cong'])
def admin_modify_balance(m):
    if not la_admin(m): return
    args = m.text.split()
    if len(args) < 3: return
    uid, amt_str = args[1], args[2]
    try: amt = int(amt_str)
    except: return
    db = doc_data()
    if uid in db:
        db[uid]["balance"] = db[uid].get("balance", 0) + amt; luu_data(db)
        bot.reply_to(m, f"✅ Đã cộng {amt:,}đ cho ID {uid}")

# XỬ LÝ TRẠNG THÁI TIN NHẮN CHUNG
@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    uid = m.from_user.id
    u = lay_thong_tin_user(uid)
    text = m.text.strip()
    if text.upper() in ["HUY", "HỦY", "❌ HỦY NHẬP MÃ"]:
        reset_state(uid)
        bot.send_message(m.chat.id, "🛑 Đã hủy!", reply_markup=tao_menu_chinh())
        return
    state = u.get("state", "NONE")
    if state == "NHAP_MA_XAC_NHAN":
        if text.upper() != lay_ma_he_thong():
            bot.send_message(m.chat.id, "❌ <b>Mã sai!</b> Nhập <code>HUY</code> để thoát.", parse_mode="HTML")
            return
        db = doc_data()
        uid_s = str(uid)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        this_week = datetime.datetime.now().strftime("%Y-%W")
        
        # Kiểm tra và reset ngày mới / tuần mới
        if db[uid_s].get("last_task_date") != today:
            db[uid_s]["last_task_date"] = today
            db[uid_s]["today_task_count"] = 0
        if db[uid_s].get("last_task_week") != this_week:
            db[uid_s]["last_task_week"] = this_week
            db[uid_s]["weekly_task_count"] = 0
            
        db[uid_s]["balance"] = db[uid_s].get("balance", 0) + 400
        db[uid_s]["today_task_count"] = db[uid_s].get("today_task_count", 0) + 1
        db[uid_s]["weekly_task_count"] = db[uid_s].get("weekly_task_count", 0) + 1
        db[uid_s]["state"] = "NONE"
        
        # CHIA HOA HỒNG MỜI BẠN (10% của 400đ = 40đ)
        ref_id = db[uid_s].get("ref_by", "")
        if ref_id and ref_id in db:
            db[ref_id]["balance"] = db[ref_id].get("balance", 0) + 40
            db[ref_id]["hoa_hong"] = db[ref_id].get("hoa_hong", 0) + 40
            try: bot.send_message(int(ref_id), f"🎁 Bạn được +40đ hoa hồng từ cấp dưới làm nhiệm vụ!")
            except: pass

        db["system_config"]["ma_xac_nhan"] = tao_ma_ngau_nhien()
        luu_data(db)
        bot.send_message(m.chat.id, f"🎉 <b>Chính xác!</b> +400đ.\n📊 Tiến độ ngày: <b>{db[uid_s]['today_task_count']}/{GIOI_HAN_NHIEM_VU_NGAY}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
    elif state == "NHAP_THONG_TIN_RUT":
        db = doc_data()
        uid_s = str(uid)
        amt = db[uid_s]["balance"]
        if amt < 20000:
            db[uid_s]["state"] = "NONE"; luu_data(db)
            bot.send_message(m.chat.id, "❌ Lỗi: Số dư không đủ.", reply_markup=tao_menu_chinh())
            return
        tid = "".join(random.choice(string.digits) for _ in range(5))
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "withdrawal_requests" not in db: db["withdrawal_requests"] = {}
        if "lich_su_rut" not in db[uid_s]: db[uid_s]["lich_su_rut"] = []
        db[uid_s]["balance"] = 0
        db[uid_s]["state"] = "NONE"
        t_data = {"user_id": uid_s, "username": u.get("username", "Không có"), "amount": amt, "info": text, "status": "PENDING", "date": dt}
        db["withdrawal_requests"][tid] = t_data
        db[uid_s]["lich_su_rut"].append({"ticket_id": tid, "amount": amt, "info": text, "status": "PENDING", "date": dt})
        luu_data(db)
        bot.send_message(m.chat.id, f"✅ Thành công!\n🆔 Mã lệnh: <code>{tid}</code>\n💰 Số tiền: <b>{amt:,} VNĐ</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        try:
            mk = types.InlineKeyboardMarkup()
            mk.row(types.InlineKeyboardButton(f"✅ Duyệt {tid}", callback_data=f"apprut_{tid}"), types.InlineKeyboardButton(f"❌ Từ Chối", callback_data=f"rejrut_{tid}"))
            bot.send_message(ADMIN_ID if ADMIN_ID != 0 else uid, f"🔔 <b>RÚT TIỀN MỚI</b>\n🆔 Mã: {tid}\n💵 Tiền: <b>{amt:,}đ</b>\n🏦 STK: `{text}`", reply_markup=mk, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(m.chat.id, "🤖 Chọn tính năng từ menu.", reply_markup=tao_menu_chinh())

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(0.5)
    bot.set_webhook(url=f"{WEB_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
                             
