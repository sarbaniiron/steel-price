import os
import logging
import random
from datetime import datetime
import jdatetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from telegram import Bot, TelegramError

# ===================== تنظیمات لاگ =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steel_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===================== دریافت پروکسی (اختیاری) =====================
def get_fresh_proxy():
    """دریافت پروکسی جدید و فعال"""
    try:
        free_proxies = [
            # 'http://proxy1:port',
            # 'http://proxy2:port',
        ]
        if free_proxies:
            proxy = random.choice(free_proxies)
            logger.info(f"پروکسی انتخاب شد: {proxy}")
            return {
                'http': proxy,
                'https': proxy
            }
        else:
            return None
    except Exception as e:
        logger.error(f"خطا در دریافت پروکسی: {str(e)}")
        return None

# ===================== ارسال پیام تلگرام =====================
def send_telegram_message(message):
    try:
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')

        if not bot_token or not chat_id:
            logger.error("توکن ربات یا چت آیدی تنظیم نشده است")
            return False

        bot = Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message)
        logger.info("پیام با موفقیت ارسال شد")
        return True

    except TelegramError as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"خطای غیرمنتظره در ارسال پیام: {str(e)}")
        return False

# ===================== استخراج قیمت‌ها =====================
def extract_prices(driver):
    """استخراج قیمت‌ها از صفحه میلگرد آهن آنلاین"""
    prices = {}
    try:
        driver.get("https://ahanonline.com/product-category/%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/%D9%82%DB%8C%D9%85%D8%AA-%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/")
        driver.implicitly_wait(10)

        # مثال استخراج: نام محصول و قیمت
        product_elements = driver.find_elements("css selector", "div.products div.product")
        for prod in product_elements:
            try:
                name = prod.find_element("css selector", "h2.woocommerce-loop-product__title").text
                price = prod.find_element("css selector", "span.woocommerce-Price-amount").text
                prices[name] = price
            except Exception:
                continue
    except WebDriverException as e:
        logger.error(f"خطا در باز کردن صفحه یا استخراج: {str(e)}")
    return prices

# ===================== اجرای اسکریپت =====================
def scrape_prices():
    try:
        # ===================== تنظیمات Chrome =====================
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)

        # ===================== دریافت قیمت‌ها =====================
        milgard_prices = extract_prices(driver)

        driver.quit()

        # ===================== تاریخ شمسی =====================
        now = datetime.now()
        jalali_date = jdatetime.datetime.fromgregorian(datetime=now).strftime('%Y/%m/%d %H:%M')

        # ===================== ایجاد پیام =====================
        message = f"📊 قیمت‌های میلگرد - {jalali_date}\n\n"
        if milgard_prices:
            for product, price in milgard_prices.items():
                message += f"🔹 {product}: {price}\n"
        else:
            message += "⚠️ قیمتی یافت نشد\n"
        message += f"\n📎 منبع: آهن آنلاین"

        # ===================== ارسال به تلگرام =====================
        send_telegram_message(message)

    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {str(e)}")

# ===================== اجرای اصلی =====================
if __name__ == "__main__":
    scrape_prices()
