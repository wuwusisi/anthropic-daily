# Anthropic Daily Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated daily digest system that collects Anthropic-related news from 8 sources, generates AI summaries, publishes a static website, and sends a Feishu notification.

**Architecture:** Python scripts run daily via GitHub Actions. Collectors fetch from 8 sources, diff against `seen.json` for new items, call MiniMax 2.7 for summaries, render static HTML with Jinja2, deploy to GitHub Pages, and notify via Feishu bot API.

**Tech Stack:** Python 3.12, requests, BeautifulSoup4, feedparser, Jinja2, GitHub Actions, GitHub Pages

---

## File Structure

```
anthropic-daily/
├── .github/
│   └── workflows/
│       └── daily.yml                  # GitHub Actions cron + workflow_dispatch
├── src/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py                # export all collector classes
│   │   ├── base.py                    # BaseCollector ABC + Article dataclass
│   │   ├── anthropic_news.py          # anthropic.com/news
│   │   ├── anthropic_research.py      # anthropic.com/research
│   │   ├── release_notes.py           # docs.anthropic.com release notes
│   │   ├── system_prompts.py          # docs.anthropic.com system prompts
│   │   ├── github_org.py              # GitHub anthropics org API
│   │   ├── dario_blog.py              # darioamodei.com
│   │   ├── transformer_circuits.py    # transformer-circuits.pub
│   │   └── import_ai.py              # importai.substack.com RSS
│   ├── dedup.py                       # seen.json read/write/diff
│   ├── summarizer.py                  # MiniMax 2.7 API caller
│   ├── renderer.py                    # Jinja2 HTML generation
│   ├── notifier.py                    # Feishu bot API push
│   └── main.py                        # orchestrator entry point
├── templates/
│   ├── daily.html                     # single day report template
│   └── index.html                     # archive index template
├── static/
│   └── style.css                      # shared stylesheet
├── tests/
│   ├── __init__.py
│   ├── test_dedup.py
│   ├── test_collectors.py
│   ├── test_summarizer.py
│   ├── test_renderer.py
│   └── test_notifier.py
├── data/
│   └── seen.json                      # persistent dedup state
├── requirements.txt
└── requirements-dev.txt
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `src/__init__.py`
- Create: `src/collectors/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/seen.json`

- [ ] **Step 1: Create requirements.txt**

```
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.0
jinja2>=3.1.0
```

- [ ] **Step 2: Create requirements-dev.txt**

```
-r requirements.txt
pytest>=8.0.0
```

- [ ] **Step 3: Create package init files and empty seen.json**

`src/__init__.py` — empty file

`src/collectors/__init__.py` — empty file (will be populated in Task 3)

`tests/__init__.py` — empty file

`data/seen.json`:
```json
{}
```

- [ ] **Step 4: Install dependencies and verify**

Run:
```bash
cd /Users/cbs/Documents/my_projects/anthropic-daily
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt requirements-dev.txt src/__init__.py src/collectors/__init__.py tests/__init__.py data/seen.json
git commit -m "chore: project scaffolding with dependencies"
```

---

## Task 2: Article Dataclass + Dedup Module

**Files:**
- Create: `src/collectors/base.py`
- Create: `src/dedup.py`
- Create: `tests/test_dedup.py`

- [ ] **Step 1: Write the failing test for dedup**

`tests/test_dedup.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_dedup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.dedup'`

- [ ] **Step 3: Implement Article dataclass**

`src/collectors/base.py`:
```python
from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    url: str
    source: str
    content: str
    tag: str = ""
    date: str = ""
    brief: str = ""
    detail: str = ""
```

- [ ] **Step 4: Implement SeenStore**

`src/dedup.py`:
```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_dedup.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/collectors/base.py src/dedup.py tests/test_dedup.py
git commit -m "feat: add Article dataclass and SeenStore dedup module"
```

---

## Task 3: BaseCollector + Anthropic News Collector

**Files:**
- Modify: `src/collectors/base.py`
- Create: `src/collectors/anthropic_news.py`
- Create: `tests/test_collectors.py`

- [ ] **Step 1: Write the failing test**

