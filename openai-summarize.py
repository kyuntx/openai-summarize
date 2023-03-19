#!/bin/env python3
# dependency modules:
#  pip install openai pydub titoken ja_sentence_segmenter
import argparse
import os
import pathlib
import subprocess
import math
import unicodedata
import openai
import textwrap
import tiktoken
import functools

# Whiper API の最大ファイルサイズ(25MB)
TARGET_FILE_SIZE = 25000000
# 分割要約の最大トークン数
# GPT3.5 では リクエストと応答の合計で 4096 トークンなので、半分強くらいをリクエストに利用
MAX_TOKEN = 2500
# 利用するモデル (GPT-4待ち……)
OPENAI_MODEL = "gpt-3.5-turbo"

# OpenAI の APIキーを環境変数に入れておくこと
# export OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
openai.api_key = os.getenv("OPENAI_API_KEY")
encoding = tiktoken.encoding_for_model(OPENAI_MODEL)

# 日本語の文章を適当に改行する
def japanese_wrap(text):
    from ja_sentence_segmenter.common.pipeline import make_pipeline
    from ja_sentence_segmenter.concatenate.simple_concatenator import concatenate_matching
    from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
    from ja_sentence_segmenter.split.simple_splitter import split_newline, split_punctuation

    split_punc2 = functools.partial(split_punctuation, punctuations=r"。!?")
    concat_tail_no = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)(の)$", remove_former_matched=False)
    segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)

    return segmenter(text)

# OpenAI APIで要約文を作成
def summarize(text):
    prompt = """
    あなたはプロの編集者です。
    以下の制約条件と、入力された文章をもとに日本語で要約を出力してください。
    ・文字数は1000文字以内。
    ・要約が英語である場合は、日本語に翻訳。
    ・重要なキーワードを取り残さない。
    ・要約された文章のみを出力。
    """
    prompt = textwrap.dedent(prompt)[1:-1]
    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        max_tokens=1200,
        #temperature=0,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]
    )
    result = completion.choices[0].message.content

    # なんでか時々日本語にしてくれない
    if not is_japanese(result):
        print("Summary is not Japanese, translate.")
        result = translate_jp(result)

    return result

# OpenAI APIで翻訳文を作成 (要約が英語で出ちゃった時用)
def translate_jp(text):
    system_message = """
    あなたはプロの翻訳者です。入力された文章をもとに最高の翻訳を出力してください。
    """
    system_message = textwrap.dedent(system_message)[1:-1]
    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": text},
        ]
    )
    return completion.choices[0].message.content

# 日本語が含まれているか判定(中国語や韓国語でも判定されてしまう)
def is_japanese(string):
    for ch in string:
        name = unicodedata.name(ch) 
        if "CJK UNIFIED" in name \
        or "HIRAGANA" in name \
        or "KATAKANA" in name:
            return True
    return False

# 指定されたトークンで文字列を分解する
def split_by_token(text,block_size,sep):
  lines = text.split(sep)
  blocks = []
  token = 0
  block = ''
  for line in lines:
    t = len(encoding.encode(line))
    if token > 0 and block_size < (token + t):
      blocks.append(block)
      token = 0
      block = '' 
    token += t
    block += line
  blocks.append(block)
  return blocks

# Whisper API で文字起こし
def transcription(inputfile):
    print("transcripting...")
    file = open(str(inputfile), "rb")
    transcription = openai.Audio.transcribe("whisper-1", file)
    os.remove(str(inputfile))
    return str(transcription["text"])

# ファイルサイズがWhisper APIの上限(25MB)を超えていたら、ビットレートを下げてエンコードし直す
def fix_audiofilesize(inputfile):
    from pydub import AudioSegment
    original_file = pathlib.Path(inputfile)
    audio_file = pathlib.Path("./audio").with_suffix(original_file.suffix)

    subprocess.run(["ffmpeg", "-loglevel", "quiet", "-i", str(original_file)
        , "-codec:a", "copy", "-vn", str(audio_file)])
        
    if audio_file.stat().st_size> TARGET_FILE_SIZE:
        # 上限を超えていたらビットレートを下げてモノラルにしてエンコードし直す
        print("This file needs to be converted.")

        # ビットレートをどこまで落とせば収まるか計算
        audio_segment = AudioSegment.from_file(str(audio_file))
        audio_length_sec = len(audio_segment)/1000

        target_kbps = int(math.floor(TARGET_FILE_SIZE * 8 / audio_length_sec / 1000 * 0.95))
        
        print("target bitrate(kbps):", target_kbps)
        # 8kbps 以下にしないと収まらない場合は諦める
        if target_kbps < 8:
            assert f"{target_kbps=} is not supported."

        converted_file = pathlib.Path("./converted").with_suffix(".mp4")
        print("converting...")
        subprocess.run(["ffmpeg", "-i", str(audio_file)
            , "-codec:a", "aac", "-ar", "16000", "-ac", "1", "-b:a", f"{target_kbps}k", "-loglevel", "quiet"
            , str(converted_file)])

        os.remove(str(audio_file))
        return converted_file
    else:
        return audio_file

# 入力ファイルの処理(音声ならWhisper APIへ、テキストならそのまま)
def process_input_file(args):
    if args.type == "audio":
        origfile = args.input
        transcription_text = '\n'.join(textwrap.wrap(transcription(fix_audiofilesize(origfile)), 80))
        if args.transcript is not None:
            with open(args.transcript, 'w') as f:
                f.write(transcription_text)
    elif args.type == "text":
        origfile = args.input
        with open(origfile, 'r', encoding='UTF-8') as f:
            transcription_text = f.read()
    return transcription_text

def main(args):
    transcription_text = process_input_file(args)
    print("-- 文字起こし --")
    print(transcription_text)

    all_token_count = len(encoding.encode(transcription_text))
    print("all_token", all_token_count)

    # トークン数が上限を超えていたら分割して要約
    if all_token_count > MAX_TOKEN:
        blocks = split_by_token(transcription_text, MAX_TOKEN, '\n')
        sumally = ''
        print("-- 部分要約 --")
        for block in blocks:
            suma = summarize(block) + '\n'
            print('\n'.join(japanese_wrap(suma)))
            sumally += suma
        print("final_sum_token", len(encoding.encode(sumally)))
    else:
        sumally = transcription_text

    final_sumally = summarize(sumally)
    print('-- 全体要約 --')
    print('\n'.join(japanese_wrap(final_sumally)))

    if args.summary is not None:
        with open(args.summary, 'w') as f:
            f.write("-- 部分要約-- \n")
            f.write('\n'.join(japanese_wrap(sumally)))
            f.write("-- 全体要約-- \n")
            f.write('\n'.join(japanese_wrap(final_sumally)))

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        prog='openai-summarize.py',
        usage='OpenAI Summarizer(Whisper API, GPT-3.5)',
        add_help=True,
    )

    argparser.add_argument('-i', '--input', help='input file(audio/text)', required=True)
    argparser.add_argument('-t', '--type', help='input file type (text | audio)', choices=["audio", "text"], required=True)
    argparser.add_argument('-ot', '--transcript', help='output transcript text')
    argparser.add_argument('-os', '--summary', help='output summary text')

    args = argparser.parse_args()
    main(args)
