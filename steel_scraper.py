import os
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import telegram
import logging
import re
import time

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    """تنظیمات Chrome WebDriver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی درایور: {e}")
        return None

def extract_detailed_prices(driver):
    """استخراج دقیق قیمت‌های میلگرد A3 به تفکیک شرکت و سایز"""
    try:
        # رفتن مستقیم به صفحه قیمت میلگرد
        logger.info("در حال بارگذاری صفحه آهن آنلاین...")
        driver.get("https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/")
        
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # منتظر ماندن برای بارگذاری کامل
        time.sleep(5)
        
        # اسکرول برای بارگذاری محتوا
        driver.execute_script("window.scrollTo(0, 800)")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 1600)")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        
        # گرفتن محتوای کامل صفحه
        page_content = driver.page_source
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        logger.info(f"محتویات صفحه: {len(page_text)} کاراکتر")
        
        # استخراج قیمت‌ها با روش‌های مختلف
        price_data = {}
        
        # روش 1: جستجو در tables
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"تعداد جداول یافت شده: {len(tables)}")
            
            for i, table in enumerate(tables):
                try:
                    table_text = table.text
                    if "میلگرد" in table_text and ("A3" in table_text.upper() or "آجدار" in table_text):
                        logger.info(f"جدول میلگرد پیدا شد: {table_text[:100]}...")
                        
                        company = extract_company_from_table(table_text)
                        if company:
                            if company not in price_data:
                                price_data[company] = {}
                            
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            for row in rows:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 2:
                                    size_text = cells[0].text.strip()
                                    price_text = cells[1].text.strip()
                                    
                                    size = extract_size(size_text)
                                    if size and price_text and "تومان" in price_text:
                                        price_data[company][f"سایز {size}"] = price_text
                except Exception as e:
                    logger.error(f"خطا در پردازش جدول {i}: {e}")
                    continue
        except Exception as e:
            logger.error(f"خطا در یافتن جداول: {e}")
        
        # روش 2: جستجو در المنت‌های محصول
        try:
            product_elements = driver.find_elements(By.CSS_SELECTOR, ".product, .product-item, .price-item, .item")
            logger.info(f"تعداد المنت‌های محصول: {len(product_elements)}")
            
            for element in product_elements:
                try:
                    text = element.text.strip()
                    if text and "میلگرد" in text and ("A3" in text.upper() or "آجدار" in text):
                        company = extract_company(text)
                        size = extract_size(text)
                        price = extract_price(text)
                        
                        if company and size and price:
                            if company not in price_data:
                                price_data[company] = {}
                            price_data[company][f"سایز {size}"] = price
                except Exception as e:
                    continue
        except Exception as e:
            logger.error(f"خطا در یافتن المنت‌های محصول: {e}")
        
        # روش 3: جستجو در کل صفحه با regex
        if not price_data:
            logger.info("جستجو در کل صفحه با regex...")
            lines = page_text.split('\n')
            for line in lines:
                if "میلگرد" in line and ("A3" in line.upper() or "آجدار" in line) and "تومان" in line:
                    company = extract_company(line)
                    size = extract_size(line)
                    price = extract_price(line)
                    
                    if company and size and price:
                        if company not in price_data:
                            price_data[company] = {}
                        price_data[company][f"سایز {size}"] = price
        
        return price_data if price_data else None
        
    except Exception as e:
        logger.error(f"خطا در استخراج دقیق قیمت‌ها: {e}")
        return None

def extract_company_from_table(table_text):
    """استخراج نام شرکت از متن جدول"""
    companies = [
        "ذوب آهن", "فولاد مبارکه", "کاویان", "ظفر بناب", "نیشابور",
        "خوزستان", "اهواز", "اصفهان", "مبارکه", "کاویان", "ظفر", "نیشابور"
    ]
    
    for company in companies:
        if company in table_text:
            return company
    return None

def extract_company(text):
    """استخراج نام شرکت از متن"""
    companies = [
        "ذوب آهن", "فولاد مبارکه", "کاویان", "ظفر بناب", "نیشابور",
        "خوزستان", "اهواز", "اصفهان", "مبارکه", "کاویان", "ظفر", "نیشابور"
    ]
    
    for company in companies:
        if company in text:
            return company
    return "نامشخص"

def extract_size(text):
    """استخراج سایز از متن"""
    size_patterns = [
        r'سایز\s*(\d+)',
        r'size\s*(\d+)',
        r'(\d+)\s*مم',
        r'(\d+)\s*mm',
        r'\b(\d{1,2})\b'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            size = match.group(1)
            if size.isdigit() and 8 <= int(size) <= 32:
                return size
    return None

def extract_price(text):
    """استخراج قیمت از متن"""
    price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*تومان', text)
    if price_match:
        return price_match.group(0)
    return None

def format_prices_message(price_data, date_str):
    """قالب‌بندی پیام قیمت‌ها"""
    message = f"📊 قیمت‌های میلگرد A3 - {date_str}\n\n"
    
    for company, sizes in price_data.items():
        message += f"🏭 {company}:\n"
        
        # مرتب کردن سایزها از کوچک به بزرگ
        sorted_sizes = sorted(
            sizes.items(),
            key=lambda x: int(x[0].replace("سایز ", ""))
        )
        
        for size, price in sorted_sizes:
            message += f"   🔸 {size} = {price}\n"
        
        message += "\n"
    
    message += "📎 منبع: آهن آنلاین\n"
    message += "⚡ استخراج آنلاین"
    
    return message

def scrape_prices():
    driver = setup_driver()
    if not driver:
        send_telegram_message("❌ خطا در راه‌اندازی مرورگر")
        return

    try:
        logger.info("در حال استخراج قیمت‌های دقیق از آهن آنلاین...")
        
        # استخراج قیمت‌های دقیق
        price_data = extract_detailed_prices(driver)
        
        if not price_data:
            error_msg = "❌ نتونستم قیمت‌های میلگرد A3 رو از سایت آهن آنلاین استخراج کنم. ممکنه ساختار سایت تغییر کرده باشه یا اطلاعات در دسترس نباشه."
            logger.error(error_msg)
            send_telegram_message(error_msg)
            return
        
        # فرمت‌بندی پیام
        date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        message = format_prices_message(price_data, date_str)
        
        # ارسال پیام
        send_telegram_message(message)
        logger.info("پیام با موفقیت ارسال شد")

    except Exception as e:
        error_msg = f"❌ خطای سیستمی در اسکراپ: {str(e)}"
        logger.error(error_msg)
        send_telegram_message(error_msg)
    finally:
        if driver:
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
        
        # تقسیم پیام طولانی
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                bot.send_message(chat_id=chat_id, text=part)
                time.sleep(1)
        else:
            bot.send_message(chat_id=chat_id, text=message)
            
    except Exception as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {e}")

if __name__ == "__main__":
    scrape_prices()
