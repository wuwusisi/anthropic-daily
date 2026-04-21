import os
import sys
import glob
from datetime import datetime, timezone, timedelta

from src.collectors import ALL_COLLECTORS
from src.dedup import SeenStore
from src.summarizer import Summarizer
from src.renderer import Renderer
from src.notifier import FeishuNotifier


def run(
    minimax_key: str,
    feishu_app_id: str,
    feishu_app_secret: str,
    feishu_user_id: str,
    github_pages_base: str,
    output_dir: str = "output",
    data_dir: str = "data",
) -> bool:
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).strftime("%Y-%m-%d")

    # 1. Collect from all sources
    all_articles = []
    errors = []
    for collector_cls in ALL_COLLECTORS:
        collector = collector_cls()
        try:
            articles = collector.collect()
            all_articles.extend(articles)
        except Exception as e:
            errors.append(collector_cls.__name__)
        if collector.error:
            errors.append(collector_cls.__name__)

    # 2. Filter new articles
    seen_path = os.path.join(data_dir, "seen.json")
    store = SeenStore(seen_path)
    new_articles = store.filter_new(all_articles)

    if not new_articles:
        print(f"[{today}] No new articles found. Skipping.")
        store.save()
        return False

    print(f"[{today}] Found {len(new_articles)} new articles.")

    # 3. Generate integrated digest
    summarizer = Summarizer(api_key=minimax_key)
    digest = summarizer.generate_digest(new_articles)

    if not digest or not digest.get("sections"):
        print(f"[{today}] Digest generation failed or empty. Skipping.")
        store.mark_seen(new_articles)
        store.save()
        return False

    print(f"[{today}] Digest generated with {len(digest.get('sections', []))} sections.")

    # 4. Render HTML
    renderer = Renderer(output_dir=output_dir)

    existing_dates = _find_existing_dates(output_dir)
    recent_dates = sorted(existing_dates, reverse=True)[:7]

    renderer.render_daily(today, digest=digest, errors=errors, recent_dates=recent_dates)
    renderer.render_index(sorted(existing_dates + [today], reverse=True))
    renderer.copy_static()

    # 5. Mark as seen
    store.mark_seen(new_articles)
    store.save()

    # 6. Notify via Feishu
    date_path = today.replace("-", "/")
    daily_url = f"{github_pages_base}/{date_path}"

    notifier = FeishuNotifier(
        app_id=feishu_app_id,
        app_secret=feishu_app_secret,
        user_open_id=feishu_user_id,
    )
    sent = notifier.send(today, len(digest.get("sections", [])), daily_url)
    if sent:
        print(f"Feishu notification sent.")
    else:
        print(f"Feishu notification failed.")

    return True


def _find_existing_dates(output_dir: str) -> list[str]:
    dates = []
    pattern = os.path.join(output_dir, "????", "??", "??", "index.html")
    for path in glob.glob(pattern):
        parts = path.replace(output_dir, "").strip("/").split("/")
        if len(parts) >= 3:
            dates.append(f"{parts[0]}-{parts[1]}-{parts[2]}")
    return dates


def main():
    run(
        minimax_key=os.environ["MINIMAX_API_KEY"],
        feishu_app_id=os.environ["FEISHU_APP_ID"],
        feishu_app_secret=os.environ["FEISHU_APP_SECRET"],
        feishu_user_id=os.environ["FEISHU_USER_ID"],
        github_pages_base=os.environ.get(
            "GITHUB_PAGES_BASE",
            "https://wuwusisi.github.io/anthropic-daily",
        ),
        output_dir=os.environ.get("OUTPUT_DIR", "output"),
        data_dir=os.environ.get("DATA_DIR", "data"),
    )


if __name__ == "__main__":
    main()
