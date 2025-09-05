import requests
from bs4 import BeautifulSoup
import logging
import random
from datetime import datetime
import jdatetime
import os
from telegram import Bot
from telegram.error import TelegramError

# تنظیمات لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steel_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("steel_scraper")


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
            return {'http': proxy, 'https': proxy}
        else:
            logger.info("هیچ پروکسی در دسترس نیست، ادامه بدون پروکسی")
            return None
            
    except Exception as e:
        logger.error(f"خطا در دریافت پروکسی: {str(e)}")
        return None


def send_telegram_message(message):
    """ارسال پیام به تلگرام"""
    try:
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.error("توکن ربات یا چت آیدی تنظیم نشده است")
            return False
            
        bot = Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        logger.info("پیام با موفقیت ارسال شد")
        return True
        
    except TelegramError as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"خطای غیرمنتظره در ارسال پیام: {str(e)}")
        return False


def extract_prices(soup):
    """استخراج قیمت میلگرد از صفحه و دسته‌بندی بر اساس کارخانه و سایز"""
    prices = {}

    # پیدا کردن محصولات
    products = soup.select("div.product-item, li.product")  # بستگی به ساختار سایت داره

    for product in products:
        # عنوان محصول
        title = product.select_one("h2.woocommerce-loop-product__title")
        if not title:
            continue
        title_text = title.get_text(strip=True)

        # قیمت محصول
        price_tag = product.select_one("span.woocommerce-Price-amount")
        if not price_tag:
            continue
        price_text = price_tag.get_text(strip=True)

        # تعیین کارخانه
        factory = "نامشخص"
        if "ذوب" in title_text:
            factory = "ذوب‌آهن اصفهان"
        elif "میانه" in title_text:
            factory = "میانه"
        elif "فایکو" in title_text:
            factory = "فایکو"
        elif "بناب" in title_text:
            factory = "بناب"

        # تعیین سایز
        size = "نامشخص"
        for s in range(8, 40):  # سایزهای معمول میلگرد
            if f"{s}" in title_text:
                size = f"{s}"
                break

        key = (factory, size)
        prices[key] = price_text

    return prices


def scrape_milgard_ahanonline():
    """اسکراپ قیمت میلگرد از آهن آنلاین"""
    milgard_prices = {}
    max_retries = 3
    
    # تاریخ و ساعت فعلی
    now = datetime.now()
    jalali_date = jdatetime.datetime.fromgregorian(datetime=now).strftime('%Y/%m/%d %H:%M')
    
    for attempt in range(max_retries):
        try:
            proxies = get_fresh_proxy()
            url = "https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://ahanonline.com/',
                'Connection': 'keep-alive'
            }
            
            logger.info(f"تلاش {attempt + 1} برای دریافت داده")
            response = requests.get(url, headers=headers, timeout=30, proxies=proxies)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                prices = extract_prices(soup)
                milgard_prices.update(prices)
                
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
                
                # ارسال
                send_telegram_message(message)
                logger.info("استخراج و ارسال با موفقیت انجام شد")
                break
            else:
                logger.warning(f"خطا در دریافت داده، کد وضعیت: {response.status_code}")
        except Exception as e:
            logger.error(f"خطا در تلاش {attempt + 1}: {str(e)}")


if __name__ == "__main__":
    scrape_milgard_ahanonline()
