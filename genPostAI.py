import yaml

# 打开配置文件
f = open("config.yaml", encoding="utf-8")
config = yaml.load(f, Loader=yaml.FullLoader)  # 也可以不写Loader=yaml.FullLoader
for k,v in config['params']['profiles'].items():
    print(k,v)