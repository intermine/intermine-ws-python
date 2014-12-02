try:
    from urllib import urlopen
    from StringIO import StringIO
except ImportError:
    from urllib.request import urlopen
    from io import StringIO

def openAnything(source):
    # Try to open with urllib (http, ftp, file url)
    try:
        return urlopen(source)
    except (ValueError, IOError, OSError):
        pass

    try:
        return open(source)
    except (IOError, OSError):
        pass

    return StringIO(str(source))

class ReadableException(Exception):
    def __init__(self, message, cause=None):
        self.message = message
        self.cause = cause

    def __str__(self):
        if self.cause is None:
            return repr(self.message)
        else:
            return repr(self.message) + repr(self.cause)
