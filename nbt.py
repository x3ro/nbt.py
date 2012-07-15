#!/usr/bin/env python

"""
Parser for the Named Binary Tag format as specified
[by Notch](http://web.archive.org/web/20110723210920/http://www.minecraft.net/docs/NBT.txt).

Currently only decoding is supported, encoding may be added if there is demand for it.

The GitHub repository (and downloads) can be found [here](https://github.com/x3ro/nbt.py).
"""

import argparse
import struct
import gzip
import os
import json



# == Command line options ==

parser = argparse.ArgumentParser(
    description='Convert NBT file to JSON',
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument('files', nargs=1, metavar='FILE',
                    help='Specifies file to be processed.')

args = parser.parse_args()

if len(args.files) < 1:
    exit("Please specify at least one file!")



# == Necessary information for the parser ==

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


# == Generic parsing functions ==

def read_tag_start(f, assume_unnamed):
    """
    Parses a tag start (i.e. the beginning of a tag).

    * `f` -- The file object from which the tag should be read
    * `assume_unnamed` -- This flag should be set if we know that the tag which we are
        about to read is unnamed (see specs for more information)
    """

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
    """
    Get a tag's name from the file currently being read.

    * `f` -- The file being read
    * `tag` -- Tag information as extracted by `#read_tag_start
    """

    if(tag['name_length'] < 1):
        return ''

    return f.read(tag['name_length'])



# == Tag type related functions ==

# Note that these functions do not read a tag's header, but only its payload! The tag header
# is read by `#read_tag_start`.



def read_tag_type_string(f):
    """
    Expected string tag format:

        TAG_Short length
        <"length" bytes of ASCII characters>
    """
    length = struct.unpack('>H', f.read(2))[0]
    return f.read(length)



def read_tag_type_list(f):
    """
    Expected list tag format:

        TAG_Byte tag_id
        TAG_Short length
        <"length" unnamed tags of type "tag_id">
    """

    tag_id = tag_functions[Tag.BYTE](f)
    length = tag_functions[Tag.INT](f)

    list = [ ]
    for i in range(0, length):
        list.append(tag_functions[tag_id](f))

    return list



def read_tag_type_byte_array(f):
    """
    Expected byte array format:

        TAG_Int length
        <"length" bytes>
    """

    length = tag_functions[Tag.INT](f)

    list = [ ]
    for i in range(0, length):
        list.append(tag_functions[Tag.BYTE](f))

    return list



def read_tag_type_compound(f, assume_unnamed=False):
    """
    Expected compound tag format: a number of named tags until a Tag_END is found, i.e.:

        <named_tag_1..named_tag_N>
        TAG_end
    """

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


# === Tag functions object ===

# This object contains functions to parse all known tag types, accessible by `tag id`.
# If you're not familiar with this idiom: it is used in a similar fashion to `switch`-statements
# in other languages ([Stackoverflow](http://stackoverflow.com/questions/374239/why-doesnt-python-have-a-switch-statement))

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


# ---

# ==== Invoke the parser ====

f = gzip.GzipFile(args.files[0], 'rb')
x = tag_functions[Tag.COMPOUND](f)



# ==== Print the resulting JSON-string to stdout ====
print json.JSONEncoder().encode(x)





