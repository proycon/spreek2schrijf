
import sys
import lxml.etree

class AudioDoc:
    def __init__(self, filename):
        self.doc = lxml.etree.parse(filename).getroot()

    def __iter__(self):
        for node in self.doc.xpath('//Word'):
            starttime = int(float(node.attrib['stime'])*1000)
            endtime = starttime + int(float(node.attrib['dur'])*1000)
            yield node.text.strip(), starttime, endtime

class SimplifiedVLOSDoc:
    def __init__(self, filename):
        self.doc = lxml.etree.parse(filename).getroot()

    def __iter__(self):
        for tekst in self.doc.xpath('//tekst'):
            for alinea in tekst.xpath('.//alinea/p'):
                yield alinea.text.strip()

class CXMLDoc:
    def __init__(self, filename):
        self.doc = lxml.etree.parse(filename).getroot()

    def __iter__(self):
        for turn in self.doc.xpath('//turn'):
            turnstarttime = int(turn.attrib['recordingTime'])
            for transcription in turn.xpath('.//transcription'):
                text = []
                words = list(transcription.xpath('.//word'))
                for i, word in enumerate(words):
                    if not text:
                        starttime = turnstarttime +  int(word.attrib['startMs'])
                    endtime = starttime + int(word.attrib['endMs'])
                    EOS = (i == len(words))
                    if "non-verbal" not in word.attrib or word.attrib['non-verbal'] == 'false':
                        if "prefix" in word.attrib:
                            text.append(word.attrib['prefix'].strip())
                        wordtext = "".join([ textnode.text for textnode in word.xpath('.//text') if textnode.text ]).strip()
                        if not wordtext:
                            print("WARNING: Empty word detected, skipping..!",file=sys.stderr)
                            #print(lxml.etree.tostring(word),file=sys.stderr)
                        else:
                            text.append(wordtext)
                        if "postfix" in word.attrib:
                            if word.attrib['postfix'][-1] in ('.','?','!'):
                                #end of sentence
                                text.append(word.attrib['postfix'].strip())
                                EOS = True
                    if EOS:
                        yield " ".join(text), starttime, endtime
                        text = []
