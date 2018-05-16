import requests
import yaml
import json
def get_all_query_names():

    x = "http://registry.intermine.org/service/instances/" + mine
    r=requests.get(x)
    dict=yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries?token=" + token
    r=requests.get(link)
    dict=yaml.load(r.text)

    for key in dict['queries'].keys():
        print(key)

def get_query():

    name = input("Enter the name of query: ")
    x = "http://registry.intermine.org/service/instances/" + mine
    r=requests.get(x)
    dict=yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries?token=" + token
    r=requests.get(link)
    dict=yaml.load(r.text)
    for key in dict['queries'].keys():
        if(name==key):
            print("Coloumns:")
            for i in range(len(dict['queries'][name]['select'])):
                print(dict['queries'][name]['select'][i])
            print("Type of model: " + dict['queries'][name]['model']['name'])


def delete_query():

    name = input("Enter the name of query to be deleted: ")
    x = "http://registry.intermine.org/service/instances/" + mine
    r=requests.get(x)
    dict=yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries/" + name + "?token=" + token
    requests.delete(link)

def xml_to_link(xml):
    count=0
    link=[]
    for i in xml:
        if (i=="<"):
            link.append('%3C')
        elif (i==">"):
            link.append('%3E')
        elif (i=="="):
            link.append('%3D')
        elif (i==" "):
            link.append('%20')
        elif (i=='"'):
            link.append('%22')
        elif (i=="/"):
            link.append('%2F')
        else:
            link.append(i)
    link = "".join(link)
    return link

def post_query():

    xml = input("Enter the xml(find it using the command `yourquery.to_xml()`): ")
    x = "http://registry.intermine.org/service/instances/" + mine
    r=requests.get(x)
    dict=yaml.load(r.text)
    link = dict["instance"]["url"] + "/service/user/queries?xml=" + xml_to_link(xml) + "&token=" + token
    requests.put(link)


token = input("Enter the api token: ")
mine = input("Enter the mine name: ")
