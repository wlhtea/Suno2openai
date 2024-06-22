[中文](https://github.com/wlhtea/Suno2openai/blob/main/README_ZH.md) English

## Suno2openai

> Integrated based on [SunoSongsCreator](https://github.com/yihong0618/SunoSongsCreator) and [Suno-API](https://github.com/SunoAI-API/Suno-API) projects, offering standardized service interfaces compliant with OpenAI formats.

## ✨ Project Highlights

- **OpenAI Format Calls**: Supports streaming output.
- **Front-end Compatibility**: Compatible with front-end projects like `chat-next-web`.
- **Docker Deployment**: Simplifies deployment process, supports `docker-compose`, `docker`.
- **Multiple Cookie Management**: Implements rotation of multiple cookies.

## 🚀 Future Plans

- Introduce request queueing optimizations.
- Support for custom parameters (such as `tags`, `prompt`, `style`, and song continuation).
- Explore development of official-like frontend pages.
- Welcome valuable suggestions! 📧 **Email**: 1544007699@qq.com

---

## 🐳 Docker Deployment

This tutorial provides step-by-step guidance on running a Docker container with specific environment variables and port mappings. For the purpose of this guide, sensitive information such as SQL names, passwords, and IP addresses will be replaced with placeholders.

### Prerequisites

- Docker is installed on your machine.
- Basic knowledge of Docker CLI.
- MySQL version >= 5.7

### How to get cookie
![image](https://github.com/wlhtea/Suno2openai/assets/115779315/51fec32d-0fe4-403d-8760-1e85f74a1fb6)
copy all content about the cookie

### Steps

1. **Pull Docker Image**

   Ensure the Docker image `wlhtea/suno2openai:latest` is available on your machine. If not, you can pull it from the Docker repository using:

   ```bash
   docker pull wlhtea/suno2openai:latest
   ```

2. **Run Docker Container**

   Run the Docker container using necessary environment variables and port mappings. Replace `<SQL_NAME>`, `<SQL_PASSWORD>`, and `<SQL_IP>` with your actual SQL database connection values. These should be kept confidential and not shared publicly.

   ```bash
   docker run -d --name wsunoapi \
      -p 8000:8000 \
      -e BASE_URL='<BASE_URL>' \
      -e SESSION_ID='<SESSION_ID>' \
      -e USER_NAME='<USER_NAME>' \
      -e SQL_NAME='<SQL_NAME>' \
      -e SQL_PASSWORD='<SQL_PASSWORD>' \
      -e SQL_IP='127.0.0.1' \
      -e SQL_DK=3306 \
      -e COOKIES_PREFIX='your_cookies_prefix' \
      -e AUTH_KEY='<AUTH_KEY>' \
      -e RETRIES=5 \
      -e BATCH_SIZE=10 \
      -e MAX_TIME=5 \
      --restart=always \
      wlhtea/suno2openai:latest
   ```

   ### Example

   ```bash
   docker run -d --name wsunoapi \
      -p 8000:8000 \
      -e BASE_URL='https://studio-api.suno.ai' \
      -e SESSION_ID='your-session-id' \
      -e USER_NAME='suno2openaiUsername' \
      -e SQL_NAME='suno2openaiSQLname' \
      -e SQL_PASSWORD='12345678' \
      -e SQL_IP='127.0.0.1' \
      -e SQL_DK=3306 \
      -e COOKIES_PREFIX='your_cookies_prefix' \
      -e AUTH_KEY='your-auth-key' \
      -e RETRIES=5 \
      -e BATCH_SIZE=10 \
      -e MAX_TIME=5 \
      --restart=always \
      wlhtea/suno2openai:latest
   ```

**Parameter Explanation:**

- `-d`: Run the container in detached mode and log the container ID.
- `--name wsunoapi`: Name your container `wsunoapi` for easy reference.
- `-p 8000:8000`: Map the container's 8000 port to the host machine's 8000 port.
- `-e`: Set environment variables for your container.
- `--restart=always`: Ensure the container always restarts, unless manually stopped.

3. **Access the Application**

   Once the container is running, the application inside should be accessible via `http://localhost:8000` or the 8000 port of your Docker host machine's IP address.

## Note

Before running the Docker container, make sure you replace placeholders like `<SQL_NAME>`, `<SQL_PASSWORD>`, `<SQL_IP>`, and `<your-session-id>` with actual values.

## 📦 Docker-Compose Deployment

_Update Time: 2024/4/7 18:18_

### Clone the Project to Your Server

```bash
git clone https://github.com/wlhtea/Suno2openai.git
```

### Create a Database

Create a database (name it as you wish), remember to save the password, and ensure the database permissions are set correctly (allow connections from all IPs or only from Docker container IPs).

### Configure Environment Variables

**Rename the `env.example` file to `.env` and fill in the corresponding details:**

```plaintext
BASE_URL=https://studio-api.suno.ai
SESSION_ID=your-session-id
USER_NAME=your-username
SQL_NAME=your-database-name
SQL_PASSWORD=your-database-password
SQL_IP=127.0.0.1
SQL_DK=3306
COOKIES_PREFIX=your_cookies_prefix
AUTH_KEY=your-auth-key
RETRIES=5
BATCH_SIZE=10
MAX_TIME=5
```

### Enter the Project Directory

```bash
cd Suno2openai
```

### Start Docker

```bash
docker compose build && docker compose up
```

**Notes:**

- **Security Group Configuration**: Ensure the port 8000 is open.
- **HTTPS Support**: If the frontend project uses HTTPS, the proxy URL of this project should also use HTTPS.

---

## 📋 API Requests

### API Overview

1. **Add Cookie**: Use the `/your_cookies_prefix/cookies` endpoint to add cookies.
2. **Get All Cookies**: Use the `/your_cookies_prefix/cookies` endpoint to retrieve all cookies.
3. **Delete Cookie**: Use the `/your_cookies_prefix/cookies` endpoint to delete specific cookies.
4. **Refresh Cookie**: Use the `/your_cookies_prefix/refresh/cookies` endpoint to refresh cookies.
5. **Generate Chat Completion**: Use the `/v1/chat/completions` endpoint to generate chat responses.

### Add Cookie Example

You can add cookies using the `/your_cookies_prefix/cookies` endpoint. Here is an example request using `requests` library in Python:

```python
import requests

url = "http://localhost:8000/your_cookies_prefix/cookies"
headers = {
    "Authorization": "Bearer your-auth-key",
    "Content-Type": "application/json"
}
data = {
    "cookies": ["cookie1", "cookie2"]
}

response = requests.put(url, headers=headers, json=data)
print(response.text)
```

### Get All Cookies Example

You can retrieve all cookies using the `/your_cookies_prefix/cookies` endpoint. Here is an example request:

```python
import requests

url = "http://localhost:8000/your_cookies_prefix/cookies"
headers = {
    "Authorization": "Bearer your-auth-key",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)
print(response.text)
```

### Delete Cookie Example

You can delete specific cookies using the `/your_cookies_prefix/cookies` endpoint. Here is an example request:

```python
import requests

url = "http://localhost:8000/your_cookies_prefix/cookies"
headers = {
    "Authorization": "Bearer your-auth-key",
    "Content-Type": "application/json"
}
data = {
    "cookies": ["cookie1", "cookie2"]
}

response = requests.delete(url, headers=headers, json=data)
print(response.text)
```

### Refresh Cookies Example

You can refresh cookies using the `/your_cookies_prefix/refresh/cookies` endpoint. Here is an example request:

```python
import requests

url = "http://localhost:8000/your_cookies_prefix/refresh/cookies"
headers = {
    "Authorization": "Bearer your-auth-key",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print(response.text)
```

### Generate Chat Completion Example

You can use the `/v1/chat/completions` endpoint to generate chat responses. Here is an example request:

```python
import requests

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-auth-key",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke."}
    ]
    # "stream": true  # Uncomment to enable streaming output
}

response = requests.post(url, headers=headers, json=data)
print(response.text)
```

### Parameter Explanation

- `BASE_URL`: Default API base URL, defaults to `https://studio-api.suno.ai` if not set.
- `SESSION_ID`: The session ID.
- `USER_NAME`: Database username.
- `SQL_NAME`: Database name.
- `SQL_PASSWORD`: Database password.
- `SQL_IP`: Database IP address.
- `SQL_DK`: Database port, default is 3306.
- `COOKIES_PREFIX`: Prefix for cookies, remember `/` to begin with.
- `AUTH_KEY`: Authorization key, default is the current timestamp.
- `RETRIES`: Number of retries, default is 5.
- `BATCH_SIZE`: Batch size, default is 10.
- `MAX_TIME`: Maximum request time (min), default is 5.

BATCH_SIZE`: Batch size, default is 10.

---

## 🎉 Effect Display

![Effect Display](https://github.com/wlhtea/Suno2openai/assets/115779315/6f289256-6ba5-4016-b9a3-20640d864302)

## 💌 Internship Opportunities

If interested in welcoming a third-year student with experience in data analysis and front-end/back-end development for an internship, please contact:

- 📧 **Email**: 1544007699@qq.com

**Support Us**: If you find this project helpful, please do not hesitate to star it ⭐! We welcome any form of support and suggestions, let’s progress together!
