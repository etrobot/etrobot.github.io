cd $(dirname "$0")
git pull
hexo clean
hexo g
git add .
git commit
git push
hexo d