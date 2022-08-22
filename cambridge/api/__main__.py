import logging

import aiofiles
import aiosqlite
import asyncio

from cambridge.api import search_word, db_context


logging.basicConfig(
    filename="data.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(filename)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


async def main():
    async with aiosqlite.connect("test.db") as con:
        async with db_context:
            cur = await con.cursor()
            html = await search_word(con, cur, "test")
            async with aiofiles.open("output.html", "w", encoding="utf-8") as f:
                await f.write(html)
            cur = await con.cursor()
            html = await search_word(con, cur, "double")
            async with aiofiles.open("output.html", "w", encoding="utf-8") as f:
                await f.write(html)


asyncio.run(main())
