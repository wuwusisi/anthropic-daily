from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    url: str
    source: str
    content: str = ""
    tag: str = ""
    date: str = ""
    brief: str = ""
    detail: str = ""


from abc import ABC, abstractmethod


class BaseCollector(ABC):
    def __init__(self):
        self.error: str | None = None

    @abstractmethod
    def collect(self) -> list[Article]:
        pass
