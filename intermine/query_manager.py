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

    for key in dict['queries'].keys():
        print(key)

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
            count = count+1
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
    link = dict["instance"]["url"] + "/service/user/queries/" + name +\
     "?token=" + token
    requests.delete(link)

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
    link = dict["instance"]["url"] + "/service/user/queries?xml=" + \
    xml_to_link(xml) + "&token=" + token
    requests.put(link)


token = input("Enter the api token: ")
mine = input("Enter the mine name: ")
