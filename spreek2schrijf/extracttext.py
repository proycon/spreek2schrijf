#!/usr/bin/env python3

import sys
import argparse
import os.path
import glob
from spreek2schrijf.formats import CXMLDoc

def main():
    parser = argparse.ArgumentParser(description="Extract text from Conversational XML", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--inputdir', type=str,help="Input directory", action='store',default=".",required=False)
    args = parser.parse_args()

    for filename in glob.glob(args.inputdir + "/*.xml"):
        print(os.path.basename(filename),file=sys.stderr)
        doc = CXMLDoc(filename)
        for text in doc:
            print(text)

if __name__ == '__main__':
    main()