`tests/test_collectors.py`:
```python
from unittest.mock import patch, Mock
from src.collectors.anthropic_news import AnthropicNewsCollector


SAMPLE_HTML = """
<html><body>
<a href="/news/article-1" class="PostCard_post__">
  <div class="PostCard_date__">Apr 15, 2026</div>
  <h3>Claude Gets New Feature</h3>
  <p>Claude can now do amazing things with the new update.</p>
</a>
<a href="/news/article-2" class="PostCard_post__">
  <div class="PostCard_date__">Apr 14, 2026</div>
  <h3>Anthropic Raises Funding</h3>
  <p>Anthropic announces new funding round.</p>
</a>
</body></html>
"""


@patch("src.collectors.anthropic_news.requests.get")
def test_anthropic_news_collects_articles(mock_get):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    mock_get.return_value = mock_resp

    collector = AnthropicNewsCollector()
    articles = collector.collect()

    assert len(articles) == 2
    assert articles[0].title == "Claude Gets New Feature"
    assert articles[0].url == "https://www.anthropic.com/news/article-1"
    assert articles[0].source == "anthropic-news"
    assert articles[0].tag == "新闻"


@patch("src.collectors.anthropic_news.requests.get")
def test_anthropic_news_handles_failure(mock_get):
    mock_get.side_effect = Exception("Connection error")

    collector = AnthropicNewsCollector()
    articles = collector.collect()

    assert articles == []
    assert collector.error is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_collectors.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Add BaseCollector ABC to base.py**

Append to `src/collectors/base.py`:
```python
from abc import ABC, abstractmethod


class BaseCollector(ABC):
    def __init__(self):
        self.error: str | None = None

    @abstractmethod
    def collect(self) -> list[Article]:
        pass
```

- [ ] **Step 4: Implement AnthropicNewsCollector**

`src/collectors/anthropic_news.py`:
```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_collectors.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/collectors/base.py src/collectors/anthropic_news.py tests/test_collectors.py
git commit -m "feat: add BaseCollector and AnthropicNewsCollector"
```

---

## Task 4: Remaining HTTP Collectors

**Files:**
- Create: `src/collectors/anthropic_research.py`
- Create: `src/collectors/release_notes.py`
- Create: `src/collectors/system_prompts.py`
- Create: `src/collectors/dario_blog.py`
- Create: `src/collectors/transformer_circuits.py`

These all follow the same pattern as AnthropicNewsCollector — subclass BaseCollector, fetch HTML, parse with BeautifulSoup. The key difference per collector is the URL, CSS selectors, and tag name.

**Important:** The exact CSS selectors below are based on current page structures and may need adjustment at implementation time. Each collector must be tested against the live site during development. If a page uses JS rendering that `requests` cannot handle, fall back to extracting from any static HTML or JSON embedded in the page source.

- [ ] **Step 1: Implement AnthropicResearchCollector**

`src/collectors/anthropic_research.py`:
```python
import requests
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector, Article


class AnthropicResearchCollector(BaseCollector):
    URL = "https://www.anthropic.com/research"

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
                source="anthropic-research",
                tag="研究",
                date=date_el.get_text(strip=True) if date_el else "",
                content=desc_el.get_text(strip=True) if desc_el else "",
            ))

        return articles
```

- [ ] **Step 2: Implement ReleaseNotesCollector**

`src/collectors/release_notes.py`:
```python
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
```

- [ ] **Step 3: Implement SystemPromptsCollector**

`src/collectors/system_prompts.py`:
```python
import hashlib
import requests
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector, Article


