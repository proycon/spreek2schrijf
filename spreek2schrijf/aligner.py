#!/usr/bin/env python3

import sys
import argparse
import json
import numpy as np
import Levenshtein
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
def smith_waterman_distance(seq1, seq2, match=3, mismatch=-1, insertion=-0.5, deletion=-0.5, normalize_score=True, ldthreshold=2):
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
    score *= len(seq2) / len(seq1)
    return score, mat

def find_sequence(seq1, seq2, match=3, mismatch=-1, insertion=-0.5, deletion=-0.5, normalize_score=True, ldthreshold=2):
    score, mat = smith_waterman(seq1,seq2,match,mismatch,insertion,deletion,normalize_score, ldthreshold)

    if score:
        #backtrack step (was not in original implementation)
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



class TimeAligner:
    def __init__(self,debug=False):
        self.loss = 0
        self.total = 0
        self.scores = []
        self.debug = debug


    def __call__(self,transcriptdoc, audiodoc, score_threshold, ldthreshold):
        audiowords = list(audiodoc)
        #print("Words in ASR output: ",len(audiowords),file=sys.stderr)
        window = audiowords[:MARGIN]
        cursor = 0
        buffer = None
        sentences = list(transcriptdoc)
        if self.debug:
            print("           asr word count:", len(audiowords),file=sys.stderr)
            print("transcript sentence count:", len(sentences), file=sys.stderr)
        begin = 0
        sentences.append((None,None,None)) #stop dummy
        for i, (sentence, transcriptstart, transcriptend) in enumerate(sentences):
            if sentence is None:
                begin = len(audiowords)
            else:
                print("PROCESSING #" + str(i+1) + "/" + str(len(sentences)) + ":",  sentence,file=sys.stderr)
                #Find strict begin according to timestamp
                for j, (audioword, audiostart, audioend) in enumerate(audiowords):
                    if j >= begin:
                        if audiostart >= transcriptstart:
                            if self.debug:
                                print("-------------------------------------------------------",file=sys.stderr)
                                print("     TRANSCRIPT: ", sentence,file=sys.stderr)
                                print(" ASR FIRST WORD: ", j, audioword,file=sys.stderr)
                                print("    ASR EXCERPT: ", " ".join([ w for w,_,_ in audiowords[j:j+10]]), "...",file=sys.stderr)
                                print("TRANSCRIPTSTART: ", transcriptstart,file=sys.stderr)
                                print("     AUDIOSTART: ", audiostart,file=sys.stderr)
                            begin = j
                            break
            if buffer is not None:
                transcriptsentence, audiobegin = buffer
                #flexibility step, see if moving the end point earlier helps:
                scores = []
                for j in range(-5,5):
                    if begin+j > audiobegin:
                        asrsentence = [ w for w,_,_ in audiowords[audiobegin:begin+j]]
                        score, mat = smith_waterman_distance(transcriptsentence, asrsentence)
                        scores.append( (j, float(score), asrsentence) )

                #no flexibility step
                #asrsentence = [ w for w,_,_ in audiowords[audiobegin:begin]]
                #scores.append( (0, smith_waterman_distance(transcriptsentence, asrsentence)[0], asrsentence))

                offset, score, asrsentence = max(scores, key=lambda x:x[1])
                begin += offset
                self.total += 1
                if np.isnan(score):
                    score = 0.0
                    self.scores.append(0.0)
                else:
                    self.scores.append(score)
                if self.debug:
                    print("BEST FLEXIBILITY OFFSET: ", offset, " SCORE=",score,file=sys.stderr)
                if score >= score_threshold:
                    yield " ".join(transcriptsentence), " ".join(asrsentence), score, offset
                else:
                    if self.debug:
                        print("Score threshold not met. SCORE=", score, "TRANSCRIPT="," ".join(transcriptsentence), "ASR=", " ".join(asrsentence), score, file=sys.stderr)
                    self.loss += 1
            if sentence is not None:
                buffer = (sentence.split(' '), begin)


def main():
    parser = argparse.ArgumentParser(description="Spreek2Schrijf Aligner", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--speech', type=str,help="AudioDoc XML", action='store',default="",required=True)
    parser.add_argument('-t','--transcript', type=str,help="Conversational XML", action='store',default="",required=True)
    parser.add_argument('-S','--score', type=float,help="Smith-Waterman distance score threshold", action='store',default=0.5,required=False)
    parser.add_argument('-D','--ldthreshold', type=int,help=argparse.SUPPRESS, action='store',default=2,required=False) #obsolete
    parser.add_argument('-d','--debug', help="Debug", action='store_true',default=False,required=False)
    args = parser.parse_args()

    audiodoc = AudioDoc(args.speech)
    transcriptdoc = CXMLDoc(args.transcript)

    print("{ \"sentence_pairs\" : [")
    aligner = TimeAligner(args.debug)
    for i, (transcriptsentence, asrsentence,score, offset) in enumerate(aligner(transcriptdoc, audiodoc, args.score, args.ldthreshold)):
        if i > 0: print(",")
        print(json.dumps({"transcript": transcriptsentence, "asr":asrsentence, "score":score, "offset": offset}, indent=4, ensure_ascii=False))
    print("]}")
    if aligner.total:
        print("LOSS: ", round((aligner.loss / aligner.total) * 100,2), "%", file=sys.stderr)
        print("AV SCORE: ", round((sum(aligner.scores) / len(aligner.scores)),2), " (prior to pruning)", file=sys.stderr)


if __name__ == '__main__':
    main()
