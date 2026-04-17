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
