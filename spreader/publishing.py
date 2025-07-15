import os
from db import SessionLocal, Processed, Content
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from sqlalchemy import or_
from spreader.telegram_message import format_telegram_message
import json

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = '@testingai_iprc'

async def publish_to_telegram(text, image_url=None):
    print("[INFO] Trying to publish to Telegram...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    # Փորձում ենք ուղարկել լուսանկարով
    if image_url:
        try:
            await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=image_url, caption=text, parse_mode="MarkdownV2")
            print("[INFO] Successfully sent to Telegram with photo.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send photo to Telegram: {e}")
            # Փորձում ենք ուղարկել առանց լուսանկարի
            try:
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text, parse_mode="MarkdownV2", disable_web_page_preview=True)
                print("[INFO] Successfully sent to Telegram without photo.")
                return True
            except Exception as e2:
                print(f"[ERROR] Failed to send message to Telegram: {e2}")
                return False
    else:
        # Եթե լուսանկար չկա, ուղարկում ենք միայն տեքստը
        try:
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text, parse_mode="MarkdownV2", disable_web_page_preview=True)
            print("[INFO] Successfully sent to Telegram without photo.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send message to Telegram: {e}")
            return False

def get_image_url(db, base_id):
    content_row = db.query(Content).filter(Content.id == base_id).first()
    if content_row and content_row.meta:
        meta = content_row.meta
        # Եթե meta-ն str է, վերծանիր, եթե dict է՝ օգտագործիր անմիջապես
        if isinstance(meta, str):
            import json
            try:
                meta = json.loads(meta)
            except Exception as e:
                print(f"[ERROR] Failed to parse meta: {e}")
                return None
        image_path = meta.get("image")
        website = content_row.website if content_row and content_row.website else ""
        if image_path and website:
            # Բացառություն՝ եթե image_path-ը արդեն լիարժեք հղում է
            if image_path.startswith("https://cdn.am.sputniknews.ru"):
                image_url = image_path
            elif image_path.startswith("//armenpress.am"):
                image_url = f"https:{image_path}"
            elif website.startswith("http"):
                image_url = f"{website.rstrip('/')}/{image_path.lstrip('/')}"
            else:
                image_url = f"https://{website.rstrip('/')}/{image_path.lstrip('/')}"
                print(image_url)
            return image_url
    return None

def get_urgent_value(path='spreader/selector_urgent_value.txt'):
    try:
        with open(path, 'r') as f:
            return int(f.read())
    except Exception:
        return 0

def publishing_cycle():
    db = SessionLocal()
    try:
        row = db.query(Processed).filter(Processed.published == "publish").first()
        if row:
            print(f"[INFO] Found content to publish. base_id={row.base_id}")
            # Fetch url from Content table
            url = ""
            content_row = db.query(Content).filter(Content.id == row.base_id).first()
            if content_row and content_row.url:
                url = content_row.url
            else:
                url = "https://t.me/testingai_iprc"  # fallback or default

            # Ստանալ image url
            image_url = get_image_url(db, row.base_id)

            message = format_telegram_message(row.title or "", row.generated_content or "", url)
            success = asyncio.run(publish_to_telegram(message, image_url))
            if success:
                row.published = "published"
                db.commit()
                print(f"[INFO] Marked base_id={row.base_id} as published.")
            else:
                print(f"[INFO] Publishing failed. base_id={row.base_id} not marked as published.")
        else:
            print("[INFO] No content with published='publish' found.")

        not_published_count = db.query(Processed).filter(
            or_(
                Processed.published != "published",
                Processed.published.is_(None)
            )
        ).count()
        print(f"[DEBUG] Not published count: {not_published_count}")

        urgent = get_urgent_value()
        print(f"[DEBUG] Urgent value: {urgent}")

        if urgent > 1:
            sleep_time = 2 * 60
        elif urgent <= 1 and not_published_count > 12:
            sleep_time = 3 * 60
        elif urgent <= 1 and not_published_count > 8:
            sleep_time = 4 * 60
        elif urgent <= 1 and not_published_count > 5:
            sleep_time = 5 * 60
        else:
            sleep_time = 6 * 60

        print(f"[INFO] Next cycle in {sleep_time // 60} minutes.")
    finally:
        db.close()
    return sleep_time