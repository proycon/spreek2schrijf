#!/usr/bin/env python3

import sys
import json

txtfile, jsonfile = sys.argv[1:]

with open(txtfile, 'r', encoding='utf-8') as f:
    sentences = list(f.readlines())

with open(jsonfile, 'r', encoding='utf-8') as f:
    events = json.load(f)

srcfile = events[0]['src']
print("<html>\n<head><title>{srcfile}</title></head>\n<body><h1>{srcfile}</h1><p>\n</p>".format(srcfile=srcfile))

for event in events:
    print("<p><b><font color=\"#00C000\">" + event['speaker'] + "</font></b> {"+str(event['begintime'])+"-"+str(event['endtime'])+"}<br>")
    for sentence in event['sentences']:
        tokens = sentences[sentence['seqnr']-1].split(' ')
        for token in tokens:
            print(token.strip() + "<wbr>")
    print("</p>")
print("</body>\n</html>")
