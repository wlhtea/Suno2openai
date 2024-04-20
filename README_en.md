# Suno2openai

> Based on the [SunoSongsCreator](https://github.com/yihong0618/SunoSongsCreator)
> and [Suno-API](https://github.com/SunoAI-API/Suno-API) project integrations, provides interface standardization services
> conforming to the OpenAI format interface standardization service.

Chinese | [English](https://github.com/wlhtea/Suno2openai/blob/main/README_en.md)

## 2024.4.10 Due to suno official update, some of the project features are not available, and have been re-changed. Projects that were pulled before 2024/4/10:15:04, please pull them again. docker will be updated later (already updated, please pay attention to the pulled version number when pulling them.)

## ✨ Project features

- **OpenAI format call**: support for streaming output content.
- **Front-end compatibility**: adapt `chat-next-web` and other front-end projects.
- **Docker deployment**: simplify the deployment process, support `docker-compose`, `docker`.
- **Multi-cookie management**: enables polling of multiple cookies for use.

## 🚀 Follow-up plans

- Introduce request queue wait optimization.
- Support for custom parameters (e.g. `tags`, `prompt`, `style` and continuation of songs).
- Explore the development of a front-end page similar to the official website.
- Welcome to make valuable suggestions! 📧 **email**: 1544007699@qq.com

---

## 🫙 Docker Deployment

This tutorial provides step-by-step instructions on how to run a Docker container using specific environment variables
and port mapping. For the purposes of this guide, sensitive information such as SQL names, passwords, and IP addresses
will be replaced with placeholders.

## Prerequisites

- You have Docker installed on your machine.
- You have basic knowledge of the Docker command line interface.

## Procedure

1. **Pulling a Docker image**

   First, make sure you have the Docker image `wlhtea/suno2openai:latest` on your machine. If not, you can pull it from
   the Docker repository using the following command:

   ```bash
   docker pull wlhtea/suno2openai:0.0.2
   ```

2. **Running a Docker container**

   Run the Docker container with the necessary environment variables and port mapping.
   Replace `<SQL_NAME>`, `<SQL_PASSWORD>` and `<SQL_IP>` with the actual values of your SQL database connection. These
   values should be kept private and not shared publicly.

   ```bash
   docker run -d --name wsunoapi \
   -p 8000:8000 \
   -e BASE_URL='https://studio-api.suno.ai' \
   -e SESSION_ID='<your-session-id could care less>' \
   -e SQL_name='<SQL_NAME>' \\
   -e SQL_password='<SQL_PASSWORD>' \\
   -e SQL_IP='<SQL_IP>' \
   -e SQL_dk=3306 \
   --restart=always \
   wlhtea/suno2openai:latest
   \ --restart=always
   ```

   **Parameter description:**
    - `-d`: Run the container in background mode and print the container ID.
    - `--name wsunoapi`: Name your container `wsunoapi` for easy referencing.
    - `-p 8000:8000`: Maps the container's port 8000 to the host's port 8000.
    - `-e`: Set environment variables for your container.
    - `--restart=always`: Ensure that the container is always restarted, unless stopped manually.

3. **Add a cookie to the database
   Just open the database and add a cookie count is the number of times remaining (an auto-import will be added later)
   ```mysql
   id = int
   cookie = Cookie
   count = int
   working = 0
   ```

Database may report error: 'NoneType' object has no attribute '
items', [check for correctness here](https://github.com/wlhtea/Suno2openai/issues/10)

5. **Access to applications**

   Once the container is running, the application inside it should be accessible on port 8000
   via `http://localhost:8000` or the IP address of your Docker host.

## Caution.

Before running the Docker container, make sure you replace placeholders such
as `<SQL_NAME>`, `<SQL_PASSWORD>`, `<SQL_IP>`, and `<your-session-id>` with their actual values.

---

## 📦 docker-compose deployment

_Updated: 2024/4/7 18:18_

### Clone the project to the server

```bash
git clone https://github.com/wlhtea/Suno2openai.git
```

### Create a database

Create a database (with any name you want), remember to save the password and make sure the database permissions are set
correctly (Allow all IPs to connect or Docker container IPs only).

### Configure environment variables

**Rename the `env.example` file to `.env` and fill in the following fields:** ``plaintext

```plaintext
BASE_URL=https://studio-api.suno.ai
SESSION_ID=cookie # This does not need to be changed.
SQL_name=<database name
SQL_password=<Password for database
SQL_IP=<database host IP>
SQL_dk=3306 # database port
```

### Enter the project directory

```bash
cd Suno2openai
```

### Update cookies

Edit the ``update_cookie_to_sql.py`` file and fill the array below with your cookies:

```python
cookies = ['cookie1', 'cookie2']
```

! [cookie location example](https://github.com/wlhtea/Suno2openai/assets/115779315/6edf9969-9eb6-420f-bfcd-dbf4b282ecbf)

### Start Docker

```bash
docker compose build && docker compose up
```

## **Notes**:

- **Security group configuration**: make sure port 8000 is open.
- **HTTPS support**: If the front-end project uses HTTPS, the reverse proxy URL for this project should also use HTTPS.

## 🤔 Frequently Asked Questions

- Calling sunoapi directly in `chat-next-web` with the deployment url works, but not via `new-api`. You may need to
  check the source code of `new-api`.

## 🔌 Accessing new-api(one-api)

Fill in the address of this project in the proxy settings of the channel in the format: `http://<server IP>:8000`. It is
recommended to use HTTPS and domain name.

## 🎉 The effect show

! [chat-next-web effect image](https://github.com/wlhtea/Suno2openai/assets/115779315/6495e840-b025-4667-82f6-19116ce71c8e)

## 💌 Call for Internships

If you are interested in hosting a junior with experience in data analytics and front-end and back-end development for
an internship, please contact:

- 📧 **email**: 1544007699@qq.com

**GIVE SUPPORT**: If this program has been helpful to you, please do not hesitate to give it a star ⭐! Any kind of
support and suggestions are welcome, let's improve together!
