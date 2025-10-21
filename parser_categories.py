import time
import json
import random
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def run_parser():
    """
    Основная функция парсера, которая собирает данные и сохраняет их в JSON.
    Возвращает True в случае успеха и False в случае ошибки.
    """
    scraped_data = {}

    options = uc.ChromeOptions()
    ua = UserAgent(platforms='pc')
    user_agent = ua.random
    print(f"Использую User-Agent: {user_agent}\n")
    options.add_argument(f'--user-agent={user_agent}')
    # Включаем headless режим для фоновой работы на сервере
    options.add_argument('--headless')

    driver = None  # Объявляем заранее, чтобы использовать в finally
    try:
        driver = uc.Chrome(options=options)
        driver.maximize_window()

        # --- ЭТАП 1: Динамический сбор категорий ---
        main_url = "https://www.amazon.com/gp/bestsellers"
        print(f"ЭТАП 1: Захожу на главную страницу для сбора ссылок: {main_url}")
        driver.get(main_url)
        time.sleep(random.uniform(5, 8))

        print("...Прокручиваю страницу для загрузки всех блоков...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        categories_to_parse = []
        category_headers = soup.select('div.a-carousel-header-row')

        print(f"...Найдено {len(category_headers)} блоков категорий. Собираю ссылки...")
        for header_block in category_headers:
            category_name_element = header_block.select_one('h2.a-carousel-heading')
            see_more_link_element = header_block.select_one('a[aria-label*="See More"]')

            if category_name_element and see_more_link_element:
                name = category_name_element.get_text(strip=True)
                url = "https://www.amazon.com" + see_more_link_element['href']
                categories_to_parse.append({'name': name, 'url': url})
                print(f"  ✅ Найдена категория: '{name}'")

        if not categories_to_parse:
            print("\nНе удалось собрать ни одной категории. Прекращаю работу.")
            return False

        # --- ЭТАП 2: Парсинг страниц категорий ---
        print("\nЭТАП 2: Начинаю обход страниц категорий...")
        for category in categories_to_parse:
            cat_name = category['name']
            cat_url = category['url']

            print(f"\n--- Обрабатываю категорию: '{cat_name}' ---")
            driver.get(cat_url)
            delay = random.uniform(8, 13)
            print(f"  ...делаю паузу на {delay:.2f} сек...")
            time.sleep(delay)

            page_soup = BeautifulSoup(driver.page_source, 'html.parser')

            product_list = page_soup.select_one('ol.a-ordered-list')
            if not product_list:
                print(f"  ❌ Не удалось найти общий список товаров для '{cat_name}'.")
                continue

            product_cards = product_list.select('li.zg-no-numbers')
            if not product_cards:
                print(f"  ❌ Не удалось найти карточки товаров для '{cat_name}'.")
                continue

            products_in_category = []
            print(f"  ✅ Найдено {len(product_cards)} карточек. Собираю данные о первых 5.")

            for card in product_cards[:5]:
                try:
                    link_tag = card.select_one('a.a-link-normal')
                    product_url = "https://www.amazon.com" + link_tag['href'] if link_tag else None
                    rank = card.select_one('span.zg-bdg-text').get_text(strip=True)
                    title = card.select_one('div[class*="_cDEzb_p13n-sc-css-line-clamp-"]').get_text(strip=True)
                    image_url = card.select_one('img')['src']
                    rating = card.select_one('span.a-icon-alt').get_text(strip=True)
                    reviews_count = card.select_one('span.a-size-small').get_text(strip=True)

                    price_element = card.select_one('span._cDEzb_p13n-sc-price_3mJ9Z')
                    if price_element:
                        price = price_element.get_text(strip=True)
                    else:
                        offer_price_element = card.select_one('span.p13n-sc-price')
                        price = offer_price_element.get_text(strip=True) if offer_price_element else 'N/A'

                    products_in_category.append({
                        "rank": rank, "title": title, "url": product_url,
                        "image_url": image_url, "rating": rating,
                        "reviews_count": reviews_count, "price": price
                    })
                except Exception:
                    continue

            if products_in_category:
                scraped_data[cat_name] = products_in_category
                print(f"  👍 Собрал информацию о {len(products_in_category)} товарах.")

        # Сохраняем данные только если что-то удалось собрать
        if scraped_data:
            with open('amazon_bestsellers_data.json', 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, ensure_ascii=False, indent=4)
            print(f"\n✅ Все данные успешно сохранены в файл.")
            return True
        else:
            print("\n❌ Не удалось собрать никаких данных. Файл не был создан.")
            return False

    except Exception as e:
        print(f"Критическая ошибка во время парсинга: {e}")
        return False
    finally:
        if driver:
            print("Закрываю браузер...")
            driver.quit()


# Этот блок позволит запускать парсер напрямую, как и раньше
if __name__ == "__main__":
    run_parser()
