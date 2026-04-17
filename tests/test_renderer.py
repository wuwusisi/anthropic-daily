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
