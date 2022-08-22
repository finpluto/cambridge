import asyncio
import datetime
import aiosqlite


db_background_tasks = set()


async def wait_all_db_tasks():
    return await asyncio.gather(
        *db_background_tasks,
        return_exceptions=True
    )


async def create_table(con, cur):
    await cur.execute(
        """CREATE TABLE words (
        "input_word" TEXT NOT NULL,
        "response_word" TEXT UNIQUE NOT NULL,
        "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        "response_url" TEXT UNIQUE NOT NULL,
        "response_text" TEXT NOT NULL)"""
    )
    await con.commit()


async def insert_into_table(con, cur, input_word, response_word, url, text):
    await cur.execute(
        "INSERT INTO words (input_word, response_word, created_at, response_url, response_text) VALUES (?, ?, ?, ?, ?)",
        (input_word, response_word, datetime.datetime.now(), url, text),
    )
    await con.commit()


async def get_cache(con, cur, word, resquest_url):
    try:
        await cur.execute(
            "SELECT response_url, response_text FROM words WHERE response_url = ? OR response_word = ? OR input_word = ?",
            (resquest_url, word, word),
        )
    except aiosqlite.OperationalError:
        await create_table(con, cur)
    else:
        data = await cur.fetchone()
        return data


async def get_response_words(cur):
    """Get all response words for l command on terminal"""

    await cur.execute("SELECT response_word, created_at FROM words")
    data = await cur.fetchall()
    return data


async def get_random_words(cur):
    """Get random response words for l -r command on terminal"""

    await cur.execute("SELECT response_word FROM words ORDER BY RANDOM() LIMIT 20")
    data = await cur.fetchall()
    return data


async def delete_word(con, cur, word):
    await cur.execute(
        "SELECT input_word, response_url FROM words WHERE input_word = ? OR response_word = ?",
        (word, word),
    )
    data = await cur.fetchone()

    if data is None:
        return (False, None)
    else:
        await cur.execute(
            "DELETE FROM words WHERE input_word = ? OR response_word = ?", (
                word, word)
        )
        await con.commit()
        return (True, data)
