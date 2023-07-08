import urllib

import feedparser
from bots import *
import yaml
from urllib.parse import urlparse
import urllib.request
from datetime import timedelta
import time
from urllib.request import ProxyHandler, build_opener

def getRss():
    urls =[
        'https://news.google.com/rss/search?q=when:24h+allinurl:www.bloomberg.com\/economics&hl=en-US&gl=US&ceid=US:en',
        'https://www.ft.com/news-feed?format=rss.&page=36',
        'https://feeds.a.dj.com/rss/RSSWSJD.xml',
        # 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',
        # 'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml',
        # 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
        # 'https://feeds.a.dj.com/rss/RSSLifestyle.xml'
    ]
    proxy_handler = ProxyHandler({'https': PROXY})

    df = pd.DataFrame(columns=['link', 'title', 'summary', 'published'])

    for url in urls:
        print(url)
        feed = feedparser.parse(url,handlers=[proxy_handler])
        for result in feed['entries']:
            if 'summary' not in result.keys():
                continue
            print(result)
            link = result['link']
            title = result['title']
            summary = result['summary']
            source = urlparse(link).netloc
            if 'google.com' in link:
                link=result['link'].split("/articles/")[1].split("?oc=")[0]
                title=title.replace(' - Bloomberg','')
                summary=''
                source = urlparse(result['source']['href']).netloc
            published = datetime.fromtimestamp(time.mktime(result['published_parsed']))
            df = df._append({'link': link,'source':source, 'title': title, 'summary': summary, 'published': published}, ignore_index=True)
    hours=12
    df.drop_duplicates(subset='link',keep='first',inplace=True)
    df = df[(df['published'] <= datetime.now() - timedelta(hours=hours)) & (df['published'] >= datetime.now() - timedelta(hours=hours+24))]
    df.sort_values(by=['published'],ascending=False,inplace=True)
    df.to_csv('payedPosts.csv',index=False)
    return df

if __name__=='__main__':
    bot = Bot()
    authorDict={
        'www.ft.com':'jarvis-ft',
        'www.wsj.com': 'friday-wall',
        'www.bloomberg.com': 'ultron-bloom'
    }
    with open("config.yaml", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    hisDf=pd.read_csv('history.csv',index_col='link')
    switchMost(int(os.environ["MJCHNSAVE"]),'relax')
    for k,v in getRss().iterrows():
        if v['title'] in hisDf['title']:
            continue
        profileKey=authorDict[v['source']]
        author = profileKey.split('-')
        authorName = ' '.join(x.capitalize() for x in author)
        title = v['title']
        promptSearch="Summaize key points of this aricle:\n '''\nTitle: %s\nLink:%s\n %s\n'''"%(v['title'],v['link'],v['summary'])
        print(promptSearch)
        bardReply = bot.bard(promptSearch)
        if bardReply is None or 'I am a large language model' in bardReply:
            continue
        print(bardReply)
        post=bot.tidyPost(bardReply)
        if post is None:
            continue
        tags = ','.join(post['tags'])
        reUsetPrompt=len([x for x in ['debt','war','politics','Musk','AI','ai'] if x in post['tags']])
        mj_prmt = 'news photo about %s'%tags + ' --ar 2:1'
        if '...' in v['title']:
            title = post['title']
        if genPost(title,post['tags'],v['published'],authorName,mj_prmt,post['post'],reUsetPrompt>0):
            with open('history.csv', mode='a') as file:
                file.write('\n"%s","%s"' %(v['link'],v['title']))
        time.sleep(10)
    switchMost(int(os.environ["MJCHNSAVE"]),'fast')