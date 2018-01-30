#!/usr/bin/env python3

import sys

names = {}
with open(sys.argv[2],'r',encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        names[line.lower()] = line

#filter duplicate punctuation
substitutions = {
    '. .': '.',
    ', ,': ',',
}

with open(sys.argv[1],'r',encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        words = line.split(' ')
        newwords = []
        skip = 0
        #recasing for known names
        for i in range(0, len(words)):
            if skip:
                skip = skip - 1
                continue
            found = False
            for l in range(4, 0,-1):
                ngram = " ".join(words[i:i+l])
                key = ngram.lower()
                if key in names:
                    if ngram != names[key]:
                        print("  Corrected name " + names[key],file=sys.stderr)
                    found = True
                    newwords += names[key].split(' ')
                elif key in substitutions:
                    if ngram != substitutions[key]:
                        print("  Applied substitution " + key + " -> " + substitutions[key],file=sys.stderr)
                    found = True
                    newwords.append(substitutions[key])
                if found:
                    skip = l-1
                    break
            if not found:
                newwords.append(words[i])
        print(" ".join(newwords))
