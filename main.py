import telebot, json, os, datetime, time, random, string, requests
from telebot import types
from flask import Flask, render_template_string, request

# ==================== CẤU HÌNH HỆ THỐNG ====================
TOKEN = '8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ'
bot = telebot.TeleBot(TOKEN, threaded=False)
DATA_FILE = "users_data.json"
ADMIN_USERNAME = "leductai51"
ADMIN_ID = 0

# Giới hạn số lượt làm trong ngày của từng bên
GIOI_HAN_LINK4M = 1  
GIOI_HAN_CLICK90S = 2 
GIOI_HAN_TRAFFIC68 = 2

# API Keys của các hệ thống link
LINK4M_API_KEY = "694cc66f558f587fcc15b845"
CLICK90S_API_KEY = "nwtr_pk_1656e40ff81" 
TRAFFIC68_API_KEY = "tf68_2727a59c0ae2aa5d6879a0f0a71762967d27046c82c95d58"
WEB_URL = "https://yen-xxch.onrender.com"

app = Flask(__name__)
BOT_USERNAME = "Bot"
try: 
    BOT_USERNAME = bot.get_me().username
except: 
    pass

# ==================== HÀM XỬ LÝ DỮ LIỆU CƠ BẢN ====================
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
        "ref_by": "", "last_task_date": "", "today_task_count": 0,
        "today_link4m_count": 0, "today_click90s_count": 0, "today_traffic68_count": 0,
        "current_task_type": "", "weekly_task_count": 0, "last_task_week": ""
    }
    for key, value in CẤU_TRÚC_CHUẨN.items():
        if key not in db[uid]: db[uid][key] = value
    if username: db[uid]["username"] = str(username).lower()
    luu_data(db)
    return db[uid]

def cap_nhat_user(user_id, key, value):
    db = doc_data()
    if str(user_id) in db: 
        db[str(user_id)][key] = value
        luu_data(db)

def reset_state(user_id): 
    cap_nhat_user(user_id, "state", "NONE")

def la_admin(m):
    u = m.from_user.username
    uid = m.from_user.id
    return uid == ADMIN_ID or (u and u.lower() == ADMIN_USERNAME.lower())

