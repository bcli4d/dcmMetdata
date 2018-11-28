# -*- coding: utf-8 -*-
"""
Perform some dcm file processing tasks
"""
from __future__ import print_function

import os, sys
from os.path import join
import pydicom


# Build a list of tag names
def loadTagNames(args):
    with open(args.tags) as f:
        tagNames = f.read().splitlines()
    tagNames.sort()
    return tagNames


# Output tag names as the first row of the table
def outputFieldNames(args, tagNames):
    print("{}\t{}".format('ZipFileName', 'DCMFileName'), end="")
    for name in tagNames:
        print("\t{}".format(name), end="")
    print("")


# Remove cr/lf from a string
def remove_crlf(t):
    t = t.replace(chr(10), '')
    t = t.replace(chr(13), '')
    return t


def clean_PatientAge(t):
    t = t.lstrip('0')
    t = t.rstrip('yY')
    return t


def clean_PatientSex(t):
    if t == 'U':
        t = ''
    elif t == 'Masculino':
        t = 'M'
    elif t == 'Feminino':
        t = 'F'
    return t


def clean_PatientWeight(t):
    if t != '' and float(t) == 0.0:
        t = ''
    return t


# Process a single dicom file.
def collectDicomTags(args, tagNames, dcmroot, dcmfile, zip_file):
    tcia_path = "gs://isb-cgc-open/TCIA/images"
    if args.verbosity >= 3:
        print("Processing file: ", join(dcmroot, dcmfile), file=sys.stderr)
    # Output the zip and dcm file paths
    print("{}/{}\t{}".format(tcia_path, zip_file, dcmfile), end="")
    dataset = pydicom.read_file(join(dcmroot, dcmfile), stop_before_pixels=True)
    # Output the value of each tag in tagNames
    for tagName in tagNames:
        if tagName in dataset:
            dataElement = dataset.data_element(tagName)
            tagValue = dataElement.value
            if dataElement.VR == 'LT':
                tagValue = remove_crlf(tagValue)
            elif tagName == "PatientAge":
                tagValue = clean_PatientAge(tagValue)
            elif tagName == "PatientSex":
                tagValue = clean_PatientSex(tagValue)
            elif tagName == "PatientWeight":
                tagValue = clean_PatientWeight(tagValue)
            print("\t{}".format(tagValue), end="")
        else:
            print("\t".format(), end="")
    print("")


if __name__ == '__main__':
    pass
