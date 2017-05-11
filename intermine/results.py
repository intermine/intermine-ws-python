try:
    import simplejson as json # Prefer this as it is faster
except ImportError: # pragma: no cover
    try:
        import json
    except ImportError:
        raise ImportError("Could not find any JSON module to import - "
            + "please install simplejson or jsonlib to continue")

import urllib
import re
import copy
import base64
import sys
import logging
from itertools import groupby
from contextlib import closing

P3K = sys.version_info >= (3,0)

logging.basicConfig()

try:
    # Python 2.x imports
    from UserDict import UserDict
    from urllib import urlencode
    from urllib2 import urlopen
    from urllib2 import HTTPError
    from urllib2 import Request
    from urlparse import urlparse
    import httplib
except ImportError:
    # Python 3.x imports
    from urllib.parse import urlencode
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import HTTPError
    from collections import UserDict
    import http.client as httplib

from intermine.errors import WebserviceError
from intermine.model import Attribute, Reference, Collection

from intermine import VERSION

class EnrichmentLine(UserDict):
    """
    An object that represents a result returned from the enrichment service.
    ========================================================================

    These objects operate as dictionaries as well as objects with predefined
    properties.
    """

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return "EnrichmentLine(%s)" % self.data

    def __getattr__(self, name):
        if name is not None:
            key_name = name.replace('_', '-')
            if key_name in list(self.keys()):
                return self.data[key_name]
        raise AttributeError(name)

class ResultObject(object):
    """
    An object used to represent result records as returned in jsonobjects format
    ============================================================================

    These objects are backed by a row of data and the class descriptor that
    describes the object. They allow access in standard object style:

        >>> for gene in query.results():
        ...    print gene.symbol
        ...    print map(lambda x: x.name, gene.pathways)

    All objects will have "id" and "type" properties. The type refers to the
    actual type of this object: if it is a subclass of the one requested, the
    subclass name will be returned. The "id" refers to the internal database id
    of the object, and is a guarantor of object identity.

    """

    def __init__(self, data, cld, view=[]):
        stripped = [v[v.find(".") + 1:] for v in view]
        self.selected_attributes = [v for v in stripped if "." not in v]
        self.reference_paths = dict(((k, list(i)) for k, i in groupby(stripped, lambda x: x[:x.find(".") + 1])))
        self._data = data
        # Make sure this object has the most specific class desc. possible
        class_name = data['class']
        if "class" not in data or cld.name == class_name:
            self._cld = cld
        else: # this could be a composed class - behave accordingly.
            self._cld = cld.model.get_class(class_name)

        self._attr_cache = {}

    def __str__(self):
        dont_show = set(["objectId", "class"])
        return "%s(%s)" % (self._cld.name, ",  ".join("%s = %r" % (k, v) for k, v in list(self._data.items())
            if not isinstance(v, dict) and not isinstance(v, list) and k not in dont_show))

    def __repr__(self):
        dont_show = set(["objectId", "class"])
        return "%s(%s)" % (self._cld.name, ", ".join("%s = %r" % (k, getattr(self, k)) for k in list(self._data.keys())
            if k not in dont_show))

    def __getattr__(self, name):
        if name in self._attr_cache:
            return self._attr_cache[name]

        if name == "type":
            return self._data["class"]

        fld = self._cld.get_field(name)
        attr = None
        if isinstance(fld, Attribute):
            if name in self._data:
                attr = self._data[name]
            if attr is None:
                attr = self._fetch_attr(fld)
        elif isinstance(fld, Reference):
            ref_paths = self._get_ref_paths(fld)
            if name in self._data:
                data = self._data[name]
            else:
                data = self._fetch_reference(fld)
            if isinstance(fld, Collection):
                if data is None:
                    attr = []
                else:
                    attr = [ResultObject(x, fld.type_class, ref_paths) for x in data]
            else:
                if data is None:
                    attr = None
                else:
                    attr = ResultObject(data, fld.type_class, ref_paths)
        else:
            raise WebserviceError("Inconsistent model - This should never happen")
        self._attr_cache[name] = attr
        return attr

    def _get_ref_paths(self, fld):
        if fld.name + "." in self.reference_paths:
            return self.reference_paths[fld.name + "."]
        else:
            return []

    @property
    def id(self):
        """Return the internal DB identifier of this object. Or None if this is not an InterMine object"""
        return self._data.get('objectId')

    def _fetch_attr(self, fld):
        if fld.name in self.selected_attributes:
            return None # Was originally selected - no point asking twice
        c = self._cld
        if "id" not in c:
            return None # Cannot reliably fetch anything without access to the objectId.
        q = c.model.service.query(c, fld).where(id = self.id)
        r = q.first()
        return r._data[fld.name] if fld.name in r._data else None

    def _fetch_reference(self, ref):
        if ref.name + "." in self.reference_paths:
            return None # Was originally selected - no point asking twice.
        c = self._cld
        if "id" not in c:
            return None # Cannot reliably fetch anything without access to the objectId.
        q = c.model.service.query(ref).outerjoin(ref).where(id = self.id)
        r = q.first()
        return r._data[ref.name] if ref.name in r._data else None

