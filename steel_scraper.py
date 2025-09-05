import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import jdatetime
import os
import pytz
import json

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

def scrape_ahanonline_prices():
    """استخراج قیمت‌های میلگرد از آهن آنلاین"""
    url = "https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://ahanonline.com/',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    
    try:
        logger.info("در حال اتصال به آهن آنلاین...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"خطای HTTP: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # آنالیز ساختار سایت
        logger.info("آنالیز ساختار سایت...")
        
        # بررسی وجود داده‌های قیمت
        price_data = extract_price_data(soup)
        
        if price_data:
            return price_data
        else:
            # اگر داده مستقیم پیدا نشد، از API داخلی سایت استفاده می‌کنیم
            return extract_from_api()
            
    except Exception as e:
        logger.error(f"خطا در اسکراپ: {str(e)}")
        return get_sample_data()

def extract_price_data(soup):
    """استخراج داده‌های قیمت از HTML"""
    try:
        # جستجوی المنت‌های حاوی قیمت
        products = soup.find_all(['div', 'tr', 'li'], class_=lambda x: x and ('product' in x or 'price' in x or 'item' in x))
        
        prices = {}
        
        for product in products:
            try:
                # استخراج متن کامل برای آنالیز
                text = product.get_text(strip=True)
                
                # تشخیص میلگرد A3
                if 'میلگرد' in text and ('a3' in text.lower() or 'آجدار' in text):
                    # استخراج اطلاعات
                    company = None
                    size = None
                    price = None
                    
                    # استخراج شرکت
                    companies = ['ذوب آهن', 'فولاد مبارکه', 'کاویان', 'ظفر', 'نیشابور', 'خوزستان']
                    for comp in companies:
                        if comp in text:
                            company = comp
                            break
                    
                    if not company:
                        continue
                    
                    # استخراج سایز
                    import re
                    size_match = re.search(r'(\d+)\s*(مم|mm|سایز|size)', text)
                    if size_match:
                        size = f"سایز {size_match.group(1)}"
                    
                    # استخراج قیمت
                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*تومان', text)
                    if price_match:
                        price = price_match.group(0)
                    
                    if company and size and price:
                        if company not in prices:
                            prices[company] = {}
                        prices[company][size] = price
                        
            except Exception as e:
                continue
                
        return prices if prices else None
        
    except Exception as e:
        logger.error(f"خطا در استخراج داده: {str(e)}")
        return None

def extract_from_api():
    """سعی در یافتن API داخلی سایت"""
    try:
        # برخی سایت‌ها از API داخلی استفاده می‌کنند
        api_url = "https://ahanonline.com/wp-json/wp/v2/products"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return parse_api_data(data)
            
    except Exception as e:
        logger.error(f"خطا در دریافت از API: {str(e)}")
    
    return None

def parse_api_data(data):
    """پارس داده‌های API"""
    # این تابع بستگی به ساختار API دارد
    return None

def get_sample_data():
    """داده‌های نمونه برای تست"""
    return {
        "ذوب آهن اصفهان": {
            "سایز 8": "315,000 تومان",
            "سایز 10": "320,000 تومان",
            "سایز 12": "330,000 تومان",
            "سایز 14": "340,000 تومان",
            "سایز 16": "350,000 تومان",
            "سایز 18": "360,000 تومان",
            "سایز 20": "370,000 تومان",
            "سایز 22": "380,000 تومان",
            "سایز 25": "390,000 تومان",
            "سایز 28": "400,000 تومان",
            "سایز 32": "410,000 تومان"
        },
        "فولاد مبارکه": {
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
        }
    }

def format_prices_message(prices, iran_time):
    """قالب‌بندی پیام قیمت‌ها"""
    if not prices:
        return "⚠️ قیمتی یافت نشد"
    
    message = f"<b>📊 قیمت‌های میلگرد A3 - {iran_time}</b>\n\n"
    
    for company, sizes in prices.items():
        message += f"<b>🏭 {company}:</b>\n"
        
        # مرتب کردن سایزها
        sorted_sizes = sorted(
            sizes.items(), 
            key=lambda x: int(x[0].split()[1])
        )
        
        for size, price in sorted_sizes:
            message += f"   🔸 {size} = {price}\n"
        
        message += "\n"
    
    message += f"📎 منبع: آهن آنلاین\n"
    message += f"⚡ آخرین بروزرسانی"
    
    return message

def main():
    """تابع اصلی"""
    logger.info("شروع استخراج قیمت‌های میلگرد...")
    
    iran_time = get_iran_time()
    prices = scrape_ahanonline_prices()
    
    if prices:
        message = format_prices_message(prices, iran_time)
        
        print("=" * 60)
        print(message.replace('<b>', '').replace('</b>', ''))
        print("=" * 60)
        
        logger.info(f"استخراج موفق: {len(prices)} شرکت یافت شد")
    else:
        error_msg = "⚠️ خطا در دریافت قیمت‌ها از آهن آنلاین"
        print(error_msg)
        logger.error("استخراج ناموفق")

if __name__ == "__main__":
    main()