class SystemPromptsCollector(BaseCollector):
    URL = "https://docs.anthropic.com/en/release-notes/system-prompts"

    def collect(self) -> list[Article]:
        try:
            resp = requests.get(self.URL, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            self.error = str(e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        for section in soup.select("section, article, div[class*='prompt'], h2"):
            if section.name == "h2":
                title = section.get_text(strip=True)
                sibling_text = ""
                for sib in section.find_next_siblings():
                    if sib.name == "h2":
                        break
                    sibling_text += sib.get_text(strip=True) + "\n"
                body = sibling_text[:2000]
            else:
                title_el = section.select_one("h2, h3")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                body = section.get_text(strip=True)[:2000]

            content_hash = hashlib.md5(body.encode()).hexdigest()[:8]
            url = f"{self.URL}#sp-{content_hash}"

            articles.append(Article(
                title=f"System Prompt: {title}",
                url=url,
                source="system-prompts",
                tag="System Prompt",
                content=body,
            ))

        return articles
```

- [ ] **Step 4: Implement DarioBlogCollector**

`src/collectors/dario_blog.py`:
```python
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
```

- [ ] **Step 5: Implement TransformerCircuitsCollector**

`src/collectors/transformer_circuits.py`:
```python
import requests
from bs4 import BeautifulSoup
from src.collectors.base import BaseCollector, Article


class TransformerCircuitsCollector(BaseCollector):
    URL = "https://transformer-circuits.pub"

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
                full_url = f"https://transformer-circuits.pub{href}"
            elif href.startswith("http"):
                full_url = href
            else:
                continue

            if full_url.rstrip("/") == self.URL:
                continue

            articles.append(Article(
                title=title,
                url=full_url,
                source="transformer-circuits",
                tag="研究",
                content="",
            ))

        return articles
```

- [ ] **Step 6: Test each collector against live site**

Run each collector manually to verify selectors work:
```bash
python3 -c "
from src.collectors.anthropic_research import AnthropicResearchCollector
c = AnthropicResearchCollector()
articles = c.collect()
print(f'Got {len(articles)} articles')
for a in articles[:3]:
    print(f'  - {a.title}: {a.url}')
if c.error:
    print(f'Error: {c.error}')
"
```

Repeat for each collector. If a collector returns 0 articles, inspect the page HTML and adjust selectors.

- [ ] **Step 7: Commit**

```bash
git add src/collectors/anthropic_research.py src/collectors/release_notes.py src/collectors/system_prompts.py src/collectors/dario_blog.py src/collectors/transformer_circuits.py
git commit -m "feat: add HTTP collectors for research, release notes, system prompts, dario blog, transformer circuits"
```

---

## Task 5: GitHub Org Collector

**Files:**
- Create: `src/collectors/github_org.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_collectors.py`:
```python
from unittest.mock import patch, Mock
from src.collectors.github_org import GitHubOrgCollector

SAMPLE_RELEASES = [
    {
        "tag_name": "v1.0.0",
        "name": "Claude Code v1.0.0",
        "html_url": "https://github.com/anthropics/claude-code/releases/tag/v1.0.0",
        "body": "New release with features",
        "published_at": "2026-04-15T00:00:00Z",
    }
]

SAMPLE_REPOS = [
    {
        "name": "new-tool",
        "html_url": "https://github.com/anthropics/new-tool",
        "description": "A new Anthropic tool",
        "created_at": "2026-04-15T00:00:00Z",
        "pushed_at": "2026-04-15T12:00:00Z",
    }
]


@patch("src.collectors.github_org.requests.get")
def test_github_org_collects_releases(mock_get):
    mock_resp_releases = Mock()
    mock_resp_releases.status_code = 200
    mock_resp_releases.json.return_value = SAMPLE_RELEASES

    mock_resp_repos = Mock()
    mock_resp_repos.status_code = 200
    mock_resp_repos.json.return_value = SAMPLE_REPOS

    mock_get.side_effect = [mock_resp_repos, mock_resp_releases]

    collector = GitHubOrgCollector()
    articles = collector.collect()

    assert len(articles) >= 1
    assert any("v1.0.0" in a.title for a in articles)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_collectors.py::test_github_org_collects_releases -v`
Expected: FAIL

- [ ] **Step 3: Implement GitHubOrgCollector**

`src/collectors/github_org.py`:
```python
import requests
from src.collectors.base import BaseCollector, Article


class GitHubOrgCollector(BaseCollector):
    ORG = "anthropics"
    REPOS_URL = f"https://api.github.com/orgs/{ORG}/repos"
    HEADERS = {"Accept": "application/vnd.github.v3+json"}

    def collect(self) -> list[Article]:
        articles = []
        try:
            articles += self._collect_repos()
            articles += self._collect_releases()
        except Exception as e:
            self.error = str(e)
        return articles

    def _collect_repos(self) -> list[Article]:
        resp = requests.get(
            self.REPOS_URL,
            params={"sort": "created", "per_page": 10},
            headers=self.HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        articles = []
        for repo in resp.json():
            articles.append(Article(
                title=f"[新仓库] {repo['name']}",
                url=repo["html_url"],
                source="github-org",
                tag="GitHub",
                date=repo.get("created_at", "")[:10],
                content=repo.get("description") or "",
            ))
        return articles

    def _collect_releases(self) -> list[Article]:
        resp = requests.get(
            f"https://api.github.com/orgs/{self.ORG}/repos",
            params={"sort": "pushed", "per_page": 5},
            headers=self.HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        articles = []
        for repo in resp.json():
            rel_resp = requests.get(
                f"https://api.github.com/repos/{self.ORG}/{repo['name']}/releases",
                params={"per_page": 3},
                headers=self.HEADERS,
                timeout=30,
            )
            if rel_resp.status_code != 200:
                continue
            for rel in rel_resp.json():
                articles.append(Article(
                    title=f"[Release] {repo['name']} {rel['tag_name']}",
                    url=rel["html_url"],
                    source="github-org",
                    tag="GitHub",
                    date=rel.get("published_at", "")[:10],
                    content=(rel.get("body") or "")[:2000],
                ))
        return articles
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_collectors.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/collectors/github_org.py tests/test_collectors.py
git commit -m "feat: add GitHub org collector for repos and releases"
```

---

## Task 6: Import AI RSS Collector

**Files:**
- Create: `src/collectors/import_ai.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_collectors.py`:
```python
from unittest.mock import patch, Mock
from src.collectors.import_ai import ImportAICollector

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Import AI #450: Agent Ecologies</title>
      <link>https://importai.substack.com/p/import-ai-450</link>
      <description>This week in AI research and policy.</description>
      <pubDate>Mon, 14 Apr 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


@patch("src.collectors.import_ai.feedparser.parse")
def test_import_ai_collects(mock_parse):
    mock_parse.return_value = Mock(
        entries=[
            Mock(
                title="Import AI #450: Agent Ecologies",
                link="https://importai.substack.com/p/import-ai-450",
                summary="This week in AI research and policy.",
                published="Mon, 14 Apr 2026 12:00:00 GMT",
            )
        ]
    )

    collector = ImportAICollector()
    articles = collector.collect()

    assert len(articles) == 1
    assert articles[0].source == "import-ai"
    assert articles[0].tag == "Newsletter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_collectors.py::test_import_ai_collects -v`
Expected: FAIL

- [ ] **Step 3: Implement ImportAICollector**

`src/collectors/import_ai.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_collectors.py -v`
Expected: all passed

- [ ] **Step 5: Update collectors __init__.py**

`src/collectors/__init__.py`:
```python
from src.collectors.anthropic_news import AnthropicNewsCollector
from src.collectors.anthropic_research import AnthropicResearchCollector
from src.collectors.release_notes import ReleaseNotesCollector
from src.collectors.system_prompts import SystemPromptsCollector
from src.collectors.github_org import GitHubOrgCollector
from src.collectors.dario_blog import DarioBlogCollector
from src.collectors.transformer_circuits import TransformerCircuitsCollector
from src.collectors.import_ai import ImportAICollector

ALL_COLLECTORS = [
    AnthropicNewsCollector,
    AnthropicResearchCollector,
    ReleaseNotesCollector,
    SystemPromptsCollector,
    GitHubOrgCollector,
    DarioBlogCollector,
    TransformerCircuitsCollector,
    ImportAICollector,
]
```

- [ ] **Step 6: Commit**

```bash
git add src/collectors/import_ai.py src/collectors/__init__.py tests/test_collectors.py
git commit -m "feat: add Import AI RSS collector and export all collectors"
```

---

## Task 7: MiniMax Summarizer

**Files:**
- Create: `src/summarizer.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: Write the failing test**

`tests/test_summarizer.py`:
```python
import json
from unittest.mock import patch, Mock
from src.summarizer import Summarizer
from src.collectors.base import Article


def _article() -> Article:
    return Article(
        title="Claude Gets Tool Use",
        url="https://example.com",
        source="test",
        content="Anthropic announced that Claude now supports tool use, allowing the model to interact with external APIs and services.",
    )


@patch("src.summarizer.requests.post")
def test_summarizer_fills_brief_and_detail(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "brief": "Claude 新增 Tool Use 功能，可调用外部 API",
                    "detail": "Anthropic 宣布 Claude 支持 Tool Use。该功能允许模型与外部 API 和服务交互，扩展了 Claude 的能力边界。"
                })
            }
        }]
    }
    mock_post.return_value = mock_resp

    summarizer = Summarizer(api_key="test-key")
    article = _article()
    summarizer.summarize(article)

    assert article.brief != ""
    assert article.detail != ""


