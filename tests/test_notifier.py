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
