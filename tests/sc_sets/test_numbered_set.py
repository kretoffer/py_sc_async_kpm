from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_client.models import ScAddr

from sc_async_kpm.sc_sets.sc_numbered_set import ScNumberedSet


class MockScTemplateResult:
    def __init__(self, addrs):
        self.addrs = addrs

    def __getitem__(self, index):
        return self.addrs[index]


@patch("sc_async_kpm.sc_sets.sc_set.generate_node", new_callable=AsyncMock)
class ScNumberedSetTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.el1, self.el2, self.el3 = ScAddr(1), ScAddr(2), ScAddr(3)
        self.set_node = ScAddr(4)

    @patch(
        "sc_async_kpm.sc_sets.sc_numbered_set.generate_by_template",
        new_callable=AsyncMock,
    )
    @patch("sc_async_kpm.sc_sets.sc_numbered_set.ScKeynodes", new_callable=MagicMock)
    @patch(
        "sc_async_kpm.sc_sets.sc_numbered_set.search_by_template",
        new_callable=AsyncMock,
    )
    async def test_add_to_numbered_set(
        self,
        search_mock: AsyncMock,
        keynodes_mock: MagicMock,
        generate_mock: AsyncMock,
        _: AsyncMock,
    ):
        search_mock.return_value = []
        keynodes_mock.rrel_index = AsyncMock(side_effect=[ScAddr(101), ScAddr(102)])
        sc_set = ScNumberedSet(self.set_node)
        await sc_set.add(self.el1, self.el2)
        generate_mock.assert_awaited_once()
        self.assertEqual(keynodes_mock.rrel_index.call_count, 2)

    @patch(
        "sc_async_kpm.sc_sets.sc_numbered_set.search_by_template",
        new_callable=AsyncMock,
    )
    async def test_get_elements_list(self, search_mock: AsyncMock, _: AsyncMock):
        search_mock.return_value = [
            MockScTemplateResult(
                [self.set_node, ScAddr(11), self.el2, ScAddr(12), ScAddr(102)]
            ),
            MockScTemplateResult(
                [self.set_node, ScAddr(14), self.el1, ScAddr(15), ScAddr(101)]
            ),
        ]
        sc_set = ScNumberedSet(self.set_node)
        elements = await sc_set.get_elements_list()
        self.assertEqual(elements, [self.el1, self.el2])

    @patch("sc_async_kpm.sc_sets.sc_numbered_set.ScKeynodes", new_callable=MagicMock)
    @patch(
        "sc_async_kpm.sc_sets.sc_numbered_set.search_by_template",
        new_callable=AsyncMock,
    )
    async def test_get_by_index(
        self, search_mock: AsyncMock, keynodes_mock: MagicMock, _: AsyncMock
    ):
        keynodes_mock.rrel_index = AsyncMock(return_value=ScAddr(101))
        search_mock.return_value = [
            MockScTemplateResult(
                [self.set_node, ScAddr(11), self.el1, ScAddr(12), ScAddr(101)]
            )
        ]
        sc_set = ScNumberedSet(self.set_node)
        element = await sc_set.get_by_index(0)
        self.assertEqual(element, self.el1)
        keynodes_mock.rrel_index.assert_awaited_once_with(1)

        search_mock.return_value = []
        with self.assertRaises(KeyError):
            await sc_set.get_by_index(1)

    @patch(
        "sc_async_kpm.sc_sets.sc_numbered_set.ScNumberedSet.clear",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_numbered_set.ScNumberedSet.add", new_callable=AsyncMock
    )
    @patch("sc_async_kpm.sc_sets.sc_numbered_set.ScNumberedSet.__aiter__")
    async def test_remove(
        self,
        iter_mock: MagicMock,
        add_mock: AsyncMock,
        clear_mock: AsyncMock,
        _: AsyncMock,
    ):
        async def async_iter(*args):
            for arg in args:
                yield arg

        iter_mock.return_value = async_iter(self.el1, self.el2, self.el3)
        sc_set = ScNumberedSet(self.set_node)
        await sc_set.remove(self.el2)
        clear_mock.assert_awaited_once()
        add_mock.assert_awaited_once_with(self.el1, self.el3)
