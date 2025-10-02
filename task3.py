import requests
from bs4 import BeautifulSoup
from fake_headers import Headers
import json
import re
import time
import random
import logging
from task2 import logger

URL = "https://habr.com/ru/articles/"
KEYWORDS = ['ИИ', 'Python', 'Хабр', 'AI', 'IT']

articles = []
seen_links = set()

# Логирование ошибок
logging.basicConfig(
    filename="parse_errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

# Декораторы для логов из ДЗ
@logger('web-scrapping.log')
def generate_headers():
    """Генерируем случайные headers для каждого запроса"""
    return Headers(browser="chrome", os="win").generate()

@logger('web-scrapping.log')
def matches_keywords(text, keywords):
    """Проверяем, есть ли ключевые слова как отдельные слова"""
    text_lower = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw.lower())}\b", text_lower):
            return True
    return False


# Загружаем главную страницу
resp = requests.get(URL, headers=generate_headers())
soup = BeautifulSoup(resp.text, "lxml")
article_tags = soup.find_all("article")

for tag in article_tags:
    try:
        time_tag = tag.find("time")
        h2_tag = tag.find("h2")
        a_tag = h2_tag.find("a")
        span_tag = a_tag.find("span")

        publication_time = time_tag["datetime"]
        absolute_article_link = a_tag["href"]
        if absolute_article_link.startswith("/"):
            absolute_article_link = "https://habr.com" + absolute_article_link

        # Защита от дублей
        if absolute_article_link in seen_links:
            continue
        seen_links.add(absolute_article_link)

        article_title = span_tag.text.strip()

        # Загружаем саму статью с новыми headers
        article_resp = requests.get(absolute_article_link, headers=generate_headers())
        article_soup = BeautifulSoup(article_resp.text, "lxml")

        # Поиск контента
        content_tag = (
            article_soup.find("div", class_="tm-article-presenter__body")
            or article_soup.select_one("div.article-formatted-body")
        )

        if not content_tag:
            continue

        full_text = content_tag.get_text(" ", strip=True)

        combined_text = (article_title + " " + full_text).strip()
        if not matches_keywords(combined_text, KEYWORDS):
            continue

        article_dict = {
            "publication_time": publication_time,
            "absolute_article_link": absolute_article_link,
            "article_title": article_title,
            "article_text": full_text
        }
        articles.append(article_dict)

        # Задержка между запросами
        time.sleep(random.uniform(1, 2))

    except Exception as e:
        logging.exception(f"Ошибка при парсинге статьи {absolute_article_link if 'absolute_article_link' in locals() else ''}")

# Сохраняем с датой, чтобы не перетирать предыдущие
filename = f"articles.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"Сохранено {len(articles)} статей в {filename}")
