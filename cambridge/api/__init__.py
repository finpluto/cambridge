import logging

from .cambridge.requester import search_cambridge
from .db import wait_all_db_tasks


logger = logging.getLogger(__name__)


async def search_word(con, cur, input_word, is_fresh=False):
    return await search_cambridge(con, cur, input_word, is_fresh)


class _DatabaseContext:
    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        results = await wait_all_db_tasks()
        logger.info("pending db task finished with: %s", results)


db_context = _DatabaseContext()
