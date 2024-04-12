中文 | [English](https://github.com/wlhtea/Suno2openai/blob/main/README.md)

# Suno2openai
> 基于 [SunoSongsCreator](https://github.com/yihong0618/SunoSongsCreator) 和 [Suno-API](https://github.com/SunoAI-API/Suno-API) 项目整合，提供符合OpenAI格式的接口标准化服务。

## 更新日志
- 2024.4.12 **完成对new-api和one-api**接入，选择openai调用，并填入项目部署地址（不需要/v1/）密钥空着即可。
- 2024.4.10 由于suno官方更新 部分项目功能无法使用 已经重新更改 在2024/4/10：15：04之前拉去的项目 请重新拉去即可 docker晚点更新(已更新，拉去时注意拉去版本号。)

## ✨ 项目特点
- **OpenAI格式调用**：支持流式输出内容。
- **前端兼容性**：适配 `chat-next-web` 等前端项目。
- **Docker部署**：简化部署流程，支持 `docker-compose`、`docker`。
- **多Cookie管理**：实现多个Cookie轮询使用。

## 🚀 后续计划
- 引入请求队列等待优化。
- 支持自定义参数（如 `tags`、`prompt`、`style` 及对歌曲的续写）。
- 探索开发类似官网的前端页面。
- 欢迎提出宝贵建议！📧 **邮箱**: 1544007699@qq.com
  
---

## 🫙 Docker部署

本教程提供如何使用特定的环境变量及端口映射来运行一个Docker容器的分步指导。为了本指南的目的，敏感信息如SQL名称、密码和IP地址将被替换为占位符。

## 前提条件

- 你的机器上安装了Docker。
- 你具有Docker命令行界面的基础知识。

## 操作步骤

1. **拉取Docker镜像**

   首先，确保你的机器上已经有了Docker镜像`wlhtea/suno2openai:0.1.0`。如果没有，你可以使用以下命令从Docker仓库中拉取它：

   ```bash
   docker pull wlhtea/suno2openai:0.1.0
   ```

2. **运行Docker容器**

   使用必要的环境变量和端口映射来运行Docker容器。将`<SQL_NAME>`、`<SQL_PASSWORD>`和`<SQL_IP>`替换为你的SQL数据库连接的实际值。这些值应当保密，不应公开分享。

   ```bash
   docker run -d --name wsunoapi \
   -p 8000:8000 \
   -e BASE_URL='https://studio-api.suno.ai' \
   -e SESSION_ID='<your-session-id 可以不管>' \
   -e SQL_name='<SQL_NAME>' \
   -e SQL_password='<SQL_PASSWORD>' \
   -e SQL_IP='<SQL_IP>' \
   -e SQL_dk=3306 \
   --restart=always \
   wlhtea/suno2openai:0.1.0
   ```

   **参数说明:**
   - `-d`: 以后台模式运行容器并打印容器ID。
   - `--name wsunoapi`: 为你的容器命名为`wsunoapi`，以便于引用。
   - `-p 8000:8000`: 将容器的8000端口映射到宿主机的8000端口。
   - `-e`: 为你的容器设置环境变量。
   - `--restart=always`: 确保容器始终重启，除非手动停止。

3. **添加cookie进数据库**
   打开数据库添加cookie即可 count为剩余次数（后续会添加一个自动导入的）
   ```mysql
   id = int
   cookie = Cookie
   count = int
   working = 0
   ```

数据库可能报错：'NoneType' object has no attribute 'items' ，[此处检查是否正确](https://github.com/wlhtea/Suno2openai/issues/10)

5. **访问应用程序**

   一旦容器运行，其内部的应用程序应该可以通过`http://localhost:8000`或你的Docker宿主机的IP地址的8000端口访问。

## 注意

在运行Docker容器之前，确保你替换了占位符，如`<SQL_NAME>`、`<SQL_PASSWORD>`、`<SQL_IP>`以及`<your-session-id>`为实际值。

---

## 📦 docker-compose 部署
_更新时间：2024/4/7 18:18_

### 克隆项目到服务器
```bash
git clone https://github.com/wlhtea/Suno2openai.git
```

### 创建数据库
创建一个数据库（名称随意），记得保存密码，并确保数据库权限正确设置（允许所有IP连接或仅限Docker容器IP）。

### 配置环境变量
**将 `env.example` 文件重命名为 `.env` 并填写相应内容：**
```plaintext
BASE_URL=https://studio-api.suno.ai
SESSION_ID=cookie # 此项不需修改
SQL_name=<数据库名称>
SQL_password=<数据库密码>
SQL_IP=<数据库主机IP>
SQL_dk=3306 # 数据库端口
```

### 进入项目目录
```bash
cd Suno2openai
```

### 更新Cookie
编辑 `update_cookie_to_sql.py` 文件，将你的cookies填入下方数组中：
```python
cookies = ['cookie1', 'cookie2']
```
![cookie位置示例](https://github.com/wlhtea/Suno2openai/assets/115779315/6edf9969-9eb6-420f-bfcd-dbf4b282ecbf)

### 启动Docker
```bash
docker compose build && docker compose up
```
**注意事项**：
- **安全组配置**：确保8000端口已开放。
- **HTTPS支持**：若前端项目使用HTTPS，本项目的反代网址也应使用HTTPS。

## 🔌 接入 new-api(one-api)
在渠道的代理设置中填写本项目地址，格式为：`http://<服务器IP>:8000`。建议使用HTTPS和域名。

## 🎉 效果展示
![chat-next-web效果图](https://github.com/wlhtea/Suno2openai/assets/115779315/6495e840-b025-4667-82f6-19116ce71c8e)

## 💌 实习机会征集
若有意向接纳一名拥有数据分析和前后端开发经验的大三学生实习，请联系：
- 📧 **邮箱**: 1544007699@qq.com

**给予支持**：如果这个项目对你有帮助，请不吝赐予星标⭐！欢迎任何形式的支持和建议，让我们一起进步！