class ResultRow(object):
    """
    An object for representing a row of data received back from the server.
    =======================================================================

    ResultRows provide access to the fields of the row through index lookup. However,
    for convenience both list indexes and dictionary keys can be used. So the
    following all work:

        >>> # Assuming the view is "Gene.symbol", "Gene.organism.name":
        >>> row[0] == row["symbol"] == row["Gene.symbol"] == row(0) == row("symbol")
        ... True

    """

    def __init__(self, data, views):
        self.data = data
        self.views = views
        self.index_map = None

    def __len__(self):
        """Return the number of cells in this row"""
        return len(self.data)

    def __iter__(self):
        """Return the list view of the row, so each cell can be processed"""
        return iter(self.to_l())

    def _get_index_for(self, key):
        if self.index_map is None:
            self.index_map = {}
            for i in range(len(self.views)):
                view = self.views[i]
                headless_view = re.sub("^[^.]+.", "", view)
                self.index_map[view] = i
                self.index_map[headless_view] = i

        return self.index_map[key]

    def __str__(self):
        root = re.sub("\..*$", "", self.views[0])
        parts = [root + ":"]
        for view in self.views:
           short_form = re.sub("^[^.]+.", "", view)
           value = self[view]
           parts.append(short_form + "=" + repr(value))
        return " ".join(parts)

    def __call__(self, name):
        return self.__getitem__(name)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.data[key]
        elif isinstance(key, slice):
            return self.data[key]
        else:
            index = self._get_index_for(key)
            return self.data[index]

    def to_l(self):
        """Return a list view of this row"""
        return [x for x in self.data]

    def to_d(self):
        """Return a dictionary view of this row"""
        return dict(list(self.items()))

    def items(self):
        return [(view, self[view]) for view in self.views]

    def iteritems(self):
        for view in self.views:
            yield (view, self[view])

    def keys(self):
        return copy.copy(self.views)

    def values(self):
        return self.to_l()

    def itervalues(self):
        return iter(self.to_l())

    def iterkeys(self):
        return iter(self.views)

    def has_key(self, key):
        try:
            self._get_index_for(key)
            return True
        except KeyError:
           return False

class TableResultRow(ResultRow):
    """
    A class for parsing results from the jsonrows data format.
    """

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.data[key]["value"]
        elif isinstance(key, slice):
            return [x["value"] for x in self.data[key]]
        else:
            index = self._get_index_for(key)
            return self.data[index]["value"]

    def to_l(self):
        """Return a list view of this row"""
        return [x["value"] for x in self.data]

def encode_str(s):
    return s.encode('utf8') if hasattr(s, 'encode') else s

def decode_binary(b):
    return b.decode('utf8') if hasattr(b, 'decode') else b

def encode_dict(input_d):
    return dict((encode_str(k), encode_str(v)) for k, v in list(input_d.items()))

