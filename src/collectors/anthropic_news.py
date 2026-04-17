import requests
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector, Article


class AnthropicNewsCollector(BaseCollector):
    URL = "https://www.anthropic.com/news"

    def collect(self) -> list[Article]:
        try:
            resp = requests.get(self.URL, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            self.error = str(e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for card in soup.select("a[class*='PostCard_post']"):
            title_el = card.select_one("h3")
            date_el = card.select_one("div[class*='PostCard_date']")
            desc_el = card.select_one("p")
            href = card.get("href", "")

            if not title_el or not href:
                continue

            articles.append(Article(
                title=title_el.get_text(strip=True),
                url=f"https://www.anthropic.com{href}" if href.startswith("/") else href,
                source="anthropic-news",
                tag="新闻",
                date=date_el.get_text(strip=True) if date_el else "",
                content=desc_el.get_text(strip=True) if desc_el else "",
            ))

        return articles
