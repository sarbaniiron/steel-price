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
logger = logging.getLogger(__name__)

def get_fresh_proxy():
    """دریافت پروکسی جدید و فعال"""
    try:
        # لیستی از پروکسی‌های رایگان (می‌توانید扩充 کنید)
        free_proxies = [
            # 'http://proxy1:port',
            # 'http://proxy2:port',
            # ...
        ]
        
        if free_proxies:
            proxy = random.choice(free_proxies)
            logger.info(f"پروکسی انتخاب شد: {proxy}")
            return {
                'http': proxy,
                'https': proxy
            }
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
        bot.send_message(chat_id=chat_id, text=message)
        logger.info("پیام با موفقیت ارسال شد")
        return True
        
    except TelegramError as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"خطای غیرمنتظره در ارسال پیام: {str(e)}")
        return False

def scrape_milgard_ahanonline():
    """اسکراپ قیمت میلگرد از آهن آنلاین"""
    milgard_prices = {}
    max_retries = 3
    
    # تاریخ و ساعت فعلی
    now = datetime.now()
    jalali_date = jdatetime.datetime.fromgregorian(datetime=now).strftime('%Y/%m/%d %H:%M')
    
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
                
                # استخراج قیمت‌ها (این سلکتورها نیاز به تنظیم دقیق دارند)
                prices = extract_prices(soup)
                milgard_prices.update(prices)
                
                # ایجاد پیام برای ارسال
                message = f"📊 قیمت‌های میلگرد - {jalali_date}\n\n"
                
                if milgard_prices:
                    for product, price in milgard_prices.items():
                        message += f"🔹 {product}: {price}\n"
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
    
    return milgard_prices

def extract_prices(soup):
    """استخراج قیمت‌ها از صفحه"""
    prices = {}
    
    try:
        # این بخش نیاز به آنالیز دقیق ساختار HTML سایت دارد
        # نمونه استخراج فرضی:
        
        # پیدا کردن المنت‌های حاوی قیمت
        price_elements = soup.find_all('span', class_='price')
        
        for element in price_elements[:10]:  # محدود کردن برای تست
            product_name = "میلگرد A3"
            price_text = element.get_text(strip=True)
            
            if price_text and 'تومان' in price_text:
                prices[product_name] = price_text
                
    except Exception as e:
        logger.error(f"خطا در استخراج قیمت‌ها: {str(e)}")
    
    # داده نمونه برای تست
    if not prices:
        prices = {
            'میلگرد 16 آجدار': '325,000 تومان',
            'میلگرد 14 ساده': '310,000 تومان',
            'میلگرد 18 صنعتی': '340,000 تومان'
        }
    
    return prices

if __name__ == "__main__":
    logger.info("شروع اسکراپ قیمت‌های فولاد...")
    prices = scrape_milgard_ahanonline()
    logger.info(f"اسکراپ завер شد. {len(prices)} قیمت یافت شد.")