@patch("src.summarizer.requests.post")
def test_summarizer_handles_api_error(mock_post):
    mock_post.side_effect = Exception("API error")

    summarizer = Summarizer(api_key="test-key")
    article = _article()
    summarizer.summarize(article)

    assert article.brief == article.title
    assert article.detail == article.content[:200]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_summarizer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Summarizer**

`src/summarizer.py`:
```python
import json
import requests
from src.collectors.base import Article

PROMPT_TEMPLATE = """你是一个 AI 行业资讯编辑。请根据以下文章内容生成：
1. brief: 一句话摘要（不超过 50 字）
2. detail: 详细摘要（3-5 句，提炼核心观点和关键信息）

要求：中文输出，专业术语保留英文原文（如 Constitutional AI、Tool Use）。
输出 JSON 格式：{{"brief": "...", "detail": "..."}}

文章标题：{title}
文章内容：{content}"""


class Summarizer:
    # MiniMax OpenAI-compatible endpoint
    API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    def __init__(self, api_key: str, model: str = "MiniMax-Text-01"):
        self.api_key = api_key
        self.model = model

    def summarize(self, article: Article) -> None:
        prompt = PROMPT_TEMPLATE.format(
            title=article.title,
            content=article.content[:2000],
        )

        try:
            resp = requests.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
            article.brief = result.get("brief", article.title)
            article.detail = result.get("detail", article.content[:200])
        except Exception:
            article.brief = article.title
            article.detail = article.content[:200] if article.content else article.title

    def summarize_batch(self, articles: list[Article]) -> None:
        for article in articles:
            if article.content or article.title:
                self.summarize(article)
```

**Note:** MiniMax API 的 endpoint 和 model 名称在实现时需根据你的 API 文档确认。上面用的是 MiniMax 的通用格式，实际参数可能需要微调。

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_summarizer.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/summarizer.py tests/test_summarizer.py
git commit -m "feat: add MiniMax summarizer with fallback on error"
```

---

## Task 8: HTML Renderer

**Files:**
- Create: `templates/daily.html`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `src/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing test**

