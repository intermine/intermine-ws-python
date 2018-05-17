import requests
import yaml
import json

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
    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries?token=" + token
    r = requests.get(link)
    dict = yaml.load(r.text)
    count = 0
    for key in dict['queries'].keys():
        count = count + 1
        print(key)

    if(count == 0):
        print("No saved queries")

def get_query(name):
    """
    A function that returns the columns that a given query constitutes of
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.get_query('queryName')
        <returns information about the query whose name is 'queryName'>

    """
    x = "http://registry.intermine.org/service/instances/" + mine

    r = requests.get(x)
    dict = yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries?token=" + token

    r = requests.get(link)
    dict = yaml.load(r.text)
    count = 0
    for key in dict['queries'].keys():
        if(name == key):
            count = count + 1
            print("Columns:")
            for i in range(len(dict['queries'][name]['select'])):
                print(dict['queries'][name]['select'][i])
    if(count == 0):
        print("No such query available")


def delete_query(name):
    """
    A function that deletes a given query
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>qm.delete_query('queryName')
        <deletes the query whose name is 'queryName' from user's account>

    """
    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = yaml.load(r.text)

    y = dict["instance"]["url"] + "/service/user/queries?token=" + token
    r = requests.get(y)
    z = yaml.load(r.text)
    count = 0
    for key in z['queries'].keys():
        if (key == name):
            count = count + 1
    if(count == 0):
        print("No such query available")

    else:
        link = dict["instance"]["url"] + "/service/user/queries/" + name +\
         "?token=" + token
        requests.delete(link)

    '''
    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries/" + name +\
     "?token=" + token
    requests.delete(link)
    '''

def xml_to_link(xml):
    """
    Converts xml to the link we desire while posting queries
    ================================================
    example:
        >>>xml_to_link('<query></query>')
        '%3Cquery%3E%3C%2Fquery%3E'
    """
    count = 0
    link = []
    for i in xml:
        if (i == "<"):
            link.append('%3C')
        elif (i == ">"):
            link.append('%3E')
        elif (i == "="):
            link.append('%3D')
        elif (i == " "):
            link.append('%20')
        elif (i == '"'):
            link.append('%22')
        elif (i == "/"):
            link.append('%2F')
        else:
            link.append(i)
    link = "".join(link)
    return link

def post_query(xml):
    """
    A function to post a query(in the form of string containg xml) to a user account
    ================================================
    example:

        >>>qm.post_query('<query name="" model="genomic" view="Gene.length Gene.symbol" \
           longDescription="" sortOrder="Gene.length asc"></query>')
    """
    x = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(x)
    dict = yaml.load(r.text)
    name = []
    for i in range(13,len(xml)):
        if(xml[i]!='"'):
            name.append(xml[i])
        else:
            break
    name = "".join(name)
    link = dict["instance"]["url"] + "/service/user/queries?token=" + token
    r = requests.get(link)
    raw = yaml.load(r.text)
    count = 0
    for key in raw['queries'].keys():
        if(key == name):
            count = count + 1
            print("Use another query name")
            resp = input("Or do you want to replace the old query? [y/n]")
            if(resp == 'y'):
                count = 0

    if(count == 0):

        link = dict["instance"]["url"] + "/service/user/queries?xml=" + \
        xml_to_link(xml) + "&token=" + token
        requests.put(link)
        flag = 0
        r = requests.get(link)
        raw = yaml.load(r.text)
        for key in raw['queries'].keys():
            if(key == name):
                flag = 1
        if(flag == 0):
            print("Incorrect xml (Note: name should contain no special symbols)")

mine = input("Enter the mine name: ")
l = "http://registry.intermine.org/service/instances/" + mine
try:
    m = requests.get(l)
    d = yaml.load(m.text)
    n = d["instance"]["url"]
    token = input("Enter the api token: ")
    n = d["instance"]["url"] + "/service/user/queries?token=" + token
    try:
        o = requests.get(n)
        d = yaml.load(o.text)
        p = d['queries'].keys()
    except:
        print ("Invalid token")
except:
    print ("Invalid mine name")
