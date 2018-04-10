#!/usr/bin/env python3
# This script is written to convert ctm files into txt format. It is based on the following assumptions:
# 1 - the CTM file corresponds to a single audio file.
# 2 - No segmentation info is available, so the wole audio file is transcribed into one segment
# 3 - Single speaker/ No speaker identification
# 4 - PUNCTUATION INFORMATION IS ALREADY INCLUDED in the CTM file (i.e. '.' words)

import sys

sentence = []
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            fields = line.split(" ")
            word = fields[4]
            if word != '#':
                sentence.append(word)
                if word in ('.','!','?'):
                    print(" ".join(sentence))
                    sentence = []






