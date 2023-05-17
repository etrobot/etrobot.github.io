import re
import sys
import yaml
from bots import *

def getTopic(bingReply):
    prompt='```\n%s\n```'%bingReply+'\n'+'summarize the topics and reply in json format liked {"topic1": topic content}'
    replyTxt=bot.gpt3Reply(prompt)
    match = re.findall(r'{[^{}]*}', replyTxt)
    content = match[-1]
    topics = json.loads(content,strict=False)
    for k, v in topics.items():
        print('%s:%s' % (k, v))
    random_key = random.choice(list(topics.keys()))
    return random_key,topics[random_key]

def genPosts(profileKey,path='content/posts/'):
    with open("config.yaml", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)  # 也可以不写Loader=yaml.FullLoader
    if profileKey != sys.argv[0] and profileKey not in list(config['params']['profiles'].keys()):
        profileKey = random.choice(list(config['params']['profiles'].keys()))

    for k,v in config['params']['profiles'].items():
        if profileKey != sys.argv[0] and k != profileKey:
            continue
        author= k.split('-')
        career=' '.join(author[1:])
        authorName=' '.join(x.capitalize() for x in author)

        selfintro='You are a {career} making a blog that {intro}, '.format(career=career,intro=v)
        blogDiscription = selfintro + " please find May-2023 hot topics on sites {sites} .".format(sites=config['params']['sites'])
        print(authorName,'\n',blogDiscription)
        replyTxt1 = bot.bing(blogDiscription)
        topic,topicIntro=getTopic(replyTxt1)

        postDiscription = selfintro + "plz write a blog post about {topic}({intro})".format(career=career,topic=topic,intro=topicIntro)
        print(authorName,'\n',postDiscription)
        replyTxt2 = bot.bing(postDiscription)
        post = bot.tidyPost(replyTxt2)
        tags=','.join(post['tags'])
        mj_prmt=config['params']['mj-suffix'][k].replace('[tags]',tags)+' --ar 2:1'
        genPost(post['title'], post['tags'], authorName, mj_prmt, post['post'])

    with open('slackmidjourney/midjourney.csv', '') as f:
        f.write('prompt,hash')

if __name__=='__main__':
    bot = Bot()
    dcToken = vikaData('recNIX08aLFPB')
    genPosts(sys.argv[-1])