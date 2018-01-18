#!/bin/bash

if [[ $(hostname) == "mlp01" ]]; then
    KALDI_main=/var/www/lamachine/src/kaldi
    S2SDIR=/var/www/webservices-lst/live/repo/spreek2schrijf/spreek2schrijf/webservice
elif [[ ${hostname:0:3} == "mlp" ]]; then
    KALDI_main=/vol/customopt/lamachine.dev/kaldi
    S2SDIR=$(realpath .)
else
    echo "Specify KALDI_main!" >&2
    exit 2
fi
KALDI_root=$KALDI_main/egs/Kaldi_NL
inputdir=$1
scratchdir=$2
outdir=$3

cd $KALDI_root
for inputfile in $inputdir/*; do
  filename=$(basename "$inputfile")
  extension="${filename##*.}"
  file_id=$(basename "$inputfile" .$extension)
  sox $inputfile -e signed-integer -c 1 -r 16000 -b 16 $scratchdir/${file_id}.wav
  target_dir=$scratchdir/${file_id}_$(date +"%y_%m_%d_%H_%m_%S")
  mkdir -p $target_dir
  ./decode_PR.sh $scratchdir/${file_id}.wav $target_dir
  cat $target_dir/${file_id}.txt | cut -d'(' -f 1 > $outdir/${file_id}.txt
  cp $target_dir/1Best.ctm $outdir/${file_id}.ctm
  cat $outdir/${file_id}.ctm | perl $S2SDIR/wordpausestatistic.perl 1.0 $outdir/${file_id}.sent
  ./scripts/ctm2xml.py $outdir $file_id $scratchdir
done
cd -
