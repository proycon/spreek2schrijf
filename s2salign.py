#!/usr/bin/env python3

import sys
import string
import argparse
import numpy as np
import json
import lxml.etree
import ucto

MARGIN = 1000

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
            for alinea in tekst.xpath('.//alinea/p'):
                yield alinea.text


#adapted from http://climberg.de/page/smith-waterman-distance-for-feature-extraction-in-nlp/ (by Christian Limbergs)
def find_sequence(seq1, seq2, match=3, mismatch=-1, insertion=-0.5, deletion=-0.5, normalize_score=True):
    """Smith Waterman algorithm"""
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
                mat[i - 1, j - 1] + (match if seq1[j - 1].lower() == seq2[i - 1].lower() else mismatch), #MAYBE TODO: match function can be made less strict
                # one word is missing in seq2, so decrease the score by deletion
                mat[i - 1, j] + deletion,
                # one additional word is in seq2, so decrease the score by insertion
                mat[i, j - 1] + insertion
            )
    # the maximum of mat is now the score, which is returned raw or normalized (with a range of 0-1)
    score = np.max(mat) / (len(seq2) * match) if normalize_score else np.max(mat)

    if score:
        #backtrack (was not in original implementation)
        i, j = np.unravel_index(np.argmax(mat), mat.shape)
        matchseq = []

        while mat[i][j] != 0:
            matchseq.append(j-1)
            neighbours = ( (i-1, j-1), (i,j-1) )
            i,j = neighbours[np.argmax([mat[n] for n in neighbours])]

        if matchseq:
            matchwords = [seq1[i] for i in reversed(matchseq) ]
            return matchwords, score, matchseq[-1]

    return [],score,0




class Aligner:

    def __init__(self,debug=False):
        self.loss = 0
        self.total = 0
        self.tokenizer = ucto.Tokenizer('tokconfig-nld', paragraphdetection=False)
        self.debug = debug

    def __call__(self,transcriptdoc, audiodoc, score_threshold):
        audiowords = list(audiodoc)
        print("Words in ASR output: ",len(audiowords),file=sys.stderr)
        paragraphs = list(transcriptdoc)
        buffer = audiowords[:MARGIN]
        cursor = 0
        for i, paragraph in enumerate(paragraphs):
            #pass paragraph to tokeniser
            print("PROCESSING #" + str(i) + "/" + str(len(paragraphs)) + ":",  paragraph,file=sys.stderr)
            self.tokenizer.process(paragraph)
            transcriptsentence = []
            for token in self.tokenizer:
                transcriptsentence.append( (str(token), token.type()) )
                if token.isendofsentence():
                    match, score, offset = find_sequence(buffer, [ word for word, wordtype in transcriptsentence if wordtype != 'PUNCTUATION' ] )
                    self.total += 1
                    if score >= score_threshold:
                        if self.debug:
                            print("--------------------------------------------------",file=sys.stderr)
                            print("TRANSCRIPT: ", " ".join([ word for word, wordtype in transcriptsentence]) ,file=sys.stderr)
                            print("       ASR: ", " ".join(match) ,file=sys.stderr)
                            print("     SCORE: ", score,file=sys.stderr)
                        if len(transcriptsentence) >= 10 and score >= 0.85:
                            #we have a strong alignment, reset the cursor for next batch
                            if self.debug:
                                print("Offset =", offset,file=sys.stderr)
                            cursor += offset
                            buffer = audiowords[cursor:cursor+MARGIN]
                            if self.debug:
                                print("--> Moved cursor to ", cursor,file=sys.stderr)
                                print(["   "] + audiowords[cursor-15:cursor] + [" >>>>CURSOR<<<< "] + buffer[:15],file=sys.stderr)
                        yield " ".join([ word for word, wordtype in transcriptsentence]), " ".join(match), score
                    else:
                        self.loss += 1
                    transcriptsentence = []

def main():
    parser = argparse.ArgumentParser(description="Spreek2Schrijf Aligner", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--speech', type=str,help="AudioDoc XML", action='store',default="",required=True)
    parser.add_argument('-t','--transcript', type=str,help="Simplified VLOS XML", action='store',default="",required=True)
    parser.add_argument('-S','--score', type=float,help="Smith-Waterman distance score threshold", action='store',default=0.8,required=False)
    parser.add_argument('-d','--debug', help="Debug", action='store_true',default=False,required=False)
    args = parser.parse_args()

    audiodoc = AudioDoc(args.speech)
    transcriptdoc = SimplifiedVLOSDoc(args.transcript)

    print("{ 'sentence_pairs' : [")
    aligner = Aligner(args.debug)
    for transcriptsentence, asrsentence, score in aligner(transcriptdoc, audiodoc, args.score):
        print(json.dumps({"transcript": transcriptsentence, "asr":asrsentence, "score": score}, indent=4, ensure_ascii=False)+",")
        if aligner.total:
            print("LOSS: ", round((aligner.loss / aligner.total) * 100,2), "%", file=sys.stderr)
    print("]}")


if __name__ == '__main__':
    main()
