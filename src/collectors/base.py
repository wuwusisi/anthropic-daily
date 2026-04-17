from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    url: str
    source: str
    content: str
    tag: str = ""
    date: str = ""
    brief: str = ""
    detail: str = ""
