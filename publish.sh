cd $(dirname "$0")

hexo clean
hexo g
git add .
git commit
git push
hexo d