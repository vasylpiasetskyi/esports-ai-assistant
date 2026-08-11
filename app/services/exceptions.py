class EsportsDataError(Exception):
    """Base exception for all esports data lookup errors."""


class PlayerNotFoundError(EsportsDataError):
    """Raised when no player matches the given game and name."""


class TeamNotFoundError(EsportsDataError):
    """Raised when no team matches the given game and name."""


class MatchNotFoundError(EsportsDataError):
    """Raised when no match matches the given game and match id."""
