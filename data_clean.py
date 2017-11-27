import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import codecs
import json

from data_audit import update_name
mapping = {"Rd":"Road"}

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SAMPLE_FILE = "sample.osm"



#  wrangle the data and transform the shape of the data

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        #build type
        node['type'] = element.tag
        #build created
        created = {}
        pos = []
        address = {}
        node_refs = []
        for elem in element.iter():
            for k in elem.attrib.keys():
                if k in CREATED:
                    created[k] = elem.get(k)
                #buid pos
                elif k == 'lat':
                    pos.append(float(elem.get(k)))
                elif k == 'lon':
                    pos.append(float(elem.get(k)))
                #skip problem
                elif problemchars.search(k):
                    continue
                #build address
                elif k == 'k':
                    l = elem.get(k).split(':')
                    if l[0] == 'addr':
                        if len(l) < 3:
                            address[l[1]] =update_name(elem.get('v'),mapping)
                #build with colon like  or k="xx:xxx" v="xxxx"
                    if len(l) > 1:
                        d = {}
                        len(l)
                        d[l[1]] = elem.get('v')
                        node[l[0]] = d
                    if len(l) == 1:
                        node[l[0]] = elem.get('v')
                else:
                    node[k] = elem.get(k)
                #build node_refs
                if element.tag == 'way' and elem.tag == "nd":
                    node_refs.append(elem.get('ref'))
        node['created'] = created
        pos.reverse()
        node['pos'] = pos
        if address <> {}:
            node['address'] = address
        if node_refs <> []:
            node['node_refs'] = node_refs
        return node
    else:
        return None


def process_map_data(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

data=process_map_data(SAMPLE_FILE,True)
pprint.pprint(data[0])
pprint.pprint(data[-1])


# import json into mongodb

