from __future__ import unicode_literals

from xml.dom import minidom
from contextlib import closing

try:
    from urlparse import urlparse
    from UserDict import DictMixin
    from urllib import urlopen
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlparse
    from urllib.parse import urlencode
    from collections import MutableMapping as DictMixin
    from urllib.request import urlopen

try:
    import simplejson as json # Prefer this as it is faster
except ImportError: # pragma: no cover
    try:
        import json
    except ImportError:
        raise ImportError("Could not find any JSON module to import - "
            + "please install simplejson or jsonlib to continue")

# Local intermine imports
from intermine.query import Query, Template
from intermine.model import Model, Attribute, Reference, Collection, Column
from intermine.lists.listmanager import ListManager
from intermine.errors import ServiceError, WebserviceError
from intermine.results import InterMineURLOpener, ResultIterator
from intermine import idresolution
from intermine.decorators import requires_version

"""
Webservice Interaction Routines for InterMine Webservices
=========================================================

Classes for dealing with communication with an InterMine
RESTful webservice.

"""

__author__ = "Alex Kalderimis"
__organization__ = "InterMine"
__license__ = "LGPL"
__contact__ = "dev@intermine.org"

class Registry(DictMixin):
    """
    A Class representing an InterMine registry.
    ===========================================

    Registries are web-services that mines can automatically register
    themselves with, and thus enable service discovery by clients.

    SYNOPSIS
    --------

    example::

        from intermine.webservice import Registry

        # Connect to the default registry service
        # at www.intermine.org/registry
        registry = Registry()

        # Find all the available mines:
        for name, mine in registry.items():
            print name, mine.version

        # Dict-like interface for accessing mines.
        flymine = registry["flymine"]

        # The mine object is a Service
        for gene in flymine.select("Gene.*").results():
            process(gene)

    This class is meant to aid with interoperation between
    mines by allowing them to discover one-another, and
    allow users to always have correct connection information.
    """

    MINES_PATH = "/mines.json"

    def __init__(self, registry_url="http://www.intermine.org/registry"):
        self.registry_url = registry_url
        opener = InterMineURLOpener()
        data = opener.open(registry_url + Registry.MINES_PATH).read()
        mine_data = json.loads(data)
        self.__mine_dict = dict(( (mine["name"], mine) for mine in mine_data["mines"]))
        self.__synonyms = dict(( (name.lower(), name) for name in list(self.__mine_dict.keys()) ))
        self.__mine_cache = {}

    def __contains__(self, name):
        return name.lower() in self.__synonyms

    def __getitem__(self, name):
        lc = name.lower()
        if lc in self.__synonyms:
            if lc not in self.__mine_cache:
                self.__mine_cache[lc] = Service(self.__mine_dict[self.__synonyms[lc]]["webServiceRoot"])
            return self.__mine_cache[lc]
        else:
            raise KeyError("Unknown mine: " + name)

    def __setitem__(self, name, item):
        raise NotImplementedError("You cannot add items to a registry")

    def __delitem__(self, name):
        raise NotImplementedError("You cannot remove items from a registry")

    def __len__(self):
        return len(self.__mine_dict)

    def __iter__(self):
        return iter(self.__mine_dict)

    def keys(self):
        return list(self.__mine_dict.keys())

def ensure_str(stringlike):
    if hasattr(stringlike, 'decode'):
        return stringlike.decode('utf8')
    else:
        return str(stringlike)

