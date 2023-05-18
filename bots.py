import asyncio
import json
import os
import random
import re
import time
import ast
from datetime import datetime
from EdgeGPT import Chatbot, ConversationStyle
from Bard import Chatbot as bardChatbot
from freeGPT import gpt3
import requests
import pandas as pd
from dotenv import load_dotenv
import poe

load_dotenv(dotenv_path='slackmidjourney/.env')

PROXY="http://127.0.0.1:7890"

def genPost(title,tags,publishTime,author,mj_prmt,post):
    randInt=random.randint(0, 3)
    template = '''
---
title: "{title}"
date: {date}
draft: true
tags: {tags}
author: {author}
thumbnail: {mj_prmt}{imgNum}_384_N.webp
---\n
![]({mj_prmt}{imgNum}.webp)
\n
{post}\n\n
            '''.format(
        title=title,
        date=publishTime.strftime('%Y-%m-%dT%H:%M:%S-06:00'),
        tags=tags,
        author=author,
        mj_prmt=mj_prmt,
        imgNum=randInt,
        post=''.join(x.strip() for x in post.split('/n'))
    )
    path='content/posts/'
    with open(path + '/%s.md' % title, 'w') as f:
        f.write(template)
    df = pd.read_csv('slackmidjourney/midjourney.csv', index_col='prompt')
    if not mj_prmt in df.index:
        mj = PassPromptToSelfBot(mj_prmt, int(os.environ["MJCHNSAVE"]))
        if mj.status_code != 204:
            pass
    updateThumbnail(path, mj_prmt)
    return True

def vikaData(id:str):
    headersVika = {
        'Authorization': 'Bearer '+os.environ['VIKA'],
        'Connection': 'close'
    }
    vikaUrl = 'https://api.vika.cn/fusion/v1/datasheets/dstMiuU9zzihy1LzFX/records?viewId=viwoAJhnS2NMT&fieldKey=name'
    vikajson = json.loads(requests.get(vikaUrl, headers=headersVika).text)['data']['records']
    return [x['fields']['value'] for x in vikajson if x['recordId'] == id][0]

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
        'authorization': dcToken
    }
    response = requests.post("https://discord.com/api/v9/interactions",
                             json=payload, headers=header)
    return response

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
        if retry==0 and mj_prmt not in df.index:
            print('not exist: '+mj_prmt)
            return

    for filename in filelist:
        if not filename.endswith('.md'):
            continue
        with open(path+filename, 'r') as f:
            data = f.read()
            new_data = data.replace(mj_prmt,df.at[mj_prmt,'url'])
        with open(path+filename, 'w') as f:
            f.write(new_data)

class Bot():
    def __init__(self):
        self.poeClient = None
        self.bardBot=None
        self.bingBot = None

    def bard(self,queryText:str):
        if self.bardBot is None:
            self.bardBot = bardChatbot(vikaData('recrhOrBcIgNl'))
        reply = self.bardBot.ask(queryText)
        return reply['content']

    def bing(self,queryText:str):
        reply_text = None
        if self.bingBot is None:
            self.bingBot = asyncio.run(Chatbot.create(cookie_path='./cookies.json', proxy=PROXY))
        reply = asyncio.run(self.bingBot.ask(prompt=queryText, conversation_style=ConversationStyle.balanced,
                                         wss_link="wss://sydney.bing.com/sydney/ChatHub"))
        if reply:
            reply_text = reply["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
        return reply_text.replace('"',' ')

    def poeReply(self,prompt:str):
        if self.poeClient is None:
            self.poeClient = poe.Client(vikaData('recsHwgXPa010'), proxy=PROXY)
        replyTxt=None
        llm='chinchilla'
        self.poeClient.send_chat_break(llm)
        for reply in self.poeClient.send_message(llm, prompt, with_chat_break=True):
            replyTxt = reply['text']
        return replyTxt.replace('",\n}','"}')

    def youReply(self,prompt:str):
        replyTxt= gpt3.Completion.create(prompt=prompt, proxy=PROXY).text
        return replyTxt.replace('",\n}', '"}')

    def tidyPost(self,bingReply,gpt='bard'):
        prompt = "```\n%s\n```" % bingReply + "plz rewrite as an blog post and output python dict format with tripple apostrophe {'title'':'''text''','tags':[text list],'post':'''markdown'''}"
        if gpt=='poe':
            replyTxt = self.poeReply(prompt)
            if not replyTxt.endswith('}'):
                if '"""' in replyTxt:
                    replyTxt += '"""}'
                else:
                    replyTxt += '}'
        elif gpt == 'you':
            replyTxt = self.youReply(prompt)
        else:
            replyTxt = self.bard(prompt)
        match = re.findall(r'{[^{}]*}', replyTxt)
        content = match[-1]
        post = ast.literal_eval(content)
        for k, v in post.items():
            print('%s:%s' % (k, v))
        return post

dcToken = vikaData('recNIX08aLFPB')