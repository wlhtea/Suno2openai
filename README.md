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
## 进入项目文件
```
cd ./Suno2openai
```

## 创建数据库
创建一个名字为WSunoAPI的数据库
```mysql
CREATE DATABASE IF NOT EXISTS WSunoAPI
```

然后将root密码填入init_sql.py文件中对应的位置（一般是root，如果你有自己的名字请自行修改）
```
    conn = await aiomysql.connect(host='127.0.0.1', port=3306,
                                  user='root', password='12345678')
```

## 运行docker
- 安全组：这里会打开8000端口，请注意开放该端口
- 证书问题：其次如果要接入newapi和chat-next-web这类项目，如果你部署这些项目是https，那么这个项目的反代网址应该也是https，否则这些项目会拒绝http服务

```
docker compose build && docker compose up
```

# 本地部署

一步一步来 我比较懒写一起了
```
cd ./Suno2openai
pip3 install -r requirements.txt
uvicorn main:app 
```

# 接入new-api(one-api)
只要在渠道中的代理填写项目地址即可，也就是http://(服务器IP):8000，建议用https和域名进行填入代理地址
![image](https://github.com/wlhtea/Suno2openai/assets/115779315/0b4d3741-b8d4-4aa8-9337-86d85868ed0b)
