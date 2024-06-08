import os

import aiomysql
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID', '')
SQL_name = os.getenv('SQL_name', '')
SQL_password = os.getenv('SQL_password', '')
SQL_IP = os.getenv('SQL_IP', '')
SQL_dk = os.getenv('SQL_dk', 3306)


async def create_database_and_table():
    try:
        # Connect to the MySQL Server
        conn = await aiomysql.connect(host=SQL_IP, port=int(SQL_dk),
                                    user=SQL_name, password=SQL_password)
        cursor = await conn.cursor()

        # Create a new database 'SunoAPI' (if it doesn't exist)
        # await cursor.execute("CREATE DATABASE IF NOT EXISTS WSunoAPI")

        # Select the newly created database
        await cursor.execute(f"USE {SQL_name}")

        # Create a new table 'cookies' (if it doesn't exist)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cookie TEXT NOT NULL,
                count INT NOT NULL,
                working BOOLEAN NOT NULL,
                UNIQUE(cookie(255))
                )
        """)

        await cursor.close()
        conn.close()
    except Exception as e:
        print(f"初始化sql失败: {str(e)}")



async def main():
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise ValueError("BASE_URL is not set")
    else:
        await create_database_and_table()
        # Here, you can continue with other database operations such as insert, update, etc.

# if __name__ == "__main__":
#     asyncio.run(main())
