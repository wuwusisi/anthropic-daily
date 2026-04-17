import json
import os
from src.dedup import SeenStore
from src.collectors.base import Article


def _article(url: str, title: str = "t") -> Article:
    return Article(
        title=title,
        url=url,
        source="test",
        content="content",
    )


def test_new_articles_detected(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text("{}")
    store = SeenStore(str(path))

    articles = [_article("https://a.com/1"), _article("https://a.com/2")]
    new = store.filter_new(articles)

    assert len(new) == 2


def test_seen_articles_filtered(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text(json.dumps({"https://a.com/1": True}))
    store = SeenStore(str(path))

    articles = [_article("https://a.com/1"), _article("https://a.com/2")]
    new = store.filter_new(articles)

    assert len(new) == 1
    assert new[0].url == "https://a.com/2"


def test_mark_seen_persists(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text("{}")
    store = SeenStore(str(path))

    store.mark_seen([_article("https://a.com/1")])
    store.save()

    data = json.loads(path.read_text())
    assert "https://a.com/1" in data


def test_empty_seen_file_created(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore(str(path))
    new = store.filter_new([_article("https://a.com/1")])

    assert len(new) == 1
