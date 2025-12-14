import os
from db import SessionLocal, Processed, News
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from sqlalchemy import or_
from spreader.telegram_message import format_telegram_message, format_telegram_message_ru
import json

load_dotenv()

WEBSITE_ID_MAP = {
    1: "news.am",
    2: "armenpress.am",
    3: "armtimes.com",
    4: "hraparak.am",
    5: "1lurer.am",
    6: "arm.sputniknews.ru",
    9: "t.me/s/rian_ru",
    # Ավելացրեք մյուսները ըստ անհրաժեշտության...
}

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = '@newsarmaipowerd'
TELEGRAM_BOT_TOKEN_RU = os.getenv('TELEGRAM_BOT_TOKEN_RU')
TELEGRAM_CHANNEL_ID_RU = '@newsrusaipowerd'

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


async def publish_to_telegram_ru(text, image_url=None):
    print("[INFO] Trying to publish to Telegram Rus...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN_RU)
    # Փորձում ենք ուղարկել լուսանկարով
    if image_url:
        try:
            await bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID_RU, photo=image_url, caption=text, parse_mode="MarkdownV2")
            print("[INFO] Successfully sent to Telegram Rus with photo.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send photo to Telegram Rus: {e}")
            # Փորձում ենք ուղարկել առանց լուսանկարի
            try:
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID_RU, text=text, parse_mode="MarkdownV2", disable_web_page_preview=True)
                print("[INFO] Successfully sent to Telegram Rus without photo.")
                return True
            except Exception as e2:
                print(f"[ERROR] Failed to send message to Telegram Rus: {e2}")
                return False
    else:
        # Եթե լուսանկար չկա, ուղարկում ենք միայն տեքստը
        try:
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID_RU, text=text, parse_mode="MarkdownV2", disable_web_page_preview=True)
            print("[INFO] Successfully sent to Telegram Rus without photo.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send message to Telegram Rus: {e}")
            return False

def get_image_url(db, base_id):
    content_row = db.query(News).filter(News.id == base_id).first()

    if not content_row:
        print(f"[DEBUG] get_image_url: Content տողը base_id={base_id}-ի համար չի գտնվել։")
        return None
    
    if not content_row.meta:
        print(f"[DEBUG] get_image_url: Content տողը base_id={base_id}-ի համար չունի 'meta' դաշտ։")
        return None

    meta = content_row.meta
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception as e:
            print(f"[DEBUG][ERROR] get_image_url: Meta JSON-ի վերծանումը ձախողվեց։ Սխալ՝ {e}")
            return None

    image_path = meta.get("image")
    website_id = content_row.website_id
    website_url = WEBSITE_ID_MAP.get(website_id)

    if image_path and website_url:
        final_image_url = None
        # === Վերականգնում ենք հին, ճիշտ աշխատող տրամաբանությունը ===

        # Դեպք 1: image_path-ը լիարժեք CDN հղում է (Sputnik)
        if image_path.startswith("https://cdn.am.sputniknews.ru"):
            final_image_url = image_path
            print(f"[DEBUG] get_image_url: Դեպք 1 (Sputnik CDN)։ Վերջնական URL՝ {final_image_url}")

        # Դեպք 2: image_path-ը պրոտոկոլից անկախ հղում է (Armenpress)
        elif image_path.startswith("//armenpress.am"):
            final_image_url = f"https:{image_path}"
            print(f"[DEBUG] get_image_url: Դեպք 2 (Armenpress)։ Վերջնական URL՝ {final_image_url}")

        # Դեպք 3: Կայքի URL-ը արդեն պարունակում է http (լիարժեք հասցե)
        elif website_url.startswith("http"):
            final_image_url = f"{website_url.rstrip('/')}/{image_path.lstrip('/')}"
            print(f"[DEBUG] get_image_url: Դեպք 3 (http)։ Վերջնական URL՝ {final_image_url}")

        # Դեպք 4: Լռելյայն դեպք (կայքի URL-ը միայն դոմենն է)
        else:
            final_image_url = f"https://{website_url.rstrip('/')}/{image_path.lstrip('/')}"
            print(f"[DEBUG] get_image_url: Դեպք 4 (Default)։ Վերջնական URL՝ {final_image_url}")
        
        return final_image_url
    
    else:
        print(f"[DEBUG] get_image_url: image_path-ը կամ website_url-ը բացակայում է, վերադարձնում ենք None։")
        return None

def get_urgent_value(path='spreader/selector_urgent_value.txt'):
    try:
        with open(path, 'r') as f:
            return int(f.read())
    except Exception:
        return 0

def publishing_cycle():
    # Սահմանում ենք լռելյայն արժեք
    sleep_time = 6 * 60  
    
    with SessionLocal() as db:
        try:
            row = db.query(Processed).filter(Processed.published == "publish").first()
            if row:
                print(f"[INFO] Found content to publish. base_id={row.base_id}")
                content_row = db.query(News).filter(News.id == row.base_id).first()
                url = content_row.url if content_row and content_row.url else "https://t.me/newsarmaipowerd"
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

            # sleep_time-ի հաշվարկի տրամաբանությունը մնում է նույնը
            not_published_count = db.query(Processed).filter(
                or_(Processed.published != "published", Processed.published.is_(None))
            ).count()
            
            urgent = get_urgent_value()
            
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
            
        except Exception as e:
            print(f"❌ Սխալ՝ հրապարակման ցիկլի ընթացքում: {e}")
            db.rollback()

    return sleep_time


def publishing_cycle_ru():
    with SessionLocal() as db:
        try:
            row = db.query(Processed).filter(Processed.published_r == "publish").first()
            if row:
                print(f"[INFO] Found RU content to publish. base_id={row.base_id}")
                content_row = db.query(News).filter(News.id == row.base_id).first()
                url = content_row.url if content_row and content_row.url else "https://t.me/newsrusaipowerd"
                image_url = get_image_url(db, row.base_id)
                
                message_ru = format_telegram_message_ru(row.title_r or "", row.generated_content_r or "", url)
                success = asyncio.run(publish_to_telegram_ru(message_ru, image_url))
                
                if success:
                    row.published_r = "published"
                    db.commit()
                    print(f"[INFO] Marked base_id={row.base_id} as published_r.")
                else:
                    print(f"[INFO] Publishing RU failed. base_id={row.base_id} not marked as published_r.")
            else:
                print("[INFO] No RU content with published_r='publish' found.")
        
        except Exception as e:
            print(f"❌ Սխալ՝ ռուսերեն հրապարակման ցիկլի ընթացքում: {e}")
            db.rollback()