FROM python:3.11-alpine

WORKDIR /app

COPY . /app

# 设置时区为中国时间
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]