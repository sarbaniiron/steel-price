import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import jdatetime
import os
from telegram import Bot
from telegram.error import TelegramError
import pytz
import re

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
        iran_timezone = pytz.timezone('Asia/Tehran')
        now_utc = datetime.utcnow()
        now_iran = now_utc.astimezone(iran_timezone)
        
        jalali_date = jdatetime.datetime.fromgregorian(
            datetime=now_iran,
            locale='fa_IR'
        )
        
        date_str = jalali_date.strftime('%Y/%m/%d')
        time_str = jalali_date.strftime('%H:%M')
        
        return f"{date_str} ساعت {time_str}"
        
    except Exception as e:
        logger.error(f"خطا در دریافت زمان ایران: {str(e)}")
        return "تاریخ نامعلوم"

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
        
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {str(e)}")
        return False

def scrape_ahanonline_prices():
    """استخراج قیمت‌های میلگرد A3 از آهن آنلاین"""
    url = "https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://ahanonline.com/',
        'Connection': 'keep-alive'
    }
    
    try:
        logger.info("در حال اتصال به آهن آنلاین...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"خطای HTTP: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # استخراج قیمت‌ها
        prices = extract_prices_from_html(soup)
        
        if not prices:
            logger.warning("هیچ قیمتی یافت نشد")
            return None
            
        return prices
        
    except Exception as e:
        logger.error(f"خطا در اسکراپ: {str(e)}")
        return None

def extract_prices_from_html(soup):
    """استخراج قیمت‌ها از HTML سایت"""
    prices = {}
    
    try:
        # پیدا کردن محصولات میلگرد
        products = soup.find_all('div', class_='product')
        
        for product in products:
            # بررسی اینکه محصول میلگرد A3 است
            title_element = product.find('h2', class_='product-title')
            if not title_element:
                continue
                
            title = title_element.get_text(strip=True).lower()
            if 'میلگرد' not in title and 'a3' not in title:
                continue
            
            # استخراج نام شرکت
            company = extract_company_name(title)
            if not company:
                continue
            
            # استخراج سایز
            size = extract_size(title)
            if not size:
                continue
            
            # استخراج قیمت
            price_element = product.find('span', class_='price')
            if not price_element:
                continue
                
            price = price_element.get_text(strip=True)
            
            # افزودن به دیکشنری
            if company not in prices:
                prices[company] = {}
            
            prices[company][f"سایز {size}"] = price
            
    except Exception as e:
        logger.error(f"خطا در استخراج از HTML: {str(e)}")
    
    return prices

def extract_company_name(title):
    """استخراج نام شرکت از عنوان محصول"""
    companies = [
        'ذوب آهن', 'فولاد مبارکه', 'کاویان', 'ظفر بناب', 'نیشابور',
        'خوزستان', 'اهواز', 'اصفهان', 'مبارکه', 'کاویان'
    ]
    
    for company in companies:
        if company in title:
            return company
    return None

def extract_size(title):
    """استخراج سایز از عنوان محصول"""
    # جستجوی الگوهای سایز (مثلاً ۱۶، 16، ۱۶مم، 16mm)
    size_patterns = [
        r'(\d+)\s*مم',
        r'(\d+)\s*mm',
        r'سایز\s*(\d+)',
        r'size\s*(\d+)',
        r'\b(\d{1,2})\b'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, title)
        if match:
            size = match.group(1)
            # اطمینان از اینکه سایز بین 8 تا 32 است
            if size.isdigit() and 8 <= int(size) <= 32:
                return size
    
    return None

def format_prices_message(prices, iran_time):
    """قالب‌بندی پیام قیمت‌ها"""
    if not prices:
        return "⚠️ قیمتی یافت نشد"
    
    message = f"<b>📊 قیمت‌های میلگرد A3 - {iran_time}</b>\n\n"
    
    for company, sizes in prices.items():
        message += f"<b>🏭 {company}:</b>\n"
        
        # مرتب کردن سایزها از کوچک به بزرگ
        sorted_sizes = sorted(sizes.items(), key=lambda x: int(x[0].replace('سایز ', '')))
        
        for size, price in sorted_sizes:
            message += f"   🔸 {size} = {price}\n"
        
        message += "\n"
    
    message += f"📎 منبع: آهن آنلاین\n"
    message += f"⚡ به روزرسانی آنی"
    
    return message

def main():
    """تابع اصلی"""
    logger.info("شروع استخراج قیمت‌های میلگرد...")
    
    # دریافت تاریخ ایران
    iran_time = get_iran_time()
    
    # استخراج قیمت‌ها از سایت
    prices = scrape_ahanonline_prices()
    
    if prices:
        # فرمت‌بندی پیام
        message = format_prices_message(prices, iran_time)
        
        # نمایش در کنسول
        print("=" * 50)
        print(message.replace('<b>', '').replace('</b>', ''))
        print("=" * 50)
        
        # ارسال به تلگرام
        send_telegram_message(message)
        
        logger.info(f"استخراج موفق: {len(prices)} شرکت یافت شد")
    else:
        error_msg = "⚠️ خطا در دریافت قیمت‌ها از آهن آنلاین"
        print(error_msg)
        send_telegram_message(error_msg)
        logger.error("استخراج ناموفق")

if __name__ == "__main__":
    main()
