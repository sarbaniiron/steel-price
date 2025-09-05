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
    
    # استفاده از Chrome پیش‌نصب شده در GitHub Actions
    options.binary_location = "/usr/bin/google-chrome"
    
    try:
        # استفاده از ChromeDriver پیش‌نصب شده
        driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
        return driver
    except WebDriverException:
        try:
            # راه‌حل جایگزین
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
        driver.get("https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/")

        wait = WebDriverWait(driver, 20)
        
        # منتظر بارگذاری صفحه بمانید
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # اسکرول به پایین برای بارگذاری کامل
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # منتظر المنت‌های قیمت بمانید
        try:
            products = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product, .price-item, [class*='price']"))
            )
        except TimeoutException:
            # اگر المنت‌های خاص پیدا نشدند، از کل صفحه استفاده کنید
            products = driver.find_elements(By.TAG_NAME, "body")

        prices_list = []
        for prod in products[:20]:  # محدود کردن برای جلوگیری از overload
            try:
                name = prod.text.strip()
                if name and ("میلگرد" in name or "قیمت" in name or "تومان" in name):
                    prices_list.append(name)
            except:
                continue

        if prices_list:
            today = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            message = f"📊 قیمت‌های میلگرد - {today}\n\n"
            for price in prices_list[:10]:  # فقط 10 آیتم اول
                message += f"• {price}\n"
        else:
            today = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            message = f"📊 قیمت‌های میلگرد - {today}\n\n⚠️ قیمتی یافت نشد\n\n"
            # نمایش HTML برای دیباگ
            message += "📋 محتوای صفحه:\n"
            message += driver.page_source[:500] + "..."  # فقط 500 کاراکتر اول

        message += "\n📎 منبع: آهن آنلاین"

        # ارسال به تلگرام
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
        bot.send_message(chat_id=chat_id, text=message)
        logger.info("پیام با موفقیت ارسال شد")
        
    except Exception as e:
        logger.error(f"خطا در ارسال پیام تلگرام: {e}")

if __name__ == "__main__":
    scrape_prices()
