import asyncio
import aiomysql
from dotenv import load_dotenv
import os

load_dotenv()

# 直接从环境变量中读取所需的参数
BASE_URL = os.getenv('BASE_URL')
SESSION_ID = os.getenv('SESSION_ID')
SQL_name = os.getenv('SQL_name')
SQL_password = os.getenv('SQL_password')
SQL_IP = os.getenv('SQL_IP')
SQL_dk = os.getenv('SQL_dk')

async def create_database_and_table():
    # Connect to the MySQL Server
    conn = await aiomysql.connect(host=SQL_IP, port=SQL_dk,
                                  user=SQL_name, password=SQL_password)
    cursor = await conn.cursor()

    # Create a new database 'SunoAPI' (if it doesn't exist)
    await cursor.execute("CREATE DATABASE IF NOT EXISTS WSunoAPI")

    # Select the newly created database
    # await cursor.execute("USE WSunoAPI")

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


async def main():
    await create_database_and_table()
    # Here, you can continue with other database operations such as insert, update, etc.


if __name__ == "__main__":
    asyncio.run(main())