class ResultIterator(object):
    """
    A facade over the internal iterator object
    ==========================================

    These objects handle the iteration over results
    in the formats requested by the user. They are responsible
    for generating an appropriate parser,
    connecting the parser to the results, and delegating
    iteration appropriately.
    """

    PARSED_FORMATS = frozenset(["rr", "list", "dict"])
    STRING_FORMATS = frozenset(["tsv", "csv", "count"])
    JSON_FORMATS = frozenset(["jsonrows", "jsonobjects", "json"])
    ROW_FORMATS = PARSED_FORMATS | STRING_FORMATS | JSON_FORMATS

    def __init__(self, service, path, params, rowformat, view, cld=None):
        """
        Constructor
        ===========

        Services are responsible for getting result iterators. You will
        not need to create one manually.

        @param root: The root path (eg: "http://www.flymine.org/query/service")
        @type root: string
        @param path: The resource path (eg: "/query/results")
        @type path: string
        @param params: The query parameters for this request
        @type params: dict
        @param rowformat: One of "rr", "object", "count", "dict", "list", "tsv", "csv", "jsonrows", "jsonobjects", "json"
        @type rowformat: string
        @param view: The output columns
        @type view: list
        @param opener: A url opener (user-agent)
        @type opener: urllib.URLopener

        @raise ValueError: if the row format is incorrect
        @raise WebserviceError: if the request is unsuccessful
        """
        if rowformat.startswith("object"): # Accept "object", "objects", "objectformat", etc...
            rowformat = "jsonobjects" # these are synonymous
        if rowformat not in self.ROW_FORMATS:
            raise ValueError("'%s' is not one of the valid row formats (%s)"
                    % (rowformat, repr(list(self.ROW_FORMATS))))

        self.row = ResultRow if service.version >= 8 else TableResultRow

        if rowformat in self.PARSED_FORMATS:
            if service.version >= 8:
                params.update({"format": "json"})
            else:
                params.update({"format" : "jsonrows"})
        elif rowformat == 'tsv':
            params.update({"format": "tab"})
        else:
            params.update({"format" : rowformat})

        self.url  = service.root + path
        self.data = urlencode(encode_dict(params), True)
        self.view = view
        self.opener = service.opener
        self.cld = cld
        self.rowformat = rowformat
        self._it = None

    def __len__(self):
        """
        Return the number of items in this iterator
        ===========================================

        Note that this requires iterating over the full result set, making the
        request in the process.
        """
        c = 0
        for x in self:
            c += 1
        return c

    def __iter__(self):
        """
        Return an iterator over the results
        ===================================

        Returns the internal iterator object.
        """
        con = self.opener.open(self.url, self.data)
        identity = lambda x: x
        flat_file_parser = lambda: FlatFileIterator(con, identity)
        simple_json_parser = lambda: JSONIterator(con, identity)

        try:
            reader = {
                "tsv"         : flat_file_parser,
                "csv"         : flat_file_parser,
                "count"       : flat_file_parser,
                "json"        : simple_json_parser,
                "jsonrows"    : simple_json_parser,
                "list"        : lambda: JSONIterator(con, lambda x: self.row(x, self.view).to_l()),
                "rr"          : lambda: JSONIterator(con, lambda x: self.row(x, self.view)),
                "dict"        : lambda: JSONIterator(con, lambda x: self.row(x, self.view).to_d()),
                "jsonobjects" : lambda: JSONIterator(con, lambda x: ResultObject(x, self.cld, self.view))
            }.get(self.rowformat)()
        except Exception as e:
            raise Exception("Couldn't get iterator for "  + self.rowformat)
        return reader

    def __next__(self):
        """2.x to 3.x bridge"""
        return self.next()

    def next(self):
        """
        Returns the next row, in the appropriate format

        @rtype: whatever the rowformat was determined to be
        """
        if self._it is None:
            self._it = iter(self)
        try:
            return self._it.next()
        except StopIteration:
            self._it = None
            raise StopIteration

class FlatFileIterator(object):
    """
    An iterator for handling results returned as a flat file (TSV/CSV).
    ===================================================================

    This iterator can be used as the sub iterator in a ResultIterator
    """

    def __init__(self, connection, parser):
        """
        Constructor
        ===========

        @param connection: The source of data
        @type connection: socket.socket
        @param parser: a handler for each row of data
        @type parser: Parser
        """
        self.connection = connection
        self.parser = parser

    def __iter__(self):
        return self

    def __next__(self):
        """2.x to 3.x bridge"""
        return self.next()

    def next(self):
        """Return a parsed line of data"""
        line = decode_binary(next(self.connection)).strip()
        if line.startswith("[ERROR]"):
            raise WebserviceError(line)
        return self.parser(line)

