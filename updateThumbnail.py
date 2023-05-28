import os
import pandas as pd

def updateThumbnail():
    path = 'content/posts/'
    filelist = os.listdir(path)
    df = pd.read_csv('slackmidjourney/midjourney.csv')
    df.drop_duplicates('prompt', keep='last', inplace=True)
    df.set_index('prompt', inplace=True)
    for filename in filelist:
        if not filename.endswith('.md'):
            continue
        with open(path + filename, 'r') as f:
            data = f.read()
            new_data = data
            for k, v in df.iterrows():
                if '--ar 2:1' not in k:
                    continue
                prmtInMd=k[:k.index('--ar 2:1')+len('--ar 2:1')]
                if prmtInMd in data:
                    print(k, df.at[k, 'url'])
                    new_data = data.replace(prmtInMd, df.at[k, 'url'])
        with open(path + filename, 'w') as f:
            f.write(new_data)

updateThumbnail()