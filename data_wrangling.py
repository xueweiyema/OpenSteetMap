import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import codecs
import json

OSM_FILE = "sydney_australia.osm"  # Replace this with your osm file
SAMPLE_FILE = "sample.osm"

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

k = 50  # Parameter: take every k-th top level element


def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


#build sample

# with open(SAMPLE_FILE, 'wb') as output:
#     output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
#     output.write('<osm>\n  ')

#     # Write every kth top level element
#     for i, element in enumerate(get_element(OSM_FILE)):
#         if i % k == 0:
#             output.write(ET.tostring(element, encoding='utf-8'))

#     output.write('</osm>')


#find out not only what tags are there, but also how many
def count_tags(filename):
    tags = {}
    for event, elem in ET.iterparse(filename):
        if tags.has_key(elem.tag):
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
    return tags


# tags = count_tags(SAMPLE_FILE)
# pprint.pprint(tags)

# check the "k" value for each "<tag>" and see if there are any potential problems


def key_type(element, keys):
    if element.tag == "tag":
        for tag in element.iter('tag'):
            if lower.search(element.attrib['k']):
                keys['lower'] += 1
            elif lower_colon.search(element.attrib['k']):
                keys['lower_colon'] += 1
            elif problemchars.search(element.attrib['k']):
                keys['problemchars'] += 1
            else:
                keys['other'] += 1
    return keys


def process_map_tags(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    return keys


# keys = process_map_tags(SAMPLE_FILE)
# pprint.pprint(keys)

#  find out how many unique users


def get_user(element):
    return


def process_map_users(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if element.get('uid') <> None:
            users.add(element.get('uid'))
    return users


# users = process_map_users(SAMPLE_FILE)
# pprint.pprint(users)

# actually fix the street name

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = [
    "Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square",
    "Lane", "Road", "Trail", "Parkway", "Commons"
]

# UPDATE THIS VARIABLE
mapping = {"Rd":"Road"}


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start", )):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name, mapping):

    l = name.split(' ')
    if mapping.has_key(l[-1]):
        l[-1] = mapping[l[-1]]
        name = " ".join(l)
    return name


st_types = audit(SAMPLE_FILE)
# pprint.pprint(dict(st_types))
for st_type, ways in st_types.iteritems():
    for name in ways:
        better_name = update_name(name, mapping)
        print better_name 

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

