import requests
from bs4 import BeautifulSoup
import os
from telegram import Bot
from telegram.error import TelegramError
import logging
import random

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# لیست پروکسی‌های ایرانی و بین‌المللی
PROXIES_LIST = [
    # پروکسی‌های ایرانی
    {"http": "http://5.160.90.91:80", "https": "http://5.160.90.91:80"},
    {"http": "http://94.130.54.171:80", "https": "http://94.130.54.171:80"},
    {"http": "http://5.160.90.92:80", "https": "http://5.160.90.92:80"},
    {"http": "http://5.160.138.110:80", "https": "http://5.160.138.110:80"},
    
    # پروکسی‌های بین‌المللی
    {"http": "http://20.210.113.32:80", "https": "http://20.210.113.32:80"},
    {"http": "http://20.206.106.192:80", "https": "http://20.206.106.192:80"},
    {"http": "http://20.24.43.214:80", "https": "http://20.24.43.214:80"},
    None  # بدون پروکسی
]

def get_steel_prices():
    """
    دریافت قیمت‌های میلگرد از ahanonline.com با پروکسی
    """
    prices = {}
    success = False
    
    for proxy in PROXIES_LIST:
        try:
            url = "https://ahanonline.com/product-category/%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/%D9%82%DB%8C%D9%85%D8%AA-%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://ahanonline.com/',
                'Connection': 'keep-alive'
            }
            
            logger.info(f"در حال تلاش با پروکسی: {proxy}")
            
            # زمان انتظار بیشتر برای پروکسی
            timeout = 15 if proxy else 30
            
            response = requests.get(url, headers=headers, timeout=timeout, proxies=proxy, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # لاگ کل صفحه برای دیباگ
                logger.info(f"صفحه با موفقیت دریافت شد. اندازه: {len(response.content)} بایت")
                
                # جستجوی قیمت‌ها - این بخش نیاز به تنظیم دارد
                price_elements = soup.find_all(['span', 'div', 'p'], class_=['price', 'amount', 'product-price'])
                
                if price_elements:
                    for i, price_element in enumerate(price_elements[:3]):  # فقط 3 قیمت اول
                        price_text = price_element.text.strip()
                        prices[f'میلگرد {12 + i*2} A3'] = price_text
                        logger.info(f"قیمت پیدا شد: میلگرد {12 + i*2} A3 - {price_text}")
                
                if prices:
                    success = True
                    break
                    
            else:
                logger.warning(f"پروکسی ناموفق. کد وضعیت: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"خطا با پروکسی {proxy}: {str(e)}")
            continue
    
    # اگر قیمتی پیدا نشد، مقادیر پیش فرض
    if not success:
        prices['میلگرد 12 A3'] = 'خطا در دریافت اطلاعات'
        prices['میلگرد 14 A3'] = 'خطا در دریافت اطلاعات'
        prices['میلگرد 16 A3'] = 'خطا در دریافت اطلاعات'
        logger.error("هیچ قیمتی پیدا نشد با هیچ پروکسی")
    
    return prices

def send_telegram_message(prices):
    """
    ارسال پیام به تلگرام
    """
    try:
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.error("توکن ربات یا شناسه چت تنظیم نشده است")
            return False
        
        bot = Bot(token=bot_token)
        
        if prices:
            message = "💰 قیمت‌های میلگرد از ahanonline.com:\n\n"
            for product, price in prices.items():
                message += f"🔸 {product}: {price}\n"
            
            message += "\n📊 منبع: ahanonline.com"
        else:
            message = "⚠️ امروز قادر به دریافت قیمت‌ها نبودم. لطفاً بعداً تلاش کنید."
        
        bot.send_message(chat_id=chat_id, text=message)
        logger.info("پیام با موفقیت ارسال شد")
        return True
        
    except TelegramError as e:
        logger.error(f"خطای تلگرام: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {str(e)}")
        return False

if __name__ == "__main__":
    # غیرفعال کردن هشدارهای SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    prices = get_steel_prices()
    send_telegram_message(prices)
