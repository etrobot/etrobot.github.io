# import asyncio
import json

import pandas as pd
import requests


# import pandas as pd
# import freeGPT

# def switchMost(mode='relax'):
#     payload={
#     'relax':{"type":2,"application_id":"936929561302675456","guild_id":"1111931476821414000","channel_id":"1111931477328941098","session_id":"5172390b7c03d655c81025d3fe4c3869","data":{"version":"987795926183731232","id":"972289487818334213","name":"relax","type":1,"options":[],"application_command":{"id":"972289487818334213","application_id":"936929561302675456","version":"987795926183731232","default_member_permissions":None,"type":1,"nsfw":False,"name":"relax","description":"Switch to relax mode","dm_permission":True,"contexts":None},"attachments":[]},"nonce":"1112233639413809152"}
#     ,'fast':{"type":2,"application_id":"936929561302675456","guild_id":"1111931476821414000","channel_id":"1111931477328941098","session_id":"02b02fc20b3620813cc6f5eb1f63d59f","data":{"version":"987795926183731231","id":"972289487818334212","name":"fast","type":1,"options":[],"application_command":{"id":"972289487818334212","application_id":"936929561302675456","version":"987795926183731231","default_member_permissions":None,"type":1,"nsfw":False,"name":"fast","description":"Switch to fast mode","dm_permission":True,"contexts":None},"attachments":[]},"nonce":"1112245417271099392"}
#     }
#     header = {
#         'authorization': 'MTAxMjM3NDI4MDcxOTMyMzI4Ng.GlewgJ.dSAwJTfI8f5Y08x8F30zsGK_l-v4lKhZkyAEF0'
#     }
#     response = requests.post("https://discord.com/api/v9/interactions",
#                              json=payload[mode], headers=header,proxies={'https':'http://127.0.0.1:7890'})
#     return response
#
# print(switchMost('relax'))

# async def main():
#         try:
#             resp = await freeGPT.gpt4.Completion.create("如何在网上赚钱",proxies="http://127.0.0.1:7890")
#             print(f"🤖: {resp}")
#         except Exception as e:
#             print(f"🤖: {e}")
#
#
# asyncio.run(main())
# def tencentNews(symbol:str):
#     params = {
#         'page': '1',
#         'symbol': symbol,
#         'n': '51',
#         '_var': 'finance_notice',
#         'type': '2',
#         # '_': '1690699699389',
#     }
#
#     response = requests.get(
#         'https://proxy.finance.qq.com/ifzqgtimg/appstock/news/info/search',
#         params=params,
#         headers={"user-agent": "Mozilla","Connection":"close"}
#     )
#     df = pd.DataFrame(json.loads(response.text[len('finance_notice='):])['data']['data'])
#     df.to_csv('tNews.csv')
#     return df
#
# tencentNews('sz002236')

import os

def replace_author_in_md_files(folder_path, old_author, new_author):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()

                # 替换author
                new_content = content.replace(f"author: {old_author}", f"author: {new_author}")

                # 将替换后的内容写回文件
                with open(file_path, "w") as f:
                    f.write(new_content)

def get_creation_time(file_path):
    """
    获取文件的创建时间
    """
    stat = os.stat(file_path)
    try:
        return stat.st_birthtime
    except AttributeError:
        # 在某些系统上，st_birthtime可能不可用，使用st_mtime代替
        return stat.st_mtime

if __name__ == "__main__":
    folder_path = "/Users/franklin/Documents/FrontEnd/cfpage/content/post/"  # 替换成你指定的文件夹路径
    # old_author = "Frank Lin"
    # new_author = "Frank"
    #
    # replace_author_in_md_files(folder_path, old_author, new_author)
    sorted_files = sorted(os.listdir(folder_path), key=lambda x: get_creation_time(os.path.join(folder_path, x)))

    for ff in sorted_files:
        if ff.endswith('.md'):
            with open(folder_path+ff, "r") as f:
                content = f.read()
                for line in content.split("\n"):
                    if line.startswith("title:"):
                        title = line[len("title:"):].strip()
                        print(title+'https://aicube.fun/post/'+ff[:-3].lower().replace(' ','-'))
