
import lxml.etree

class AudioDoc:
    def __init__(self, filename):
        self.doc = lxml.etree.parse(filename).getroot()

    def __iter__(self):
        for node in self.doc.xpath('//Word'):
            yield node.text.strip()

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
        for utterance in self.doc.xpath('//utterance'):
            text = utterance.text
            #strip [Speaker:] metadata
            i = text.find(']')
            if i != -1 and i < 100:
                text = text[i+1:]
            yield text.strip()
