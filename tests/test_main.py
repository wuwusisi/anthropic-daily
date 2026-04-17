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
