import os
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import telegram
import logging

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    """تنظیمات Chrome WebDriver برای GitHub Actions"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        # در GitHub Actions از chrome-action استفاده می‌کنیم
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی درایور: {e}")
        return None

def scrape_prices():
    driver = setup_driver()
    if not driver:
        send_telegram_message("❌ خطا در راه‌اندازی مرورگر")
        return

    try:
        logger.info("در حال باز کردن صفحه آهن آنلاین...")
        driver.get("https://ahanonline.com/")
        
        # ابتدا به صفحه اصلی برویم سپس به صفحه قیمت‌ها
        wait = WebDriverWait(driver, 20)
        
        # پیدا کردن لینک قیمت میلگرد
        try:
            milgard_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'میلگرد') or contains(text(), 'قیمت')]"))
            )
            milgard_link.click()
            logger.info("رفتن به صفحه قیمت میلگرد...")
        except:
            # اگر لینک مستقیم پیدا نشد، مستقیماً به URL برویم
            driver.get("https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/")
        
        # منتظر بارگذاری صفحه
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)  # منتظر بمانید تا JavaScript اجرا شود
        
        # اسکرول به پایین
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # استخراج اطلاعات از صفحه
        page_content = driver.page_source
        
        # آنالیز ساده محتوا
        prices_list = []
        
        # جستجوی قیمت‌ها در متن صفحه
        import re
        price_matches = re.findall(r'(\d{1,3}(?:,\d{3})*\s*تومان)', page_content)
        product_matches = re.findall(r'(میلگرد|آجدار|A3|سایز\s*\d+)', page_content)
        
        if price_matches:
            for i, price in enumerate(price_matches[:10]):  # فقط 10 قیمت اول
                product_name = product_matches[i] if i < len(product_matches) else "میلگرد"
                prices_list.append(f"{product_name}: {price}")
        
        # آماده کردن پیام
        today = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        
        if prices_list:
            message = f"📊 قیمت‌های میلگرد - {today}\n\n"
            message += "\n".join(prices_list)
        else:
            message = f"📊 قیمت‌های میلگرد - {today}\n\n"
            message += "⚠️ قیمت مستقیم یافت نشد\n\n"
            message += "📋 محتوای شناسایی شده:\n"
            
            # نمایش برخی از متن‌های مرتبط
            content_samples = re.findall(r'.{0,100}(میلگرد|قیمت|تومان).{0,100}', page_content)
            for sample in content_samples[:5]:
                message += f"• {sample}\n"
        
        message += "\n📎 منبع: آهن آنلاین"
        
        # ارسال پیام
        send_telegram_message(message)

    except Exception as e:
        error_msg = f"❌ خطا در اسکراپ: {str(e)}"
        logger.error(error_msg)
        send_telegram_message(error_msg)
    finally:
        driver.quit()

def send_telegram_message(message):
    """ارسال پیام به تلگرام"""
    try:
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        
        if not bot_token or not chat_id:
            logger.error("توکن ربات یا چت آیدی تنظیم نشده است")
            return
            
        bot = telegram.Bot(token=bot_token)
        
        # تقسیم پیام طولانی به قسمت‌های کوچکتر
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                bot.send_message(chat_id=chat_id, text=part)
                time.sleep(1)
        else:
            bot.send_message(chat_id=chat_id, text=message)
            
        logger.info("پیام با موفقیت ارسال شد")
        
    except Exception as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {e}")

if __name__ == "__main__":
    import time
    scrape_prices()
