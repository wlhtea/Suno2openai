# syntax=docker/dockerfile:1
FROM python:3.10-slim-buster

# 声明构建参数
ARG BASE_URL
ARG SESSION_ID
ARG SQL_NAME
ARG USER_NAME
ARG SQL_PASSWORD
ARG SQL_IP
ARG SQL_DK
ARG COOKIES_PREFIX
ARG AUTH_KEY
ARG RETRIES=3

# 将构建参数转换为环境变量，以便运行时使用.
ENV BASE_URL=${BASE_URL} \
    SESSION_ID=${SESSION_ID} \
    USER_NAME=${USER_NAME} \
    SQL_NAME=${SQL_NAME} \
    SQL_PASSWORD=${SQL_PASSWORD} \
    SQL_IP=${SQL_IP} \
    SQL_DK=${SQL_DK} \
    COOKIES_PREFIX=${COOKIES_PREFIX} \
    AUTH_KEY=${AUTH_KEY} \
    RETRIES=${RETRIES} \
    TZ=Asia/Shanghai

RUN apt-get update && apt-get install -y tzdata

WORKDIR /app

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]
