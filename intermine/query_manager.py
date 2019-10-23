import requests
from lxml import etree
import json
try:
    import urllib.request as req
except ImportError:
    import urllib as req
"""
Functions for better usage of queries
================================================
Prompts the user to enter the API token and mine corresponding to the account
example:

    >>>from intermine import query_manager as qm
"""


def save_mine_and_token(m, t):
    """
    A function to access an account from a particular mine
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.save_mine_and_token("flymine","<enter token>")
        <now you can access account linked to the token>

    """
    global mine
    global token
    mine = m
    token = t
    # if no tests are taking place
    if mine != 'mock':
        # source of the request
        src = "http://registry.intermine.org/service/instances/" + mine
        try:
            # tests if mine is valid by checking if object 'obj' exists
            m = requests.get(src)
            data = json.loads(m.text)
            obj = data["instance"]["url"]
            obj = data["instance"]["url"] + "/service/user/queries?token=" + \
                token
            try:
                # tests if token is valid by checking if object 'obj' exists
                o = requests.get(obj)
                data = json.loads(o.text)
                obj = data['queries'].keys()
                # checks the type fo exception
            except Exception as ex:
                template = "An exception of type {0} occurred."
                message = template.format(type(ex).__name__, ex.args)
                return message + " Check token"
        except Exception as ex:
            template = "An exception of type {0} occurred."
            message = template.format(type(ex).__name__, ex.args)
            return message + " Check mine"


def get_all_query_names():
    """
    A function to list all the queries that are saved in a user account
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.save_mine_and_token("flymine","<enter token>")
        >>>qm.get_all_query_names()
        <returns the names of all the saved queries in user account>

    """
    # mock dict for tests
    if mine == 'mock':
        dict = {'queries': {'query1': 1}}
    else:
        # source of the initial request
        x = "http://registry.intermine.org/service/instances/" + mine
        # data retreived as an object
        r = requests.get(x)
        # data converted to dict
        dict = json.loads(r.text)
        # source of next requests
        link = dict["instance"]["url"] + "/service/user/queries?token=" + token
        r = requests.get(link)
        dict = json.loads(r.text)
    # count used to check existence of the query
    count = 0
    # list where output is stored
    result = []
    for key in dict['queries'].keys():
        count = count + 1
        # appends the names in result
        result.append(key)

    if count == 0:
        # if no such query name exists in the account
        return "No saved queries"

    return ", ".join(result)


def get_query(name):
    """
    A function that returns the columns that a given query constitutes of
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.save_mine_and_token("flymine","<enter token>")
        >>>qm.get_query('queryName')
        <returns information about the query whose name is 'queryName'>

    """
    # mock dict for testing
    if mine == 'mock':
        if name == 'query1':
            ans = 'c1, c2'
        else:
            ans = '<saved-queries></saved-queries>'
    else:
        # source of the initial request
        x = "http://registry.intermine.org/service/instances/" + mine
        r = requests.get(x)
        dict = json.loads(r.text)
        link = dict["instance"]["url"] + "/service/user/queries?filter=" + \
            name + "&format=xml&token=" + token
        r = requests.get(link)
        ans = r.text
    if ans == '<saved-queries></saved-queries>':
        return "No such query available"
    else:
        return ans


def delete_query(name):
    """
    A function that deletes a given query
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.save_mine_and_token("flymine","<enter token>")
        >>>qm.delete_query('queryName')
        <deletes the query whose name is 'queryName' from user's account>

    """
    # mock z for testing
    if mine == 'mock':
        z = {'queries': {'query1': 1, 'query2': 2}}
    else:
        # source of the initial request
        x = "http://registry.intermine.org/service/instances/" + mine
        r = requests.get(x)
        dict = json.loads(r.text)
        # source of the next request
        y = dict["instance"]["url"] + "/service/user/queries?token=" + token
        r = requests.get(y)
        # dictionary form of data
        z = json.loads(r.text)
    # checks if query name exists
    count = 0
    for key in z['queries'].keys():
        if key == name:
            count = count + 1
    if count == 0:
        return "No such query available"

    else:
        # returns just a message for tests
        if mine == 'mock':
            return name + " is deleted"
        else:
            link = dict["instance"]["url"] + "/service/user/queries/" + name +\
                "?token=" + token
            requests.delete(link)
            return name + " is deleted"


def post_query(value):
    """
    A function to post a query(in the form of string containing xml or json)
    to a user account
    ================================================
    example:
        >>>from intermine import query_manager as qm
        >>>qm.save_mine_and_token("flymine","<enter token>")
        >>>qm.post_query('<query name="" model="genomic" view="Gene.length\
            Gene.symbol" longDescription="" sortOrder="Gene.length asc">\
            </query>')
    Note that the name should be defined first
    """
    # default parameter name to xml
    paramName = "xml"
    # parsing
    root = etree.fromstring(value)
    # mock raw for testing
    if mine == 'mock':
        raw = {'queries': {'query1': 1, 'query2': 2}}
    else:
        # source of the initial request
        x = "http://registry.intermine.org/service/instances/" + mine
        r = requests.get(x)
        dict = json.loads(r.text)
        # finding the version
        v_link = dict["instance"]["url"] + "/service/version?token=" + token
        r = requests.get(v_link)
        VERSION = json.loads(r.text)
        # change parameter name to query if newer version is used
        if VERSION >= 27:
            paramName = "query"

        link = dict["instance"]["url"] + "/service/user/queries?token=" + token
        r = requests.get(link)
        raw = json.loads(r.text)
    count = 0
    for key in raw['queries'].keys():
        if key == root.attrib['name']:
            count = count + 1
            print("The query name exists")
            try:
                resp = input("Do you want to replace the old query? [y/n]")
            except NameError:
                resp = raw_input("Please enter response again [y/n]")
            if resp == 'y':
                count = 0

    if count == 0:
        # mock raw for testing
        if mine == 'mock':
            raw = {'queries': {'query1': 1, 'query2': 2, 'query3': 3}}
        else:
            link = dict["instance"]["url"] + "/service/user/queries?" + \
                paramName + "=" + \
                req.pathname2url(value) + "&token=" + token
            requests.put(link)
            r = requests.get(link)
            raw = json.loads(r.text)
        flag = 0
        for key in raw['queries'].keys():
            if key == root.attrib['name']:
                flag = 1
        if flag == 0:
            print("Note: name should contain no special symbol\
            and should be defined first")
            return "Incorrect format"
        else:
            return root.attrib['name'] + " is posted"

    else:
        print("Use a query name other than " + root.attrib['name'])
