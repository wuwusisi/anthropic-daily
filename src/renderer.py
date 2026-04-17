import os
import shutil
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from src.collectors.base import Article

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


class Renderer:
    def __init__(self, output_dir: str, template_dir: str = TEMPLATE_DIR):
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render_daily(
        self,
        date: str,
        articles: List[Article],
        errors: Optional[List[str]] = None,
        recent_dates: Optional[List[str]] = None,
    ) -> str:
        parts = date.split("-")
        daily_dir = os.path.join(self.output_dir, *parts)
        os.makedirs(daily_dir, exist_ok=True)

        css_path = "../" * len(parts) + "static/style.css"
        root_path = "../" * len(parts)

        template = self.env.get_template("daily.html")
        html = template.render(
            date=date,
            articles=articles,
            errors=errors or [],
            recent_dates=recent_dates or [],
            css_path=css_path,
            root_path=root_path.rstrip("/"),
        )

        output_path = os.path.join(daily_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def render_index(self, dates: List[str]) -> str:
        template = self.env.get_template("index.html")
        html = template.render(dates=dates)

        output_path = os.path.join(self.output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def copy_static(self) -> None:
        dest = os.path.join(self.output_dir, "static")
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(STATIC_DIR, dest)
