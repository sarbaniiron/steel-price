import requests
from bs4 import BeautifulSoup
import logging
from fp.fp import FreeProxy
import random

logger = logging.getLogger(__name__)

def get_fresh_proxy():
    """دریافت پروکسی جدید و فعال"""
    try:
        proxy_list = FreeProxy(country_id=['US', 'CA', 'DE', 'FR'], https=True).get_proxy_list()
        if proxy_list:
            proxy = random.choice(proxy_list)
            logger.info(f"پروکسی جدید انتخاب شد: {proxy}")
            return {
                'http': proxy,
                'https': proxy
            }
    except Exception as e:
        logger.error(f"خطا در دریافت پروکسی: {str(e)}")
    
    return None

def scrape_milgard_ahanonline():
    """اسکراپ قیمت میلگرد A3 از آهن آنلاین"""
    milgard_prices = {}
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # دریافت پروکسی تازه
            proxies = get_fresh_proxy()
            
            url = "https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://ahanonline.com/'
            }
            
            logger.info(f"تلاش {attempt + 1} با پروکسی: {proxies}")
            
            response = requests.get(url, headers=headers, timeout=30, proxies=proxies)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # استخراج قیمت‌های ذوب آهن اصفهان
                zob_ahan_prices = extract_zob_ahan_prices(soup)
                milgard_prices.update(zob_ahan_prices)
                
                # استخراج قیمت‌های کاویان
                kavian_prices = extract_kavian_prices(soup)
                milgard_prices.update(kavian_prices)
                
                # استخراج قیمت‌های فولاد مبارکه
                mobarake_prices = extract_mobarake_prices(soup)
                milgard_prices.update(mobarake_prices)
                
                logger.info("استخراج قیمت‌ها با موفقیت انجام شد")
                break
                
            else:
                logger.warning(f"خطای HTTP: {response.status_code}")
                
        except requests.exceptions.ProxyError:
            logger.warning("پروکسی نامعتبر، تلاش با پروکسی جدید...")
            continue
        except requests.exceptions.Timeout:
            logger.warning("اتصال timeout شد، تلاش مجدد...")
            continue
        except Exception as e:
            logger.error(f"خطا در اسکراپ: {str(e)}")
            continue
    
    return milgard_prices

def extract_zob_ahan_prices(soup):
    """استخراج قیمت‌های ذوب آهن اصفهان"""
    prices = {}
    try:
        # سلکتورهای ذوب آهن - باید با سایت تطبیق داده شود
        sizes = {
            '8': '.zob-ahan-8',
            '10': '.zob-ahan-10',
            '12': '.zob-ahan-12',
            '14': '.zob-ahan-14',
            '16': '.zob-ahan-16',
            '18': '.zob-ahan-18',
            '20': '.zob-ahan-20',
            '22': '.zob-ahan-22',
            '25': '.zob-ahan-25',
            '28': '.zob-ahan-28',
            '32': '.zob-ahan-32'
        }
        
        for size, selector in sizes.items():
            element = soup.select_one(selector)
            if element:
                price = element.text.strip().replace(',', '')
                prices[f'ذوب آهن اصفهان {size}'] = f"{int(price):,} تومان"
                
    except Exception as e:
        logger.error(f"خطا در استخراج ذوب آهن: {str(e)}")
    
    return prices

def extract_kavian_prices(soup):
    """استخراج قیمت‌های کاویان"""
    prices = {}
    try:
        # سلکتورهای کاویان
        sizes = {
            '8': '.kavian-8',
            '10': '.kavian-10',
            '12': '.kavian-12',
            '14': '.kavian-14',
            '16': '.kavian-16',
            '18': '.kavian-18',
            '20': '.kavian-20',
            '22': '.kavian-22',
            '25': '.kavian-25',
            '28': '.kavian-28',
            '32': '.kavian-32'
        }
        
        for size, selector in sizes.items():
            element = soup.select_one(selector)
            if element:
                price = element.text.strip().replace(',', '')
                prices[f'کاویان {size}'] = f"{int(price):,} تومان"
                
    except Exception as e:
        logger.error(f"خطا در استخراج کاویان: {str(e)}")
    
    return prices

def extract_mobarake_prices(soup):
    """استخراج قیمت‌های فولاد مبارکه"""
    prices = {}
    try:
        # سلکتورهای فولاد مبارکه
        sizes = {
            '8': '.mobarake-8',
            '10': '.mobarake-10',
            '12': '.mobarake-12',
            '14': '.mobarake-14',
            '16': '.mobarake-16',
            '18': '.mobarake-18',
            '20': '.mobarake-20',
            '22': '.mobarake-22',
            '25': '.mobarake-25',
            '28': '.mobarake-28',
            '32': '.mobarake-32'
        }
        
        for size, selector in sizes.items():
            element = soup.select_one(selector)
            if element:
                price = element.text.strip().replace(',', '')
                prices[f'فولاد مبارکه {size}'] = f"{int(price):,} تومان"
                
    except Exception as e:
        logger.error(f"خطا در استخراج فولاد مبارکه: {str(e)}")
    
    return prices
