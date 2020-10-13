import requests
import json
from intermine.webservice import Service
"""
Functions for making use of registry data
================================================

"""


def getVersion(mine):
    """
    A function to return the API version, release version and
    InterMine version numbers
    ================================================
    example:

        >>> from intermine import registry
        >>> registry.getVersion('flymine')
        >>> {'API Version:': '30', 'Release Version:': '48 2019 October',
        'InterMine Version:': '4.1.0'}

    """
    link = "http://registry.intermine.org/service/instances/" + mine
    try:
        r = requests.get(link)
        dict = json.loads(r.text)
        return {
            "API Version:": dict["instance"]["api_version"],
            "Release Version:": dict["instance"]["release_version"],
            "InterMine Version:": dict["instance"]["intermine_version"]
        }
    except KeyError:
        return "No such mine available"


def getInfo(mine):
    """
    A function to get information about a mine
    ================================================
    example:

        >>> from intermine import registry
        >>> registry.getInfo('flymine')
        Description:  An integrated database for Drosophila genomics
        URL: https://www.flymine.org/flymine
        API Version: 25
        Release Version: 45.1 2017 August
        InterMine Version: 1.8.5
        Organisms:
        D. melanogaster
        Neighbours:
        MODs

    """
    link = "http://registry.intermine.org/service/instances/" + mine
    try:
        r = requests.get(link)

        dict = json.loads(r.text)
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


def getMines(organism=None):
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
    link = "http://registry.intermine.org/service/instances"

    r = requests.get(link)
    count = 0
    dict = json.loads(r.text)
    for i in range(len(dict["instances"])):
        if organism is None:
            print(dict["instances"][i]["name"])
            count = count+1
        else:
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
