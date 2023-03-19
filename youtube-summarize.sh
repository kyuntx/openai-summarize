#!/bin/sh
# usage: ./youtume-summarize.sh "https://www.youtube.com/watch?v=xxxxxxxx"
# require: https://github.com/yt-dlp/yt-dlp , ffmpeg

./yt-dlp --extract-audio --audio-format m4a -o input.m4a "$1"
python3 ./openai-summarize.py -t audio -i input.m4a -ot transcript.txt
rm input.m4a