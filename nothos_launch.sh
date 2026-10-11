#!/bin/bash

cd "$HOME/Downloads/nothos_v5" || exit 1
source .venv/bin/activate

clear

# Medusa — preferred 45×25
chafa --size 45x25 assets/medusa.png

echo

# Gold FIGlet title
printf '\033[1;38;2;212;175;55m'
figlet -f slant NOTHOS
printf '\033[0m'

# Cyan subtitle
printf '\033[1;38;2;56;189;248m'
echo '  GREEK RESEARCH • SOURCE FIRST'
printf '\033[0m'

# Purple edition label
printf '\033[38;2;168;85;247m'
echo '  MEDUSA EDITION • ANCIENT TEXT CORPUS'
printf '\033[0m'

echo

if [ "$#" -gt 0 ]; then
    exec python nothos.py "$@"
fi
