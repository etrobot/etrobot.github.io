#!/bin/bash
git config --global user.email "etrobot@outlook.com"
git config remote.origin.url "https://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@github.com/etrobot/cfpage"
curPath="$(dirname "$0")"
cd $curPath || exit
cd .. && /opt/homebrew/bin/hugo -D && git add . && git commit -m 'daily' && git push
cd public && git add . && git commit -m 'daily' && git push