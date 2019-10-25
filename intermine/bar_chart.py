from lxml import etree
import json
try:
    import urllib.request as req
except ImportError:
    import urllib as req

from intermine.webservice import Service
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def save_mine_and_token(m, t):
    """
    A function to access an account from a particular mine
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>b.save_mine_and_token("humanmine","<enter token>")
        <now you can access account linked to the token>
    """
    global mine
    global token
    mine = m
    token = t
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


def plot_go_vs_p(list_name):
    """
    A function to plot GO Term vs P-value with label of gene count on each bar
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>b.plot_go_vs_p("PL_obesityMonogen_ORahilly09")

    """
    link = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(link)

    dict = json.loads(r.text)
    url = dict["instance"]["url"]
    service = Service(url)

    lm = service.list_manager()
    store = lm.get_list(name=list_name)
    r = store.calculate_enrichment(widget="go_enrichment_for_gene")

    gene_count = []
    identifier = []
    p_value = []
    object_count = 0
    for i in r:
        if object_count < 5:
            gene_count.append(i.matches)
            identifier.append(i.identifier)
            p_value.append(i.p_value)
            object_count = object_count + 1
        else:
            if object_count >= 5:
                break
    y = pd.Series(p_value)
    x = identifier
    # Plot the figure.

    ax = y.plot(kind='bar')
    ax.set_title('GO Term vs p-value (Label: Gene count)')
    ax.set_xlabel('GO Term')
    ax.set_ylabel('p_value')
    ax.set_xticklabels(x, rotation='horizontal')

    def autolabel(rects, ax):
        i = 0
        for rect in rects:
            x = rect.get_x() + rect.get_width() / 2.
            y = rect.get_height()
            ax.annotate(gene_count[i], (x, y),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center',
                        va='bottom')
            i = i + 1

    autolabel(ax.patches, ax)

    ax.margins(y=0.1)
    plt.show()


def plot_go_vs_count(list_name):
    """
    A function to plot GO Term vs gene count with label of annotation
    on each bar
    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>b.plot_go_vs_count("PL_obesityMonogen_ORahilly09")

    """
    link = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(link)

    dict = json.loads(r.text)
    url = dict["instance"]["url"]
    service = Service(url)

    lm = service.list_manager()
    store = lm.get_list(name=list_name)
    r = store.calculate_enrichment(widget="go_enrichment_for_gene")

    gene_count = []
    identifier = []
    p_value = []
    annotation_count = []
    object_count = 0
    for i in r:
        if object_count < 5:
            gene_count.append(i.matches)
            identifier.append(i.identifier)
            p_value.append(i.p_value)
            annotation_count.append(i.populationAnnotationCount)
            object_count = object_count + 1
        else:
            if object_count >= 5:
                break

    y = pd.Series(gene_count)
    x = identifier

    # Plot the figure.

    ax = y.plot(kind='bar')
    ax.set_title('GO Term vs Count (Label: Annotation)')
    ax.set_xlabel('GO Term')
    ax.set_ylabel('Number of Genes')
    ax.set_xticklabels(x, rotation='horizontal')

    def autolabel(rects, ax):
        i = 0
        for rect in rects:
            x = rect.get_x() + rect.get_width() / 2.
            y = rect.get_height()
            ax.annotate(annotation_count[i], (x, y),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center',
                        va='bottom')
            i = i + 1

    autolabel(ax.patches, ax)
    ax.margins(y=0.1)
    plt.show()


def get_query(xml):
    """
    A function to retrieve the query in list format from xml
    ================================================

    """
    link = "http://registry.intermine.org/service/instances/" + mine
    r = requests.get(link)
    dict = json.loads(r.text)
    link = dict["instance"]["url"] + "/service/query/results?query=" + \
        req.pathname2url(xml)
    r = requests.get(link)
    list = (r.text).split('\n')
    for i in range(0, len(list) - 1):
        list[i] = list[i].split('\t')
    return (list)


def query_to_barchart_log(xml, resp):
    """
    A function to plot a query from its xml
    NOTE: first argument:
            The second column of query is x-axis
            The third column of query in y-axis
            The first column of query is the gene
          second argument:
          only if 'true' convert third column to its log values

    ================================================
    example:

        >>>from intermine import query_manager as qm
        >>>b.query_to_barchart_log(<xml>, 'true')
        <plots the second column vs log(third column)>

    """
    list = get_query(xml)
    root = etree.fromstring(xml)
    store = root.attrib['view']
    store = store.split(' ')
    x_val = []
    y_val = []
    for i in range(0, len(list) - 1):
        x_val.append(list[i][1])
        y_val.append(float(list[i][2]))

    if resp == 'true':
        y_val = np.log(y_val)
        y_val = np.round_(y_val, 2)

    y = pd.Series(y_val)
    x = pd.Series(x_val)

    ax = y.plot(kind='bar')
    ax.set_title(list[0][0])
    ax.set_xlabel(l[1])
    if resp == 'true':
        ax.set_ylabel('log(' + l[2] + ')')
    else:
        ax.set_ylabel(l[2])
    ax.set_xticklabels(x, rotation='vertical')

    def autolabel(rects, ax):
        i = 0
        for rect in rects:
            x = rect.get_x() + rect.get_width() / 2.
            y = rect.get_height()
            ax.annotate(y_val[i], (x, y),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center',
                        va='bottom')
            i = i + 1

    autolabel(ax.patches, ax)

    ax.margins(y=0.1)
    plt.show()
