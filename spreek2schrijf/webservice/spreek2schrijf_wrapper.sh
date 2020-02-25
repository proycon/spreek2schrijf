#!/usr/bin/env bash

###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- CLAM Wrapper script Template --
#       by Maarten van Gompel (proycon)
#       https://proycon.github.io/clam
#       Centre for Language and Speech Technology
#       Radboud University Nijmegen
#
#       Licensed under GPLv3
#
###############################################################

#This is a template wrapper which you can use a basis for writing your own
#system wrapper script. The system wrapper script is called by CLAM, it's job it
#to call your actual tool.

#This script will be called by CLAM and will run with the current working directory set to the specified project directory

#This is the shell version of the system wrapper script. You can also use the
#Python version, which is generally more powerful as it parses the XML settings
#file for you, unlike this template. Using Python is recommended for more
#complex webservices and for additional security.

#this script takes three arguments from CLAM: $STATUSFILE $INPUTDIRECTORY $OUTPUTDIRECTORY. (as configured at COMMAND= in the service configuration file)
STATUSFILE=$1
INPUTDIRECTORY=$2
OUTPUTDIRECTORY=$3
SCRATCHDIRECTORY=$4
WEBSERVICEDIR=$5
mkdir -p $SCRATCHDIRECTORY

#If $PARAMETERS was passed COMMAND= in the service configuration file, the remainder of the arguments are custom parameters for which you either need to do your own parsing, or you pass them directly to your application
# PARAMETERS=${@:4}

#Output a status message to the status file that users will see in the interface
echo "Starting..." >> $STATUSFILE

#Example parameter parsing using getopt:
#while getopts ":h" opt "$PARAMETERS"; do
#  case $opt in
#    h)
#      echo "Help option was triggered" >&2
#      ;;
#    \?)
#      echo "Invalid option: -$OPTARG" >&2
#      ;;
#  esac
#done

#Loop over all input files, here we assume they are txt files, adapt to your situation:
#Invoke your actual system, whatever it may be, adapt accordingly

if [[ $(hostname) == "mlp01" ]]; then
    KALDI_main=/var/www/lamachine2/weblamachine/opt/kaldi
    export S2SDIR=/var/www/webservices-lst/live/repo/spreek2schrijf
    MOSESDIR=/var/www/lamachine2/weblamachine/bin/moses
    KALDI_NL=/var/www/lamachine2/weblamachine/opt/kaldi_nl
elif [[ ${hostname:0:3} == "mlp" ]]; then
    KALDI_main=/vol/customopt/lamachine.dev/kaldi
    export S2SDIR=$(realpath ../../)
    MOSESDIR=/var/www/lamachine2/weblamachine/bin/moses
    KALDI_NL=$KALDI_main/egs/Kaldi_NL
else
    echo "Specify KALDI_main!" >&2
    exit 2
fi

cd $KALDI_NL
for inputfile in $INPUTDIRECTORY/*; do
  inputfile_absolute=$(realpath "$inputfile")
  filename=$(basename "$inputfile")
  extension="${filename##*.}"
  file_id=$(basename "$inputfile" .$extension)
  if [ "$extension" = "ctm" ]; then
      echo "Using CTM file $filename..." >&2
      echo "Using CTM file $filename..." >> $STATUSFILE
      cp $inputfile $OUTPUTDIRECTORY/${file_id}.ctm
      python3 $S2SDIR/spreek2schrijf/webservice/ctm2txt.py $OUTPUTDIRECTORY/$file_id.ctm > $OUTPUTDIRECTORY/${file_id}.spraak.txt
  elif [ "$extension" = "html" ]; then
      echo "Using HTML file $filename..." >&2
      echo "Using HTML file $filename..." >> $STATUSFILE
      cd $OUTPUTDIRECTORY
      python3 $S2SDIR/spreek2schrijf/webservice/parseflemishhtml.py $inputfile_absolute
      if [ $? -ne 0 ]; then
          echo "Parse flemish HTML failed, input was $inputfile_absolute">&2
          exit 2
      fi
      mv out.txt ${file_id}.spraak.txt
      mv out.json ${file_id}.spraak.json
      cd $KALDI_NL
  else
      echo "Audio conversion $filename..." >&2
      echo "Audio conversion $filename..." >> $STATUSFILE
      sox $inputfile -e signed-integer -c 1 -r 16000 -b 16 $SCRATCHDIRECTORY/${file_id}.wav
      target_dir=$SCRATCHDIRECTORY/${file_id}_$(date +"%y_%m_%d_%H_%m_%S")
      mkdir -p $target_dir
      echo "ASR Decoding $filename..." >&2
      echo "ASR Decoding $filename..." >> $STATUSFILE
      ./decode_PR.sh $SCRATCHDIRECTORY/${file_id}.wav $target_dir
      cat $target_dir/${file_id}.txt | cut -d'(' -f 1 > $OUTPUTDIRECTORY/${file_id}.spraak.txt
      cp $target_dir/1Best.ctm $OUTPUTDIRECTORY/${file_id}.ctm
      cat $OUTPUTDIRECTORY/${file_id}.ctm | perl $S2SDIR/spreek2schrijf/webservice/wordpausestatistic.perl 1.0 $OUTPUTDIRECTORY/${file_id}.sent #currently computed but ignored!!!
  fi
  #python3 $S2SDIR/spreek2schrijf/webservice/ctm2xml.py $OUTPUTDIRECTORY $file_id $SCRATCHDIRECTORY
  sed -e "s|path=|path=$S2SDIR/model/|g" $S2SDIR/model/moses.ini > $SCRATCHDIRECTORY/moses.ini
  cat $SCRATCHDIRECTORY/moses.ini >&2
  echo "MT Decoding $filename..." >&2
  echo "MT Decoding $filename..." >> $STATUSFILE
  $MOSESDIR/moses -f $SCRATCHDIRECTORY/moses.ini  < $OUTPUTDIRECTORY/${file_id}.spraak.txt > $OUTPUTDIRECTORY/${file_id}.mt-out.txt
  python3 $S2SDIR/spreek2schrijf/webservice/postcorrect.py $OUTPUTDIRECTORY/${file_id}.mt-out.txt $S2SDIR/spreek2schrijf/webservice/namen.txt > $OUTPUTDIRECTORY/${file_id}.schrijf.txt
  if [ "$extension" = "html" ]; then
     python3 $S2SDIR/spreek2schrijf/webservice/writeflemishhtml.py $OUTPUTDIRECTORY/${file_id}.schrijf.txt $OUTPUTDIRECTORY/${file_id}.spraak.json > $OUTPUTDIRECTORY/${file_id}.html
  fi
  if [ ! -z "$target_dir" ] && [ -d "$target_dir" ]; then
      rm -Rf $target_dir
  fi
done
cd -

echo "Done." >> $STATUSFILE



