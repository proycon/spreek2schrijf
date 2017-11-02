#!/usr/bin/env python3

import sys
import string
import argparse
import numpy as np
import lxml.etree

class AudioDoc:
    def __init__(self, filename):
        self.doc = lxml.etree.parse(filename).getroot()

    def __iter__(self):
        for node in self.doc.xpath('//Word'):
            yield node.text

class SimplifiedVLOSDoc:
    def __init__(self, filename):
        self.doc = lxml.etree.parse(filename).getroot()

    def __iter__(self):
        for tekst in self.doc.xpath('//tekst'):
            for alinea in tekst.xpath('//alinea/p'):
                yield alinea.text


#adapted from http://climberg.de/page/smith-waterman-distance-for-feature-extraction-in-nlp/ (by Christian Limbergs)
def smith_waterman(seq1, seq2, match=3, mismatch=-1, insertion=-0.5, deletion=-0.5, normalize_score=1):
    # switch sequences, so that seq1 is the longer sequence to search for seq2
    if len(seq2) > len(seq1): seq1, seq2 = seq2, seq1
    # create the distance matrix
    mat = np.zeros((len(seq2) + 1, len(seq1) + 1))
    # iterate over the matrix column wise
    for i in range(1, mat.shape[0]):
        # iterate over the matrix row wise
        for j in range(1, mat.shape[1]):
            # set the current matrix element with the maximum of 4 different cases
            mat[i, j] = max(
                # negative values are not allowed
                0,
                # if previous word matches increase the score by match, else decrease it by mismatch
                mat[i - 1, j - 1] + (match if seq1[j - 1].lower() == seq2[i - 1].lower() else mismatch),
                # one word is missing in seq2, so decrease the score by deletion
                mat[i - 1, j] + deletion,
                # one additional word is in seq2, so decrease the score by insertion
                mat[i, j - 1] + insertion
            )
    # the maximum of mat is now the score, which is returned raw or normalized (with a range of 0-1)
    score = np.max(mat) / (len(seq2) * match) if normalize_score else np.max(mat)

    #backtrack (was not in original implementation)
    i, j = np.unravel_index(np.argmax(mat), mat.shape)
    matchseq = []

    while mat[i][j] != 0:
        matchseq.append(seq1[j-1])
        neighbours = ( (i-1, j-1), (i,j-1) )
        i,j = neighbours[np.argmax([mat[n] for n in neighbours])]

    matchseq.reverse()
    return matchseq, score



def align(transcriptdoc, audiodoc):
    audiowords = list(audiodoc)
    print("Words in audio: ",len(audiowords),file=sys.stderr)
    for paragraph in transcriptdoc:
        #crude tokenisation
        transcriptwords = [ w.strip(string.punctuation) for w in paragraph.split(' ') ]
        #find most likely sequence for this input
        match, score = smith_waterman(audiowords, transcriptwords)
        print("ORIGINAL: ", " ".join(transcriptwords),file=sys.stderr)
        print("MATCH: ", " ".join(match),file=sys.stderr)
        print("SCORE: ", score,file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Spreek2Schrijf Aligner", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--speech', type=str,help="AudioDoc XML", action='store',default="",required=True)
    parser.add_argument('-t','--transcript', type=str,help="Simplified VLOS XML", action='store',default="",required=True)
    args = parser.parse_args()

    audiodoc = AudioDoc(args.speech)
    transcriptdoc = SimplifiedVLOSDoc(args.transcript)

    align(transcriptdoc, audiodoc)








if __name__ == '__main__':
    main()



