from __future__ import unicode_literals

import weakref
import sys
import logging

from functools import partial
from contextlib import closing

# Use core json for 2.6+, simplejson for <=2.5
try:
    import json
except ImportError:
    import simplejson as json

try:
    # Python 2.x imports
    from urllib import urlencode
except ImportError:
    # Python 3.x imports
    from urllib.parse import urlencode

import urllib
import codecs

from intermine.errors import WebserviceError
from intermine.lists.list import List

P3K = sys.version_info >= (3,0)

logging.basicConfig()

def safe_key(maybe_unicode):
    if P3K:
        return maybe_unicode # that is fine

    return maybe_unicode.decode('utf8')

class ListManager(object):
    """
    A Class for Managing List Content and Operations
    ================================================

    This class provides methods to manage list contents and operations.

    This class may be called itself, but all the useful methods it has
    are also available on the Service object, which delegates to this class, while
    other methods are more coneniently accessed through the list objects themselves.

    NB: The methods for creating lists can conflict in threaded applications, if
    two threads are each allocated the same unused list name. You are
    strongly advised to use locks to synchronise any list creation requests (create_list,
    or intersect, union, subtract, diff) unless you are choosing your own names each time
    and are confident that these will not conflict.
    """

    LOG = logging.getLogger('listmanager')
    DEFAULT_LIST_NAME = "my_list"
    DEFAULT_DESCRIPTION = "List created with Python client library"

    INTERSECTION_PATH = '/lists/intersect/json'
    UNION_PATH = '/lists/union/json'
    DIFFERENCE_PATH = '/lists/diff/json'
    SUBTRACTION_PATH = '/lists/subtract/json'

    def __init__(self, service):
        self.service = weakref.proxy(service)
        self.lists = None
        self._temp_lists = set()

    def refresh_lists(self):
        """Update the list information with the latest details from the server"""
        self.lists = {}
        url = self.service.root + self.service.LIST_PATH
        data = self.service.opener.read(url)
        list_info = json.loads(data)
        self.LOG.debug("LIST INFO: {0}".format(list_info))
        if not list_info.get("wasSuccessful"):
            raise ListServiceError(list_info.get("error"))
        for l in list_info["lists"]:
            l = ListManager.safe_dict(l) # Workaround for python 2.6 unicode key issues
            self.lists[l["name"]] = List(service=self.service, manager=self, **l)

    @staticmethod
    def safe_dict(d):
        """Recursively clone json structure with UTF-8 dictionary keys"""
        if isinstance(d, dict):
            return dict((safe_key(k), v) for k, v in d.items())
        else:
            return d

    def get_list(self, name):
        """Return a list from the service by name, if it exists"""
        if self.lists is None:
            self.refresh_lists()
        return self.lists.get(name)

    def l(self, name):
        """Alias for get_list"""
        return self.get_list(name)

    def get_all_lists(self):
        """Get all the lists on a webservice"""
        if self.lists is None:
            self.refresh_lists()
        return self.lists.values()

    def get_all_list_names(self):
        """Get all the names of the lists in a particular webservice"""
        if self.lists is None:
            self.refresh_lists()
        return self.lists.keys()

    def get_list_count(self):
        """
        Return the number of lists accessible at the given webservice.
        This number will vary depending on who you are authenticated as.
        """
        return len(self.get_all_list_names())

    def get_unused_list_name(self):
        """
        Get an unused list name
        =======================

        This method returns a new name that does not conflict
        with any currently existing list name.

        The list name is only guaranteed to be unused at the time
        of allocation.
        """
        self.refresh_lists()
        list_names = self.get_all_list_names()
        self.LOG.debug("CURRENT LIST NAMES: {0}".format(list_names))
        counter = 1
        get_name = partial('{0}_{1}'.format, self.DEFAULT_LIST_NAME)
        name = get_name(counter)
        while name in list_names:
            counter += 1
            name = get_name(counter)
        self._temp_lists.add(name)
        return name

    def _get_listable_query(self, queryable):
        q = queryable.to_query()
        if not q.views:
            q.add_view(q.root.name + ".id")
        else:
            # Check to see if the class of the selected items is unambiguous
            up_to_attrs = set((v[0:v.rindex(".")] for v in q.views))
            if len(up_to_attrs) == 1:
                q.select(up_to_attrs.pop() + ".id")
        return q

    def _create_list_from_queryable(self, queryable, name, description, tags):
        q = self._get_listable_query(queryable)
        uri = q.get_list_upload_uri()
        params = q.to_query_params()
        params["listName"] = name
        params["description"] = description
        params["tags"] = ";".join(tags)
        form = urlencode(params)
        resp = self.service.opener.open(uri, form)
        data = resp.read()
        resp.close()
        return self.parse_list_upload_response(data)

    def create_list(self, content, list_type="", name=None, description=None, tags=[], add=[]):
        """
        Create a new list in the webservice
        ===================================

        If no name is given, the list will be considered to be a temporary
        list, and will be automatically deleted when the program ends. To prevent
        this happening, give the list a name, either on creation, or by renaming it.

        This method is not thread safe for anonymous lists - it will need synchronisation
        with locks if you intend to create lists with multiple threads in parallel.

        @param content: The source of the identifiers for this list. This can be:
                          * A string with white-space separated terms.
                          * The name of a file that contains the terms.
                          * A file-handle like thing (something with a 'read' method)
                          * An iterable of identifiers
                          * A query with a single column.
                          * Another list.
        @param list_type: The type of objects to include in the list. This parameter is not
                          required if the content parameter implicitly includes the type
                          (as queries and lists do).
        @param name: The name for the new list. If none is provided one will be generated, and the
                     list will be deleted when the list manager exits context.
        @param description: A description for the list (free text, default = None)
        @param tags: A set of strings to use as tags (default = [])
        @param add: The issues groups that can be treated as matches. This should be a
                    collection of strings naming issue groups that would otherwise be ignored, but
                    in this case will be added to the list. The available groups are:
                      * DUPLICATE - More than one match was found.
                      * WILDCARD - A wildcard match was made.
                      * TYPE_CONVERTED - A match was found, but in another type (eg. found a protein
                                         and we could convert it to a gene).
                      * OTHER - other issue types
                      * :all - All issues should be considered acceptable.
                    This only makes sense with text uploads - it is not required (or used) when
                    the content is a list or a query.

        @rtype: intermine.lists.List
        """
        if description is None:
            description = self.DEFAULT_DESCRIPTION

        if name is None:
            name = self.get_unused_list_name()

        try:
            ids = content.read() # File like thing
        except AttributeError:
            try:
                with closing(codecs.open(content, 'r', 'UTF-8')) as c: # File name
                    ids = c.read()
            except (TypeError, IOError):
                try:
                    ids = content.strip() # Stringy thing
                except AttributeError:
                    try: # Queryable
                        return self._create_list_from_queryable(content, name, description, tags)
                    except AttributeError:
                        try: # Array of idents
                            idents = iter(content)
                            ids = "\n".join(map('"{0}"'.format, idents))
                        except AttributeError:
                            raise TypeError("Cannot create list from " + repr(content))

        uri = self.service.root + self.service.LIST_CREATION_PATH
        query_form = {
            'name': name,
            'type': list_type,
            'description': description,
            'tags': ";".join(tags)
        }
        if len(add): query_form['add'] = [x.lower() for x in add if x]

        uri += "?" + urlencode(query_form, doseq = True)
        data = self.service.opener.post_plain_text(uri, ids)
        return self.parse_list_upload_response(data)

    def parse_list_upload_response(self, response):
        """
        Intepret the response from the webserver to a list request, and return the List it describes
        """
        try:
            response_data = json.loads(response.decode('utf8'))
        except ValueError:
            raise ListServiceError("Error parsing response: " + response)

        if not response_data.get("wasSuccessful"):
            raise ListServiceError(response_data.get("error"))

        self.LOG.debug("response data: {0}".format(response_data))
        self.refresh_lists()
        new_list = self.get_list(response_data["listName"])
        failed_matches = response_data.get("unmatchedIdentifiers")
        new_list._add_failed_matches(failed_matches)
        return new_list

    def delete_lists(self, lists):
        """Delete the given lists from the webserver"""
        self.refresh_lists()
        all_names = self.get_all_list_names()
        for l in lists:
            if isinstance(l, List):
                name = l.name
            else:
                name = str(l)
            if name not in all_names:
                self.LOG.debug('{0} does not exist - skipping'.format(name))
                continue
            self.LOG.debug('deleting {0}'.format(name))
            uri = self.service.root + self.service.LIST_PATH
            query_form = {'name': name}
            uri += "?" + urlencode(query_form)
            response = self.service.opener.delete(uri)
            response_data = json.loads(response.decode('utf8'))
            if not response_data.get("wasSuccessful"):
                raise ListServiceError(response_data.get("error"))
        self.refresh_lists()

    def remove_tags(self, to_remove_from, tags):
        """
        Add the tags to the given list
        ==============================

        Returns the current tags of this list.
        """
        uri = self.service.root + self.service.LIST_TAG_PATH
        form = {"name": to_remove_from.name, "tags": ";".join(tags)}
        uri += "?" + urlencode(form)
        body = self.service.opener.delete(uri)
        return self._body_to_json(body)["tags"]

    def add_tags(self, to_tag, tags):
        """
        Add the tags to the given list
        ==============================

        Returns the current tags of this list.
        """
        uri = self.service.root + self.service.LIST_TAG_PATH
        form = {"name": to_tag.name, "tags": ";".join(tags)}
        resp = self.service.opener.open(uri, urlencode(form))
        body = resp.read()
        resp.close()
        return self._body_to_json(body)["tags"]

    def get_tags(self, im_list):
        """
        Get the up-to-date set of tags for a given list
        ===============================================

        Returns the current tags of this list.
        """
        uri = self.service.root + self.service.LIST_TAG_PATH
        form = {"name": im_list.name}
        uri += "?" + urlencode(form)
        resp = self.service.opener.open(uri)
        body = resp.read()
        resp.close()
        return self._body_to_json(body)["tags"]

    def _body_to_json(self, body):
        try:
            data = json.loads(body.decode('utf8'))
        except ValueError:
            raise ListServiceError("Error parsing response: " + body)
        if not data.get("wasSuccessful"):
            raise ListServiceError(data.get("error"))
        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self.LOG.debug("Exiting context - deleting {0}".format(self._temp_lists))
        self.delete_temporary_lists()

    def delete_temporary_lists(self):
        """Delete all the lists considered temporary (those created without names)"""
        if self._temp_lists:
            self.delete_lists(self._temp_lists)
            self._temp_lists = set()

    def intersect(self, lists, name=None, description=None, tags=[]):
        """Calculate the intersection of a given set of lists, and return the list representing the result"""
        return self._do_operation(self.INTERSECTION_PATH, "Intersection", lists, name, description, tags)

    def union(self, lists, name=None, description=None, tags=[]):
        """Calculate the union of a given set of lists, and return the list representing the result"""
        return self._do_operation(self.UNION_PATH, "Union", lists, name, description, tags)

    def xor(self, lists, name=None, description=None, tags=[]):
        """Calculate the symmetric difference of a given set of lists, and return the list representing the result"""
        return self._do_operation(self.DIFFERENCE_PATH, "Difference", lists, name, description, tags)

    def subtract(self, lefts, rights, name=None, description=None, tags=[]):
        """Calculate the subtraction of rights from lefts, and return the list representing the result"""
        left_names = self.make_list_names(lefts)
        right_names = self.make_list_names(rights)
        if description is None:
            description = "Subtraction of " + ' and '.join(right_names) + " from " + ' and '.join(left_names)
        if name is None:
            name = self.get_unused_list_name()
        uri = self.service.root + self.SUBTRACTION_PATH
        uri += '?' + urlencode({
            "name": name,
            "description": description,
            "references": ';'.join(left_names),
            "subtract": ';'.join(right_names),
            "tags": ";".join(tags)
            })
        resp = self.service.opener.open(uri)
        data = resp.read()
        resp.close()
        return self.parse_list_upload_response(data)

    def _do_operation(self, path, operation, lists, name, description, tags):
        list_names = self.make_list_names(lists)
        if description is None:
            description = operation + " of " + ' and '.join(list_names)
        if name is None:
            name = self.get_unused_list_name()
        uri = self.service.root + path
        uri += '?' + urlencode({
            "name": name,
            "lists": ';'.join(list_names),
            "description": description,
            "tags": ";".join(tags)
            })
        resp = self.service.opener.open(uri)
        data = resp.read()
        resp.close()
        return self.parse_list_upload_response(data)


    def make_list_names(self, lists):
        """Turn a list of things into a list of list names"""
        list_names = []
        for l in lists:
            try:
                t = l.list_type
                list_names.append(l.name)
            except AttributeError:
                try:
                    m = l.model
                    list_names.append(self.create_list(l).name)
                except AttributeError:
                    list_names.append(str(l))

        return list_names

class ListServiceError(WebserviceError):
    """Errors thrown when something goes wrong with list requests"""
    pass
