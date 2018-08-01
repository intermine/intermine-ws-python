import requests
import json
from intermine.webservice import Service
"""
Functions for making use of registry data
================================================

"""


def getInfo(mine):
    """
    A function to get information about a mine
    ================================================
    example:

        >>> from intermine import registry
        >>> registry.getInfo('flymine')
        Description:  An integrated database for Drosophila genomics
        URL: http://www.flymine.org/flymine
        API Version: 25
        Release Version: 45.1 2017 August
        InterMine Version: 1.8.5
        Organisms:
        D. melanogaster
        Neighbours:
        MODs

    """
    if mine == 'mock':
        dict = {'instance': {'organisms': ['xxx'], 'url': 'xxx', 'release_version': 'xxx', 'api_version': 'xxx', 'description': 'xxx', 'neighbours': ['xxx'], 'intermine_version': 'xxx'}}
    else:

        link = "http://registry.intermine.org/service/instances/" + mine

        r = requests.get(link)

        dict = json.loads(r.text)

    try:
        print("Description: " + dict["instance"]["description"])
        print("URL: " + dict["instance"]["url"])
        print("API Version: " + dict["instance"]["api_version"])
        print("Release Version: " + dict["instance"]["release_version"])
        print("InterMine Version: " + dict["instance"]["intermine_version"])
        print("Organisms: "),
        for organism in dict["instance"]["organisms"]:
            print(organism),
        print("Neighbours: "),
        for neighbour in dict["instance"]["neighbours"]:
            print(neighbour),
        return None
    except KeyError:
        return "No such mine available"



def getData(mine):
    """
    A function to get datasets corresponding to a mine
    ================================================
    example:

        >>> from intermine import registry
        >>> registry.getData('flymine')
        Name: Affymetrix array: Drosophila1
        Name: Affymetrix array: Drosophila2
        Name: Affymetrix array: GeneChip Drosophila Genome 2.0 Array
        Name: Affymetrix array: GeneChip Drosophila Genome Array
        Name: Anoph-Expr data set
        Name: BDGP cDNA clone data set.....


    """
    x = "http://registry.intermine.org/service/instances/" + mine
    try:
        r = requests.get(x)
        dict = json.loads(r.text)
        link = dict["instance"]["url"]
        service = Service(link)
        query = service.new_query("DataSet")
        query.add_view("name", "url")
        list = []

        for row in query.rows():
            try:
                list.append(row["name"])

            except KeyError:
                print("No info available")
        list.sort()
        for i in range(len(list)):
            print("Name: " + list[i])
        return None
    except KeyError:
        return "No such mine available"


def getMines(organism):
    """
    A function to get mines containing the organism
    ================================================
    example:

        >>> from intermine import registry
        >>> registry.getMines('D. melanogaster')
        FlyMine
        FlyMine Beta
        XenMine

    """
    if organism == 'mock':
        dict = {'instances':[{"organisms":["mock"],"name":"mock"}]}
    else:
        link = "http://registry.intermine.org/service/instances"

        r = requests.get(link)

        dict = json.loads(r.text)
    count = 0
    for i in range(len(dict["instances"])):
        for j in range(len(dict["instances"][i]["organisms"])):
            if dict["instances"][i]["organisms"][j] == organism:
                print(dict["instances"][i]["name"])
                count = count+1
            elif dict["instances"][i]["organisms"][j] == " " + organism:
                print(dict["instances"][i]["name"])
                count = count+1
    if(count == 0):
        return "No such mine available"
    else:
        return None
