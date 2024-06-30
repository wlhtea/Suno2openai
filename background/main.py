import streamlit as st
import pandas as pd
import pymysql
import requests
from pyecharts.charts import Pie, Bar
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts
from config import (SQL_IP, SQL_DK, USER_NAME,
                         SQL_PASSWORD, SQL_NAME, COOKIES_PREFIX,
                         BATCH_SIZE, AUTH_KEY,PROXY)

st.set_page_config(page_title="Suno2OpenAI Backend", layout="wide")
Server_Base_Url = f'127.0.0.1:8000'
print((SQL_IP, SQL_DK, USER_NAME,
                         SQL_PASSWORD, SQL_NAME, COOKIES_PREFIX,
                         BATCH_SIZE, AUTH_KEY,PROXY))
def create_connection():
    return pymysql.connect(
        host=SQL_IP,
        port=int(SQL_DK),
        user=USER_NAME,
        password=SQL_PASSWORD,
        database=SQL_NAME
    )

# Get table content
def get_table_content(table_name):
    connection = create_connection()
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# Get all tables
def get_all_tables():
    connection = create_connection()
    query = "SHOW TABLES"
    tables = pd.read_sql(query, connection)
    connection.close()
    return tables

# Perform request
def perform_request(endpoint, method="GET", headers=None, json_data=None):
    url = f"http://{Server_Base_Url}{endpoint}"
    headers = {
        'Authorization': f'Bearer {AUTH_KEY}'
    }
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, json=json_data)
        else:
            st.error("Unsupported method")
            return None

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Request failed with status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None


# Main application content
st.title("🌞 Suno2OpenAI 后端操作界面")

# Create tabs
tab1, tab2, tab3 = st.tabs(["🍪 Cookies 操作", "🗃️ 表内容查看", "ℹ️ 关于"])

with tab1:
    st.header("Cookies")

    with st.expander("获取和刷新 Cookies"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("获取 Cookies 🍪")
            if st.button("获取 Cookies", key="get_cookies"):
                headers = {"Authorization": f"Bearer {AUTH_KEY}"}
                with st.spinner('请求中...'):
                    result = perform_request(endpoint=f"/{COOKIES_PREFIX}/cookies",method='POST', headers=headers)
                if result:
                    st.success("Cookies 获取成功")
                    st.json(result)

        with col2:
            st.subheader("刷新 Cookies 🔄")
            if st.button("刷新 Cookies", key="refresh_cookies"):
                headers = {"Authorization": f"Bearer {AUTH_KEY}"}
                with st.spinner('请求中...'):
                    result = perform_request(f"/{COOKIES_PREFIX}/refresh/cookies", headers=headers)
                if result and result.get('messages'):
                    st.success(result.get('messages'))

    with st.expander("添加 Cookies"):
        st.subheader("添加 Cookies ➕")
        cookies = st.text_area("输入 Cookies（以逗号分隔）")
        if st.button("添加 Cookies", key="add_cookies"):
            if cookies:
                headers = {"Authorization": f"Bearer {AUTH_KEY}"}
                json_data = {"cookies": cookies.split(",")}
                with st.spinner('添加中...'):
                    result = perform_request(f"/{COOKIES_PREFIX}/cookies", method="PUT", headers=headers, json_data=json_data)
                # for i in result.iter_lines():
                # st.text()
                st.success(f"Cookies {result.get('messages')}")


            else:
                st.error("请输入 Cookies")

    with st.expander("删除 Cookies"):
        st.subheader("删除 Cookies ➖")
        cookies_to_delete = st.text_area("输入要删除的 Cookies（以逗号分隔）")
        if st.button("删除 Cookies", key="delete_cookies"):
            if cookies_to_delete:
                headers = {"Authorization": f"Bearer {AUTH_KEY}"}
                json_data = {"cookies": cookies_to_delete.split(",")}
                with st.spinner('删除中...'):
                    result = perform_request(f"/{COOKIES_PREFIX}/cookies", method="DELETE", headers=headers, json_data=json_data)
                if result:
                    st.success("Cookies 删除成功")
                    st.json(result)
            else:
                st.error("请输入要删除的 Cookies")

    # with st.expander("清除重复 Cookies"):
    #     st.subheader("清除重复 Cookies")
    #     if st.button("清除重复 Cookies"):
    #         with st.spinner('清除中...'):
    #             result = perform_request(f"/{COOKIES_PREFIX}/clear_duplicates", method="DELETE")
    #         if result and result.get("status") == "success":
    #             st.success("重复的 Cookies 已清除")
    #         else:
    #             st.error(f"清除重复的 Cookies 时出错: {result}")

with tab2:
    st.header("数据库")
    try:
        with st.spinner('加载中...'):
            tables = get_all_tables()
        if "suno2openai" in tables.values:
            df = get_table_content("suno2openai")
            st.write(f"表 suno2openai 的内容:")
            st.dataframe(df)

            # 可视化统计信息
            st.subheader("统计信息")
            active_cookies = df[df['count'] >= 0]
            inactive_cookies = df[df['count'] == -1]
            st.write(f"活跃的 Cookies: {len(active_cookies)}")
            st.write(f"失效的 Cookies: {len(inactive_cookies)}")

            # 使用 Pyecharts 绘制饼图
            pie = (
                Pie()
                .add(
                    "",
                    [("活跃", len(active_cookies)), ("失效", len(inactive_cookies))],
                    radius=["40%", "75%"],
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="Cookies 状态分布"),
                    legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
                )
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
            )
            st_pyecharts(pie)

            # 使用 Pyecharts 绘制柱状图
            count_distribution = df['count'].value_counts().sort_index()
            bar = (
                Bar()
                .add_xaxis(count_distribution.index.tolist())
                .add_yaxis("数量", count_distribution.values.tolist())
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="Cookies Count 分布"),
                    xaxis_opts=opts.AxisOpts(name="Count"),
                    yaxis_opts=opts.AxisOpts(name="数量"),
                )
            )
            st_pyecharts(bar)
        else:
            st.write("数据库中没有 suno2openai 表")
    except Exception as e:
        st.error(f"获取表内容时出错: {str(e)}")

with tab3:
    st.header("关于")
    st.write("""
    这个应用展示了如何使用 Streamlit 与 FastAPI 进行前后端分离。
    项目地址: [Suno2OpenAI](https://github.com/wlhtea/Suno2openai)
    - **Cookies 操作** 选项卡允许用户获取、添加、删除和刷新 Cookies。
    - **表内容查看** 选项卡允许用户选择一个表并查看表的内容。

    请确保安全使用，避免泄露敏感信息。
    """)
