import asyncio
import aiomysql


async def create_database_and_table():
    # Connect to the MySQL Server
    conn = await aiomysql.connect(host='127.0.0.1', port=3306,
                                  user='root', password='12345678')
    cursor = await conn.cursor()

    # Create a new database 'SunoAPI' (if it doesn't exist)
    # await cursor.execute("CREATE DATABASE IF NOT EXISTS WSunoAPI")

    # Select the newly created database
    await cursor.execute("USE WSunoAPI")

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
