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
