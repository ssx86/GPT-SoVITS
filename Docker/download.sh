#!/usr/bin/env bash

set -Eeuo pipefail

echo "Downloading models..."

aria2c --disable-ipv6 --input-file /workspace/Docker/links.txt --dir /workspace --continue

echo "Checking SHA256..."

parallel --will-cite -a /workspace/Docker/links.sha256 "echo -n {} | sha256sum -c"

# nltk models
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/taggers/averaged_perceptron_tagger.zip --dir /root/nltk_data/taggers --continue
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/taggers/averaged_perceptron_tagger_eng.zip --dir /root/nltk_data/taggers --continue
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/taggers/averaged_perceptron_tagger_ru.zip --dir /root/nltk_data/taggers --continue
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/taggers/averaged_perceptron_tagger_rus.zip --dir /root/nltk_data/taggers --continue
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/taggers/maxent_treebank_pos_tagger.zip --dir /root/nltk_data/taggers --continue
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/taggers/maxent_treebank_pos_tagger_tab.zip --dir /root/nltk_data/taggers --continue
aria2c --disable-ipv6 https://gitee.com/KnoDRy/nltk_data/raw/gh-pages/packages/corpora/cmudict.zip --dir /root/nltk_data/corpora --continue

cd /root/nltk_data/taggers
for f in ./*.zip; do
  python3 -m zipfile -e $f .
done

cd /root/nltk_data/corpora
for f in ./*.zip; do
  python3 -m zipfile -e $f .
done

cd /workspace
