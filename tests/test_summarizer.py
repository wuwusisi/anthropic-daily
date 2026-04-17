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
