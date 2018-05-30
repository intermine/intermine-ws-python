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
    Enter the api token: <enter api token from account>
    Enter the mine name: <enter mine name>
"""


def get_all_query_names():
    """
    A function to list all the queries that are saved in a user account
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.get_all_query_names()
        <returns the names of all the saved queries in user account>

    """

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
    for key in dict['queries'].keys():
        count = count + 1
        # prints the names
        print(key)

    if count == 0:
        # if no such query name exists in the account
        print("No saved queries")

    return None


def get_query(name):
    """
    A function that returns the columns that a given query constitutes of
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.get_query('queryName')
        <returns information about the query whose name is 'queryName'>

    """

    # source of the initial request

    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = json.loads(r.text)
    link = dict["instance"]["url"] + "/service/user/queries?token=" + token

    r = requests.get(link)
    dict = json.loads(r.text)
    count = 0
    for key in dict['queries'].keys():
        if name == key:
            count = count + 1
            # prints the columns a query is made of
            print("Columns:")
            for i in range(len(dict['queries'][name]['select'])):
                print(dict['queries'][name]['select'][i])
    if count == 0:
        return "No such query available"
    else:
        return None


def delete_query(name):
    """
    A function that deletes a given query
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.delete_query('queryName')
        <deletes the query whose name is 'queryName' from user's account>

    """

    # source of the initial request
    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = json.loads(r.text)
    # source of the next request
    y = dict["instance"]["url"] + "/service/user/queries?token=" + token
    r = requests.get(y)
    # dictionary form of data
    z = json.loads(r.text)
    count = 0
    for key in z['queries'].keys():
        if key == name:
            count = count + 1
    if count == 0:
        return "No such query available"

    else:
        link = dict["instance"]["url"] + "/service/user/queries/" + name +\
         "?token=" + token
        requests.delete(link)
        return name + " is deleted"

def post_query(xml):
    """
    A function to post a query(in the form of string containing xml)
    to a user account
    ================================================
    example:

        >>>qm.post_query('<query name="" model="genomic" view="Gene.length\
            Gene.symbol" longDescription="" sortOrder="Gene.length asc">\
            </query>')
    Note that the name should be defined first
    """

    # source of the initial request
    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = json.loads(r.text)
    # xml parsing
    root = etree.fromstring(xml)

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

        link = dict["instance"]["url"] + "/service/user/queries?xml=" + \
        req.pathname2url(xml) + "&token=" + token
        requests.put(link)
        flag = 0
        r = requests.get(link)
        raw = json.loads(r.text)
        for key in raw['queries'].keys():
            if key == root.attrib['name']:
                flag = 1
        if flag == 0:
            print("Note: name should contain no special symbol\
            and should be defined first")
            return "Incorrect xml"
        else:
            return root.attrib['name'] + " is posted"

    else:
        return "Use a query name other than " + root.attrib['name']


def save_mine_and_token(m,t):
    global mine
    mine = m
    # source of the request
    src = "http://registry.intermine.org/service/instances/" + mine
    try:
        # tests if mine is valid by checking if object 'obj' exists
        m = requests.get(src)
        data = json.loads(m.text)
        obj = data["instance"]["url"]
        global token
        token = t
        obj = data["instance"]["url"] + "/service/user/queries?token=" + token
        try:
            # tests if token is valid by checking if object 'obj' exists
            o = requests.get(obj)
            data = json.loads(o.text)
            obj = data['queries'].keys()
            # checks the type fo exception
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            return message
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)

        return message
