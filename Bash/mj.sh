#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd .. && slackmidjourney/venv/bin/python -u updateThumbnail.py;