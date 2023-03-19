#!/bin/sh
# usage: ./web-summarize.sh "https://www.example.com/foo/bar.html"

python3 ./web2text.py "$1" > webinput.txt
python3 ./openai-summarize.py -t text -i webinput.txt
