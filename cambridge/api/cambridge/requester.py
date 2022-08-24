"""Parse and print cambridge dictionary."""

import sys
import asyncio
import logging
import aiosqlite
from user_agent import generate_user_agent

from cambridge.api.db import get_cache, insert_into_table, db_background_tasks
from cambridge.utils import *
from cambridge.settings import OP
from cambridge.api.linearize import LinearRequester
from cambridge.api.exceptions import CacheNotFoundException

from .parser import parse_and_export_html, parse_response_word

CAMBRIDGE_URL = "https://dictionary.cambridge.org"
CAMBRIDGE_DICT_BASE_URL = CAMBRIDGE_URL + "/dictionary/english/"
CAMBRIDGE_SPELLCHECK_URL = CAMBRIDGE_URL + "/spellcheck/english/?q="

requester = LinearRequester(trust_env=True)
logger = logging.getLogger(__name__)

# ----------Request Web Resource----------


async def search_cambridge(con, cur, input_word, is_fresh=False):
    req_url = get_request_url(CAMBRIDGE_DICT_BASE_URL, input_word, DICTS[0])
    if is_fresh:
        return await fetch_by_request(con, cur, input_word, req_url)

    try:
        html = await fetch_from_cache(con, cur, input_word, req_url)
        logger.info("cache html found for word: %s, len: %d",
                    input_word, len(html))
        return html
    except CacheNotFoundException:
        logger.info(
            "cache not found for word: %s, fallback to fresh run.", input_word)
        return await fetch_by_request(con, cur, input_word, req_url)


async def fetch_from_cache(con, cur, input_word, req_url):
    data = await get_cache(con, cur, input_word, req_url)
    if not data:
        raise CacheNotFoundException()

    res_url, res_text = data
    soup = make_a_soup(res_text)
    return await parse_and_export_html(res_url, soup)


async def fetch_by_request(con, cur, input_word, req_url):
    result = await fetch_cambridge_async(req_url, input_word)
    found = result[0]
    if found:
        res_url, res_text = result[1]
        soup = make_a_soup(res_text)
        response_word = parse_response_word(soup)

        # db work in seperated tasks.
        db_tasks = asyncio.create_task(
            save_word_response(con, cur, input_word,
                               response_word, res_url, res_text)
        )
        db_background_tasks.add(db_tasks)
        db_tasks.add_done_callback(db_background_tasks.discard)

        return await parse_and_export_html(res_url, soup)

    spell_res_url, spell_res_text = result[1]
    soup = make_a_soup(spell_res_text)
    return await parse_and_export_html(spell_res_url, soup)


async def fetch(url):
    async with requester as session:
        ua = generate_user_agent(os=("win", "linux"), navigator="chrome")
        logger.debug("generate User-Agent header: %s", ua)
        headers = {
            "User-Agent": ua
        }
        session.headers.update(headers)
        for attempt in range(1, 4):
            try:
                logger.info("fetching url: %s, attempt: %d", url, attempt)
                async with session.get(url) as resp:
                    return str(resp.url), await resp.text()
            except Exception as e:
                logger.error(
                    "fetching url: %s, attempt: %d failed. %s", url, attempt, e)
        logger.error("maximum retries reached. \nExit")

    sys.exit(1)


async def save_word_response(con, cur, input_word, response_word, res_url, res_text):
    try:
        await insert_into_table(
            con, cur, input_word, response_word, res_url, res_text
        )
        logger.info('%s the search result of "%s"', OP[7], input_word)
    except aiosqlite.IntegrityError as exception:
        logger.error('%s caching "%s" because of %s',
                     OP[8], input_word, exception)


async def fetch_cambridge_async(req_url, input_word):
    """Get response url and response text for future parsing."""

    url, text = await fetch(req_url)

    # spellcheck case
    if url == CAMBRIDGE_DICT_BASE_URL:
        logger.debug("%s %s in %s", OP[6], input_word, DICTS[0])

        spell_req_url = get_request_url_spellcheck(
            CAMBRIDGE_SPELLCHECK_URL, input_word
        )
        spell_res_url, spell_res_text = await fetch(spell_req_url)

        return False, (spell_res_url, spell_res_text)

    logger.debug("%s %s in %s", OP[5], input_word, DICTS[0])
    return True, (parse_response_url(url), text)