class JSONIterator(object):
    """
    An iterator for handling results returned in the JSONRows format
    ================================================================

    This iterator can be used as the sub iterator in a ResultIterator
    """

    LOG = logging.getLogger('JSONIterator')

    def __init__(self, connection, parser):
        """
        Constructor
        ===========

        @param connection: The source of data
        @type connection: socket.socket
        @param parser: a handler for each row of data
        @type parser: Parser
        """
        self.connection = connection
        self.parser = parser
        self.header = ""
        self.footer = ""
        self.parse_header()
        self._is_finished = False

    def __iter__(self):
        return self

    def __next__(self):
        """2.6.x-3.x bridge"""
        return self.next()

    def next(self):
        """Returns a parsed row of data"""
        if self._is_finished:
            raise StopIteration
        return self.get_next_row_from_connection()

    def parse_header(self):
        """Reads out the header information from the connection"""
        self.LOG.debug('Connection = {0}'.format(self.connection))
        try:
            line = decode_binary(next(self.connection)).strip()
            self.header += line
            if not line.endswith('"results":['):
                self.parse_header()
        except StopIteration:
            raise WebserviceError("The connection returned a bad header" + self.header)

    def check_return_status(self):
        """
        Perform status checks
        =====================

        The footer containts information as to whether the result
        set was successfully transferred in its entirety. This
        method makes sure we don't silently accept an
        incomplete result set.

        @raise WebserviceError: if the footer indicates there was an error
        """
        container = self.header + self.footer
        info = None
        try:
            info = json.loads(container)
        except:
            raise WebserviceError("Error parsing JSON container: " + container)

        if not info["wasSuccessful"]:
            raise WebserviceError(info["statusCode"], info["error"])

    def get_next_row_from_connection(self):
        """
        Reads the connection to get the next row, and sends it to the parser

        @raise WebserviceError: if the connection is interrupted
        """
        next_row = None
        try:
            line = decode_binary(next(self.connection))
            if line.startswith("]"):
                self.footer += line;
                for otherline in self.connection:
                    self.footer += line
                self.check_return_status()
            else:
                line = line.strip().strip(',')
                if len(line) > 0:
                    try:
                        row = json.loads(line)
                    except json.decoder.JSONDecodeError as e:
                        raise WebserviceError("Error parsing line from results: '"
                                + line + "' - " + str(e))
                    next_row = self.parser(row)
        except StopIteration:
            raise WebserviceError("Connection interrupted")

        if next_row is None:
            self._is_finished = True
            raise StopIteration
        else:
            return next_row

def encode_headers(headers):
    return dict((k.encode('ascii') if isinstance(k, unicode) else k, \
                 v.encode('ascii') if isinstance(v, unicode) else v) \
                 for k, v in list(headers.items()))

