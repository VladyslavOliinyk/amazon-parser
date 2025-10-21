import time
import random
import json
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

# Настройки
MAX_ITEMS = 5
DATA_FILE = "data.json"


def create_driver(headless: bool = False, proxy: Optional[str] = None):
    options = uc.ChromeOptions()
    ua = UserAgent(platforms='pc')
    user_agent = ua.random
    print(f"[INFO] Using User-Agent: {user_agent}")
    options.add_argument(f'--user-agent={user_agent}')

    if headless:
        # Для Docker/Render нам нужен headless
        options.add_argument('--headless=new')

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    driver = uc.Chrome(options=options)
    return driver


def human_wait(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))


# Эта функция нам больше не нужна, так как мы будем парсить ссылки иначе
# def extract_product_links_from_category(...)

def parse_product_page(driver, url: str, rank: int):
    print(f"  > Parsing product URL: {url}")
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#productTitle, #centerCol"))
    )
    human_wait(1.5, 3.5)

    driver.execute_script("window.scrollBy(0, 500);")
    human_wait(0.5, 1.5)

    soup = BeautifulSoup(driver.page_source, "lxml")

    # --- Извлечение данных с улучшенными селекторами ---

    title = soup.select_one("#productTitle")
    title_text = title.get_text(strip=True) if title else "N/A"

    asin = None
    asin_tag = soup.select_one('input#ASIN')
    if asin_tag and asin_tag.get('value'):
        asin = asin_tag['value']
    else:
        # Запасной метод извлечения ASIN из URL
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            asin = match.group(1)

    # Рейтинг и отзывы
    rating_text = "N/A"
    rating_tag = soup.select_one("#acrPopover")
    if rating_tag and rating_tag.get('title'):
        rating_text = rating_tag['title']

    reviews_text = "0"
    reviews_tag = soup.select_one("#acrCustomerReviewText")
    if reviews_tag:
        reviews_text = reviews_tag.get_text(strip=True)

    # Картинка
    image_url = None
    img_tag = soup.select_one("#landingImage")
    if img_tag and img_tag.get('src'):
        image_url = img_tag['src']

    # Буллеты
    bullets = [li.get_text(strip=True) for li in soup.select("#feature-bullets ul li")[:5]]

    # --- НОВАЯ УЛУЧШЕННАЯ ЛОГИКА ДЛЯ ЦЕНЫ, СКИДКИ И PRIME ---

    price, list_price, discount = "N/A", None, None
    is_prime = False

    price_block = soup.select_one("#corePrice_feature_div, #tmmSwatches")
    if price_block:
        # Текущая цена
        current_price_tag = price_block.select_one("span.a-offscreen")
        if current_price_tag:
            price = current_price_tag.get_text(strip=True)

        # Старая (зачеркнутая) цена
        list_price_tag = price_block.select_one("span[data-a-strike='true'] span.a-offscreen")
        if list_price_tag:
            list_price = list_price_tag.get_text(strip=True)

        # Просчет скидки, если есть обе цены
        if price != "N/A" and list_price:
            try:
                p_float = float(re.sub(r'[$,]', '', price))
                lp_float = float(re.sub(r'[$,]', '', list_price))
                if lp_float > p_float:
                    discount = f"{int(round((lp_float - p_float) / lp_float * 100))}%"
            except (ValueError, ZeroDivisionError):
                pass

    # Проверка на Prime (ищем иконку)
    if soup.select_one("i.a-icon-prime"):
        is_prime = True

    # BSR
    bsr = "N/A"
    detail = soup.select_one("#detailBullets_feature_div") or soup.select_one("#productDetails_detailBullets_sections1")
    if detail:
        for li in detail.select('li'):
            text = li.get_text()
            if "Best Sellers Rank" in text:
                bsr_text = ' '.join(li.get_text().split())
                bsr = bsr_text.replace("Best Sellers Rank: ", "").split(' (')[0]
                break

    return {
        "asin": asin, "rank": rank, "title": title_text, "price": price,
        "list_price": list_price, "discount_percent": discount, "rating": rating_text,
        "reviews_count": reviews_text, "is_prime": is_prime, "best_sellers_rank": bsr,
        "bullet_points": bullets, "main_image_url": image_url, "url": url
    }


def parse_category_selenium(category_url: str, max_items=MAX_ITEMS, headless=False, proxy: Optional[str] = None):
    driver = create_driver(headless=headless, proxy=proxy)

    # --- ИМИТАЦИЯ ЧЕЛОВЕКА ---
    driver.maximize_window()
    driver.set_window_size(1920, 1080)

    # "Прогрев": заходим на главную страницу, чтобы получить cookies
    print("[INFO] Warming up session by visiting main page...")
    driver.get("https://www.amazon.com/")
    human_wait(2, 4)
    # --------------------------

    try:
        print(f"[INFO] Parsing category: {category_url}")
        driver.get(category_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.p13n-desktop-grid")))

        soup = BeautifulSoup(driver.page_source, "lxml")

        # Находим ссылки на товары
        product_links = []
        product_grid = soup.select_one('div.p13n-desktop-grid')
        if product_grid:
            links = product_grid.select('a.a-link-normal', href=True)
            for link in links:
                href = link['href']
                if href.startswith('/'):
                    full_url = "https://www.amazon.com" + href
                    if full_url not in product_links:
                        product_links.append(full_url)
                if len(product_links) >= max_items:
                    break

        if not product_links:
            print("[ERROR] Could not find product links on the category page.")
            return []

        results = []
        for i, url in enumerate(product_links, start=1):
            try:
                item = parse_product_page(driver, url, rank=i)
                results.append(item)
            except Exception as e:
                print(f"[ERROR] Failed to parse product {url}: {e}")

        print(f"[INFO] Writing {len(results)} items to {DATA_FILE}")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return results
    finally:
        driver.quit()


if __name__ == "__main__":
    url = "https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden"
    res = parse_category_selenium(url, max_items=5, headless=False)
    print(f"Done. Parsed: {len(res)} items.")
