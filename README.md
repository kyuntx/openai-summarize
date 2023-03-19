# openai-summarize

- OpenAI API(gpt-3.5-turbo) と Whisper API を利用して、テキストファイル、または音声ファイルの文字起こしから要約を作成します。
- 長文の要約は分割して行います。
  - 参考： https://zenn.dev/kurehajime/scraps/f78d6247c63aa3
- Whisper APIの上限25MBを超える場合はビットレートを下げてエンコードし直します。
  - 参考： https://dev.classmethod.jp/articles/openai-api-whisper-about-data-limit/
- 英語の記事、音声は日本語に翻訳して要約します。
- おまけで web からテキスト部分を引っ張ってきて要約するスクリプト、Youtubeからダウンロードして音声ファイルに変換して要約するスクリプトもつけてます

## 準備
```
# for openai-summarize.py
pip install openai pydub titoken ja_sentence_segmenter
```

## 使い方
```
./openai-summarize.py -h
usage: OpenAI Summarizer(Whisper API, GPT-3.5)

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input file [audio(mp4,m4a,mp3,wav)|text(utf-8)]
  -t {audio,text}, --type {audio,text}
                        input file type
  -ot TRANSCRIPT, --transcript TRANSCRIPT
                        output transcript text
  -os SUMMARY, --summary SUMMARY
                        output summary text
```

- テキストファイルをから要約（標準出力）
```
export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
python3 ./openai-summarize.py -t text -i input.txt
```

- テキストファイルをから要約、要約したテキストをファイル保存
```
export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
python3 ./openai-summarize.py -t text -i input.txt -os summary.txt
```

- 音声ファイルをから要約
```
export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
python3 ./openai-summarize.py -t audio -i input.m4a
```

- 音声ファイルをから要約して、文字起こしをテキストファイルに保存
```
export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
python3 ./openai-summarize.py -t audio -i input.m4a -ot transcript.txt
```

## Webページ要約

- 準備
```
pip install BeautifulSoup4 pandas chardet
```

- 要約
```
export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
./web-summarize.sh "https://www.example.com/foo/bar.html"
```

## Youtubeコンテンツ要約

- 準備
```
# ffmpegのインストール
wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
chmod +x yt-dlp 
```

- 要約
```
export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
./youtume-summarize.sh "https://www.youtube.com/watch?v=xxxxxxxx"
```