#!/bin/bash
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
curPath="$(dirname "$0")"
cd $curPath || exit
cd .. && slackmidjourney/venv/bin/python -u AIReadPayed.py;