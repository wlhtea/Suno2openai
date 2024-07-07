import streamlit as st
import pandas as pd
import pymysql
import requests
from pyecharts.charts import Pie, Bar, Line, Scatter
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts
from streamlit_option_menu import option_menu

from config import (SQL_IP, SQL_DK, USER_NAME,
                    SQL_PASSWORD, SQL_NAME, COOKIES_PREFIX,
                    BATCH_SIZE, AUTH_KEY, PROXY, VALID_USERNAME, VALID_PASSWORD, OpenManager,Address)

st.set_page_config(page_title="Suno2OpenAI Backend", layout="wide")
Server_Base_Url = Address


class Suno2OpenAIApp:
    def __init__(self):
        self.check_authentication()

    def check_authentication(self):
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False

        # 创建侧边栏
        with st.sidebar:
            self.selected = option_menu(
                "Suno2openai", ["管理员面板", "体验 Suno2OpenAI", "关于"],
                icons=['lock', 'robot', 'info-circle'],
                menu_icon="cast", default_index=0,
            )

        if self.selected == "管理员面板":
            if OpenManager:
                if not st.session_state["authenticated"]:
                    self.login_page()
                else:
                    st.sidebar.success("已登录")
                    self.show_admin_panel()
            else:
                st.session_state["authenticated"] = True
                self.show_admin_panel()
        elif self.selected == "体验 Suno2OpenAI":
            self.show_experience_page()
        elif self.selected == "关于":
            self.show_about_page()

    def login_page(self):
        st.markdown("<h2 style='text-align: center;'>登录</h2>", unsafe_allow_html=True)
        st.markdown("<style>div.stButton > button:first-child {width: 100%;}</style>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("用户名", key="username", max_chars=20)
            password = st.text_input("密码", type="password", key="password", max_chars=20)
            st.button("登录", on_click=self.authenticate_user)

    def authenticate_user(self):
        if st.session_state["username"] == VALID_USERNAME and st.session_state["password"] == VALID_PASSWORD:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False
            st.error("用户名或密码错误")

    def show_admin_panel(self):
        def create_connection():
            return pymysql.connect(
                host=SQL_IP,
                port=int(SQL_DK),
                user=USER_NAME,
                password=SQL_PASSWORD,
                database=SQL_NAME
            )

        def get_table_content(table_name):
            connection = create_connection()
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, connection)
            connection.close()
            return df

        def get_all_tables():
            connection = create_connection()
            query = "SHOW TABLES"
            tables = pd.read_sql(query, connection)
            connection.close()
            return tables

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

        st.title("🌞 Suno2OpenAI 后端操作界面")

        tab1, tab2 = st.tabs(["🍪 Cookies 操作", "🗃️ 表内容查看"])

        with tab1:
            st.header("Cookies")

            with st.expander("获取和刷新 Cookies"):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("获取 Cookies 🍪")
                    if st.button("获取 Cookies", key="get_cookies"):
                        headers = {"Authorization": f"Bearer {AUTH_KEY}"}
                        with st.spinner('请求中...'):
                            result = perform_request(endpoint=f"/{COOKIES_PREFIX}/cookies", method='POST',
                                                     headers=headers)
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
                            result = perform_request(f"/{COOKIES_PREFIX}/cookies", method="PUT", headers=headers,
                                                     json_data=json_data)
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
                            result = perform_request(f"/{COOKIES_PREFIX}/cookies", method="DELETE", headers=headers,
                                                     json_data=json_data)
                        if result:
                            st.success("Cookies 删除成功")
                            st.json(result)
                    else:
                        st.error("请输入要删除的 Cookies")

        with tab2:
            st.header("数据库")
            try:
                with st.spinner('加载中...'):
                    tables = get_all_tables()

                table_name = st.selectbox("选择一个表", tables.values.flatten())

                if table_name:
                    df = get_table_content(table_name)
                    st.write(f"表 {table_name} 的内容:")
                    st.dataframe(df)

                    if 'count' in df.columns:
                        st.subheader("统计信息")

                        # 计算 count 列的统计信息
                        st.write(f"count 列的统计信息:")
                        st.write(df['count'].describe())

                        # 创建饼图
                        active_cookies = df[df['count'] >= 0]
                        inactive_cookies = df[df['count'] == -1]
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

                        # 创建柱状图
                        count_distribution = df['count'].value_counts().sort_index()
                        bar = (
                            Bar()
                            .add_xaxis(count_distribution.index.astype(str).tolist())
                            .add_yaxis("数量", count_distribution.tolist())
                            .set_global_opts(
                                title_opts=opts.TitleOpts(title="Cookies Count 分布"),
                                xaxis_opts=opts.AxisOpts(name="Count"),
                                yaxis_opts=opts.AxisOpts(name="数量"),
                            )
                        )

                        # 创建折线图
                        line = (
                            Line()
                            .add_xaxis(count_distribution.index.astype(str).tolist())
                            .add_yaxis("数量", count_distribution.tolist())
                            .set_global_opts(
                                title_opts=opts.TitleOpts(title="Cookies Count 变化趋势"),
                                xaxis_opts=opts.AxisOpts(name="Count"),
                                yaxis_opts=opts.AxisOpts(name="数量"),
                            )
                        )

                        # 使用 Streamlit 的列布局将图表并排显示
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st_pyecharts(pie)
                        with col2:
                            st_pyecharts(bar)
                        with col3:
                            st_pyecharts(line)
                    else:
                        st.error("表中没有 'count' 列，无法生成统计信息和图表")

            except Exception as e:
                st.error(f"获取表内容时出错: {str(e)}")

    def show_experience_page(self):
        st.title("体验 Suno2OpenAI")
        st.write("这里展示了 Suno2OpenAI 的功能，可以供用户体验。")
        # 这里可以添加 Suno2OpenAI 的体验功能

    def show_about_page(self):
        st.title("关于")
        st.write("""
        这个应用展示了如何使用 Streamlit 与 FastAPI 进行前后端分离。
        项目地址: [Suno2OpenAI](https://github.com/wlhtea/Suno2openai)
        - **Cookies 操作** 选项卡允许用户获取、添加、删除和刷新 Cookies。
        - **表内容查看** 选项卡允许用户选择一个表并查看表的内容。
        请确保安全使用，避免泄露敏感信息。
        """)


if __name__ == "__main__":
    Suno2OpenAIApp()
