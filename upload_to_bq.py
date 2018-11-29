from __future__ import print_function

import os, sys
import argparse
from os.path import join
import json

import numpy as np
import pandas as pd
from initState import *

keywords = []
ignoredKeywords = []
metadata = []


def removeIgnoredKeywordColumns(args, df):
    cols = df.columns.tolist()
    for keyword in ignoredKeywords:
        if keyword in cols:
            df = df.drop(columns=keyword)
            if args.verbosity >= 1:
                print("Dropped column {}".format(keyword))
    return df

def reorderColumns(args, df):
    cols = df.columns.tolist()
    # Put the file name and patient id as first columns
    newCols = ['ZipFileName','PatientID']
    for col in cols:
        if not col in newCols:
            newCols.append(col)
    df = df[newCols]
    if args.verbosity >= 1:
        print("Reordered columns: {}".format(df.columns.tolist()))
    return df

def outputTSV(args, df):
    with open(args.csv,'w') as f:
        df.to_csv(f,sep='\t',na_rep="",index=False,)

def prepareDataframe(args):
    df = pd.DataFrame(metadata)
    #print(type(df))
    df = removeIgnoredKeywordColumns(args,df)
    df = reorderColumns(args,df)
    outputTSV(args,df)


def setup(args):
    keywords = loadKeywords(args)
    ignoredKeywords = loadIgnoredKeywords(args)
    metadata = loadMetadata(args)
    return (keywords, ignoredKeywords, metadata)

def parse_args():
    parser = argparse.ArgumentParser(description="Build DICOM image metadata table")
    parser.add_argument("-v", "--verbosity", action="count", default=2, help="increase output verbosity")
    parser.add_argument("-k", "--keywords", type=str, help="path to file containing keywords found",
                        default='./keywords.txt')
    parser.add_argument("-i", "--ignoredKeywords", type=str,
                        help="path to file containing keywords that are not to be processed",
                        default='./ignoredkeywords.txt')
    parser.add_argument("-m", "--metadata", type=str, help="path to file containing extracted metadata",
                        default='./metadata.json')
    parser.add_argument("-c", "--csv", type=str, help="path to file to receive csv formatted metadata",
                        default='./csv.json')

    return parser.parse_args()



if __name__ == '__main__':

    args = parse_args()

    # Initialize work variables from previously generated data in files
    keywords, ignoredKeywords, metadata = setup(args)

    t0 = time.time()
    fileCount = prepareDataframe(args)
    t1 = time.time()

    if args.verbosity > 0:
        print("{} zip files processed in {} seconds".format(fileCount, t1 - t0),
              file=sys.stderr)
