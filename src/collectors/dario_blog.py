import requests
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector, Article


class DarioBlogCollector(BaseCollector):
    URL = "https://www.darioamodei.com"

    def collect(self) -> list[Article]:
        try:
            resp = requests.get(self.URL, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            self.error = str(e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for link in soup.select("a[href]"):
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or len(title) < 10:
                continue
            if href.startswith("/"):
                full_url = f"https://www.darioamodei.com{href}"
            elif href.startswith("http"):
                full_url = href
            else:
                continue

            if full_url == self.URL or full_url == self.URL + "/":
                continue

            articles.append(Article(
                title=title,
                url=full_url,
                source="dario-blog",
                tag="博客",
                content="",
            ))

        return articles
