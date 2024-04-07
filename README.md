中文   [English](https://github.com/wlhtea/Suno2openai/blob/main/README_en.md)

# Suno2openai
这是一个基于[SunoSongsCretor](https://github.com/yihong0618/SunoSongsCreator)和[Suno-API](https://github.com/SunoAI-API/Suno-API)两个项目结合而成，我进行整合和接口标准化为openai格式

## 项目特点
- 支持Openai格式调用并流式输出内容
- 支持chat-next-web等前端项目的使用
- 支持docker-compose部署
- 支持多个cookie进行轮询使用

## 后续计划
- 添加对请求的队列等待优化
- 添加自定义参数支持（tags、prompt、style和对歌曲的续写）
- 有机会写一个对标官网的前端页面
- 如果有什么建议可以向我提出 邮箱:1544007699@qq.com

# 如何使用Suno2openai
如果其中有哪一步卡住了，请自行gpt或者搜索相关解决方案！
## 克隆项目到服务器
```
git clone https://github.com/wlhtea/Suno2openai.git
```

# docker-compose

## 创建数据库
创建一个数据库

## **修改env.example为.env,并按照格式进行填写内容**
```
BASE_URL=https://studio-api.suno.ai
SESSION_ID=cookie（不需要理会这个，甚至这句话都不用删）
SQL_name=数据库名称
SQL_password=数据库密码
SQL_IP=数据库主机IP
SQL_dk=数据库主机IP的暴露端口（3306）
```
## 进入项目文件
```
cd ./Suno2openai
```


**补充内容**
打开update_cookie_to_sql.py并将cookie填入cookies中
![cookie的位置](https://github.com/wlhtea/Suno2openai/assets/115779315/6edf9969-9eb6-420f-bfcd-dbf4b282ecbf)

```
cookies = \
    ['cookie1','cookie2']
```

## 运行docker
- 安全组：这里会打开8000端口，请注意开放该端口
- 证书问题：其次如果要接入newapi和chat-next-web这类项目，如果你部署这些项目是https，那么这个项目的反代网址应该也是https，否则这些项目会拒绝http服务

```
docker compose build && docker compose up
```

# 由于不知道什么愿因 在chat-next-web直接填入部署的网址，是可以对sunoapi进行调用 但是经过new-api就不行了 前几天也会但是当时 我改了一个位置就好了 现在不记得了又得去看new-api源码了

# 本地部署
（这一段先这样 本地二开的 其实和docker-compose一样的）

# 接入new-api(one-api)
只要在渠道中的代理填写项目地址即可，也就是http://(服务器IP):8000，建议用https和域名进行填入代理地址
![image](https://github.com/wlhtea/Suno2openai/assets/115779315/0b4d3741-b8d4-4aa8-9337-86d85868ed0b)

# 效果
![chat-next-web效果图](https://github.com/wlhtea/Suno2openai/assets/115779315/6495e840-b025-4667-82f6-19116ce71c8e)


## 如果有老板愿意接受我这个比二本多一本，比一本多两本的三本崽去实习可以发送邮件给我
- 邮箱 1544007699@qq.com
- 大三简历还没写 数据分析和前后端 (比赛经历中等丰富中等成绩)
- 如果有老板想要私有化部署大模型的我可以试试

该项目如果对你有帮助请给我点一个star吧！如果没有帮助也要给我点个star
项目可能存在一些不足的地方和很大的进步空间！希望各位有能力和想法的小伙伴可以支持一下这个项目，万分感谢！
这是我的[中转站](https://token.w-l-h.xyz)提供openai接口
