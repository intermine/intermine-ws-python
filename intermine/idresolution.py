import weakref
import time

# Use core json for 2.6+, simplejson for <=2.5
try:
    import json
except ImportError:
    import simplejson as json

def get_json(service, path, key):
    sock = None
    try:
        sock = service.opener.open(service.root + path)
        text = sock.read()
    finally:
        if sock: sock.close()
    data = json.loads(text)
    if data['error'] is not None:
        raise Exception(data['error'])
    if key not in data:
        raise Exception(key + " not returned from " + path)
    return data[key]

ONE_MINUTE = 60

COMPLETED = set(["SUCCESS", "ERROR"])

class Job(object):

    INITIAL_DECAY = 1.25
    INITIAL_BACKOFF = 0.05
    MAX_BACKOFF = ONE_MINUTE

    def __init__(self, service, uid):
        self.service = weakref.proxy(service)
        self.uid = uid
        self.status = None
        self.backoff = Job.INITIAL_BACKOFF
        self.decay = Job.INITIAL_DECAY
        self.max_backoff = Job.MAX_BACKOFF
        if self.uid is None:
            raise Exception("No uid found")

    def poll(self):
        if self.status not in COMPLETED:
            backoff = self.backoff
            self.backoff = min(self.max_backoff, backoff * self.decay)
            time.sleep(backoff)
            self.status = self.fetch_status()
        return self.status in COMPLETED

    def fetch_status(self):
        return get_json(self.service, "/ids/{0}/status".format(self.uid), "status")

    def fetch_results(self):
        return get_json(self.service, "/ids/{0}/result".format(self.uid), "results")
