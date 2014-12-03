import weakref
import time

# Use core json for 2.6+, simplejson for <=2.5
try:
    import json
except ImportError:
    import simplejson as json

def get_json(service, path, key):
    text = service.opener.read(service.root + path)
    data = json.loads(text)
    if data['error'] is not None:
        raise Exception(data['error'])
    if key not in data:
        raise Exception(key + " not returned from " + path)
    return data[key]

ONE_MINUTE = 60

COMPLETED = set(["SUCCESS", "ERROR"])

class Job(object):
    """
    A Representation of an Identifier Resolution Job
    ================================================

    Users can submit requests to resolve sets of IDs to
    objects in the data-store. These jobs begin in a PENDING
    state, and transition through RUNNING to either SUCCESS
    or ERROR.

    Upon completion, the results of the job may be fetched, and the
    job may be deleted on the server.
    """

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
        """
        Check to see if the job has been completed, updating the
        status of the job in the process.

        @return: Boolean Whether or not the job is complete.
        """
        if self.status not in COMPLETED:
            backoff = self.backoff
            self.backoff = min(self.max_backoff, backoff * self.decay)
            time.sleep(backoff)
            self.status = self.fetch_status()
        return self.status in COMPLETED

    def fetch_status(self):
        """
        Retrieve the results of this completed job from the server.

        @rtype: dict
        """
        return get_json(self.service, "/ids/{0}/status".format(self.uid), "status")

    def delete(self):
        """
        Delete the job from the server.

        The job should not be used again once this method has been invoked.
        """
        path = "/ids/" + self.uid
        response = self.service.opener.delete(self.service.root + path)
        response_data = json.loads(response)
        if response_data['error'] is not None:
            raise Exception(response_data['error'])

    def fetch_results(self):
        """
        Retrieve the current status of this job from the server.

        @rtype String
        """
        return get_json(self.service, "/ids/{0}/result".format(self.uid), "results")
