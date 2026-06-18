import os
import logging
import math
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Cấu hình log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# LẤY TOKEN TỪ ENVIRONMENT VARIABLE CỦA RENDER
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8818249568:AAGTRAGYVloZINECSOf6hAzNYQl9XJS5dWQ")

def process_neural_matrix(hash_str: str) -> str:
    hash_str = hash_str.strip().lower().replace(" ", "")
    if not re.match(r"^[0-9a-f]+$", hash_str):
        return "❌ *Chuỗi không hợp lệ!* Chỉ chấp nhận ký tự chuẩn Hex (0-9, a-f)."
    
    length = len(hash_str)
    if length not in (32, 64):
        return "⚠️ *Sai cấu trúc dữ liệu!* Hệ thống chỉ hỗ trợ MD5 (32 ký tự) hoặc SHA-256 (64 ký tự)."

    nibbles = [int(char, 16) for char in hash_str]
    matrix_score = 0.0
    cols = 8
    rows = length // cols

    # TẦNG 1
    main_diagonal_sum = 0
    anti_diagonal_sum = 0
    for r in range(rows):
        main_diagonal_sum += nibbles[(r * cols) + (r % cols)]
        anti_diagonal_sum += nibbles[(r * cols) + ((cols - 1 - r) % cols)]
    matrix_score += 1.5 if (main_diagonal_sum % 2 == 0) else -1.5
    matrix_score += 1.2 if (anti_diagonal_sum % 2 == 0) else -1.2

    # TẦNG 2
    fwd_register = 0xABCDE123
    bwd_register = 0x321EDCBA
    for i in range(length):
        fwd_register ^= (nibbles[i] << (i % 7)) & 0xFFFFFFFF
        fwd_register = ((fwd_register & 0xFFFFFFFF) >> 1) | ((fwd_register << 31) & 0xFFFFFFFF)
        rev_idx = length - 1 - i
        bwd_register ^= (nibbles[rev_idx] << (i % 7)) & 0xFFFFFFFF
        bwd_register = ((bwd_register & 0xFFFFFFFF) >> 1) | ((bwd_register << 31) & 0xFFFFFFFF)
    combined_link = (fwd_register ^ bwd_register) & 0xFFFFFFFF
    matrix_score += 2.0 if ((combined_link & 1) == 0) else -2.0

    # TẦNG 3
    edge_sum = 0
    for c in range(cols):
        edge_sum += nibbles[c] + nibbles[(rows - 1) * cols + c]
    matrix_score += 1.3 if (edge_sum % 2 == 0) else -1.3

    # KẾT LUẬN
    choice = "🔴 TÀI" if matrix_score > 0 else "🟢 XỈU" if matrix_score < 0 else "⚪ BỎ QUA"
    type_label = "MD5" if length == 32 else "SHA-256"
    
    k = 0.5
    x = abs(matrix_score)
    sigmoid_rate = 50 + (49.6 / (1 + math.exp(-k * (x - 2))))

    return (
        f"📊 *KẾT QUẢ PHÂN TÍCH MA TRẬN KHỐI*\n"
        f"--------------------------------------\n"
        f"🔹 *Loại chuỗi:* {type_label}\n"
        f"🔮 *Gợi ý:* {choice}\n"
        f"🎯 *Độ tin cậy:* `{sigmoid_rate:.1f}%`"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Neural Matrix Engine Bot Đã Sẵn Sàng!*\n\nGửi mã MD5/SHA-256 để phân tích.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = process_neural_matrix(update.message.text)
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # CẤU HÌNH TỰ ĐỘNG THÍCH ỨNG VỚI RENDER (WEBHOOK)
    PORT = int(os.environ.get('PORT', 8443))
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') # Render tự cấp biến này

    if RENDER_URL:
        # Chạy Webhook trên Render
        logger.info(f"Starting webhook on port {PORT} with URL {RENDER_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_URL}/{TOKEN}"
        )
    else:
        # Chạy Polling bình thường nếu test ở máy cục bộ
        logger.info("Starting local polling...")
        application.run_polling()

if __name__ == '__main__':
    main()
  
