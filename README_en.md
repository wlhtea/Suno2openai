[Chinese](https://github.com/wlhtea/Suno2openai/blob/main/README.md) English

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
- I'll have a chance to write a front-end page that benchmarks the official website.
- If there are any suggestions you can ask me 邮箱:1544007699@qq.com

# docker-compose deployment (updated 2024/4/7:18:18)

## Clone project to server
```
git clone https://github.com/wlhtea/Suno2openai.git
```

## Create a database
- Create a database with whatever name you want and a password you want to remember.

## **Modify env.example to .env, and fill in the content according to the format....
```
BASE_URL=https://studio-api.suno.ai
SESSION_ID=cookie (don't bother with this, don't even delete this sentence)
SQL_name=database name
SQL_password=database password
SQL_IP=database host IP
SQL_dk=exposed port of database host IP (3306)
```
## Go to the project file
```
cd . /Suno2openai
```
**Additional content**
Open update_cookie_to_sql.py and fill the cookie with cookies
![location of cookie](https://github.com/wlhtea/Suno2openai/assets/115779315/6edf9969-9eb6-420f-bfcd-dbf4b282ecbf)

```
cookies = \
    ['cookie1','cookie2']
```

## Run docker
- Security group: here it will open port 8000, please take care to open this port
- Certificate issues: secondly if you want to access projects like newapi and chat-next-web, if you deploy these projects as https, then the reverse generation URL of this project should be https as well, otherwise these projects will reject http services

```
docker compose build && docker compose up
```

# For some reason filling in the deployment url directly in chat-next-web works for sunoapi, but not for new-api. It worked the other day, but then I changed the location and it worked. I don't remember now, I have to look at the new-api source again.

# Local deployment
(This is the first part, the local deployment is actually the same as docker-compose)

# Access to new-api (one-api)
As long as the agent in the channel to fill in the project address can be, that is, http:// (server IP):8000, it is recommended to use https and domain name to fill in the agent address
![image](https://github.com/wlhtea/Suno2openai/assets/115779315/0b4d3741-b8d4-4aa8-9337-86d85868ed0b)

# Effect
![chat-next-web effect image](https://github.com/wlhtea/Suno2openai/assets/115779315/6495e840-b025-4667-82f6-19116ce71c8e)


## If there are bosses willing to accept me, a three-book pup with one more than a two-book, and two more than a one-book, to do an internship, you can send me an email.
- Email 1544007699@qq.com
- Junior Resume not yet written Data Analytics and Front and Back End (Moderately rich competition experience Moderately successful)
- If there is a boss who wants to privatize the deployment of large models I can try.

Please give me a star if this project helped you! If not, please give me a star.
The project may have some shortcomings and a lot of room for improvement! I hope all of you who have the ability and ideas can support this project, thank you very much!
This is my [staging area](https://token.w-l-h.xyz) provide openai interface
*** Translated with www.DeepL.com/Translator (free version) ***

