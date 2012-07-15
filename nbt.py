#!/usr/bin/env python

# Parser for the Named Binary Tag format as specified by Notch:
# http://web.archive.org/web/20110723210920/http://www.minecraft.net/docs/NBT.txt

import argparse
import struct
import gzip
import os
import pprint
import json

parser = argparse.ArgumentParser(
    description='Convert NBT files to JSON',
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument('files', nargs='*', metavar='FILE',
                    help='Specifies files to be processed.')

args = parser.parse_args()

if len(args.files) < 1:
    exit("Please specify at least one file!")



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


def read_tag_start_old(file, assume_unnamed):
    bytes = file.read(3)

    print "length: " + str(len(bytes))
    if len(bytes) == 0:
        return { 'type': Tag.END, 'name_length': 0 }
    if len(bytes) == 1:
        # We reached the end of the file, and therefore return a Tag.END if the byte is "0"
        byte = struct.unpack('>B', bytes)[0]
        if byte != 0:
            raise Exception("Expected Tag.END at the end of the file, found " + str(byte))

        return { 'type': Tag.END, 'name_length': 0 }


    field_names = ('type', 'name_length')
    data = struct.unpack('>BH', bytes)

    tag = dict(zip(field_names, data))

    if tag['type'] == Tag.END or assume_unnamed:
        f.seek(-2, os.SEEK_CUR) # The END tag has only a single byte, the following two
                                # are already part of the next TAG. Therefore, rewind by 2
        return { 'type': Tag.END, 'name_length': 0 }
    else:
        return tag


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
# -------------------------

def read_tag_type_string(f):
    length = struct.unpack('>H', f.read(2))[0]
    return f.read(length)

def read_tag_type_list(f):
    tag_id = tag_functions[Tag.BYTE](f)
    length = tag_functions[Tag.INT](f)

    list = [ ]
    for i in range(0, length):
        list.append(tag_functions[tag_id](f))

    return list


def read_tag_type_byte_array(f):
    length = tag_functions[Tag.INT](f)

    for i in range(0, length):
        list.append(tag_functions[Tag.BYTE](f))

    return list

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





