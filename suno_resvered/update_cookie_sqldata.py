from uilt.init_sql import insert_or_update_cookie,get_remaining_count
from suno import SongsGen
cookies = \
    []
for cookie in cookies:
    try:
        remaining_count = SongsGen(cookie).get_limit_left()
        insert_or_update_cookie(cookie, remaining_count)
    except:
        insert_or_update_cookie(cookie,0)