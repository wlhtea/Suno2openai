#!/bin/bash

# 启动 Python 应用程序
python app.py &

# 启动 Streamlit 应用程序
streamlit run background/main.py
