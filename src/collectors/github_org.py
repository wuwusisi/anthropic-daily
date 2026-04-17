import requests
from src.collectors.base import BaseCollector, Article


class GitHubOrgCollector(BaseCollector):
    ORG = "anthropics"
    REPOS_URL = f"https://api.github.com/orgs/{ORG}/repos"
    HEADERS = {"Accept": "application/vnd.github.v3+json"}

    def collect(self) -> list[Article]:
        articles = []
        try:
            repos = self._fetch_repos()
            articles += self._collect_repos(repos)
            articles += self._collect_releases(repos)
        except Exception as e:
            self.error = str(e)
        return articles

    def _fetch_repos(self) -> list[dict]:
        resp = requests.get(
            self.REPOS_URL,
            params={"sort": "pushed", "per_page": 10},
            headers=self.HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _collect_repos(self, repos: list[dict]) -> list[Article]:
        articles = []
        for repo in repos:
            articles.append(Article(
                title=f"[新仓库] {repo['name']}",
                url=repo["html_url"],
                source="github-org",
                tag="GitHub",
                date=repo.get("created_at", "")[:10],
                content=repo.get("description") or "",
            ))
        return articles

    def _collect_releases(self, repos: list[dict]) -> list[Article]:
        articles = []
        for repo in repos:
            rel_resp = requests.get(
                f"https://api.github.com/repos/{self.ORG}/{repo['name']}/releases",
                params={"per_page": 3},
                headers=self.HEADERS,
                timeout=30,
            )
            if rel_resp.status_code != 200:
                continue
            for rel in rel_resp.json():
                articles.append(Article(
                    title=f"[Release] {repo['name']} {rel['tag_name']}",
                    url=rel["html_url"],
                    source="github-org",
                    tag="GitHub",
                    date=rel.get("published_at", "")[:10],
                    content=(rel.get("body") or "")[:2000],
                ))
        return articles
