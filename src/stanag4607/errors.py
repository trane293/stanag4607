"""Public protocol errors."""


class DecodeError(ValueError):
    """Raised when bytes cannot be decoded as the requested wire structure."""

