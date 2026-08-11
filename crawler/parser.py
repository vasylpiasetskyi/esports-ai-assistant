from bs4 import BeautifulSoup

from crawler.models import RawPage

_STRIP_CLASSES = ("infobox", "navbox", "mw-editsection", "references", "reference")
_STRIP_TAGS = ("script", "style")


class MediaWikiHtmlParser:
    def extract(self, raw_page: RawPage) -> str:
        soup = BeautifulSoup(raw_page.html, "html.parser")

        for tag in soup.find_all(_STRIP_TAGS):
            tag.decompose()

        for class_name in _STRIP_CLASSES:
            for tag in soup.find_all(class_=class_name):
                tag.decompose()

        text = soup.get_text(separator=" ")
        return " ".join(text.split())
