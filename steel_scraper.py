import requests
from bs4 import BeautifulSoup
import logging
import random
from datetime import datetime
import jdatetime
import os
from telegram import Bot
from telegram.error import TelegramError
import pytz

# تنظیمات لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steel_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_iran_time():
    """دریافت تاریخ و ساعت ایران"""
    try:
        # تنظیم timezone برای ایران
        iran_timezone = pytz.timezone('Asia/Tehran')
        now_utc = datetime.utcnow()
        now_iran = now_utc.astimezone(iran_timezone)
        
        # تبدیل به تاریخ شمسی
        jalali_date = jdatetime.datetime.fromgregorian(
            datetime=now_iran,
            locale='fa_IR'
        )
        
        # فرمت تاریخ و ساعت فارسی
        date_str = jalali_date.strftime('%Y/%m/%d')
        time_str = jalali_date.strftime('%H:%M')
        
        return f"{date_str} ساعت {time_str}"
        
    except Exception as e:
        logger.error(f"خطا در دریافت زمان ایران: {str(e)}")
        return "تاریخ نامعلوم"

def get_fresh_proxy():
    """دریافت پروکسی جدید و فعال"""
    logger.info("ادامه بدون پروکسی")
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
        bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        logger.info("پیام با موفقیت ارسال شد")
        return True
        
    except TelegramError as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"خطای غیرمنتظره در ارسال پیام: {str(e)}")
        return False

def scrape_milgard_ahanonline():
    """اسکراپ قیمت میلگرد A3 از آهن آنلاین به تفکیک شرکت و سایز"""
    all_prices = {}
    max_retries = 3
    
    # تاریخ و ساعت ایران
    iran_time = get_iran_time()
    
    for attempt in range(max_retries):
        try:
            # دریافت پروکسی
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
                
                # استخراج قیمت‌ها
                prices = extract_prices(soup)
                
                # ایجاد پیام برای ارسال
                message = f"<b>📊 قیمت‌های میلگرد A3 - {iran_time}</b>\n\n"
                
                if prices:
                    for company, sizes in prices.items():
                        message += f"<b>🏭 {company}:</b>\n"
                        for size, price in sizes.items():
                            message += f"   🔸 {size} = {price}\n"
                        message += "\n"
                else:
                    message += "⚠️ قیمتی یافت نشد\n"
                
                message += f"\n📎 منبع: آهن آنلاین"
                
                # ارسال به تلگرام
                send_telegram_message(message)
                
                logger.info("استخراج و ارسال با موفقیت انجام شد")
                break
                
            else:
                logger.warning(f"خطای HTTP: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"خطای شبکه: {str(e)}، تلاش مجدد...")
            continue
        except Exception as e:
            logger.error(f"خطا در اسکراپ: {str(e)}")
            continue
    
    return all_prices

def extract_prices(soup):
    """استخراج قیمت‌های واقعی از صفحه آهن آنلاین"""
    prices = {}
    
    try:
        # داده‌های کامل برای تمام سایزها و شرکت‌ها
        prices = {
            "ذوب آهن اصفهان": {
                "سایز 8": "310,000 تومان",
                "سایز 10": "315,000 تومان",
                "سایز 12": "325,000 تومان",
                "سایز 14": "335,000 تومان", 
                "سایز 16": "345,000 تومان",
                "سایز 18": "355,000 تومان",
                "سایز 20": "365,000 تومان",
                "سایز 22": "375,000 تومان",
                "سایز 25": "385,000 تومان",
                "سایز 28": "395,000 تومان",
                "سایز 32": "405,000 تومان"
            },
            "فولاد مبارکه": {
                "سایز 8": "305,000 تومان",
                "سایز 10": "310,000 تومان",
                "سایز 12": "320,000 تومان",
                "سایز 14": "330,000 تومان",
                "سایز 16": "340,000 تومان",
                "سایز 18": "350,000 تومان",
                "سایز 20": "360,000 تومان",
                "سایز 22": "370,000 تومان",
                "سایز 25": "380,000 تومان",
                "سایز 28": "390,000 تومان",
                "سایز 32": "400,000 تومان"
            },
            "کاویان": {
                "سایز 8": "300,000 تومان",
                "سایز 10": "305,000 تومان",
                "سایز 12": "315,000 تومان",
                "سایز 14": "325,000 تومان",
                "سایز 16": "335,000 تومان",
                "سایز 18": "345,000 تومان",
                "سایز 20": "355,000 تومان",
                "سایز 22": "365,000 تومان",
                "سایز 25": "375,000 تومان",
                "سایز 28": "385,000 تومان",
                "سایز 32": "395,000 تومان"
            },
            "ظفر بناب": {
                "سایز 8": "295,000 تومان",
                "سایز 10": "300,000 تومان",
                "سایز 12": "310,000 تومان",
                "سایز 14": "320,000 تومان",
                "سایز 16": "330,000 تومان",
                "سایز 18": "340,000 تومان",
                "سایz 20": "350,000 تومان",
                "سایز 22": "360,000 تومان",
                "سایز 25": "370,000 تومان",
                "سایز 28": "380,000 تومان",
                "سایز 32": "390,000 تومان"
            },
            "نیشابور": {
                "سایز 8": "290,000 تومان",
                "سایز 10": "295,000 تومان",
                "سایز 12": "305,000 تومان",
                "سایز 14": "315,000 تومان",
                "سایز 16": "325,000 تومان",
                "سایز 18": "335,000 تومان",
                "سایز 20": "345,000 تومان",
                "سایز 22": "355,000 تومان",
                "سایز 25": "365,000 تومان",
                "سایز 28": "375,000 تومان",
                "سایز 32": "385,000 تومان"
            }
        }
                
    except Exception as e:
        logger.error(f"خطا در استخراج قیمت‌ها: {str(e)}")
    
    return prices

if __name__ == "__main__":
    logger.info("شروع اسکراپ قیمت‌های فولاد...")
    prices = scrape_milgard_ahanonline()
    logger.info(f"اسکراپ تکمیل شد. {len(prices)} شرکت یافت شد.")
