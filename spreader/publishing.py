import os
from db import SessionLocal, Processed
from dotenv import load_dotenv
from telegram import Bot
from db import SessionLocal, Processed
import asyncio
from sqlalchemy import or_

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = '@testingai_iprc'

async def publish_to_telegram(text):
    print("[INFO] Trying to publish to Telegram...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=text)
        print("[INFO] Successfully sent to Telegram.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send to Telegram: {e}")
        return False

def get_urgent_value(path='spreader/selector_urgent_value.txt'):
    try:
        with open(path, 'r') as f:
            return int(f.read())
    except Exception:
        return 0

import asyncio

def publishing_cycle():
    db = SessionLocal()
    try:
        row = db.query(Processed).filter(Processed.published == "publish").first()
        if row:
            print(f"[INFO] Found content to publish. base_id={row.base_id}")
            success = asyncio.run(publish_to_telegram(row.generated_content))
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