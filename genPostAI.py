import asyncio
import datetime
import json
import os
import random
import re
import time
import sys
import ast

import yaml
from EdgeGPT import Chatbot, ConversationStyle
from freeGPT import gpt3
import requests
import pandas as pd
from dotenv import load_dotenv
import poe

load_dotenv(dotenv_path='slackmidjourney/.env')

def PassPromptToSelfBot(prompt: str,dcChannel:int):
    payload = {"type": 2, "application_id": "936929561302675456", "guild_id": int(os.environ["MJSEVERID"]),
               "channel_id":dcChannel, "session_id": "2fb980f65e5c9a77c96ca01f2c242cf6",
               "data": {"version": "1077969938624553050", "id": "938956540159881230", "name": "imagine", "type": 1,
                        "options": [{"type": 3, "name": "prompt", "value": prompt}],
                        "application_command": {"id": "938956540159881230",
                                                "application_id": "936929561302675456",
                                                "version": "1077969938624553050",
                                                "default_permission": True,
                                                "default_member_permissions": None,
                                                "type": 1, "nsfw": False, "name": "imagine",
                                                "description": "Create images with Midjourney",
                                                "dm_permission": True,
                                                "options": [{"type": 3, "name": "prompt",
                                                             "description": "The prompt to imagine",
                                                             "required": True}]},
                        "attachments": []}}

    header = {
        'authorization': os.environ["DCTOKEN"]
    }
    response = requests.post("https://discord.com/api/v9/interactions",
                             json=payload, headers=header)
    return response
def getTopic(bingReply):
    prompt='```\n%s\n```'%bingReply+'\n'+'summarize the topics and reply in json format liked {"topic1": topic content}'
    replyTxt=gpt3Reply(prompt)
    match = re.findall(r'{[^{}]*}', replyTxt)
    content = match[-1]
    topics = json.loads(content,strict=False)
    for k, v in topics.items():
        print('%s:%s' % (k, v))
    random_key = random.choice(list(topics.keys()))
    return random_key,topics[random_key]

def tidyPost(bingReply):
    prompt = '```\n%s\n```' % bingReply + "plz rewrite as an blog post in python dict format with apostrophe {'title':text,'tags':[text list],'post':markdown}"
    replyTxt=gpt3Reply(prompt)
    if not replyTxt.endswith('}'):
        if '"""' in replyTxt:
            replyTxt+='"""}'
        else:
            replyTxt+='}'
    post = ast.literal_eval(replyTxt)
    for k, v in post.items():
        print('%s:%s' % (k, v))
    return post

def updateThumbnail(path:str,mj_prmt:str):
    filelist=os.listdir(path)
    retry=2
    while retry>0:
        time.sleep(30 * retry * retry)
        df=pd.read_csv('slackmidjourney/midjourney.csv')
        df.drop_duplicates(subset='prompt',keep='last',inplace=True)
        df.set_index('prompt',inplace=True)
        if not mj_prmt in df.index:
            print('retry to read prompt '+mj_prmt)
        else:
            break
        retry -= 1

    for filename in filelist:
        if not filename.endswith('.md'):
            continue
        with open(path+filename, 'r') as f:
            data = f.read()
            new_data = data.replace(mj_prmt,'https://cdn.midjourney.com/%s/0_'%df.at[mj_prmt,'hash'])
        with open(path+filename, 'w') as f:
            f.write(new_data)
def bing(queryText):
    reply_text = None
    reply = asyncio.run(bingBot.ask(prompt=queryText, conversation_style=ConversationStyle.balanced,
                                     wss_link="wss://sydney.bing.com/sydney/ChatHub"))
    if reply:
        reply_text = reply["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
    return reply_text.replace('"',' ')

def gpt3Reply(prompt:str):
    replyTxt=None
    if poeClient:
        llm='chinchilla'
        poeClient.send_chat_break(llm)
        for reply in poeClient.send_message(llm, prompt, with_chat_break=True):
            replyTxt = reply['text']
    if replyTxt is None:
        replyTxt= gpt3.Completion.create(prompt=prompt, proxy='127.0.0.1:7890').text
    return replyTxt.replace('",\n}','"}')

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

        selfintro='I am a {career},I am making a blog that {intro}, '.format(career=career,intro=v)
        blogDiscription = selfintro + " please help me to find recent hot topics on sites {sites} .".format(sites=config['params']['sites'])
        print(authorName,'\n',blogDiscription)
        replyTxt1 = bing(blogDiscription)
        topic,topicIntro=getTopic(replyTxt1)

        postDiscription = selfintro + "plz help me to write a blog post about {topic}({intro})".format(career=career,topic=topic,intro=topicIntro)
        print(authorName,'\n',postDiscription)
        replyTxt2 = bing(postDiscription)
        post = tidyPost(replyTxt2)
        tags=','.join(post['tags'])
        mj_prmt=config['params']['mj-suffix'][k].replace('[tags]',tags)+' --ar 2:1'
        template='''
---
title: "{title}"
date: {date}
draft: true
tags: {tags}
author: {author}
thumbnail: {mj_prmt}0_384_N.webp
---\n
![]({mj_prmt}0.webp)
\n
{post}\n\n
        '''.format(
            title=post['title'],
            date=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
            tags=post['tags'],
            author=authorName,
            mj_prmt=mj_prmt,
            post=post['post']
        )
        with open(path+'/%s.md'%post['title'], 'w') as f:
            f.write(template)
        if PassPromptToSelfBot(mj_prmt,int(os.environ["MJCHNSAVE"])).status_code==204:
            updateThumbnail(path,mj_prmt)
    with open('slackmidjourney/midjourney.csv','') as f:
        f.write('prompt,hash')

if __name__=='__main__':
    bingBot = asyncio.run(Chatbot.create(cookie_path='./cookies.json',proxy="http://127.0.0.1:7890"))
    poeClient = poe.Client(os.environ["PB"],proxy='http://127.0.0.1:7890')
    genPosts(sys.argv[-1])