# ==================== ĐOẠN API RÚT GỌN LINK ====================
def tu_dong_tao_link_link4m(url):
    try:
        res = requests.get(f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={url}", timeout=10).json()
        if res.get("status") == "success": return res.get("shortenedUrl")
    except: pass
    return None

def tu_dong_tao_link_click90s(url):
    try:
        res = requests.get(f"https://click90s.com/api/public/v1/st?api={CLICK90S_API_KEY}&url={url}", timeout=10)
        if res.status_code == 200:
            try:
                data = res.json()
                if "shortenedUrl" in data: return data["shortenedUrl"]
                if "shortlink" in data: return data["shortlink"]
            except:
                if res.text.startswith("http"): return res.text.strip()
    except: pass
    return None

def tu_dong_tao_link_traffic68(url):
    try:
        res = requests.get(f"https://traffic68.com/api/quicklink/st?api={TRAFFIC68_API_KEY}&url={url}", timeout=10)
        if res.status_code == 200:
            try:
                data = res.json()
                if "shortenedUrl" in data: return data["shortenedUrl"]
                if "shortlink" in data: return data["shortlink"]
                if "shortened_url" in data: return data["shortened_url"]
            except:
                if res.text.startswith("http"): return res.text.strip()
    except: pass
    return None

# ==================== ĐỊNH NGHĨA MENU BÀN PHÍM ====================
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

# ==================== CẤU HÌNH WEBHOOK FLASK ====================
HTML_TRANG_DICH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>XÁC MINH</title><style>body{font-family:'Segoe UI',sans-serif;background:#f4f6f9;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.container{background:white;padding:30px;border-radius:15px;box-shadow:0 10px 25px rgba(0,0,0,0.1);text-align:center;max-width:400px;width:90%}h2{color:#2ecc71}p{color:#666;font-size:14px}.code-box{background:#f8f9fa;border:2px dashed #cbd5e1;padding:15px;font-size:24px;font-weight:bold;color:#1e293b;border-radius:8px;margin:20px 0}.btn-copy{background:#3498db;color:white;border:none;padding:12px;font-size:14px;border-radius:5px;cursor:pointer;width:100%;font-weight:bold}</style></head><body><div class="container"><h2>🎉 Vượt Link Thành Công!</h2><p>Sau khi sao chép mã dưới đây, hãy quay lại Bot Telegram dán vào nhé.</p><div class="code-box" id="auth-code">{{ma_so}}</div><button class="btn-copy" onclick="navigator.clipboard.writeText(document.getElementById('auth-code').innerText).then(()=>{alert('Đã sao chép mã thành công!');})">📋 SAO CHÉP MÃ</button></div></body></html>"""

@app.route('/')
def web_trang_chu(): 
    loai_link = request.args.get('type', '').lower()
    ma_goc = lay_ma_he_thong()
    if loai_link == 'l4m':
        ma_goc = f"{ma_goc}-L4M"
    elif loai_link == 'c90':
        ma_goc = f"{ma_goc}-C90"
    elif loai_link == 'tf68':
        ma_goc = f"{ma_goc}-TF68"
    return render_template_string(HTML_TRANG_DICH, ma_so=ma_goc)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

# ==================== ĐIỀU HƯỚNG BOT TELEGRAM ====================
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

    bot.send_message(m.chat.id, "👋 Chào mừng bạn đến với Bot kiếm tiền vượt link!", reply_markup=tao_menu_chinh())

@bot.message_handler(func=lambda m: m.text in ["👤 Tài khoản", "💸 Rút tiền", "✉️ Mời bạn", "⛏️ Kiếm tiền", "🏆 BXH Tuần"])
def handle_menu_navigation(m):
    uid = m.from_user.id
    reset_state(uid)
    
    if m.text == "👤 Tài khoản":
        u = lay_thong_tin_user(uid, m.from_user.username)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        done_l4m = u['today_link4m_count'] if u['last_task_date'] == today else 0
        done_c90 = u['today_click90s_count'] if u['last_task_date'] == today else 0
        done_tf68 = u.get('today_traffic68_count', 0) if u['last_task_date'] == today else 0
        
        bot.send_message(m.chat.id, f"👤 <b>THÔNG TIN TÀI KHOẢN</b>\n────────────────────────\n🆔 ID của bạn: <code>{uid}</code>\n💰 Số dư: <b>{u['balance']:,} VNĐ</b>\n👥 Đã mời: <b>{u.get('da_moi', 0)} người</b>\n🎁 Hoa hồng nhận: <b>{u.get('hoa_hong', 0):,} VNĐ</b>\n📊 Nhiệm vụ hôm nay:\n- Link4M: <b>{done_l4m}/{GIOI_HAN_LINK4M}</b>\n- Click90s: <b>{done_c90}/{GIOI_HAN_CLICK90S}</b>\n- Traffic68: <b>{done_tf68}/{GIOI_HAN_TRAFFIC68}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        
    elif m.text == "💸 Rút tiền":
        u = lay_thong_tin_user(uid)
        if u['balance'] < 20000:
            bot.send_message(m.chat.id, f"❌ Tối thiểu rút tiền là 20,000 VNĐ. Hiện tại bạn có: <b>{u['balance']:,} VNĐ</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
            return
        cap_nhat_user(uid, "state", "NHAP_THONG_TIN_RUT")
        bot.send_message(m.chat.id, f"💸 <b>RÚT TIỀN HỆ THỐNG</b>\n────────────────────────\n💰 Số dư khả dụng: <b>{u['balance']:,} VNĐ</b>\n👉 Hãy nhập thông tin nhận tiền theo mẫu:\n<code>TÊN NGÂN HÀNG - STK - TÊN NGƯỜI NHẬN</code>", reply_markup=tao_menu_huy(), parse_mode="HTML")
        
    elif m.text == "✉️ Mời bạn":
        u = lay_thong_tin_user(uid)
        link_moi = f"https://t.me/{BOT_USERNAME}?start={uid}"
        bot.send_message(m.chat.id, f"✉️ <b>GIỚI THIỆU BẠN BÈ</b>\n────────────────────────\n🤝 Mời bạn bè tham gia nhận ngay 10% số tiền từ mỗi nhiệm vụ cấp dưới hoàn thành!\n\n👥 Đã mời: <b>{u.get('da_moi', 0)} người</b>\n💰 Tổng hoa hồng: <b>{u.get('hoa_hong', 0):,} VNĐ</b>\n\n🔗 Link giới thiệu độc quyền của bạn:\n<code>{link_moi}</code>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        
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
            msg += "<i>Chưa có dữ liệu tuần này! Hãy là người đầu tiên lên top.</i>"
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
            cap_nhat_user(uid, "today_link4m_count", 0)
            cap_nhat_user(uid, "today_click90s_count", 0)
            cap_nhat_user(uid, "today_traffic68_count", 0)
            u["today_link4m_count"] = 0
            u["today_click90s_count"] = 0
            u["today_traffic68_count"] = 0
            
        l4m_con = u.get("today_link4m_count", 0) < GIOI_HAN_LINK4M
        c90_con = u.get("today_click90s_count", 0) < GIOI_HAN_CLICK90S
        tf68_con = u.get("today_traffic68_count", 0) < GIOI_HAN_TRAFFIC68
            
        if not l4m_con and not c90_con and not tf68_con:
            bot.send_message(m.chat.id, f"❌ Bạn đã hoàn thành toàn bộ giới hạn nhiệm vụ hôm nay!\n(Link4M: {GIOI_HAN_LINK4M}/{GIOI_HAN_LINK4M}, Click90s: {GIOI_HAN_CLICK90S}/{GIOI_HAN_CLICK90S}, Traffic68: {GIOI_HAN_TRAFFIC68}/{GIOI_HAN_TRAFFIC68})")
            return
            
        bot.send_message(m.chat.id, "⏳ <i>Hệ thống đang khởi tạo các liên kết nhiệm vụ...</i>", parse_mode="HTML")
        
        mk = types.InlineKeyboardMarkup(row_width=1)
        co_link = False
        
        if l4m_con:
            link_l4m = tu_dong_tao_link_link4m(f"{WEB_URL}/?t={int(time.time())}&type=l4m")
            if link_l4m:
                mk.add(types.InlineKeyboardButton(f"🔗 Vượt Link Link4M ({u.get('today_link4m_count', 0)}/{GIOI_HAN_LINK4M}) - Nhận 400đ", url=link_l4m))
                co_link = True
                
        if c90_con:
            link_c90 = tu_dong_tao_link_click90s(f"{WEB_URL}/?t={int(time.time())}&type=c90")
            if link_c90:
                mk.add(types.InlineKeyboardButton(f"🔗 Vượt Link Click90s ({u.get('today_click90s_count', 0)}/{GIOI_HAN_CLICK90S}) - Nhận 400đ", url=link_c90))
                co_link = True

        if tf68_con:
            link_tf68 = tu_dong_tao_link_traffic68(f"{WEB_URL}/?t={int(time.time())}&type=tf68")
            if link_tf68:
                mk.add(types.InlineKeyboardButton(f"🔗 Vượt Link Traffic68 ({u.get('today_traffic68_count', 0)}/{GIOI_HAN_TRAFFIC68}) - Nhận 400đ", url=link_tf68))
                co_link = True
                
        if not co_link:
            bot.send_message(m.chat.id, "❌ Các hệ thống API đối tác đang bận, vui lòng thử lại sau vài giây!")
            return
            
        cap_nhat_user(uid, "state", "NHAP_MA_XAC_NHAN")
        
        bot.send_message(m.chat.id, f"<b>Nhiệm vụ kiếm tiền (400đ)</b>\n────────────────────────\n👉 Bước 1: Ấn vào một trong các liên kết khả dụng bên dưới.\n👉 Bước 2: Vượt link quảng cáo để lấy mã xác nhận.\n👉 Bước 3: Copy mã dán vào đây để nhận thưởng.", reply_markup=mk, parse_mode="HTML")
        bot.send_message(m.chat.id, "📝 Nhập hoặc ấn nút <code>HUY</code> bên dưới để hủy nhận mã.", reply_markup=tao_menu_huy(), parse_mode="HTML")

# ==================== HỆ THỐNG QUẢN TRỊ ADMIN ====================
@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if not la_admin(m): return
    global ADMIN_ID
    ADMIN_ID = m.from_user.id 
    db = doc_data()
    ex = ["system_config", "withdrawal_requests"]
    total_users = sum(1 for k in db.keys() if k not in ex)
    total_balance = sum(db[k].get("balance", 0) for k in db.keys() if k not in ex)
    msg = f"👑 <b>PANEL QUẢN TRỊ ADMIN</b>\n👥 Tổng số Users: <b>{total_users}</b>\n💰 Quỹ thành viên: <b>{total_balance:,}đ</b>\n\n"
    tkts = db.get("withdrawal_requests", {})
    p_tkts = {tid: t for tid, t in tkts.items() if t.get("status") == "PENDING"}
    if not p_tkts:
        msg += "🎉 <i>Không có lệnh rút tiền nào đang chờ duyệt!</i>"
        bot.send_message(m.chat.id, msg, parse_mode="HTML")
    else:
        bot.send_message(m.chat.id, msg, parse_mode="HTML")
        for tid, t in p_tkts.items():
            t_msg = f"⏳ <b>Mã GD: {tid}</b>\n👤 User: @{t.get('username')}\n💵 Số tiền: <b>{t.get('amount', 0):,}đ</b>\n🏦 Thông tin: <code>{t.get('info')}</code>"
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
        bot.edit_message_text(f"🟢 <b>ĐÃ DUYỆT THÀNH CÔNG</b>\n🆔 Mã lệnh: {tid}\n💰 Số tiền: {amt:,}đ", c.message.chat.id, c.message.message_id, parse_mode="HTML")
        try: bot.send_message(int(t_uid), f"🎉 Yêu cầu rút tiền mã <code>{tid}</code> trị giá <b>{amt:,}đ</b> đã được Admin duyệt và chuyển khoản!", parse_mode="HTML")
        except: pass
    elif action == "reject":
        db["withdrawal_requests"][tid]["status"] = "REJECTED"
        if t_uid in db: db[t_uid]["balance"] = db[t_uid].get("balance", 0) + amt
        luu_data(db)
        bot.edit_message_text(f"🔴 <b>ĐÃ TỪ CHỐI</b>\n🆔 Mã lệnh: {tid}\n💰 Hoàn lại ví: {amt:,}đ", c.message.chat.id, c.message.message_id, parse_mode="HTML")
        try: bot.send_message(int(t_uid), f"🛑 Lệnh rút tiền mã <code>{tid}</code> đã bị Admin từ chối. Số tiền được hoàn trả vào tài khoản.", parse_mode="HTML")
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
        bot.send_message(m.chat.id, f"🔍 <b>THÔNG TIN THÀNH VIÊN {uid}</b>\n💰 Số dư hiện tại: <b>{u.get('balance', 0):,}đ</b>\n⚡ Tiến độ hôm nay:\n- Link4M: {u.get('today_link4m_count', 0)}/{GIOI_HAN_LINK4M}\n- Click90s: {u.get('today_click90s_count', 0)}/{GIOI_HAN_CLICK90S}\n- Traffic68: {u.get('today_traffic68_count', 0)}/{GIOI_HAN_TRAFFIC68}", parse_mode="HTML")

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
        bot.reply_to(m, f"✅ Đã cộng {amt:,}đ vào tài khoản ID {uid}")

# ==================== XỬ LÝ TRẠNG THÁI NHẬP TIN NHẮN TỰ DO ====================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    uid = m.from_user.id
    u = lay_thong_tin_user(uid)
    text = m.text.strip()
    
    if text.upper() in ["HUY", "HỦY", "❌ HỦY NHẬP MÃ"]:
        reset_state(uid)
        bot.send_message(m.chat.id, "🛑 Đã hủy thao tác hiện tại!", reply_markup=tao_menu_chinh())
        return
        
    state = u.get("state", "NONE")
    
    if state == "NHAP_MA_XAC_NHAN":
        ma_goc = lay_ma_he_thong()
        input_text = text.upper()
        
        if input_text == f"{ma_goc}-L4M":
            kenh_lam = "link4m"
        elif input_text == f"{ma_goc}-C90":
            kenh_lam = "click90s"
        elif input_text == f"{ma_goc}-TF68":
            kenh_lam = "traffic68"
        elif input_text == ma_goc:
            db = doc_data()
            if db[str(uid)].get("today_link4m_count", 0) < GIOI_HAN_LINK4M: kenh_lam = "link4m"
            elif db[str(uid)].get("today_click90s_count", 0) < GIOI_HAN_CLICK90S: kenh_lam = "click90s"
            else: kenh_lam = "traffic68"
        else:
            bot.send_message(m.chat.id, "❌ <b>Mã xác nhận không chính xác!</b>\n\nVui lòng kiểm tra lại mã hoặc nhập <code>HUY</code> để thoát nhiệm vụ.", parse_mode="HTML")
            return
            
        db = doc_data()
        uid_s = str(uid)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        this_week = datetime.datetime.now().strftime("%Y-%W")
        
        if db[uid_s].get("last_task_date") != today:
            db[uid_s]["last_task_date"] = today
            db[uid_s]["today_task_count"] = 0
            db[uid_s]["today_link4m_count"] = 0
            db[uid_s]["today_click90s_count"] = 0
            db[uid_s]["today_traffic68_count"] = 0
        if db[uid_s].get("last_task_week") != this_week:
            db[uid_s]["last_task_week"] = this_week
            db[uid_s]["weekly_task_count"] = 0
            
        if kenh_lam == "link4m":
            db[uid_s]["today_link4m_count"] = db[uid_s].get("today_link4m_count", 0) + 1
            ten_hien_thi = "Link4M"
            da_lam = db[uid_s]["today_link4m_count"]
            gioi_han = GIOI_HAN_LINK4M
        elif kenh_lam == "click90s":
            db[uid_s]["today_click90s_count"] = db[uid_s].get("today_click90s_count", 0) + 1
            ten_hien_thi = "Click90s"
            da_lam = db[uid_s]["today_click90s_count"]
            gioi_han = GIOI_HAN_CLICK90S
        else:
            db[uid_s]["today_traffic68_count"] = db[uid_s].get("today_traffic68_count", 0) + 1
            ten_hien_thi = "Traffic68"
            da_lam = db[uid_s]["today_traffic68_count"]
            gioi_han = GIOI_HAN_TRAFFIC68
            
        db[uid_s]["balance"] = db[uid_s].get("balance", 0) + 400
        db[uid_s]["today_task_count"] = db[uid_s].get("today_task_count", 0) + 1
        db[uid_s]["weekly_task_count"] = db[uid_s].get("weekly_task_count", 0) + 1
        db[uid_s]["state"] = "NONE"
        
        ref_id = db[uid_s].get("ref_by", "")
        if ref_id and ref_id in db:
            db[ref_id]["balance"] = db[ref_id].get("balance", 0) + 40
            db[ref_id]["hoa_hong"] = db[ref_id].get("hoa_hong", 0) + 40
            try: bot.send_message(int(ref_id), f"🎁 Cấp dưới vừa hoàn thành nhiệm vụ! Bạn nhận được +40đ hoa hồng.")
            except: pass

        db["system_config"]["ma_xac_nhan"] = tao_ma_ngau_nhien()
        luu_data(db)
        bot.send_message(m.chat.id, f"🎉 <b>Chính xác!</b> Bạn nhận được +400đ từ nhiệm vụ <b>{ten_hien_thi}</b>.\n📊 Tiến độ hôm nay: <b>{da_lam}/{gioi_han}</b>", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        
    elif state == "NHAP_THONG_TIN_RUT":
        db = doc_data()
        uid_s = str(uid)
        amt = db[uid_s]["balance"]
        if amt < 20000:
            db[uid_s]["state"] = "NONE"; luu_data(db)
            bot.send_message(m.chat.id, "❌ Lỗi hệ thống: Số dư tài khoản không đủ.", reply_markup=tao_menu_chinh())
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
        
        bot.send_message(m.chat.id, f"✅ Tạo lệnh rút tiền thành công!\n🆔 Mã giao dịch: <code>{tid}</code>\n💰 Số tiền rút: <b>{amt:,} VNĐ</b>\n⏳ Trạng thái: Đang chờ Admin duyệt.", reply_markup=tao_menu_chinh(), parse_mode="HTML")
        try:
            mk = types.InlineKeyboardMarkup()
            mk.row(types.InlineKeyboardButton(f"✅ Duyệt {tid}", callback_data=f"apprut_{tid}"), types.InlineKeyboardButton(f"❌ Từ Chối", callback_data=f"rejrut_{tid}"))
            bot.send_message(ADMIN_ID if ADMIN_ID != 0 else uid, f"🔔 <b>YÊU CẦU RÚT TIỀN MỚI</b>\n🆔 Mã GD: {tid}\n💵 Số tiền: <b>{amt:,}đ</b>\n🏦 STK: `{text}`", reply_markup=mk, parse_mode="HTML")
        except: pass
    else:
        bot.send_message(m.chat.id, "🤖 Vui lòng chọn tính năng từ menu hệ thống bên dưới.", reply_markup=tao_menu_chinh())

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(0.5)
    bot.set_webhook(url=f"{WEB_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
