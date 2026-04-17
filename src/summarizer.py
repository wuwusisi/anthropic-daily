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