class Service(object):
    """
    A class representing connections to different InterMine WebServices
    ===================================================================

    The intermine.webservice.Service class is the main interface for the user.
    It will provide access to queries and templates, as well as doing the
    background task of fetching the data model, and actually requesting
    the query results.

    SYNOPSIS
    --------

    example::

      from intermine.webservice import Service
      service = Service("http://www.flymine.org/query/service")

      template = service.get_template("Gene_Pathways")
      for row in template.results(A={"value":"zen"}):
        do_something_with(row)
        ...

      query = service.new_query()
      query.add_view("Gene.symbol", "Gene.pathway.name")
      query.add_constraint("Gene", "LOOKUP", "zen")
      for row in query.results():
        do_something_with(row)
        ...

      new_list = service.create_list("some/file/with.ids", "Gene")
      list_on_server = service.get_list("On server")
      in_both = new_list & list_on_server
      in_both.name = "Intersection of these lists"
      for row in in_both:
        do_something_with(row)
        ...

    OVERVIEW
    --------
    The two methods the user will be most concerned with are:
      - L{Service.new_query}: constructs a new query to query a service with
      - L{Service.get_template}: gets a template from the service
      - L{ListManager.create_list}: creates a new list on the service

    For list management information, see L{ListManager}.

    TERMINOLOGY
    -----------
    X{Query} is the term for an arbitrarily complex structured request for
    data from the webservice. The user is responsible for specifying the
    structure that determines what records are returned, and what information
    about each record is provided.

    X{Template} is the term for a predefined "Query", ie: one that has been
    written and saved on the webservice you will access. The definition
    of the query is already done, but the user may want to specify the
    values of the constraints that exist on the template. Templates are accessed
    by name, and while you can easily introspect templates, it is assumed
    you know what they do when you use them

    X{List} is a saved result set containing a set of objects previously identified
    in the database. Lists can be created and managed using this client library.

    @see: L{intermine.query}
    """
    QUERY_PATH             = '/query/results'
    LIST_ENRICHMENT_PATH   = '/list/enrichment'
    WIDGETS_PATH           = '/widgets'
    SEARCH_PATH            = '/search'
    QUERY_LIST_UPLOAD_PATH = '/query/tolist'
    QUERY_LIST_APPEND_PATH = '/query/append/tolist'
    MODEL_PATH             = '/model'
    TEMPLATES_PATH         = '/templates'
    TEMPLATEQUERY_PATH     = '/template/results'
    LIST_PATH              = '/lists'
    LIST_CREATION_PATH     = '/lists'
    LIST_RENAME_PATH       = '/lists/rename'
    LIST_APPENDING_PATH    = '/lists/append'
    LIST_TAG_PATH          = '/list/tags'
    SAVEDQUERY_PATH        = '/savedqueries/xml'
    VERSION_PATH           = '/version/ws'
    RELEASE_PATH           = '/version/release'
    SCHEME                 = 'http://'
    SERVICE_RESOLUTION_PATH = "/check/"
    IDS_PATH               = "/ids"
    USERS_PATH             = "/users"

    def __init__(self, root,
            username=None, password=None, token=None,
            prefetch_depth=1, prefetch_id_only=False):
        """
        Constructor
        ===========

        Construct a connection to a webservice::

            url = "http://www.flymine.org/query/service"

            # An unauthenticated connection - access to all public data
            service = Service(url)

            # An authenticated connection - access to private and public data
            service = Service(url, token="ABC123456")


        @param root: the root url of the webservice (required)
        @param username: your login name (optional)
        @param password: your password (required if a username is given)
        @param token: your API access token(optional - used in preference to username and password)

        @raise ServiceError: if the version cannot be fetched and parsed
        @raise ValueError:   if a username is supplied, but no password

        There are two alternative authentication systems supported by InterMine
        webservices. The first is username and password authentication, which
        is supported by all webservices. Newer webservices (version 6+)
        also support API access token authentication, which is the recommended
        system to use. Token access is more secure as you will never have
        to transmit your username or password, and the token can be easily changed
        or disabled without changing your webapp login details.

        """
        o = urlparse(root)
        if not o.scheme: root = "http://" + root
        if not root.endswith("/service"): root = root + "/service"

        self.root = root
        self.prefetch_depth = prefetch_depth
        self.prefetch_id_only = prefetch_id_only
        # Initialize empty cached data.
        self._templates = None
        self._model = None
        self._version = None
        self._release = None
        self._widgets = None
        self._list_manager = ListManager(self)
        self.__missing_method_name = None
        if token:
            self.opener = InterMineURLOpener(token=token)
        elif username:
            if token:
                raise ValueError("Both username and token credentials supplied")

            if not password:
                raise ValueError("Username given, but no password supplied")

            self.opener = InterMineURLOpener((username, password))
        else:
            self.opener = InterMineURLOpener()

        try:
            self.version
        except WebserviceError as e:
            raise ServiceError("Could not validate service - is the root url (%s) correct? %s" % (root, e))

        if token and self.version < 6:
            raise ServiceError("This service does not support API access token authentication")

        # Set up sugary aliases
        self.query = self.new_query

    # Delegated list methods

    LIST_MANAGER_METHODS = frozenset(["get_list", "get_all_lists",
        "get_all_list_names",
        "create_list", "get_list_count", "delete_lists", "l"])

    def list_manager(self):
        """
        Get a new ListManager to use with this service.
        ===============================================

        This method is primarily useful as a context manager
        when creating temporary lists, since on context exit all
        temporary lists will be cleaned up::

            with service.list_manager() as manager:
                temp_a = manager.create_list(file_a, "Gene")
                temp_b = manager.create_list(file_b, "Gene")
                for gene in (temp_a & temp_b):
                    print gene.primaryIdentifier, "is in both"

        @rtype: ListManager
        """
        return ListManager(self)

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        if name in self.LIST_MANAGER_METHODS:
            method = getattr(self._list_manager, name)
            return method
        raise AttributeError("Could not find " + name)

    def __del__(self): # On going out of scope, try and clean up.
        try:
            self._list_manager.delete_temporary_lists()
        except ReferenceError:
            pass

    @property
    def version(self):
        """
        Returns the webservice version
        ==============================

        The version specifies what capabilities a
        specific webservice provides. The most current
        version is 3

        may raise ServiceError: if the version cannot be fetched

        @rtype: int
        """
        try:
            if self._version is None:
                try:
                    url = self.root + self.VERSION_PATH
                    self._version = int(self.opener.open(url).read())
                except ValueError as e:
                    raise ServiceError("Could not parse a valid webservice version: " + str(e))
        except AttributeError as e:
            raise Exception(e)
        return self._version

    def resolve_service_path(self, variant):
        """Resolve the path to optional services"""
        url = self.root + self.SERVICE_RESOLUTION_PATH + variant
        return self.opener.open(url).read()

    @property
    def release(self):
        """
        Returns the datawarehouse release
        =================================

        Service.release S{->} string

        The release is an arbitrary string used to distinguish
        releases of the datawarehouse. This usually coincides
        with updates to the data contained within. While a string,
        releases usually sort in ascending order of recentness
        (eg: "release-26", "release-27", "release-28"). They can also
        have less machine readable meanings (eg: "beta")

        @rtype: string
        """
        if self._release is None:
            self._release = ensure_str(urlopen(self.root + self.RELEASE_PATH).read()).strip()
        return self._release

    def load_query(self, xml, root=None):
        """
        Construct a new Query object for the given webservice
        =====================================================

        This is the standard method for instantiating new Query
        objects. Queries require access to the data model, as well
        as the service itself, so it is easiest to access them through
        this factory method.

        @return: L{intermine.query.Query}
        """
        return Query.from_xml(xml, self.model, root=root)

    def select(self, *columns, **kwargs):
        """
        Construct a new Query object with the given columns selected.
        =============================================================

        As new_query, except that instead of a root class, a list of
        output column expressions are passed instead.
        """
        if "xml" in kwargs:
            return self.load_query(kwargs["xml"])
        if len(columns) == 1:
            view = columns[0]
            if isinstance(view, Attribute):
                return Query(self.model, self).select("%s.%s" % (view.declared_in.name, view))
            if isinstance(view, Reference):
                return Query(self.model, self).select("%s.%s.*" % (view.declared_in.name, view))
            elif not isinstance(view, Column) and not str(view).endswith("*"):
                path = self.model.make_path(view)
                if not path.is_attribute():
                    return Query(self.model, self).select(str(view) + ".*")
        return Query(self.model, self).select(*columns)

    new_query = select

    def get_template(self, name):
        """
        Returns a template of the given name
        ====================================

        Tries to retrieve a template of the given name
        from the webservice. If you are trying to fetch
        a private template (ie. one you made yourself
        and is not available to others) then you may need to authenticate

        @see: L{intermine.webservice.Service.__init__}

        @param name: the template's name
        @type name: string

        @raise ServiceError: if the template does not exist
        @raise QueryParseError: if the template cannot be parsed

        @return: L{intermine.query.Template}
        """
        try:
            t = self.templates[name]
        except KeyError:
            raise ServiceError("There is no template called '"
                + name + "' at this service")
        if not isinstance(t, Template):
            t = Template.from_xml(t, self.model, self)
            self.templates[name] = t
        return t

    def _get_json(self, path, payload = None):
        headers = {'Accept': 'application/json'}
        with closing(self.opener.open(self.root + path, payload, headers = headers)) as resp:
            data = json.loads(ensure_str(resp.read()))
            if data['error'] is not None:
                raise ServiceError(data['error'])
            return data

    def _get_xml(self, path):
        headers = {'Accept': 'application/xml'}
        with closing(self.opener.open(self.root + path, headers = headers)) as sock:
            return minidom.parse(sock)

    def search(self, term, **facets):
        """
        Perform an unstructured search by term
        =======================================

        This seach method performs a search of all objects
        indexed by the service endpoint, returning results
        and facets for those results.

        @param term The search term
        @param facets The facets to search by (eg: Organism = 'H. sapiens')

        @return (list, dict) The results, and a dictionary of facetting informtation.
        """
        if hasattr(term, 'encode'):
            term = term.encode('utf8')
        params = [('q', term)]
        for facet, value in list(facets.items()):
            if hasattr(value, 'encode'):
                value = value.encode('utf8')
            params.append(("facet_{0}".format(facet), value))
        payload = urlencode(params, doseq = True)
        resp = self._get_json(self.SEARCH_PATH, payload = payload)
        return (resp['results'], resp['facets'])

    @property
    def widgets(self):
        """
        The dictionary of widgets from the webservice
        ==============================================

        The set of widgets available to a service does not
        change between releases, so they are cached.
        If you are running a long running process, you may
        wish to periodically dump the cache by calling
        L{Service.flush}, or simply get a new Service object.

        @return dict
        """
        if self._widgets is None:
            ws = self._get_json(self.WIDGETS_PATH)['widgets']
            self._widgets = dict(([w['name'], w] for w in ws))
        return self._widgets

    def resolve_ids(self, data_type, identifiers, extra = '', case_sensitive = False, wildcards = False):
        """
        Submit an Identifier Resolution Job
        ===================================

        Request that a set of identifiers be resolved to objects in
        the data store.

        @param data_type: The type of these identifiers (eg. 'Gene')
        @type data_type: String

        @param identifiers: The ids to resolve (eg. ['eve', 'zen', 'pparg'])
        @type identifiers: iterable of string

        @param extra: A disambiguating value (eg. "Drosophila melanogaster")
        @type extra: String

        @param case_sensitive: Whether to treat IDs case sensitively.
        @type case_sensitive: Boolean

        @param wildcards: Whether or not to interpret wildcards (eg: "eve*")
        @type wildcards: Boolean

        @return: {idresolution.Job} The job.
        """
        if self.version < 10:
            raise ServiceError("This feature requires API version 10+")
        if not data_type:
            raise ServiceError("No data-type supplied")
        if not identifiers:
            raise ServiceError("No identifiers supplied")

        data = json.dumps({
            "type": data_type,
            "identifiers": list(identifiers),
            "extra": extra,
            "caseSensitive": case_sensitive,
            "wildCards": wildcards
        })
        text = self.opener.post_content(self.root + self.IDS_PATH, data, InterMineURLOpener.JSON)
        ret = json.loads(text)
        if ret['error'] is not None:
            raise ServiceError(ret['error'])
        if ret['uid'] is None:
            raise Exception("No uid found in " + ret)

        return idresolution.Job(self, ret['uid'])

    def flush(self):
        """
        Flushes any cached data.
        """
        self._list_manager.delete_temporary_lists()
        self._list_manager = ListManager(self)
        self._templates = None
        self._model = None
        self._version = None
        self._release = None
        self._widgets = None

    @property
    def templates(self):
        """
        The dictionary of templates from the webservice
        ===============================================

        Service.templates S{->} dict(intermine.query.Template|string)

        For efficiency's sake, Templates are not parsed until
        they are required, and until then they are stored as XML
        strings. It is recommended that in most cases you would want
        to use L{Service.get_template}.

        You can use this property however to test for template existence though::

         if name in service.templates:
            template = service.get_template(name)

        @rtype: dict

        """
        if self._templates is None:
            templates = {}
            dom = self._get_xml(self.TEMPLATES_PATH)
            for e in dom.getElementsByTagName('template'):
                name = e.getAttribute('name')
                if name in templates:
                    raise ServiceError("Two templates with same name: " + name)
                else:
                    templates[name] = e.toxml()
            self._templates = templates
        return self._templates

    @property
    def model(self):
        """
        The data model for the webservice you are querying
        ==================================================

        Service.model S{->} L{intermine.model.Model}

        This is used when constructing queries to provide them
        with information on the structure of the data model
        they are accessing. You are very unlikely to want to
        access this object directly.

        raises ModelParseError: if the model cannot be read

        @rtype: L{intermine.model.Model}

        """
        if self._model is None:
            model_url = self.root + self.MODEL_PATH
            self._model = Model(model_url, self)
        return self._model

    def get_results(self, path, params, rowformat, view, cld=None):
        """
        Return an Iterator over the rows of the results
        ===============================================

        This method is called internally by the query objects
        when they are called to get results. You will not
        normally need to call it directly

        @param path: The resource path (eg: "/query/results")
        @type path: string
        @param params: The query parameters for this request as a dictionary
        @type params: dict
        @param rowformat: One of "rr", "object", "count", "dict", "list", "tsv", "csv", "jsonrows", "jsonobjects"
        @type rowformat: string
        @param view: The output columns
        @type view: list

        @raise WebserviceError: for failed requests

        @return: L{intermine.webservice.ResultIterator}
        """
        return ResultIterator(self, path, params, rowformat, view, cld)

    @requires_version(9)
    def register(self, username, password):
        """
        Register a new user with this service.
        =======================================

        @return {Service} an authenticated service.
        """
        username = bytearray(username, 'utf8')
        password = bytearray(password, 'utf8')
        payload = urlencode({'name': username, 'password': password})
        registrar = Service(self.root)
        resp = registrar._get_json(self.USERS_PATH, payload = payload)
        token = resp['user']['temporaryToken']
        return Service(self.root, token = token)

    @requires_version(16)
    def get_deregistration_token(self, validity = 300):
        if validity < 1 or validity > 24 * 60 * 60:
            raise ValueError("Validity not a reasonable value: 1ms - 2hrs")
        params = urlencode({'validity': str(validity)})
        resp = self._get_json('/user/deregistration', payload = params)
        return resp['token']

    @requires_version(16)
    def deregister(self, deregistration_token):
        """
        Remove a User from the service
        ==============================

        @param deregistration_token A token to prove you really want to do this

        @return string All the user's data.
        """
        if 'uuid' in deregistration_token:
            deregistration_token = deregistration_token['uuid']

        path = self.root + '/user'
        params = {'deregistrationToken': deregistration_token, 'format': 'xml'}
        uri = path + '?' + urlencode(params)
        self.flush()
        userdata = self.opener.delete(uri)
        return userdata

