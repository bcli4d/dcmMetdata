from __future__ import print_function
import pydicom
import os, sys
import json

# Build a list of keywords
def loadKeywords(args):
    with open(args.keywords) as f:
        strings = f.read().splitlines()
        keywords = set(strings)
        print("keywords {}".format(keywords))
    return keywords

# Build a list of ignored keywords
def loadIgnoredKeywords(args):
    with open(args.ignoredKeywords) as f:
        strings = f.read().splitlines()
        ignoredKeywords = set(strings)
        print("ignoredKeywords {}".format(ignoredKeywords))
    return ignoredKeywords


# Load existing metadata
def loadMetadata(args):
    with open(args.metadata) as f:
        f.seek(0, 2)  # Go to the end of file
        if f.tell() == 0:  # Check if file is empty
            metadata = {}
        else:
            f.seek(0)
            strings = f.read()
            metadata = json.loads(strings)
    series = metadata.keys()
    if args.verbosity > 1:
        print("Have metadata for {} series".format(len(series)))
    return series


# Build a list of ignored element types
def loadIgnoredTypes(args):
    with open(args.ignoredTypes) as f:
        strings = f.read().splitlines()
        ignoredTypes = set(strings)
        print("Ignored strings: {}".format(ignoredTypes))
    return ignoredTypes


# Build a list of keywords
def loadZips(args):
    with open(args.zips) as f:
        strings = f.read().splitlines()
        zips = set(strings)
        print("zips: {}".format(zips))
    return zips

def setup(args):
    keywords = loadKeywords(args)
    ignoredKeywords = loadIgnoredKeywords(args)
    ignoredTypes = loadIgnoredTypes(args)
    series = loadMetadata(args)
    zips = loadZips(args)
    return (keywords, ignoredKeywords, ignoredTypes, series, zips)

