import time
import json
import random
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import sys

def create_driver():
    """Создает и настраивает новый экземпляр драйвера для облачного окружения."""
    options = uc.ChromeOptions()
    ua = UserAgent(platforms='pc')
    user_agent = ua.random
    
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    return uc.Chrome(options=options)

def parse_single_category(category_name, category_url):
    """
    Запускает отдельный браузер для парсинга ОДНОЙ категории.
    Это самый надежный метод для сред с малым количеством памяти.
    """
    print(f"\n--- Обрабатываю категорию: '{category_name}' ---")
    driver = None
    try:
        driver = create_driver()
        driver.get(category_url)
        
        delay = random.uniform(9, 14) # Немного увеличим паузу для надежности
        print(f"  ...делаю паузу на {delay:.2f} сек...")
        time.sleep(delay)
        
        page_soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        product_list = page_soup.select_one('ol.a-ordered-list')
        if not product_list:
            print(f"  ❌ Не удалось найти общий список товаров (ol.a-ordered-list) для '{category_name}'.")
            return []

        product_cards = product_list.select('li.zg-no-numbers')
        if not product_cards:
            print(f"  ❌ Не удалось найти карточки товаров (li.zg-no-numbers) для '{category_name}'.")
            return []

        products_in_category = []
        print(f"  ✅ Найдено {len(product_cards)} карточек. Собираю данные о первых 5.")
        
        for card in product_cards[:5]:
            try:
                rank = card.select_one('span.zg-bdg-text').get_text(strip=True)
                title = card.select_one('div[class*="_cDEzb_p13n-sc-css-line-clamp-"]').get_text(strip=True)
                image_url = card.select_one('img')['src']
                rating = card.select_one('span.a-icon-alt').get_text(strip=True)
                reviews_count = card.select_one('span.a-size-small').get_text(strip=True)
                link_tag = card.select_one('a.a-link-normal')
                product_url = "https://www.amazon.com" + link_tag['href'] if link_tag and link_tag.get('href') else None
                
                price_element = card.select_one('span._cDEzb_p13n-sc-price_3mJ9Z, span.p13n-sc-price')
                price = price_element.get_text(strip=True) if price_element else 'N/A'
                
                products_in_category.append({
                    "rank": rank, "title": title, "url": product_url, "image_url": image_url,
                    "rating": rating, "reviews_count": reviews_count, "price": price
                })
            except Exception:
                continue
        
        print(f"  👍 Собрал информацию о {len(products_in_category)} товарах.")
        return products_in_category

    finally:
        if driver:
            driver.quit()
            print("  ...драйвер для категории закрыт, память освобождена.")

def run_parser():
    """
    Главная функция-оркестратор. Использует жестко заданный список категорий
    для максимальной надежности и экономии памяти.
    """
    # Жестко заданный список категорий - это убирает необходимость в первом парсинге
    categories_to_parse = [
        {'name': 'Best Sellers in Automotive', 'url': 'https://www.amazon.com/gp/bestsellers/automotive/'},
        {'name': 'Best Sellers in Electronics', 'url': 'https://www.amazon.com/gp/bestsellers/electronics/'},
        {'name': 'Best Sellers in Clothing, Shoes & Jewelry', 'url': 'https://www.amazon.com/gp/bestsellers/fashion/'},
        {'name': 'Best Sellers in Kitchen & Dining', 'url': 'https://www.amazon.com/gp/bestsellers/kitchen/'},
        {'name': 'Best Sellers in Beauty & Personal Care', 'url': 'https://www.amazon.com/gp/bestsellers/beauty/'},
        {'name': 'Best Sellers in Tools & Home Improvement', 'url': 'https://www.amazon.com/gp/bestsellers/hi/'},
    ]
    print(f"Начинаю парсинг {len(categories_to_parse)} предопределенных категорий...")
    
    final_data = {}
    for category in categories_to_parse:
        products = parse_single_category(category['name'], category['url'])
        if products:
            final_data[category['name']] = products
    
    if not final_data:
        print("Критическая ошибка: не удалось собрать данные ни по одной категории.", file=sys.stderr)
        return False

    with open('amazon_bestsellers_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    
    print("\nПарсинг полностью завершен. Файл успешно сохранен.")
    return True

if __name__ == '__main__':
    run_parser()

