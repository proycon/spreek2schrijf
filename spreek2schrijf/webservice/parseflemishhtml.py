#!/usr/bin/env python3

import sys
import json
from bs4 import BeautifulSoup

with open(sys.argv[1], 'r',encoding='utf-8') as f:
    doc = BeautifulSoup(f.read(), 'html.parser')

srcfile = doc.title.string
seqnr = 0
events = []
sentences = []
sentence = []
begintime, endtime = 0,0
speaker = "unknown"
for font in doc.find('div', id='transcript').find_all('font'):
    if 'speaker' in font['class']:
        print(srcfile, speaker, begintime, endtime,file=sys.stderr)
        if sentences:
            if sentence:
                sentences.append({'seqnr': seqnr, 'tokens': sentence})
                sentence = []
            events.append({'speaker': speaker, 'src': srcfile, 'begintime': begintime, 'endtime': endtime, 'sentences':sentences})
            sentences = []
        speaker = font.get_text().strip()
        begintime, endtime = font['ts'], font['te']
    elif 'player' in font['class']:
        token = font.get_text().strip()
        if token[-1] == '.':
            sentence.append(token[:-1])
            sentence.append('.')
            seqnr += 1
            sentences.append({'seqnr': seqnr, 'tokens': sentence})
            sentence = []
        else:
            sentence.append(token)
if sentences:
    if sentence:
        sentences.append({'seqnr': seqnr, 'tokens': sentence})
        sentence = []
    events.append({'speaker': speaker, 'src': srcfile, 'begintime': begintime, 'endtime': endtime, 'sentences':sentences})

with open('out.json','w',encoding='utf-8') as f:
    json.dump(events, f, indent=4, ensure_ascii=False)
with open('out.txt','w',encoding='utf-8') as f:
    for event in events:
        for sentence in event['sentences']:
            print(" ".join(sentence['tokens']), file=f)
