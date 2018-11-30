# -*- coding: utf-8 -*-
"""
Walk a directory tree starting at the --dir paramenter. Expand each zip
file and Build a TSV table of tag from all extracted dcm files. Specific
tags to collect are listed in tags file
Output result to standard out.
"""
from __future__ import print_function

#from process_a_file import loadTagNames, outputFieldNames, collectDicomTags
import os, sys
import argparse
import zipfile
from os.path import join
import pydicom
import time
import json
import subprocess
import shutil
from cleanMetadata import cleanValue
from initState import *

zipFileCount = 0
keywords = set()
ignoredKeywords = set()
ignoredTypes = set()
zips = set()
series = []


# Record in file of all keywords encountered
def writeKeywords(args, keywords):
    with open(args.keywords, 'w') as f:
        f.write(json.dumps(keywords).encode())

# Add every keyword seen to set of keywords
def addKeyword(args,keyword, keywords):
    if not keyword in keywords:
        keywords[keyword] = 1
    else:
        keywords[keyword] += 1
    return keywords

# Record in file of keywords to be ignored
def writeIgnoredKeywords(args, ignoreKeywords):
    with open(args.ignoredKeywords, 'w') as f:
        f.write(json.dumps(ignoredKeywords).encode())

# Found another keyword to ignore, typically because instances in a series may have different values for this element
def addIgnoredKeyword(args,ignoredKeyword, ignoredKeywords):
    #    keywords.remove(keyword)
    if not ignoredKeyword in ignoredKeywords:
        ignoredKeywords[ignoredKeyword] = 1
    else:
        ignoredKeywords[ignoredKeyword] += 1
    return ignoredKeywords

# Append metadata collected for a series to the metadata file
def appendMetadata(args, zip, dataset):
    #Add zip file name to the dataset
    dataset['ZipFileName'] = zip
    #Create a one element dictionary
#    metadataset = {}
#    metadataset[zip]=dataset
    with open(args.metadata, 'ab+') as f:
        f.seek(0, 2)  # Go to the end of file
        if f.tell() == 0:  # Check if file is empty
            f.write('['.encode())
            #f.write(json.dumps(metadataset).encode()[1:-1])  # If empty, write an array
            f.write(json.dumps(dataset).encode())  # If empty, write an array
        else:
            f.seek(-1, 2)
            f.truncate()  # Remove the last character, open the array
            f.write(' , '.encode())
            #f.write(json.dumps(metadataset).encode()[1:-1])  # Dump the dictionary
            f.write(json.dumps(dataset).encode())  # Dump the dictionary
        f.write(']'.encode())  # Close the array

# Add name of processed file
def appendDones(args, zip):
    with open(args.dones, 'a') as f:
        f.write("{}\n".format(zip))


# Add the data of am element to the dataset dictionary after cleaning
def addToDataset(args, dataset, dataElement, keyword):
    if not dataElement.VR in ignoredTypes:
        cleanedValue = cleanValue(args, dataElement)
        dataset[keyword] = cleanedValue
#What else?

# Copy a zip file for some series from GCA and extract dicoms
def getZipFromGCS(args, zip):
    zipfileName = os.path.join(args.scratch,'dcm.zip')
    dicomDirectory = os.path.join(args.scratch,'dicoms')

    subprocess.call(['gsutil', 'cp', zip, zipfileName])

    # Open the file and extract the .dcm files to scratch directory
    zf = zipfile.ZipFile(zipfileName)
    zf.extractall(dicomDirectory)

    return dicomDirectory

# Remove zip file and extracted .dcms of a series after processing
def cleanupSeries(args):
    zipfileName = os.path.join(args.scratch,'dcm.zip')
    dicomDirectory = os.path.join(args.scratch,'dicoms')

    shutil.rmtree(dicomDirectory)
    os.remove(zipfileName)


# Create a dictionary of metadata for a single series
def processSeries(args, zip, keywords, ignoredKeywords):
    zipFilesPath = getZipFromGCS(args, zip)

    dicoms = os.listdir(zipFilesPath)
    dicoms.sort()

    # We need to determine which values are unique across all the instances of a series.
    # We do this by opening the first and last instances and seeing which VRs are
    # not identical. Those tags are added to the notUniqueTags file.
    # Series for which there is just a single instance are treated as if all tags are
    # unique.
    firstDataset = pydicom.read_file(os.path.join(zipFilesPath,dicoms[0]))
    lastDataset = pydicom.read_file(os.path.join(zipFilesPath,dicoms[-1]))
    dataset = {}

    for dataElement in firstDataset:
        try:
            keyword = pydicom.datadict.dictionary_keyword(dataElement.tag)
        except:
            if args.verbosity > 2:
                print("Ignoring keyword {}; not in dictionary".format(dataElement.tag))
        else:
            keywords = addKeyword(args, keyword, keywords)
            if args.verbosity > 2:
                print("Adding keyword {}".format(keyword))
            addToDataset(args, dataset, dataElement, keyword)
            try:
                if dataElement.value != lastDataset[dataElement.tag].value:
                    ignoredKeywords = addIgnoredKeyword(args, keyword, ignoredKeywords)
                    if args.verbosity > 2:
                        print("New ignored keyword {}".format(keyword))
            except:
                print("New ignored keyword {}; not in all instances".format(keyword))
                return
    appendMetadata(args, zip, dataset)
    writeKeywords(args, keywords)
    writeIgnoredKeywords(args, ignoredKeywords)
    appendDones(args, zip)
    cleanupSeries(args)


# Extract metadata from specified set of files in GCS
def scanZips(args, keywords, ignoredKeywords):

    for zip in zips:
        global zipFileCount
        if not zip in series:
            processSeries(args, zip, keywords, ignoredKeywords)
            zipFileCount += 1
        else:
            if args.verbosity > 1:
                print("Previously done {}".format(zip))


    return zipFileCount

def setup(args):
    keywords = loadKeywords(args)
    ignoredKeywords = loadIgnoredKeywords(args)
    ignoredTypes = loadIgnoredTypes(args)
    #loadMetadata(args)
    series = loadDones(args)
    zips = loadZips(args)
    return (keywords, ignoredKeywords, ignoredTypes, series, zips)

def parse_args():
    parser = argparse.ArgumentParser(description="Build DICOM image metadata table")
    parser.add_argument("-v", "--verbosity", action="count", default=2, help="increase output verbosity")
    parser.add_argument("-z", "--zips", type=str, help="path to file of zip files in GCS to process",
                        default='./zips.txt')
    parser.add_argument("-k", "--keywords", type=str, help="path to file containing keywords found",
                        default='./keywords.txt')
    parser.add_argument("-i", "--ignoredKeywords", type=str,
                        help="path to file containing keywords that are not to be processed",
                        default='./ignoredKeywords.txt')
    parser.add_argument("-t", "--ignoredTypes", type=str, help="path to file containing element types to be ignored",
                        default='./ignoredTypes.txt')
    parser.add_argument("-m", "--metadata", type=str, help="path to file containing extracted metadata",
                        default='./metadata.json')
    parser.add_argument("-d", "--dones", type=str, help="path to file containing names of processed series",
                        default='./dones.txt')
    parser.add_argument("-s", "--scratch", type=str, help="path to scratch directory",
                        default='.')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    # Initialize work variables from previously generated data in files
    keywords, ignoredKeywords, ignoredTypes, series, zips = setup(args)

    t0 = time.time()
    fileCount = scanZips(args, keywords, ignoredKeywords)
    t1 = time.time()

    if args.verbosity > 0:
        print("{} zip files processed in {} seconds".format(fileCount, t1 - t0),
              file=sys.stderr)
