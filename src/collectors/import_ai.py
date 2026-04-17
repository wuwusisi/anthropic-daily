import feedparser
from src.collectors.base import BaseCollector, Article


class ImportAICollector(BaseCollector):
    FEED_URL = "https://importai.substack.com/feed"

    def collect(self) -> list[Article]:
        try:
            feed = feedparser.parse(self.FEED_URL)
        except Exception as e:
            self.error = str(e)
            return []

        articles = []
        for entry in feed.entries:
            articles.append(Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source="import-ai",
                tag="Newsletter",
                date=entry.get("published", ""),
                content=entry.get("summary", "")[:2000],
            ))

        return articles
