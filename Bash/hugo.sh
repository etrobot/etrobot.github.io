#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd .. && hugo -D && git add . && git commit -m 'daily' && git push
cd public && git add . && git commit -m 'daily' && git push