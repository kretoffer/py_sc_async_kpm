from typing import Iterable, Iterator

from sc_async_client.client import get_link_content
from sc_async_client.models import ScAddr
from sc_async_client.models.sc_construction import ScLinkContent, ScLinkContentData


def iter_link_contents_data(
    contents: Iterable[ScLinkContent],
) -> Iterator[ScLinkContentData]:
    """Iterate by data in link contents"""
    for content in contents:
        yield content.data


async def iter_links_data(links: Iterable[ScAddr]) -> Iterator[ScLinkContentData]:
    """Iterate by contents data in links"""
    contents = await get_link_content(*links)
    return iter_link_contents_data(contents)
