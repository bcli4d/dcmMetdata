from __future__ import print_function
import os, sys
import json


# Build a list of keywords
def loadKeywords(args):
    if os.path.exists(args.keywords):
        with open(args.keywords) as f:
            strings = f.read().splitlines()
            keywords = json.loads(strings[0])
            print("keywords {}".format(keywords))
    else:
        keywords = {}
    return keywords

# Build a list of ignored keywords
def loadIgnoredKeywords(args):
    if os.path.exists(args.ignoredKeywords):
        with open(args.ignoredKeywords) as f:
            strings = f.read().splitlines()
            ignoredKeywords = json.loads(strings[0])
            print("ignoredKeywords {}".format(ignoredKeywords))
    else:
        ignoredKeywords = {}
    return ignoredKeywords


# Load existing metadata
def loadMetadata(args):
    if os.path.exists(args.metadata):
        with open(args.metadata) as f:
            f.seek(0, 2)  # Go to the end of file
            if f.tell() == 0:  # Check if file is empty
                metadata = {}
            else:
                f.seek(0)
                strings = f.read()
                metadata = json.loads(strings)
    else:
        metadata = []
    return metadata

# Get the series we've already processed
def loadDones(args):
    if os.path.exists(args.dones):
        with open(args.dones) as f:
            strings = f.read().splitlines()
            dones = set(strings)
            #print("dones {}".format(dones))
    else:
        dones = set()
    return dones



# Build a list of ignored element types
def loadIgnoredTypes(args):
    with open(args.ignoredTypes) as f:
        strings = f.read().splitlines()
        ignoredTypes = set(strings)
        print("Ignored strings: {}".format(ignoredTypes))
    return ignoredTypes


# Build a list of files to process
def loadZips(args):
    with open(args.zips) as f:
        strings = f.read().splitlines()
        zips = sorted(list(strings))
        #print("zips: {}".format(zips))
    return zips

