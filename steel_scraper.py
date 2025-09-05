import requests
from bs4 import BeautifulSoup
import os
from telegram import Bot
from telegram.error import TelegramError
import logging
from datetime import datetime
import jdatetime
import time

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات پروکسی - پروکسی خود را اینجا قرار دهید
PROXIES = {
    'http': 'http://username:password@proxy_ip:proxy_port',
    'https': 'http://username:password@proxy_ip:proxy_port'
}

def scrape_ahan_online_milgard():
    """اسکراپ قیمت میلگردهای A3 از آهن آنلاین"""
    prices = {}
    try:
        url = "https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(url, headers=headers, timeout=30, proxies=PROXIES)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # اینجا سلکتورهای دقیق سایت را باید قرار دهید
            # مثال فرضی:
            products = {
                '12': '.rebar-12-price',
                '14': '.rebar-14-price', 
                '16': '.rebar-16-price',
                '18': '.rebar-18-price',
                '20': '.rebar-20-price'
            }
            
            for size, selector in products.items():
                element = soup.select_one(selector)
                if element:
                    prices[f'میلگرد سایز {size}'] = element.text.strip() + ' تومان'
                    
        else:
            logger.error(f"خطا در دریافت میلگرد. کد وضعیت: {response.status_code}")
            
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت میلگرد: {str(e)}")
    
    return prices

def scrape_ahan_online_profile():
    """اسکراپ قیمت پروفیل از آهن آنلاین"""
    prices = {}
    try:
        url = "https://ahanonline.com/product-category/انواع-پروفیل/پروفیل/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=30, proxies=PROXIES)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # سلکتورهای پروفیل
            profiles = {
                '4x4': '.profile-4x4-price',
                '5x5': '.profile-5x5-price',
                '6x6': '.profile-6x6-price',
                '8x8': '.profile-8x8-price'
            }
            
            for size, selector in profiles.items():
                element = soup.select_one(selector)
                if element:
                    prices[f'قوطی {size}'] = element.text.strip() + ' تومان'
                    
        else:
            logger.error(f"خطا در دریافت پروفیل. کد وضعیت: {response.status_code}")
            
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت پروفیل: {str(e)}")
    
    return prices

def scrape_ahan_online_nabshi():
    """اسکراپ قیمت نبشی از آهن آنلاین"""
    prices = {}
    try:
        url = "https://ahanonline.com/product-category/نشبی-و-ناودانی/نشبی/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=30, proxies=PROXIES)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # سلکتورهای نبشی
            nabshi_sizes = {
                '40': {
                    '4mm': '.nabshi-40-4mm-price',
                    '5mm': '.nabshi-40-5mm-price'
                },
                '50': {
                    '5mm': '.nabshi-50-5mm-price', 
                    '6mm': '.nabshi-50-6mm-price'
                },
                '60': {
                    '6mm': '.nabshi-60-6mm-price',
                    '8mm': '.nabshi-60-8mm-price'
                }
            }
            
            for size, thicknesses in nabshi_sizes.items():
                for thickness, selector in thicknesses.items():
                    element = soup.select_one(selector)
                    if element:
                        prices[f'نبشی {size} ضخامت {thickness}'] = element.text.strip() + ' تومان'
                        
        else:
            logger.error(f"خطا در دریافت نبشی. کد وضعیت: {response.status_code}")
            
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت نبشی: {str(e)}")
    
    return prices

def scrape_ahan_online_loule():
    """اسکراپ قیمت لوله از آهن آنلاین"""
    prices = {}
    try:
        url = "https://ahanonline.com/product-category/انواع-لوله/لوله-درز-مستقیم/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=30, proxies=PROXIES)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # سلکتورهای لوله
            loule_sizes = {
                '1': '.loule-1-price',
                '2': '.loule-2-price',
                '3': '.loule-3-price', 
                '4': '.loule-4-price',
                '5': '.loule-5-price',
                '6': '.loule-6-price'
            }
            
            for size, selector in loule_sizes.items():
                element = soup.select_one(selector)
                if element:
                    prices[f'لوله سایز {size}'] = element.text.strip() + ' تومان'
                    
        else:
            logger.error(f"خطا در دریافت لوله. کد وضعیت: {response.status_code}")
            
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت لوله: {str(e)}")
    
    return prices

def get_all_prices():
    """دریافت قیمت‌ها از تمام دسته‌ها"""
    all_prices = {}
    
    # استخراج از تمام بخش‌ها
    all_prices.update(scrape_ahan_online_milgard())
    all_prices.update(scrape_ahan_online_profile())
    all_prices.update(scrape_ahan_online_nabshi())
    all_prices.update(scrape_ahan_online_loule())
    
    return all_prices

def send_telegram_message(prices):
    """ارسال پیام به تلگرام"""
    try:
        bot_token = os.getenv('BOT_TOKEN')
        chat_id = os.getenv('CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.error("توکن ربات یا شناسه چت تنظیم نشده است")
            return False
        
        bot = Bot(token=bot_token)
        
        if prices:
            # تاریخ شمسی
            jalali_date = jdatetime.datetime.now().strftime('%Y/%m/%d')
            
            message = f"💰 قیمت آهن آلات - {jalali_date}\n\n"
            
            # گروه‌بندی قیمت‌ها
            categories = {
                'میلگرد': [],
                'قوطی': [],
                'نبشی': [],
                'لوله': []
            }
            
            for product, price in prices.items():
                if 'میلگرد' in product:
                    categories['میلگرد'].append(f"🔸 {product}: {price}")
                elif 'قوطی' in product:
                    categories['قوطی'].append(f"🔸 {product}: {price}")
                elif 'نبشی' in product:
                    categories['نبشی'].append(f"🔸 {product}: {price}")
                elif 'لوله' in product:
                    categories['لوله'].append(f"🔸 {product}: {price}")
            
            # ساخت پیام نهایی
            for category, items in categories.items():
                if items:
                    message += f"💰 {category}:\n"
                    message += "\n".join(items) + "\n\n"
            
            message += "📊 منبع: ahanonline.com"
            
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
    prices = get_all_prices()
    send_telegram_message(prices)