class InterMineURLOpener(object):
    """
    Specific implementation of FancyURLopener for this client
    ================================================================

    Provides user agent and authentication headers, and handling of errors
    """
    USER_AGENT = "InterMine-Client-{0}/python-{1}".format(VERSION, sys.version_info)
    PLAIN_TEXT = "text/plain"
    JSON = "application/json"

    def __init__(self, credentials=None, token=None):
        """
        Constructor
        ===========

        InterMineURLOpener((username, password)) S{->} InterMineURLOpener

        Return a new url-opener with the appropriate credentials
        """
        self.token = token
        if credentials and len(credentials) == 2:
            encoded = '{0}:{1}'.format(*credentials).encode('utf8')
            base64string = 'Basic {0}'.format(base64.encodestring(encoded)[:-1].decode('ascii'))
            self.auth_header = base64string
            self.using_authentication = True
        elif self.token is not None:
            token_header = 'Token {0}'.format(self.token)
            self.auth_header = token_header
            self.using_authentication = True
        else:
            self.using_authentication = False

    def clone(self):
        clone = InterMineURLOpener()
        clone.token = self.token
        clone.using_authentication = self.using_authentication
        if self.using_authentication:
            clone.auth_header = self.auth_header
        return clone

    def headers(self, content_type = None, accept = None):
        h = {'UserAgent': self.USER_AGENT}
        if self.using_authentication:
            h['Authorization'] = self.auth_header
        if content_type is not None:
            h['Content-Type'] = content_type
        if accept is not None:
            h['Accept'] = accept
        return h

    def post_plain_text(self, url, body):
        return self.post_content(url, body, InterMineURLOpener.PLAIN_TEXT)

    def post_content(self, url, body, mimetype, charset = "utf-8"):
        content_type = "{0}; charset={1}".format(mimetype, charset)

        with closing(self.open(url, body, {'Content-Type': content_type})) as f:
            return f.read()

    def open(self, url, data=None, headers = None, method = None):
        url = self.prepare_url(url)
        buff = data if data is None else bytearray(data, 'utf8')
        hs = self.headers()
        if headers is not None:
            hs.update(headers)
        req = Request(url, buff, headers = hs)
        if method is not None:
            req.get_method = lambda: method
        try:
            return urlopen(req)
        except HTTPError as e:
            args = (url, e, e.code, # The next two lines are python2.6 workarounds
                    e.reason if hasattr(e, 'reason') else None,
                    e.headers if hasattr(e, 'headers') else None)
            handler = {
                    400: self.http_error_400,
                    401: self.http_error_401,
                    403: self.http_error_403,
                    404: self.http_error_404,
                    500: self.http_error_500
                    }.get(e.code, self.http_error_default)
            handler(*args)

    def read(self, url, data = None):
        with closing(self.open(url, data)) as conn:
            content = conn.read()
            return decode_binary(content)

    def prepare_url(self, url):
        # Generally unnecessary these days - will be deprecated one of these days.
        if self.token:
            token_param = urlencode(encode_dict(dict(token = self.token)))
            o = urlparse(url)
            if o.query:
                url += "&" + token_param
            else:
                url += "?" + token_param

        return url

    def delete(self, url):
        with closing(self.open(url, method = 'DELETE')) as f:
            return f.read()

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        """Re-implementation of http_error_default, with content now supplied by default"""
        content = fp.read()
        fp.close()
        raise WebserviceError(errcode, errmsg, content)

    def http_error_400(self, url, fp, errcode, errmsg, headers, data=None):
        """
        Handle 400 HTTP errors, attempting to return informative error messages
        =======================================================================

        400 errors indicate that something about our request was incorrect

        @raise WebserviceError: in all circumstances

        """
        content = fp.read()
        fp.close()
        try:
            message = json.loads(content)["error"]
        except:
            message = content
        raise WebserviceError("There was a problem with our request", errcode, errmsg, message)

    def http_error_401(self, url, fp, errcode, errmsg, headers, data=None):
        """
        Handle 401 HTTP errors, attempting to return informative error messages
        =======================================================================

        401 errors indicate we don't have sufficient permission for the resource
        we requested - usually a list or a tempate

        @raise WebserviceError: in all circumstances

        """
        content = fp.read()
        fp.close()
        if self.using_authentication:
            auth = self.auth_header
            raise WebserviceError("Insufficient permissions - {0}".format(auth), errcode, errmsg, content)
        else:
            raise WebserviceError("No permissions - not logged in", errcode, errmsg, content)

    def http_error_403(self, url, fp, errcode, errmsg, headers, data=None):
        """
        Handle 403 HTTP errors, attempting to return informative error messages
        =======================================================================

        401 errors indicate we don't have sufficient permission for the resource
        we requested - usually a list or a tempate

        @raise WebserviceError: in all circumstances

        """
        content = fp.read()
        fp.close()
        try:
            message = json.loads(content)["error"]
        except:
            message = content
        if self.using_authentication:
            raise WebserviceError("Insufficient permissions", errcode, errmsg, message)
        else:
            raise WebserviceError("No permissions - not logged in", errcode, errmsg, message)

    def http_error_404(self, url, fp, errcode, errmsg, headers, data=None):
        """
        Handle 404 HTTP errors, attempting to return informative error messages
        =======================================================================

        404 errors indicate that the requested resource does not exist - usually
        a template that is not longer available.

        @raise WebserviceError: in all circumstances

        """
        content = fp.read()
        fp.close()
        try:
            message = json.loads(content)["error"]
        except:
            message = content
        raise WebserviceError("Missing resource", errcode, errmsg, message)

    def http_error_500(self, url, fp, errcode, errmsg, headers, data=None):
        """
        Handle 500 HTTP errors, attempting to return informative error messages
        =======================================================================

        500 errors indicate that the server borked during the request - ie: it wasn't
        our fault.

        @raise WebserviceError: in all circumstances

        """
        content = fp.read()
        fp.close()
        try:
            message = json.loads(content)["error"]
        except:
            message = content
        raise WebserviceError("Internal server error", errcode, errmsg, message)

