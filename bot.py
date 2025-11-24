import logging
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Environment variables dan o'qiymiz
BOT_TOKEN = os.getenv("BOT_TOKEN", "8226993737:AAErIjCoq80NhvBsXr0nMbMMKWLBXSoaAD4")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7800649803"))

print(f"🔧 Bot token: {BOT_TOKEN[:10]}...")
print(f"🔧 Admin ID: {ADMIN_ID}")

# Ma'lumotlarni saqlash uchun
DATA_FILE = "bot_data.json"

# Logging sozlash
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
            for video in data["videos"]:
                if "code" not in video:
                    video["code"] = "eski_kod"
                if "used_by" not in video:
                    video["used_by"] = []
                if "caption" not in video:
                    video["caption"] = ""
            return data
    except Exception as e:
        print(f"❌ JSON fayl yuklashda xatolik: {e}")
        return {"videos": []}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ JSON fayl saqlashda xatolik: {e}")

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"👤 Start bosildi: {user_id}")
    
    if user_id == ADMIN_ID:
        data = load_data()
        video_count = len(data["videos"])
        await update.message.reply_text(
            f"👋 Salom Admin!\n📹 Video yuklash uchun video yuboring\n📊 Jami videolar: {video_count} ta\n🔐 Har bir video uchun alohida kod berasiz"
        )
    else:
        await update.message.reply_text("👋 Salom!\nVideo ko'rish uchun kod yuboring.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"📹 Video qabul qilindi: {user_id}")
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Faqat admin video yuklay oladi!")
        return
    
    video_file = update.message.video
    if video_file:
        caption = update.message.caption or ""
        data = load_data()
        
        await update.message.reply_text("📹 Video qabul qilindi!\n🔐 Ushbu video uchun kodni yuboring:")
        
        context.user_data["pending_video"] = {
            "file_id": video_file.file_id,
            "file_unique_id": video_file.file_unique_id,
            "file_size": video_file.file_size,
            "timestamp": datetime.now().isoformat(),
            "caption": caption
        }

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text
    print(f"📨 Matn qabul qilindi: {user_id} -> {user_input}")
    
    data = load_data()
    
    if user_id == ADMIN_ID and "pending_video" in context.user_data:
        video_data = context.user_data["pending_video"]
        
        for video in data["videos"]:
            if video["code"] == user_input:
                await update.message.reply_text("❌ Bu kod allaqachon mavjud! Boshqa kod yuboring:")
                return
        
        new_video = {
            **video_data,
            "code": user_input,
            "video_number": len(data["videos"]) + 1,
            "used_by": []
        }
        
        data["videos"].append(new_video)
        save_data(data)
        del context.user_data["pending_video"]
        
        await update.message.reply_text(
            f"✅ Video #{new_video['video_number']} saqlandi!\n📹 Kod: {user_input}\n📊 Jami: {len(data['videos'])} ta"
        )
        return
    
    if user_id == ADMIN_ID:
        await update.message.reply_text("ℹ️ Video yuklash uchun avval video yuboring.")
        return
    
    if not data["videos"]:
        await update.message.reply_text("📹 Hozircha videolar mavjud emas!")
        return
    
    found_video = None
    for video in data["videos"]:
        if "code" in video and video["code"] == user_input:
            found_video = video
            break
    
    if found_video:
        user_info = f"{update.effective_user.first_name} (ID: {user_id})"
        if "used_by" not in found_video:
            found_video["used_by"] = []
        if user_info not in found_video["used_by"]:
            found_video["used_by"].append(user_info)
            save_data(data)
        
        try:
            caption_text = f"🎉 Video #{found_video['video_number']} ochildi!"
            if found_video.get('caption'):
                caption_text += f"\n\n{found_video['caption']}"
            
            await update.message.reply_video(
                video=found_video["file_id"],
                caption=caption_text
            )
            print(f"✅ Video yuborildi: {user_id} -> {found_video['code']}")
        except Exception as e:
            await update.message.reply_text(f"❌ Video yuborishda xatolik: {str(e)}")
    else:
        await update.message.reply_text("❌ Noto'g'ri kod! Qayta urinib ko'ring.")

async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if video.get('caption'):
            message += f"   Yozuv: {video['caption'][:30]}{'...' if len(video['caption']) > 30 else ''}\n"
        message += f"   Foydalanuvchilar: {len(video.get('used_by', []))} ta\n\n"
    
    await update.message.reply_text(message)

async def handle_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    data = {"videos": []}
    save_data(data)
    await update.message.reply_text("✅ Barcha videolar o'chirildi!")

async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("ℹ️ Admin: Video yuboring yoki /list ni bosing")
    else:
        await update.message.reply_text("ℹ️ Video ko'rish uchun kod yuboring")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Xatolik yuz berdi:", exc_info=context.error)
    print(f"❌ Xatolik: {context.error}")

def main():
    print("🚀 Bot ishga tushmoqda...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        print("✅ Application yaratildi")
        
        data = load_data()
        save_data(data)
        print("✅ JSON fayl to'g'rilandi")
        
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/start"), handle_start))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/list"), handle_list))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/clear"), handle_clear))
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))
        application.add_handler(MessageHandler(filters.TEXT, handle_text))
        application.add_handler(MessageHandler(filters.ALL, handle_other))
        application.add_error_handler(error_handler)
        
        print("✅ Handlerlar qo'shildi")
        print("🤖 Bot ishga tushdi!")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Bot ishga tushmadi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
