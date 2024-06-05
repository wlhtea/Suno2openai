# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

# 声明构建参数
ARG BASE_URL
ARG SESSION_ID
ARG SQL_name
ARG USER_name
ARG SQL_password
ARG SQL_IP
ARG SQL_dk

# 将构建参数转换为环境变量，以便运行时使用
ENV BASE_URL=${BASE_URL} \
    SESSION_ID=${SESSION_ID} \
    USER_name=${USER_name} \
    SQL_name=${SQL_name} \
    SQL_password=${SQL_password} \
    SQL_IP=${SQL_IP} \
    SQL_dk=${SQL_dk}

WORKDIR /app

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]
