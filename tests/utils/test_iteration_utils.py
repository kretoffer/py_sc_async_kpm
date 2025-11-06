from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from sc_async_client.models import ScAddr, ScLinkContent

from sc_async_kpm.utils.iteration_utils import iter_link_contents_data, iter_links_data


class TestIterationUtils(IsolatedAsyncioTestCase):
    def test_iter_link_contents_data(self):
        contents = [
            ScLinkContent("a", 0),
            ScLinkContent(1, 1),
            ScLinkContent(2.0, 2),
        ]
        data = list(iter_link_contents_data(contents))
        self.assertEqual(data, ["a", 1, 2.0])

    @patch(
        "sc_async_kpm.utils.iteration_utils.get_link_content", new_callable=AsyncMock
    )
    async def test_iter_links_data(self, get_link_content_mock: AsyncMock):
        links = [ScAddr(1), ScAddr(2)]
        contents = [
            ScLinkContent("a", 0),
            ScLinkContent("b", 0),
        ]
        get_link_content_mock.return_value = contents

        iterator = await iter_links_data(links)
        data = list(iterator)

        self.assertEqual(data, ["a", "b"])
        get_link_content_mock.assert_awaited_once_with(*links)
