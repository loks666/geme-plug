class GemePlugError(Exception):
    """Base exception for geme-plug."""


class ConnectionError(GemePlugError):
    """Raised when the MQTT broker connection cannot be established."""


class RequestTimeoutError(GemePlugError):
    """Raised when the plug does not respond within the configured timeout."""


class ProtocolError(GemePlugError):
    """Raised when a malformed or unexpected device response is received."""
