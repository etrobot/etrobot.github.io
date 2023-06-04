import time
from datetime import datetime
import json
import os
import random
import re
import ast
from Bard import Chatbot as bardChatbot
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv(dotenv_path='slackmidjourney/.env')

PROXY="http://127.0.0.1:7890"

def switchMost(dcChannel:int,mode='relax'):
    payload={
        'relax':{"type":2,"application_id":"936929561302675456","guild_id":int(os.environ["MJSEVERID"]),"channel_id":dcChannel,"session_id":"5172390b7c03d655c81025d3fe4c3869","data":{"version":"987795926183731232","id":"972289487818334213","name":"relax","type":1,"options":[],"application_command":{"id":"972289487818334213","application_id":"936929561302675456","version":"987795926183731232","default_member_permissions":None,"type":1,"nsfw":False,"name":"relax","description":"Switch to relax mode","dm_permission":True,"contexts":None},"attachments":[]},"nonce":"1112233639413809152"}
        ,'fast':{"type":2,"application_id":"936929561302675456","guild_id":int(os.environ["MJSEVERID"]),"channel_id":dcChannel,"session_id":"02b02fc20b3620813cc6f5eb1f63d59f","data":{"version":"987795926183731231","id":"972289487818334212","name":"fast","type":1,"options":[],"application_command":{"id":"972289487818334212","application_id":"936929561302675456","version":"987795926183731231","default_member_permissions":None,"type":1,"nsfw":False,"name":"fast","description":"Switch to fast mode","dm_permission":True,"contexts":None},"attachments":[]},"nonce":"1112245417271099392"}
    }
    header = {
        'authorization': dcToken
    }
    response = requests.post("https://discord.com/api/v9/interactions",
                             json=payload[mode], headers=header,proxies={'https':'http://127.0.0.1:7890'})
    return response

def genPost(title,tags,publishTime,author,mj_prmt,post,reUsedPrmpt=False):
    path='content/posts/'
    if reUsedPrmpt:
        df = pd.read_csv('slackmidjourney/midjourney.csv')
        for tag in tags:
            mjdf = df[df['prompt'].str.contains(tag)]
            if len(mjdf)>0:
                mj_prmt=mjdf.sample()['prompt'].values[0]
                break
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
    with open(path + '/%s.md' % title, 'w') as f:
        f.write(template)
    if not reUsedPrmpt:
        mj = PassPromptToSelfBot(mj_prmt, int(os.environ["MJCHNSAVE"]))
        if mj.status_code == 204:
            with open('midjourney.csv', mode='a') as file:
                file.write('\n"%s", %s, %s' % (mj_prmt,'',''))
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
                             json=payload, headers=header,proxies={'https':PROXY})
    return response

class Bot():
    def __init__(self):
        self.poeClient = None
        self.bardBot=None
        self.bingBot = None

    def bard(self,queryText:str):
        if self.bardBot is None:
            self.bardBot = bardChatbot(vikaData('recrhOrBcIgNl'),proxy=PROXY)
        reply = self.bardBot.ask(queryText)
        if reply['content'].startswith('I’m a large language model'):
            return
        return reply['content']

    def tidyPost(self,reply):
        prompt = "```\n%s\n```" % reply + "plz rewrite as an blog post and output as python dict {'title'':'''text''','tags':[text list],'post':'''markdown'''}"
        retry = 2
        while retry>0:
            try:
                replyTxt = self.bard(prompt)
                match = re.findall(r'{[^{}]*}', replyTxt)
                content = match[-1]
                post = ast.literal_eval(content)
                for k, v in post.items():
                    print('%s:%s' % (k, v))
                return post
            except Exception as e:
                print(e)
                prompt+=',plz make sure the output format is a python dict'
                retry-=1
                time.sleep(10)
        return None

dcToken = vikaData('recNIX08aLFPB')