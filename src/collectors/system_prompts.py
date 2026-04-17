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
