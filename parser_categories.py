import requests
import json
from bs4 import BeautifulSoup
import sys

# !!! ВАЖНО: Вставьте сюда ваш API ключ от ScrapingBee !!!
SCRAPINGBEE_API_KEY = "M00NT9JIDD7YT6OAYXX3MLX7WW878MN8UO1NF92SLLJ26SITDMMR76U2D8Z4ANX8XIX6QRES6TH22DGL"

def get_html(url):
    """Отправляет запрос через ScrapingBee и возвращает HTML."""
    print(f"  ...отправляю запрос на URL: {url}")
    response = requests.get(
        url='https://app.scrapingbee.com/api/v1/',
        params={
            'api_key': SCRAPINGBEE_API_KEY,
            'url': url,
            'render_js': 'true', # Говорим ScrapingBee выполнить JavaScript на странице
            'wait_for': '#gridItemRoot, ol.a-ordered-list', # Ждать загрузки этих элементов
        },
        timeout=120 # Ждем ответа до 2 минут
    )
    if response.status_code == 200:
        return response.text
    else:
        print(f"  ❌ Ошибка от ScrapingBee: {response.status_code} {response.text}")
        return None

def parse_single_category(category_name, category_url):
    """Парсит ОДНУ категорию, используя легкие запросы."""
    print(f"\n--- Обрабатываю категорию: '{category_name}' ---")
    html = get_html(category_url)
    if not html:
        return []

    page_soup = BeautifulSoup(html, 'html.parser')
    
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

def run_parser():
    """Главная функция-оркестратор."""
    categories_to_parse = [
        {'name': 'Best Sellers in Automotive', 'url': 'https://www.amazon.com/gp/bestsellers/automotive/'},
        {'name': 'Best Sellers in Electronics', 'url': 'https://www.amazon.com/gp/bestsellers/electronics/'},
        {'name': 'Best Sellers in Clothing, Shoes & Jewelry', 'url': 'https://www.amazon.com/gp/bestsellers/fashion/'},
        {'name': 'Best Sellers in Kitchen & Dining', 'url': 'https://www.amazon.com/gp/bestsellers/kitchen/'},
        {'name': 'Best Sellers in Beauty & Personal Care', 'url': 'https://www.amazon.com/gp/bestsellers/beauty/'},
        {'name': 'Best Sellers in Tools & Home Improvement', 'url': 'https://www.amazon.com/gp/bestsellers/hi/'},
    ]
    print(f"Начинаю парсинг {len(categories_to_parse)} предопределенных категорий через ScrapingBee...")
    
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

