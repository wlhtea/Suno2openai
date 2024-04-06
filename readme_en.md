[中文](https://github.com/wlhtea/Suno2openai/blob/main/README.md)   English

# Suno2openai
This is a project based on the combination of [SunoSongsCretor](https://github.com/yihong0618/SunoSongsCreator) and [Suno-API](https://github.com/SunoAI-API/Suno-API). I integrated and standardized the interface to openai format.

## Project features
- Support Openai format call and streaming output content.
- Support chat-next-web and other front-end projects.
- Support docker-compose deployment
- Supports multiple cookies for polling

## Follow-up plan
- Add queue wait optimization for requests
- Add support for custom parameters (tags, prompt, style and continuation of songs)
- I'll have a chance to write a front-end page that benchmarks against the official website.
- If there are any suggestions you can ask me 邮箱:1544007699@qq.com

# How to use Suno2openai
If any of these steps are stuck, please gpt yourself or search for solutions!
## Clone project to server
``
git clone https://github.com/wlhtea/Suno2openai.git
```

## docker-compose
## Go to the project file
```
cd . /Suno2openai
```

## Create a database
Create a database with the name WSunoAPI
``` mysql
CREATE DATABASE IF NOT EXISTS WSunoAPI
```

Then fill the root password into the corresponding location in the init_sql.py file (usually root, if you have your own name please change it)
Remote database set the database permissions to ip access, fill in the project ip address, and fill in the rest as usual.
``
    conn = await aiomysql.connect(host='127.0.0.1', port=3306,
                                  user='root', password='12345678')
```

**Additional content**
Open update_cookie_to_sql.py and fill the cookie with cookies
```
cookies = \
    ['cookie1','cookie2']
```

## Run docker
- Security group: here it will open port 8000, please take care to open this port
- Certificate issues: secondly if you want to access projects like newapi and chat-next-web, if you deploy these projects as https, then the reverse generation URL of this project should be https as well, otherwise these projects will reject http services

``
docker compose build && docker compose up
```

# Deploy locally

Step by step. I'm lazy, I'm writing it all together.
```
cd . /Suno2openai
pip3 install -r requirements.txt
uvicorn main:app 
```

# Access to new-api(one-api)
Just fill in the proxy in the channel to the project address, that is, http://(server IP):8000, it is recommended to use https and domain name to fill in the proxy address
! [image](https://github.com/wlhtea/Suno2openai/assets/115779315/0b4d3741-b8d4-4aa8-9337-86d85868ed0b)

# Effect
! [chat-next-web effect image](https://github.com/wlhtea/Suno2openai/)
*** Translated with www.DeepL.com/Translator (free version) ***

