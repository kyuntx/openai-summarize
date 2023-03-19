#!/bin/env python3
# Dependency:
#  pip install BeautifulSoup4 pandas chardet

import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
import textwrap
import chardet


def fetch_html(url):
    """Fetch HTML from the specified URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def detect_encoding(content):
    """Detect the character encoding of the given content."""
    return chardet.detect(content)['encoding']


def convert_to_utf8(content, encoding):
    """Convert content to UTF-8 using the provided encoding."""
    return content.decode(encoding).encode('utf-8')


def remove_scripts_and_styles(soup):
    """Remove script and style tags from BeautifulSoup object."""
    for script in soup(["script", "style"]):
        script.decompose()


def extract_text(html):
    """Extract text from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    remove_scripts_and_styles(soup)
    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def main(url):
    content = fetch_html(url)
    encoding = detect_encoding(content)

    if encoding.lower() != "utf-8":
        content = convert_to_utf8(content, encoding)

    text = extract_text(content)
    formatted_text = '\n'.join(textwrap.wrap(text, 80))
    print(formatted_text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    main(url)
