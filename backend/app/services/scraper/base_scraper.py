from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self, timeout: int = 30, headless: bool = True):
        self.timeout = timeout
        self.headless = headless

    @abstractmethod
    def scrape(self, product_name: str):
        raise NotImplementedError
