#!/usr/bin/env python

# Parser for the Named Binary Tag format as specified by Notch:
# http://web.archive.org/web/20110723210920/http://www.minecraft.net/docs/NBT.txt

import argparse
import struct
import gzip
import os
import json

# == Command line options ==

parser = argparse.ArgumentParser(
    description='Convert NBT files to JSON',
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument('files', nargs='*', metavar='FILE',
                    help='Specifies files to be processed.')

args = parser.parse_args()

if len(args.files) < 1:
    exit("Please specify at least one file!")



# == The parsing codes ==

# Enum containing all known Tag-types.
class Tag:
    END = 0
    BYTE = 1
    SHORT = 2
    INT = 3
    LONG = 4
    FLOAT = 5
    DOUBLE = 6
    BYTE_ARRAY = 7
    STRING = 8
    LIST = 9
    COMPOUND = 10


def read_tag_start(f, assume_unnamed):
    tag_type = f.read(1)

    if len(tag_type) < 1:
        return { 'type': Tag.END, 'name_length': 0 }
    else:
        tag_type = struct.unpack('>B', tag_type)[0]

    if assume_unnamed or tag_type == Tag.END:
        return { 'type': tag_type, 'name_length': 0 }

    name_length = struct.unpack('>H', f.read(2))[0]
    return { 'type': tag_type, 'name_length': name_length }




def read_tag_name(f, tag):
    if(tag['name_length'] < 1):
        return ''

    return f.read(tag['name_length'])



# -------------------------
# Begin: Tag type functions
# Note that these functions do not read a tag's header, but only its payload!
# -------------------------

# String tag format:
#
# TAG_Short length
# <"length" bytes of ASCII characters>
#
def read_tag_type_string(f):
    length = struct.unpack('>H', f.read(2))[0]
    return f.read(length)


# List tag format:
#
# TAG_Byte tag_id
# TAG_Short length
# <"length" unnamed tags of type "tag_id">
#
def read_tag_type_list(f):
    tag_id = tag_functions[Tag.BYTE](f)
    length = tag_functions[Tag.INT](f)

    list = [ ]
    for i in range(0, length):
        list.append(tag_functions[tag_id](f))

    return list


# Byte array format:
#
# TAG_Int length
# <"length" bytes>
#
def read_tag_type_byte_array(f):
    length = tag_functions[Tag.INT](f)

    for i in range(0, length):
        list.append(tag_functions[Tag.BYTE](f))

    return list


# Compound tag format: named tags until a Tag_END is found, i.e.:
#
# <named_tag_1..named_tag_N>
# TAG_end
#
def read_tag_type_compound(f, assume_unnamed=False):
    current = { }

    while(True):
        tag = read_tag_start(f, assume_unnamed)
        name = read_tag_name(f, tag)

        if tag['type'] == Tag.COMPOUND:
            current[name] = tag_functions[tag['type']](f)
        elif tag['type'] == Tag.END:
            break
        else:
            current[name] = tag_functions[tag['type']](f)

    return current


tag_functions = {
    Tag.END: lambda f: struct.unpack('>B', f.read(1))[0],
    Tag.BYTE: lambda f: struct.unpack('>B', f.read(1))[0],
    Tag.SHORT: lambda f: struct.unpack('>h', f.read(2))[0],
    Tag.INT: lambda f: struct.unpack('>i', f.read(4))[0],
    Tag.LONG: lambda f: struct.unpack('>q', f.read(8))[0],
    Tag.FLOAT: lambda f: struct.unpack('>f', f.read(4))[0],
    Tag.DOUBLE: lambda f: struct.unpack('>d', f.read(8))[0],
    Tag.BYTE_ARRAY: read_tag_type_byte_array,
    Tag.STRING: read_tag_type_string,
    Tag.LIST: read_tag_type_list,
    Tag.COMPOUND: read_tag_type_compound
}


# -------------------------
# End: Tag type functions
# -------------------------


f = gzip.GzipFile(args.files[0], 'rb')

x = tag_functions[Tag.COMPOUND](f)
print json.JSONEncoder().encode(x)





