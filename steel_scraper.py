from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import logging, os, jdatetime
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import time

# لاگ
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("steel_scraper_selenium")

def send_telegram_message(message):
    try:
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        if not bot_token or not chat_id:
            logger.error("توکن یا Chat ID تنظیم نشده")
            return False
        bot = Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        logger.info("پیام ارسال شد")
        return True
    except TelegramError as e:
        logger.error(f"Telegram error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

def scrape_prices():
    url = "https://ahanonline.com/product-category/%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/%D9%82%DB%8C%D9%85%D8%AA-%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # بدون باز کردن مرورگر
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(5)  # صبر برای لود کامل جاوااسکریپت
        
        # پیدا کردن بخش‌های برندها
        brand_sections = driver.find_elements(By.CSS_SELECTOR, "div.products > ul > li")
        
        milgard_prices = {}
        for brand in brand_sections:
            try:
                factory_name = brand.find_element(By.CSS_SELECTOR, "h2 a").text.strip()
                rows = brand.find_elements(By.CSS_SELECTOR, "table tr")[1:]  # حذف هدر
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 3:
                        size = cols[0].text.strip()
                        price = cols[2].text.strip()
                        milgard_prices[(factory_name, size)] = price
            except:
                continue
        
        now = datetime.now()
        jalali_date = jdatetime.datetime.fromgregorian(datetime=now).strftime('%Y/%m/%d %H:%M')
        
        # ساخت پیام
        message = f"📊 قیمت‌های میلگرد - {jalali_date}\n\n"
        if milgard_prices:
            grouped = {}
            for (factory, size), price in milgard_prices.items():
                grouped.setdefault(factory, []).append((size, price))
            
            for factory, items in grouped.items():
                message += f"🏭 <b>{factory}</b>\n"
                for size, price in sorted(items, key=lambda x: int(x[0]) if x[0].isdigit() else 999):
                    message += f"   🔹 سایز {size}: {price}\n"
                message += "\n"
        else:
            message += "⚠️ قیمتی یافت نشد\n"
        
        message += "📎 منبع: آهن آنلاین"
        send_telegram_message(message)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_prices()
