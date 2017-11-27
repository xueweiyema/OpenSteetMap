import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import codecs
import json

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SAMPLE_FILE = "sample.osm"

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