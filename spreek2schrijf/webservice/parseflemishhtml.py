#!/usr/bin/env python3

import sys
import json
from bs4 import BeautifulSoup

with open(sys.argv[1], 'r',encoding='utf-8') as f:
    doc = BeautifulSoup(f.read(), 'html.parser')

srcfile = doc.title.string

seqnr = 0
events = []
for p in doc.find_all('p'):
    if p.font:
        speaker = p.font.string

        raw_p = str(p)
        begintimeindex = raw_p.find('{')
        endtimeindex = raw_p.find('}')
        breakindex = raw_p.find('<br/>') + 6
        begintime, endtime = [ float(x) for x in raw_p[begintimeindex+1:endtimeindex].split('-') ]
        print(srcfile, speaker, begintime, endtime,file=sys.stderr)
        raw_body = raw_p[breakindex:len(raw_p) - 4]
        sentence = []
        sentences = []
        for token in [ t.strip() for t in raw_body.split("<wbr/>") if t.strip() ]:
            if token[-1] == '.':
                sentence.append(token[:-1])
                sentence.append('.')
                seqnr += 1
                sentences.append({'seqnr': seqnr, 'tokens': sentence})
                sentence = []
            else:
                sentence.append(token)
        if sentence: #trailing sentence
            sentences.append({'seqnr': seqnr, 'tokens': sentence})
            sentence = []
        events.append({'speaker': speaker, 'src': srcfile, 'begintime': begintime, 'endtime': endtime, 'sentences':sentences})

with open('out.json','w',encoding='utf-8') as f:
    json.dump(events, f, indent=4, ensure_ascii=False)
with open('out.txt','w',encoding='utf-8') as f:
    for event in events:
        for sentence in event['sentences']:
            print(" ".join(sentence['tokens']), file=f)
