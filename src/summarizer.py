import json
import re
import requests
from src.collectors.base import Article

DIGEST_PROMPT = """你是一位面向产品经理的 AI 行业资讯编辑。以下是今天从 Anthropic 相关信源采集到的所有更新内容。

读者是一位产品经理，最关心的方向（按优先级排列）：
- 新产品发布、功能更新、产品策略变化
- 商业化模式、定价、合作伙伴生态
- 新模型发布、模型能力对比、应用场景
- Agent 设计理念、交互范式、用户体验创新
- AI 安全与对齐研究中对产品设计有启发的部分

请你整合提炼这些信息，生成一份高质量的中文日报。要求：

1. 优先突出上述产品经理关心的内容，纯底层技术实现细节可以简略带过或省略
2. 按主题分类，根据实际内容灵活分类（不必每次都用固定分类）
3. 合并相关内容，去除重复信息
4. 没有实质内容的条目直接忽略
5. 对产品和商业层面的变化，点明"这意味着什么"——对用户、开发者或行业的影响
6. 专业术语保留英文原文
7. 每个分类末尾附上相关原文链接

输出 JSON 格式：
{{
  "sections": [
    {{
      "title": "分类标题",
      "content": "整合后的内容描述（markdown 格式，可以用列表、加粗等）",
      "links": [{{"title": "原文标题", "url": "链接"}}]
    }}
  ],
  "summary": "今日一句话总结（不超过 80 字）"
}}

以下是今天采集到的内容：

{articles}"""


class Summarizer:
    API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7"):
        self.api_key = api_key
        self.model = model

    def generate_digest(self, articles: list[Article]) -> dict:
        """Generate an integrated digest from all articles."""
        # Build article list text, skip items with no real content
        article_texts = []
        for a in articles:
            if len(a.title.strip()) < 5 and len(a.content.strip()) < 20:
                continue
            text = f"【{a.tag or a.source}】{a.title}"
            if a.content:
                text += f"\n{a.content[:500]}"
            text += f"\n链接: {a.url}"
            article_texts.append(text)

        if not article_texts:
            return {}

        prompt = DIGEST_PROMPT.format(articles="\n\n---\n\n".join(article_texts))

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
                    "max_tokens": 4096,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            # Strip markdown code block if present
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
            return json.loads(content)
        except Exception as e:
            print(f"Digest generation failed: {e}")
            return {}
