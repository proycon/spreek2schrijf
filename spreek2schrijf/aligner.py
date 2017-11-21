#!/usr/bin/env python3

import sys
import string
import argparse
import numpy as np
import json
import lxml.etree
import Levenshtein
import ucto
from spreek2schrijf.formats import AudioDoc, CXMLDoc

MARGIN = 1000


def wordmatch(s1,s2, threshold=2):
    s1 = s1.lower()
    s2 = s2.lower()
    l1 = len(s1)
    l2 = len(s2)
    if s1 == s2:
        return True
    elif min(l1,l2) <= threshold+2 or l1 > l2 + threshold or l2 > l1 + threshold:
        return False
    else:
        return Levenshtein.distance(s1,s2) <= threshold


#adapted from http://climberg.de/page/smith-waterman-distance-for-feature-extraction-in-nlp/ (by Christian Limbergs)
def find_sequence(seq1, seq2, match=3, mismatch=-1, insertion=-0.5, deletion=-0.5, normalize_score=True, ldthreshold=2):
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
                mat[i - 1, j - 1] + (match if wordmatch(seq1[j - 1],seq2[i - 1], ldthreshold) else mismatch), #MAYBE TODO: match function can be made less strict
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
            return matchwords, score, matchseq[0]+1

    return [],score,0




class Aligner:

    def __init__(self,debug=False):
        self.loss = 0
        self.total = 0
        self.tokenizer = ucto.Tokenizer('tokconfig-nld', paragraphdetection=False)
        self.debug = debug

    def processbuffer(self, match,score, cursor_newbegin, transcriptsentence, audiowords):
        if self.buffer:
            #yield previous instance
            prevtranscript, prevmatch, prevscore,  cursor_end = self.buffer
            if score >= 0.75 and match and transcriptsentence and match[0].lower() == transcriptsentence[0][0].lower():
                gap = cursor_newbegin - cursor_end
                print("       GAP: ", gap,file=sys.stderr)
                if gap > 0 and gap < 3:
                    tail = audiowords[cursor_end:cursor_newbegin]
                    if tail:
                        if self.debug:
                            print("      TAIL: ", " ".join(tail),file=sys.stderr)
                        prevmatch += tail
            self.buffer = None
            return " ".join(prevtranscript), " ".join(prevmatch), prevscore
        return None

    def __call__(self,transcriptdoc, audiodoc, score_threshold, ldthreshold):
        audiowords = list(audiodoc)
        print("Words in ASR output: ",len(audiowords),file=sys.stderr)
        paragraphs = list(transcriptdoc)
        window = audiowords[:MARGIN]
        cursor = 0
        self.buffer = None
        for i, paragraph in enumerate(paragraphs):
            #pass paragraph to tokeniser
            print("PROCESSING #" + str(i) + "/" + str(len(paragraphs)) + ":",  paragraph,file=sys.stderr)
            self.tokenizer.process(paragraph)
            transcriptsentence = []
            for token in self.tokenizer:
                transcriptsentence.append( (str(token), token.type()) )
                if token.isendofsentence():
                    match, score, offset = find_sequence(window, [ word for word, wordtype in transcriptsentence if wordtype != 'PUNCTUATION' ] , ldthreshold=ldthreshold)
                    self.total += 1
                    if score >= score_threshold:
                        cursor_begin = (cursor + offset) - len(match)
                        assert audiowords[cursor_begin] == match[0]
                        result = self.processbuffer(match,score,cursor_begin, transcriptsentence, audiowords)
                        if result: yield result
                        if self.debug:
                            print("------------------------------------------------------------------------------",file=sys.stderr)
                            print("TRANSCRIPT: ", " ".join([ word for word, wordtype in transcriptsentence]) ,file=sys.stderr)
                            print("       ASR: ", " ".join(match) ,file=sys.stderr)
                            print("     SCORE: ", score,file=sys.stderr)
                            print("  PROGRESS: ", round((cursor / len(audiowords))*100,1), '%',file=sys.stderr)
                            print("      LOSS: ", round((self.loss / self.total) * 100,1), "%", file=sys.stderr)
                            print("    CURSOR: ", cursor,file=sys.stderr)
                            print("   +OFFSET: ", cursor+offset,file=sys.stderr)
                            print("    WINDOW: ", " ".join(window[:10]) + " ...",file=sys.stderr)
                        cursor_end = cursor + offset
                        if len(transcriptsentence) >= 10 and score >= 0.85:
                            #we have a strong alignment, reset the cursor for next batch
                            cursor += offset
                            window = audiowords[cursor:cursor+MARGIN]
                            if self.debug:
                                print("NXT WINDOW: ", " ".join(window[:10]) + " ...",file=sys.stderr)
                        #we buffer the instance rather than yielding it immediately
                        self.buffer = ([ word for word, wordtype in transcriptsentence], match, score, cursor_end)
                    else:
                        self.loss += 1
                    transcriptsentence = []
            result = self.processbuffer(match,score,cursor+offset, transcriptsentence, audiowords)
            if result: yield result

def main():
    parser = argparse.ArgumentParser(description="Spreek2Schrijf Aligner", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--speech', type=str,help="AudioDoc XML", action='store',default="",required=True)
    parser.add_argument('-t','--transcript', type=str,help="Conversational XML", action='store',default="",required=True)
    parser.add_argument('-S','--score', type=float,help="Smith-Waterman distance score threshold", action='store',default=0.8,required=False)
    parser.add_argument('-D','--ldthreshold', type=int,help="Levensthein distance score threshold for a word match", action='store',default=2,required=False)
    parser.add_argument('-d','--debug', help="Debug", action='store_true',default=False,required=False)
    args = parser.parse_args()

    audiodoc = AudioDoc(args.speech)
    transcriptdoc = CXMLDoc(args.transcript)

    print("{ \"sentence_pairs\" : [")
    aligner = Aligner(args.debug)
    for transcriptsentence, asrsentence, score in aligner(transcriptdoc, audiodoc, args.score, args.ldthreshold):
        print(json.dumps({"transcript": transcriptsentence, "asr":asrsentence, "score": score}, indent=4, ensure_ascii=False)+",")
        if aligner.total and not args.debug:
            print("LOSS: ", round((aligner.loss / aligner.total) * 100,2), "%", file=sys.stderr)
    print("]}")


if __name__ == '__main__':
    main()
