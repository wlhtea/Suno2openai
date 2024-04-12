# Suno2openai
> Based on the [SunoSongsCreator](https://github.com/yihong0618/SunoSongsCreator) and [Suno-API](https://github.com/SunoAI-API/Suno-API) projects, this integration provides a service that conforms to OpenAI's interface standards.

[中文](https://github.com/wlhtea/Suno2openai/blob/main/README_ZH.md) English

## Update Log
- 2024.4.12 **Completed the integration of new-api and one-api**, select OpenAI for calls, and enter the project deployment address (no need for /v1/); the key can be left empty.
- 2024.4.10 Due to updates from Suno official, some project features were unavailable and have been changed. Projects pulled before 2024/4/10 15:04 should be pulled again; Docker has been updated later (note to pull the version number when doing so).

## ✨ Project Features
- **OpenAI format calling**: Supports streaming output content.
- **Front-end compatibility**: Compatible with front-end projects such as `chat-next-web`.
- **Docker deployment**: Simplifies the deployment process, supports `docker-compose`, `docker`.
- **Multi-Cookie management**: Implements the use of multiple cookies in rotation.

## 🚀 Future Plans
- Introduce request queuing for optimization.
- Support custom parameters (such as `tags`, `prompt`, `style` and continuation of songs).
- Explore the development of front-end pages similar to the official website.
- Welcome any valuable suggestions! 📧 **Email**: 1544007699@qq.com

---

## 🫙 Docker Deployment

This tutorial provides step-by-step guidance on how to run a Docker container using specific environment variables and port mappings. For the purposes of this guide, sensitive information such as SQL name, password, and IP address will be replaced with placeholders.

## Prerequisites

- Docker is installed on your machine.
- You have basic knowledge of the Docker command line interface.

## Steps

1. **Pull the Docker Image**

   First, ensure that the Docker image `wlhtea/suno2openai:0.1.0` is already on your machine. If not, you can pull it from the Docker repository using the following command:

   ```bash
   docker pull wlhtea/suno2openai:0.1.0
   ```

2. **Run the Docker Container**

   Run the Docker container using the necessary environment variables and port mappings. Replace `<SQL_NAME>`, `<SQL_PASSWORD>`, and `<SQL_IP>` with the actual values of your SQL database connection. These values should be kept confidential and not shared publicly.

   ```bash
   docker run -d --name wsunoapi \
   -p 8000:8000 \
   -e BASE_URL='https://studio-api.suno.ai' \
   -e SESSION_ID='<your-session-id, can be ignored>' \
   -e SQL_name='<SQL_NAME>' \
   -e SQL_password='<SQL_PASSWORD>' \
   -e SQL_IP='<SQL_IP>' \
   -e SQL_dk=3306 \
   --restart=always \
   wlhtea/suno2openai:0.1.0
   ```

   **Parameter Explanation:**
   - `-d`: Run the container in detached mode and print the container ID.
   - `--name wsunoapi`: Name your container `wsunoapi` for easy reference.
   - `-p 8000:8000`: Map the container's port 8000 to the host machine's port 8000.
   - `-e`: Set environment variables for your container.
   - `--restart=always`: Ensure the container always restarts unless manually stopped.

3. **Add Cookies to the Database**
   Open the database and add cookies as needed, count as remaining uses (will add an automatic import feature later).
   ```mysql
   id = int
   cookie = Cookie
   count = int
   working = 0
   ```

The database might report an error: 'NoneType' object has no attribute 'items', [check here for correctness](https://github.com/wlhtea/Suno2openai/issues/10)

5. **Access the Application**

   Once the container is running, the application inside should be accessible via `http://localhost:8000` or the 8000 port of your Docker host machine's IP address.

## Note

Before running the Docker container, ensure you replace placeholders such as `<SQL_NAME>`, `<SQL_PASSWORD>`, `<SQL_IP>`, and `<your-session-id>` with actual values.

---

## 📦 docker-compose Deployment
_Last Updated: 2024/4/7 18:18_

### Clone the Project to the Server
```bash
git clone https://github.com/wlhtea/Suno2openai

.git
```

### Create a Database
Create a database (name at your discretion), remember to save the password, and ensure the database permissions are set correctly (allow all IP connections or only Docker container IPs).

### Configure Environment Variables
**Rename the `env.example` file to `.env` and fill in the relevant content:**
```plaintext
BASE_URL=https://studio-api.suno.ai
SESSION_ID=cookie # This item does not need modification
SQL_name=<database name>
SQL_password=<database password>
SQL_IP=<database host IP>
SQL_dk=3306 # Database port
```

### Enter the Project Directory
```bash
cd Suno2openai
```

### Update Cookie
Edit the `update_cookie_to_sql.py` file, entering your cookies in the array below:
```python
cookies = ['cookie1', 'cookie2']
```
![Example of cookie location](https://github.com/wlhtea/Suno2openai/assets/115779315/6edf9969-9eb6-420f-bfcd-dbf4b282ecbf)

### Start Docker
```bash
docker compose build && docker compose up
```
**Considerations**:
- **Security Group Configuration**: Ensure the 8000 port is open.
- **HTTPS Support**: If the front-end project uses HTTPS, the proxy URL for this project should also use HTTPS.

## 🔌 Connect new-api (one-api)
In the channel's proxy settings, enter the project address in the format: `http://<server IP>:8000`. HTTPS and domain name are recommended.

## 🎉 Display Effect
![Effect in chat-next-web](https://github.com/wlhtea/Suno2openai/assets/115779315/6495e840-b025-4667-82f6-19116ce71c8e)

## 💌 Internship Opportunities Wanted
If interested in taking on an intern who is a junior with experience in data analysis and front-end/back-end development, please contact:
- 📧 **Email**: 1544007699@qq.com

**Support**: If this project has been helpful to you, please don't hesitate to give it a star ⭐! We welcome any form of support and suggestions, let's progress together!
