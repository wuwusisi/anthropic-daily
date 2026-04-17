import json
import os
from src.collectors.base import Article


class SeenStore:
    def __init__(self, path: str):
        self.path = path
        if os.path.exists(path):
            with open(path, "r") as f:
                self._seen: dict[str, bool] = json.load(f)
        else:
            self._seen = {}

    def filter_new(self, articles: list[Article]) -> list[Article]:
        return [a for a in articles if a.url not in self._seen]

    def mark_seen(self, articles: list[Article]) -> None:
        for a in articles:
            self._seen[a.url] = True

    def save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._seen, f, ensure_ascii=False, indent=2)
