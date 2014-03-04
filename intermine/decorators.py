from functools import wraps
from intermine.errors import ServiceError

def requires_version(required):

    error_fmt = "Service must be at version %s, but is at %s"

    def decorator(f):

        @wraps(f)
        def wrapper(self, *args, **kwargs):
            if self.version < required:
                raise ServiceError(error_fmt % (required, self.version))
            return f(self, *args, **kwargs)

        return wrapper

    return decorator

