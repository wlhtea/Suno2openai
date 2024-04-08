import asyncio
import aiomysql
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv('BASE_URL',None)
SESSION_ID = os.getenv('SESSION_ID','cookie')
SQL_name = os.getenv('SQL_name',None)
SQL_password = os.getenv('SQL_password',None)
SQL_IP = os.getenv('SQL_IP',None)
SQL_dk = os.getenv('SQL_dk',3306)
async def create_database_and_table():
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


async def main():
    if BASE_URL is None:
        raise ValueError("BASE_URL is not set")
    else:
        await create_database_and_table()
        # Here, you can continue with other database operations such as insert, update, etc.


if __name__ == "__main__":
    asyncio.run(main())
