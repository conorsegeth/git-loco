class LocationUnavailableError(Exception):
    """Raised when location cannot be captured."""


class ProviderError(Exception):
    """Raised when a sync provider is unknown or fails."""
