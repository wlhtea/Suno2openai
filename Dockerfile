FROM python:3.11-slim

WORKDIR /app

COPY . /app

# 设置时区为中国时间
RUN apt-get update && apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone && \
    apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000 8501

CMD bash -c "python app.py & streamlit run background/main.py"
