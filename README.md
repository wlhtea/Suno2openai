# Suno2openai
基于[SunoSongsCreator](https://github.com/yihong0618/SunoSongsCreator/edit/main/README.md)逆向工程进行优化，以openai格式调用suno api，并将cookie保存为数据库，实现cookie池调用
(理论上可以，至于可不可以你们试试，本人没有那么多时间去部署在实际环境中，如果有大佬愿意帮忙测试一下！万分感谢)

# 获取cookie
- 登录 https://app.suno.ai/ 。
- 使用 `Chrome` 或其他浏览器检查网络请求（F12 -> XHR）。
- XHR 查找此 url 中的 cookie -> https://clerk.suno.ai/v1/client?_clerk_js_version=4.70.5 
- 复制 cookie。
- ![image](https://github.com/wlhtea/Suno2openai/assets/115779315/268ec4ec-145a-486c-a42a-092a3b9e8412)

# 如何使用
# 克隆本仓库
```
git clone https://github.com/wlhtea/Suno2openai.git
```

```
cd ./Sun2opeani
```

```
pip install -r requirements.txt
```

```
cd ./suno_resvered
```

# 配置./suno_resvered/setting.py
先创建一个sunoapi的数据，然后在setting.py中填入密码和用户（如果你不是root）
```
DATABASE_URI = 'mysql+pymysql://root:密码@127.0.0.1/sunoapi'
```

# 打开./suno_resvered/update_cookie_sqldata.py
将一开始复制的cookie填入cookies中，如果有多个以列表标准形式即可
```
from uilt.init_sql import insert_or_update_cookie,get_remaining_count
from suno import SongsGen
cookies = \
    ["""cookie""",
    """cookie02""",
    """......""",
    """cookie0n"""]
for cookie in cookies:
    try:
        remaining_count = SongsGen(cookie).get_limit_left()
        insert_or_update_cookie(cookie, remaining_count)
    except:
        insert_or_update_cookie(cookie,0)
```

## 初始化数据库
```
cd ./uilt
python init_sql.py
```

## 运行后端接口
```
cd ../
python main.py
```


# 然后就可以进行测试了，例如：
## 再打开一个命令框
```
cd ./suno_resvered/uilt
python test.py
```

效果（至于可不可以接入one-api或者new-api，不知道大概率不太可以，需要进一步优化）：
![image](https://github.com/wlhtea/Suno2openai/assets/115779315/28fa7659-9a95-4f2b-a099-27461f7dbf2f)

# 待优化：
- cookie池不是轮询是随机，有任务在执行时会报错
- 没有做请求的优化，并发和处理可能什么什么的
- 还有一些问题吧，等待大家的pull。

## 如果这个项目对你有帮助请点个小小的star吧
