class CrawlerError(Exception):
    """Base exception for all crawler errors."""


class PageNotFoundError(CrawlerError):
    """Raised when a requested page does not exist at the source."""


class SourceUnavailableError(CrawlerError):
    """Raised when the source cannot be reached (network or server error)."""
