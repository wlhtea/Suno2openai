from suno_resvered.models import Cookie
from suno_resvered.models import Session

# 插入新记录
def insert_or_update_cookie(cookie_value, count=5):
    session = Session()
    cookie = session.query(Cookie).filter_by(cookie=cookie_value).first()
    if cookie is None:
        cookie = Cookie(cookie=cookie_value, count=count)
        session.add(cookie)
    else:
        cookie.count = count
    session.commit()
    session.close()


# 查询特定cookie的剩余次数
def query_cookie(cookie_name):
    session = Session()
    cookie = session.query(Cookie).filter(Cookie.cookie == cookie_name).first()
    session.close()
    if cookie:
        return cookie.count
    else:
        return None

# 更新特定cookie的次数
def update_cookie_count(cookie_name, new_count):
    session = Session()
    cookie = session.query(Cookie).filter(Cookie.cookie == cookie_name).first()
    if cookie:
        cookie.count = new_count
        session.commit()
    session.close()

def get_remaining_count(cookie_value):
    session = Session()
    cookie = session.query(Cookie).filter_by(cookie=cookie_value).first()
    session.close()
    if cookie:
        return cookie.count
    else:
        return None

# # 示例使用
# insert_or_update_cookie('example_cookie_123', 5)
# print(query_cookie('example_cookie_123'))
# update_cookie_count('example_cookie_123', 4)
# print(query_cookie('example_cookie_123'))
