import requests
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector, Article


class ReleaseNotesCollector(BaseCollector):
    URL = "https://docs.anthropic.com/en/release-notes/overview"

    def collect(self) -> list[Article]:
        try:
            resp = requests.get(self.URL, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            self.error = str(e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for section in soup.select("section, article, div.release-note, div[class*='release']"):
            title_el = section.select_one("h2, h3")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            body = section.get_text(strip=True)[:2000]
            anchor = title_el.get("id", "")
            url = f"{self.URL}#{anchor}" if anchor else self.URL

            articles.append(Article(
                title=title,
                url=url,
                source="release-notes",
                tag="API",
                content=body,
            ))

        return articles
