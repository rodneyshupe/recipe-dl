class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class UrlError(Error):
    """Exception raised for errors in the input.

    Attributes:
        url -- url for which the error occurred
        message -- explanation of the error
    """

    def __init__(self, url, message):
        self.url = url
        self.message = message
