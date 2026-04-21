import json
import re
import requests
from src.collectors.base import Article

PROMPT_TEMPLATE = """你是一个 AI 行业资讯编辑。请根据以下文章内容生成：
1. title_zh: 中文标题（简洁准确，不超过 30 字）
2. brief: 一句话中文摘要（不超过 50 字）
3. detail: 详细中文摘要（3-5 句，提炼核心观点和关键信息）

要求：全部中文输出，专业术语保留英文原文（如 Constitutional AI、Tool Use）。
输出 JSON 格式：{{"title_zh": "...", "brief": "...", "detail": "..."}}

文章标题：{title}
文章内容：{content}"""


class Summarizer:
    API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7"):
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
            # Strip markdown code block if present
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
            result = json.loads(content)
            if result.get("title_zh"):
                article.title = result["title_zh"]
            article.brief = result.get("brief", article.title)
            article.detail = result.get("detail", article.content[:200])
        except Exception:
            article.brief = article.title
            article.detail = article.content[:200] if article.content else article.title

    def summarize_batch(self, articles: list[Article]) -> None:
        for article in articles:
            if article.content or article.title:
                self.summarize(article)
