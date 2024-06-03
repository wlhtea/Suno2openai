import asyncio
import os
from suno.suno import SongsGen
from sql_uilts import DatabaseManager
BASE_URL = os.getenv('BASE_URL','https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID','')
SQL_name = os.getenv('SQL_name','')
SQL_password = os.getenv('SQL_password','')
SQL_IP = os.getenv('SQL_IP','')
SQL_dk = os.getenv('SQL_dk',3306)
cookies = \
    ['__cf_bm=z0fmOnL0WR4eqsWjjXs.EPWeswoBK0DALc34ApSbLVE-1717419211-1.0.1.1-yya_QPsxBpSbXjTNqCk.2GT2aH9R8fN6BaNHTlLJzAhEDpI2KaUHdPeWgBmMbOVe.gY1lHGDfl9AkDGEyUSDjA; _cfuvid=yJTQfwBENvtR8B6ycV8jqMIf.JE8TM1FLjXgh79tq1w-1717419211006-0.0.1.1-604800000; __client=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImNsaWVudF8yaE4wUlNESllCb1VSRHhXR0dRclRYc0szaUYiLCJyb3RhdGluZ190b2tlbiI6ImZ4d2doY2wwbHhtajJneWkxNDl4d3czbmZrZnhsY3ZzcWRuM3lxbnYifQ.Dl_TmF3x3NsEiwcbcSjmxlYIHeEHmbIx5Qw6FPnWi9apduSxaBavMIaWMCgn5qw-nvlvdHgITQnK0OhlCMoNOach6MK0F9M2idnUsg8xW3AOJOkKqr1Cofj1vSz8qoZLwIABnwUDMY6ISGes_fa5vMoITptAulAsxnqvPtQO1PkzUXfqC3BsSO4S3R2pwK8sbNB-MjLjm_0c-4IEgWatAlsmRxmC5XDr1haACZVkDtOJ3LwUoneJaURj4d-R0Xr0ckoziUmvJ05mxhqOY0flBcj3PUVYod1uUs_WjlSdy2U0rZASJ-C8U1mP4oeKtn6KYmft8Va9VngnkFAFNQ-1nQ; __client_uat=1717419230; mp_26ced217328f4737497bd6ba6641ca1c_mixpanel=%7B%22distinct_id%22%3A%20%225a96919e-8046-4f17-9ffe-34cbbb9e93d6%22%2C%22%24device_id%22%3A%20%2218fde2971f4141d-04129a60e4379e-745d5774-154ac4-18fde2971f4141d%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22%24user_id%22%3A%20%225a96919e-8046-4f17-9ffe-34cbbb9e93d6%22%7D']

async def fetch_limit_left(cookie,db_manager):
    song_gen = SongsGen(cookie)

    try:
        remaining_count = song_gen.get_limit_left()
        print(f"Remaining count: {remaining_count}")

        await db_manager.insert_cookie(cookie, remaining_count, False)
    except:
        print(cookie)

async def main():
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise ValueError("BASE_URL is not set")
    else:
        db_manager = DatabaseManager(SQL_IP, int(SQL_dk), SQL_name, SQL_password, SQL_name)
        await db_manager.create_pool()
        tasks = [fetch_limit_left(cookie,db_manager) for cookie in cookies if cookie]
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())