`tests/test_renderer.py`:
```python
import os
from src.renderer import Renderer
from src.collectors.base import Article


def _articles():
    return [
        Article(
            title="Claude Update",
            url="https://example.com/1",
            source="anthropic-news",
            tag="新闻",
            brief="Claude 发布新功能",
            detail="Anthropic 宣布 Claude 新增了重要功能，提升了模型能力。",
        ),
        Article(
            title="New Paper",
            url="https://example.com/2",
            source="anthropic-research",
            tag="研究",
            brief="新论文发布",
            detail="关于 Constitutional AI 的最新研究成果。",
        ),
    ]


def test_render_daily(tmp_path):
    renderer = Renderer(output_dir=str(tmp_path))
    renderer.render_daily("2026-04-17", _articles(), errors=["system-prompts"])

    daily_path = tmp_path / "2026" / "04" / "17" / "index.html"
    assert daily_path.exists()

    html = daily_path.read_text()
    assert "Claude Update" in html
    assert "New Paper" in html
    assert "system-prompts" in html
    assert "2026-04-17" in html


def test_render_index(tmp_path):
    renderer = Renderer(output_dir=str(tmp_path))
    renderer.render_index(["2026-04-17", "2026-04-16"])

    index_path = tmp_path / "index.html"
    assert index_path.exists()

    html = index_path.read_text()
    assert "2026-04-17" in html
    assert "2026-04-16" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_renderer.py -v`
Expected: FAIL

- [ ] **Step 3: Create style.css**

`static/style.css`:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #fafafa;
    max-width: 720px;
    margin: 0 auto;
    padding: 20px 16px;
}

h1 {
    font-size: 1.5em;
    margin-bottom: 4px;
}

.subtitle {
    color: #888;
    font-size: 0.9em;
    margin-bottom: 24px;
}

.article-item {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    margin-bottom: 12px;
    overflow: hidden;
}

.article-header {
    padding: 14px 16px;
    cursor: pointer;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}

.article-header:hover {
    background: #f5f5f5;
}

.toggle-icon {
    flex-shrink: 0;
    font-size: 0.8em;
    color: #999;
    margin-top: 3px;
    transition: transform 0.2s;
}

.article-item.open .toggle-icon {
    transform: rotate(90deg);
}

.article-body {
    flex: 1;
}

.tag {
    display: inline-block;
    font-size: 0.75em;
    padding: 2px 8px;
    border-radius: 4px;
    background: #e8f4f8;
    color: #0a7e8c;
    margin-right: 8px;
    font-weight: 500;
}

.article-title {
    font-size: 1em;
    font-weight: 600;
    margin-bottom: 4px;
}

.article-brief {
    font-size: 0.9em;
    color: #666;
}

.article-detail {
    display: none;
    padding: 0 16px 14px 42px;
    font-size: 0.9em;
    color: #555;
    line-height: 1.7;
}

.article-item.open .article-detail {
    display: block;
}

.article-detail a {
    color: #0a7e8c;
    text-decoration: none;
}

.article-detail a:hover {
    text-decoration: underline;
}

.original-link {
    display: inline-block;
    margin-top: 10px;
    font-size: 0.85em;
}

.errors {
    margin-top: 20px;
    padding: 12px 16px;
    background: #fff8e1;
    border: 1px solid #ffe082;
    border-radius: 8px;
    font-size: 0.85em;
    color: #8d6e00;
}

.archive {
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid #e8e8e8;
    font-size: 0.9em;
}

.archive a {
    color: #0a7e8c;
    text-decoration: none;
    margin-right: 12px;
}

/* Index page */
.date-list {
    list-style: none;
}

.date-list li {
    padding: 10px 0;
    border-bottom: 1px solid #eee;
}

.date-list a {
    color: #0a7e8c;
    text-decoration: none;
    font-size: 1.05em;
}
```

- [ ] **Step 4: Create daily.html template**

`templates/daily.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anthropic Daily · {{ date }}</title>
    <link rel="stylesheet" href="{{ css_path }}">
</head>
<body>
    <h1>Anthropic Daily · {{ date }}</h1>
    <div class="subtitle">共 {{ articles|length }} 条更新</div>

    {% for article in articles %}
    <div class="article-item" onclick="this.classList.toggle('open')">
        <div class="article-header">
            <span class="toggle-icon">&#9654;</span>
            <div class="article-body">
                <span class="tag">{{ article.tag }}</span>
                <div class="article-title">{{ article.title }}</div>
                <div class="article-brief">{{ article.brief }}</div>
            </div>
        </div>
        <div class="article-detail">
            <p>{{ article.detail }}</p>
            <a href="{{ article.url }}" target="_blank" rel="noopener" class="original-link">&#128279; 查看原文</a>
        </div>
    </div>
    {% endfor %}

    {% if errors %}
    <div class="errors">
        &#9888;&#65039; 本次未能获取: {{ errors | join(", ") }}
    </div>
    {% endif %}

    {% if recent_dates %}
    <div class="archive">
        历史日报:
        {% for d in recent_dates %}
        <a href="{{ root_path }}/{{ d.replace('-', '/') }}">{{ d }}</a>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
