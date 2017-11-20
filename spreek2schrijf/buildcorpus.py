#!/usr/bin/env python3

import json
import argparse
import codecs
import glob

def main():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i','--inputdir', type=str,help="Input directory", action='store',default=".",required=False)
    parser.add_argument('-o','--outputprefix', type=str,help="Output prefix", action='store',default="corpus",required=False)
    args = parser.parse_args()

    spraak = open(args.outputprefix +  ".spraak.txt",'w',encoding='utf-8')
    schrijf = open(args.outputprefix +  ".schrijf.txt",'w',encoding='utf-8')

    for filename in glob.glob(args.inputdir + "/*.json"):
        with open(filename,'r',encoding='utf-8') as f:
            data = json.load(codecs.getreader(f,'utf-8'))
            for sentencepair in data['sentence_pairs']:
                if 'asr' in sentencepair and 'transcript' in sentencepair:
                    print(sentencepair['asr'],file=spraak)
                    print(sentencepair['transcript'],file=schrijf)

if __name__ == '__main__':
    main()
