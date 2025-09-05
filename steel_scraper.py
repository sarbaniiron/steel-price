import requests
from bs4 import BeautifulSoup
import os
from telegram import Bot
from telegram.error import TelegramError
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_steel_prices():
    """
    دریافت قیمت‌های آهن آلات از سایت‌های مختلف
    """
    prices = {}
    
    try:
        # سایت اول: فولادینو (به عنوان مثال)
        url = "https://fooladino.ir/price-list"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # این بخش باید با سایت واقعی تطبیق داده شود
            # پیدا کردن قیمت میلگرد (مثال)
            rebar_elements = soup.find_all('div', class_='price')
            if rebar_elements and len(rebar_elements) > 0:
                prices['میلگرد'] = rebar_elements[0].text.strip() + ' تومان'
            
            # پیدا کردن قیمت قوطی (مثال)
            pipe_elements = soup.find_all('span', class_='amount')
            if pipe_elements and len(pipe_elements) > 1:
                prices['قوطی'] = pipe_elements[1].text.strip() + ' تومان'
                
        else:
            logger.error(f"خطا در دریافت داده از سایت. کد وضعیت: {response.status_code}")
            
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت‌ها: {str(e)}")
    
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
            message = "💰 قیمت‌های امروز آهن آلات:\n\n"
            for product, price in prices.items():
                message += f"🔸 {product}: {price}\n"
            
            message += "\n📊 منبع: فولادینو"
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
    prices = get_steel_prices()
    send_telegram_message(prices)