```

- [ ] **Step 5: Create index.html template**

`templates/index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anthropic Daily</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <h1>Anthropic Daily</h1>
    <div class="subtitle">Anthropic 资讯日报归档</div>

    <ul class="date-list">
        {% for date in dates %}
        <li><a href="{{ date.replace('-', '/') }}">{{ date }}</a></li>
        {% endfor %}
    </ul>
</body>
</html>
```

- [ ] **Step 6: Implement Renderer**

`src/renderer.py`:
```python
import os
import shutil
from jinja2 import Environment, FileSystemLoader
from src.collectors.base import Article

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


class Renderer:
    def __init__(self, output_dir: str, template_dir: str = TEMPLATE_DIR):
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_daily(
        self,
        date: str,
        articles: list[Article],
        errors: list[str] | None = None,
        recent_dates: list[str] | None = None,
    ) -> str:
        parts = date.split("-")
        daily_dir = os.path.join(self.output_dir, *parts)
        os.makedirs(daily_dir, exist_ok=True)

        # Calculate relative path to CSS
        css_path = "../" * len(parts) + "static/style.css"
        root_path = "../" * len(parts)

        template = self.env.get_template("daily.html")
        html = template.render(
            date=date,
            articles=articles,
            errors=errors or [],
            recent_dates=recent_dates or [],
            css_path=css_path,
            root_path=root_path.rstrip("/"),
        )

        output_path = os.path.join(daily_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def render_index(self, dates: list[str]) -> str:
        template = self.env.get_template("index.html")
        html = template.render(dates=dates)

        output_path = os.path.join(self.output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def copy_static(self) -> None:
        dest = os.path.join(self.output_dir, "static")
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(STATIC_DIR, dest)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_renderer.py -v`
Expected: 2 passed

- [ ] **Step 8: Open a daily page in browser to check styling**

Run:
```bash
python3 -c "
from src.renderer import Renderer
from src.collectors.base import Article
import webbrowser, os

articles = [
    Article(title='Claude 新增 Tool Use', url='https://example.com', source='test', tag='API', brief='Claude 现在支持调用外部工具', detail='Anthropic 宣布 Claude 新增 Tool Use 功能，允许模型与外部 API 交互。这一功能大幅扩展了 Claude 的应用场景。'),
    Article(title='Scaling Laws 新论文', url='https://example.com', source='test', tag='研究', brief='新的 scaling laws 研究成果', detail='Anthropic 研究团队发布了关于 scaling laws 的最新论文，揭示了模型规模与性能之间的新关系。'),
]
r = Renderer(output_dir='/tmp/anthropic-daily-preview', template_dir='templates')
r.render_daily('2026-04-17', articles, errors=['system-prompts'], recent_dates=['2026-04-16', '2026-04-15'])
r.copy_static()
webbrowser.open('file:///tmp/anthropic-daily-preview/2026/04/17/index.html')
"
```

Verify in browser: layout is clean, cards expand/collapse on click, mobile-friendly.

- [ ] **Step 9: Commit**

```bash
git add templates/ static/ src/renderer.py tests/test_renderer.py
git commit -m "feat: add Jinja2 HTML renderer with daily and index templates"
```

---

## Task 9: Feishu Notifier

**Files:**
- Create: `src/notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Write the failing test**

`tests/test_notifier.py`:
```python
from unittest.mock import patch, Mock
from src.notifier import FeishuNotifier


@patch("src.notifier.requests.post")
@patch("src.notifier.requests.request")
def test_notifier_sends_message(mock_request, mock_post):
    # Mock tenant token response
    mock_token_resp = Mock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "tenant_access_token": "test-token",
        "code": 0,
    }
    mock_post.return_value = mock_token_resp

    # Mock send message response
    mock_send_resp = Mock()
    mock_send_resp.status_code = 200
    mock_send_resp.json.return_value = {"code": 0}
    mock_request.return_value = mock_send_resp

    notifier = FeishuNotifier(
        app_id="test-id",
        app_secret="test-secret",
        user_open_id="ou_test",
    )
    result = notifier.send("2026-04-17", 5, "https://example.com/2026/04/17")

    assert result is True
    mock_request.assert_called_once()


@patch("src.notifier.requests.post")
def test_notifier_handles_token_error(mock_post):
    mock_post.side_effect = Exception("Network error")

    notifier = FeishuNotifier(
        app_id="test-id",
        app_secret="test-secret",
        user_open_id="ou_test",
    )
    result = notifier.send("2026-04-17", 5, "https://example.com")

    assert result is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_notifier.py -v`
Expected: FAIL

- [ ] **Step 3: Implement FeishuNotifier**

`src/notifier.py`:
```python
import json
import requests


class FeishuNotifier:
    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages"

    def __init__(self, app_id: str, app_secret: str, user_open_id: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.user_open_id = user_open_id

    def _get_token(self) -> str:
        resp = requests.post(
            self.TOKEN_URL,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["tenant_access_token"]

    def send(self, date: str, count: int, url: str) -> bool:
        try:
            token = self._get_token()

            content = {
                "zh_cn": {
                    "title": f"Anthropic 日报 · {date}",
                    "content": [
                        [{"tag": "text", "text": f"今日 {count} 条更新\n\n"}],
                        [{"tag": "a", "text": "查看日报", "href": url}],
                    ],
                }
            }

            resp = requests.request(
                "POST",
                self.SEND_URL,
                params={"receive_id_type": "open_id"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "receive_id": self.user_open_id,
                    "msg_type": "post",
                    "content": json.dumps(content),
                },
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("code") == 0
        except Exception:
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_notifier.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/notifier.py tests/test_notifier.py
git commit -m "feat: add Feishu notifier using app bot API"
```

---

## Task 10: Main Orchestrator

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Write the failing test**

Append to or create `tests/test_main.py`:
```python
import json
from unittest.mock import patch, Mock, MagicMock
from src.main import run


@patch("src.main.FeishuNotifier")
@patch("src.main.Summarizer")
@patch("src.main.Renderer")
@patch("src.main.SeenStore")
def test_run_skips_when_no_new_articles(mock_store_cls, mock_renderer_cls, mock_summarizer_cls, mock_notifier_cls):
    mock_store = mock_store_cls.return_value
    mock_store.filter_new.return_value = []

    with patch("src.main.ALL_COLLECTORS", []):
        result = run(
            minimax_key="k",
            feishu_app_id="id",
            feishu_app_secret="secret",
            feishu_user_id="uid",
            github_pages_base="https://example.github.io/anthropic-daily",
            output_dir="/tmp/test-output",
            data_dir="/tmp/test-data",
        )

    assert result is False
    mock_notifier_cls.return_value.send.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_main.py -v`
Expected: FAIL

- [ ] **Step 3: Implement main.py**

`src/main.py`:
```python
import os
import sys
import glob
from datetime import datetime, timezone, timedelta

from src.collectors import ALL_COLLECTORS
from src.dedup import SeenStore
from src.summarizer import Summarizer
from src.renderer import Renderer
from src.notifier import FeishuNotifier


def run(
    minimax_key: str,
    feishu_app_id: str,
    feishu_app_secret: str,
    feishu_user_id: str,
    github_pages_base: str,
    output_dir: str = "output",
    data_dir: str = "data",
) -> bool:
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).strftime("%Y-%m-%d")

    # 1. Collect from all sources
    all_articles = []
    errors = []
    for collector_cls in ALL_COLLECTORS:
        collector = collector_cls()
        try:
            articles = collector.collect()
            all_articles.extend(articles)
        except Exception as e:
            errors.append(collector_cls.__name__)
        if collector.error:
            errors.append(collector_cls.__name__)

    # 2. Filter new articles
    seen_path = os.path.join(data_dir, "seen.json")
    store = SeenStore(seen_path)
    new_articles = store.filter_new(all_articles)

    if not new_articles:
        print(f"[{today}] No new articles found. Skipping.")
        store.save()
        return False

    print(f"[{today}] Found {len(new_articles)} new articles.")

    # 3. Summarize
    summarizer = Summarizer(api_key=minimax_key)
    summarizer.summarize_batch(new_articles)

    # 4. Render HTML
    renderer = Renderer(output_dir=output_dir)

    # Get list of existing dates for archive links
    existing_dates = _find_existing_dates(output_dir)
    recent_dates = sorted(existing_dates, reverse=True)[:7]

    renderer.render_daily(today, new_articles, errors=errors, recent_dates=recent_dates)
    renderer.render_index(sorted(existing_dates + [today], reverse=True))
    renderer.copy_static()

    # 5. Mark as seen
    store.mark_seen(new_articles)
    store.save()

    # 6. Notify via Feishu
    date_path = today.replace("-", "/")
    daily_url = f"{github_pages_base}/{date_path}"

    notifier = FeishuNotifier(
        app_id=feishu_app_id,
        app_secret=feishu_app_secret,
        user_open_id=feishu_user_id,
    )
    sent = notifier.send(today, len(new_articles), daily_url)
    if sent:
        print(f"Feishu notification sent.")
    else:
        print(f"Feishu notification failed.")

    return True


def _find_existing_dates(output_dir: str) -> list[str]:
    dates = []
    pattern = os.path.join(output_dir, "????", "??", "??", "index.html")
    for path in glob.glob(pattern):
        parts = path.replace(output_dir, "").strip("/").split("/")
        if len(parts) >= 3:
            dates.append(f"{parts[0]}-{parts[1]}-{parts[2]}")
    return dates


def main():
    run(
        minimax_key=os.environ["MINIMAX_API_KEY"],
        feishu_app_id=os.environ["FEISHU_APP_ID"],
        feishu_app_secret=os.environ["FEISHU_APP_SECRET"],
        feishu_user_id=os.environ["FEISHU_USER_ID"],
        github_pages_base=os.environ.get(
            "GITHUB_PAGES_BASE",
            "https://wuwusisi.github.io/anthropic-daily",
        ),
        output_dir=os.environ.get("OUTPUT_DIR", "output"),
        data_dir=os.environ.get("DATA_DIR", "data"),
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_main.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: add main orchestrator - collect, summarize, render, notify"
```

---

## Task 11: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: Create the workflow file**

`.github/workflows/daily.yml`:
```yaml
name: Anthropic Daily

on:
  schedule:
    - cron: '0 4 * * *'  # UTC 4:00 = Beijing 12:00
  workflow_dispatch:       # manual trigger

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout main
        uses: actions/checkout@v4
        with:
          ref: main

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Checkout gh-pages output
        run: |
          git fetch origin gh-pages || true
          if git rev-parse --verify origin/gh-pages >/dev/null 2>&1; then
            git worktree add output origin/gh-pages
          else
            mkdir -p output
          fi

      - name: Run collector
        env:
          MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
          FEISHU_APP_ID: ${{ secrets.FEISHU_APP_ID }}
          FEISHU_APP_SECRET: ${{ secrets.FEISHU_APP_SECRET }}
          FEISHU_USER_ID: ${{ secrets.FEISHU_USER_ID }}
          GITHUB_PAGES_BASE: "https://wuwusisi.github.io/anthropic-daily"
          OUTPUT_DIR: output
          DATA_DIR: data
          PYTHONPATH: .
        run: python3 src/main.py

      - name: Commit seen.json to main
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/seen.json
          git diff --staged --quiet || git commit -m "data: update seen.json [skip ci]"
          git push origin main

      - name: Deploy to gh-pages
        run: |
          cd output
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "deploy: daily update $(date -u +%Y-%m-%d)"
          git push origin HEAD:gh-pages
```

- [ ] **Step 2: Verify YAML syntax**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily.yml'))" 2>/dev/null || python3 -c "
# Basic YAML validation without PyYAML
with open('.github/workflows/daily.yml') as f:
    content = f.read()
    assert 'on:' in content
    assert 'jobs:' in content
    print('YAML structure looks valid')
"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily.yml
git commit -m "ci: add GitHub Actions daily workflow"
```

---

## Task 12: GitHub Setup + First Deploy

This task is done manually with guidance.

- [ ] **Step 1: Install GitHub CLI**

Run:
```bash
brew install gh
```

- [ ] **Step 2: Authenticate with GitHub**

Run:
```bash
gh auth login
```

Follow the interactive prompts — choose GitHub.com, HTTPS, and authenticate via browser.

- [ ] **Step 3: Create GitHub repository**

Run:
```bash
cd /Users/cbs/Documents/my_projects/anthropic-daily
gh repo create anthropic-daily --public --source=. --push
```

- [ ] **Step 4: Enable GitHub Pages**

Run:
```bash
# Create an empty gh-pages branch
git checkout --orphan gh-pages
git reset --hard
git commit --allow-empty -m "init gh-pages"
git push origin gh-pages
git checkout main

# Enable Pages via API
gh api repos/wuwusisi/anthropic-daily/pages -X POST -f "source[branch]=gh-pages" -f "source[path]=/"
```

- [ ] **Step 5: Set GitHub Secrets**

Run (you will be prompted to paste values):
```bash
gh secret set MINIMAX_API_KEY
gh secret set FEISHU_APP_ID
gh secret set FEISHU_APP_SECRET
gh secret set FEISHU_USER_ID
```

For `FEISHU_USER_ID`, use: `ou_62d7c9c0669ba47a450f133065ab57e1` (from your existing OpenClaw config).

- [ ] **Step 6: Trigger first run manually**

Run:
```bash
gh workflow run daily.yml
```

Watch the run:
```bash
gh run watch
```

- [ ] **Step 7: Verify the result**

1. Check the GitHub Actions run succeeded: `gh run list`
2. Open `https://wuwusisi.github.io/anthropic-daily/` in browser
3. Check Feishu for the notification message

- [ ] **Step 8: Commit any fixes needed**

If selectors or API calls need adjustment based on the first real run, fix and commit:
```bash
git add -A
git commit -m "fix: adjust selectors based on first live run"
git push origin main
```

---

## Task 13: Run All Tests

- [ ] **Step 1: Run full test suite**

Run:
```bash
cd /Users/cbs/Documents/my_projects/anthropic-daily
PYTHONPATH=. python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Fix any failures and commit**

If tests fail, fix and commit:
```bash
git add -A
git commit -m "fix: resolve test failures"
git push origin main
```
