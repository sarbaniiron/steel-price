import os
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import telegram

def scrape_prices():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://ahanonline.com/product-category/%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/%D9%82%DB%8C%D9%85%D8%AA-%D9%85%DB%8C%D9%84%DA%AF%D8%B1%D8%AF/")

        wait = WebDriverWait(driver, 15)
        products = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul#megaMenu li a.menu-item"))
        )

        prices_list = []
        for prod in products:
            try:
                name = prod.text.strip()
                # اگر قیمت داخل متن نیست، اینجا میتونیم یک selector دیگه بزنیم
                price = "⚠️ نیاز به بررسی دقیق صفحه برای قیمت"
                prices_list.append(f"{name}: {price}")
            except:
                continue

        if prices_list:
            today = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            message = f"📊 قیمت‌های میلگرد - {today}\n\n" + "\n".join(prices_list)
        else:
            message = f"📊 قیمت‌های میلگرد - {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}\n\n⚠️ قیمتی یافت نشد"

        message += "\n\n📎 منبع: آهن آنلاین"

        # ارسال به تلگرام
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("CHAT_ID")
        bot = telegram.Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message)

    except TimeoutException:
        print("❌ المنت‌ها لود نشدند")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_prices()
