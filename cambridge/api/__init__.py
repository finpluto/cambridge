from .cambridge.requester import search_cambridge


async def search_word(con, cur, input_word, is_fresh=False):
    return await search_cambridge(con, cur, input_word, is_fresh)
