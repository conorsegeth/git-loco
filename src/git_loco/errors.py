class LocationUnavailableError(Exception):
    """Raised when location cannot be captured."""


class ProviderError(Exception):
    """Raised when a sync provider is unknown or fails."""


class NotInRepoError(Exception):
    """Raised when a git command requires a repository but none is present."""
