import logging
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8226993737:AAErIjCoq80NhvBsXr0nMbMMKWLBXSoaAD4")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7800649803"))

print(f"🔧 Bot token: {BOT_TOKEN[:10]}...")
print(f"🔧 Admin ID: {ADMIN_ID}")

DATA_FILE = "bot_data.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            if "videos" not in data:
                data["videos"] = []
            return data
    except:
        return {"videos": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        data = load_data()
        video_count = len(data["videos"])
        await update.message.reply_text(
            f"👋 Salom Admin!\n📹 Video yuklash uchun video yuboring\n📊 Jami videolar: {video_count} ta"
        )
    else:
        await update.message.reply_text("👋 Salom! Video ko'rish uchun kod yuboring.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Faqat admin video yuklay oladi!")
        return
    
    video_file = update.message.video
    if video_file:
        caption = update.message.caption or ""
        await update.message.reply_text("📹 Video qabul qilindi! Kodni yuboring:")
        
        context.user_data["pending_video"] = {
            "file_id": video_file.file_id,
            "caption": caption,
            "timestamp": datetime.now().isoformat()
        }

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text
    data = load_data()
    
    if user_id == ADMIN_ID and "pending_video" in context.user_data:
        video_data = context.user_data["pending_video"]
        
        # Kod takrorlanmasligini tekshirish
        for video in data["videos"]:
            if video.get("code") == user_input:
                await update.message.reply_text("❌ Bu kod allaqachon mavjud! Boshqa kod yuboring:")
                return
        
        # Yangi video qo'shish
        new_video = {
            **video_data,
            "code": user_input,
            "video_number": len(data["videos"]) + 1
        }
        
        data["videos"].append(new_video)
        save_data(data)
        del context.user_data["pending_video"]
        
        await update.message.reply_text(
            f"✅ Video #{new_video['video_number']} saqlandi!\n📹 Kod: {user_input}"
        )
        return
    
    if user_id == ADMIN_ID:
        await update.message.reply_text("ℹ️ Video yuklash uchun avval video yuboring.")
        return
    
    # Oddiy foydalanuvchi - kod tekshirish
    found_video = None
    for video in data["videos"]:
        if video.get("code") == user_input:
            found_video = video
            break
    
    if found_video:
        try:
            caption_text = f"🎉 Video #{found_video['video_number']} ochildi!"
            if found_video.get('caption'):
                caption_text += f"\n\n{found_video['caption']}"
            
            await update.message.reply_video(
                video=found_video["file_id"],
                caption=caption_text
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Video yuborishda xatolik: {str(e)}")
    else:
        await update.message.reply_text("❌ Noto'g'ri kod! Qayta urinib ko'ring.")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    data = load_data()
    if not data["videos"]:
        await update.message.reply_text("📹 Hozircha videolar yo'q")
        return
    
    message = "📋 Videolar ro'yxati:\n\n"
    for video in data["videos"]:
        message += f"#{video['video_number']} - Kod: {video['code']}\n"
    
    await update.message.reply_text(message)

def main():
    print("🚀 Bot ishga tushmoqda...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_videos))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Bot ishga tushdi!")
    application.run_polling()

if __name__ == "__main__":
    main()
