# -*- coding: utf-8 -*-
"""
Walk a directory tree starting at the --dir paramenter. Expand each zip
file and Build a TSV table of tag from all extracted dcm files. Specific
tags to collect are listed in tags file
Output result to standard out.
"""
from __future__ import print_function

from process_a_file import loadTagNames, outputFieldNames, collectDicomTags
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
from initState import setup

zipFileCount = 0
keywords = set()
ignoredKeywords = set()
ignoredTypes = set()
zips = set()
series = []


# Record in file of all keywords encountered
def appendKeyword(args, keyword):
    with open(args.keywords, 'a') as f:
        f.write("{}\n".format(keyword))

# Add every keyword seen to set of keywords
def addKeyword(args,keyword):
    if not keyword in keywords:
        keywords.add(keyword)
        appendKeyword(args, keyword)


# Record in file of keywords to be ignored
def appendIgnoredKeyword(args, keyword):
    with open(args.ignoredKeywords, 'a') as f:
        f.write("{}\n".format(keyword))

# Found another keyword to ignore, typically because instances in a series may have different values for this element
def ignoreKeyword(args,keyword):
    #    keywords.remove(keyword)
    if not keyword in ignoredKeywords:
        ignoredKeywords.add(keyword)
        appendIgnoredKeyword(args, keyword)

# Append metadata collected for a series to the metadata file
def appendMetadata(args, zip, dataset):
    metadataset = {}
    metadataset[zip]=dataset
    with open(args.metadata, 'ab+') as f:
        f.seek(0, 2)  # Go to the end of file
        if f.tell() == 0:  # Check if file is empty
            f.write('{'.encode())
            f.write(json.dumps(metadataset).encode()[1:-1])  # If empty, write an array
        else:
            f.seek(-1, 2)
            f.truncate()  # Remove the last character, open the array
            f.write(' , '.encode())
            f.write(json.dumps(metadataset).encode()[1:-1])  # Dump the dictionary
        f.write('}'.encode())  # Close the array

# Add the data of am element to the dataset dictionary after cleaning
def addToDataset(args, dataset, dataElement, keyword):
    if not dataElement.VR in ignoredTypes:
        cleanedValue = cleanValue(dataElement)
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
def processSeries(args, zip):
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
            if not keyword in ignoredKeywords:
                try:
                    if dataElement.value == lastDataset[dataElement.tag].value:
                        addKeyword(args, keyword)
                        addToDataset(args, dataset, dataElement, keyword)
                    else:
                        if args.verbosity > 1:
                            print("New ignored {}".format(keyword))
                        ignoreKeyword(args, keyword)
                except:
                    print("Instances in {} have different schemas".format(zipFileName))
                    return
            else:
                if args.verbosity > 2:
                    print("Ignoring {}".format(keyword))

        except:
            if args.verbosity > 2:
                print("Ignoring tag {}; not in dictionary".format(dataElement.tag))

    appendMetadata(args, zip, dataset)
    cleanupSeries(args)


# Extract metadata from specified set of files in GCS
def scanZips(args):

    for zip in zips:
        global zipFileCount
        if not zip in series:
            processSeries(args, zip)
            zipFileCount += 1
        else:
            if args.verbosity > 1:
                print("Previously done {}".format(zip))


    return zipFileCount

def parse_args():
    parser = argparse.ArgumentParser(description="Build DICOM image metadata table")
    parser.add_argument("-v", "--verbosity", action="count", default=2, help="increase output verbosity")
    parser.add_argument("-z", "--zips", type=str, help="path to file of zip files in GCS to process",
                        default='./zips.txt')
    parser.add_argument("-k", "--keywords", type=str, help="path to file containing keywords found",
                        default='./keywords.txt')
    parser.add_argument("-i", "--ignoredKeywords", type=str,
                        help="path to file containing keywords that are not to be processed",
                        default='./ignoredkeywords.txt')
    parser.add_argument("-t", "--ignoredTypes", type=str, help="path to file containing element types to be ignored",
                        default='./ignoredTypes.txt')
    parser.add_argument("-m", "--metadata", type=str, help="path to file containing extracted metadata",
                        default='./metadata.json')
    parser.add_argument("-s", "--scratch", type=str, help="path to scratch directory",
                        default='.')

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    # Initialize work variables from previously generated data in files
    keywords, ignoredKeywords, ignoredTypes, series, zips = setup(args)

    t0 = time.time()
    fileCount = scanZips(args)
    t1 = time.time()

    if args.verbosity > 0:
        print("{} zip files processed in {} seconds".format(fileCount, t1 - t0),
              file=sys.stderr)
