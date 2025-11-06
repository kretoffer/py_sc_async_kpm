from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from sc_async_client.constants import sc_type
from sc_async_client.models import ScAddr, ScConstruction

from sc_async_kpm.sc_sets.sc_set import ScSet


class MockScTemplateResult:
    def __init__(self, addrs):
        self.addrs = addrs

    def __getitem__(self, index):
        return self.addrs[index]


@patch("sc_async_kpm.sc_sets.sc_set.generate_node", new_callable=AsyncMock)
class ScSetTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.el1, self.el2, self.el3 = ScAddr(1), ScAddr(2), ScAddr(3)

    @patch("sc_async_kpm.sc_sets.sc_set.generate_elements", new_callable=AsyncMock)
    async def test_create_sc_set(
        self, gen_elements_mock: AsyncMock, gen_node_mock: AsyncMock
    ):
        set_node = ScAddr(4)
        gen_node_mock.return_value = set_node
        sc_set = await ScSet.create(self.el1, self.el2)
        gen_node_mock.assert_awaited_once_with(sc_type.CONST_NODE)
        gen_elements_mock.assert_awaited_once()
        self.assertEqual(sc_set.set_node, set_node)

    @patch("sc_async_kpm.sc_sets.sc_set.generate_elements", new_callable=AsyncMock)
    async def test_add(self, gen_elements_mock: AsyncMock, gen_node_mock: AsyncMock):
        set_node = ScAddr(4)
        sc_set = ScSet(set_node)
        await sc_set.add(self.el1, self.el2)
        gen_elements_mock.assert_awaited_once()
        (construction,), _ = gen_elements_mock.call_args
        self.assertIsInstance(construction, ScConstruction)

    @patch("sc_async_kpm.sc_sets.sc_set.search_by_template", new_callable=AsyncMock)
    async def test_get_elements(self, search_mock: AsyncMock, gen_node_mock: AsyncMock):
        search_mock.return_value = [
            MockScTemplateResult([ScAddr(0), ScAddr(1), self.el1]),
            MockScTemplateResult([ScAddr(0), ScAddr(2), self.el2]),
        ]
        sc_set = ScSet(ScAddr(4))
        elements = await sc_set.get_elements_set()
        self.assertEqual(elements, {self.el1, self.el2})
        search_mock.assert_awaited_once()

    @patch("sc_async_kpm.sc_sets.sc_set.search_by_template", new_callable=AsyncMock)
    async def test_size(self, search_mock: AsyncMock, gen_node_mock: AsyncMock):
        search_mock.return_value = [
            MockScTemplateResult([ScAddr(0), ScAddr(1), self.el1]),
            MockScTemplateResult([ScAddr(0), ScAddr(2), self.el2]),
        ]
        sc_set = ScSet(ScAddr(4))
        self.assertEqual(await sc_set.size(), 2)

    @patch("sc_async_kpm.sc_sets.sc_set.search_by_template", new_callable=AsyncMock)
    async def test_is_empty(self, search_mock: AsyncMock, gen_node_mock: AsyncMock):
        sc_set = ScSet(ScAddr(4))
        search_mock.return_value = []
        self.assertTrue(await sc_set.is_empty())
        self.assertFalse(await sc_set.is_nonempty())
        search_mock.return_value = [
            MockScTemplateResult([ScAddr(0), ScAddr(1), self.el1])
        ]
        self.assertFalse(await sc_set.is_empty())
        self.assertTrue(await sc_set.is_nonempty())

    @patch("sc_async_kpm.sc_sets.sc_set.search_by_template", new_callable=AsyncMock)
    async def test_contains(self, search_mock: AsyncMock, gen_node_mock: AsyncMock):
        search_mock.return_value = [
            MockScTemplateResult([ScAddr(0), ScAddr(1), self.el1])
        ]
        sc_set = ScSet(ScAddr(4))
        self.assertTrue(await sc_set.contains(self.el1))
        self.assertFalse(await sc_set.contains(self.el2))

    @patch("sc_async_kpm.sc_sets.sc_set.erase_elements", new_callable=AsyncMock)
    @patch("sc_async_kpm.sc_sets.sc_set.search_by_template", new_callable=AsyncMock)
    async def test_remove(
        self, search_mock: AsyncMock, erase_mock: AsyncMock, gen_node_mock: AsyncMock
    ):
        arc1 = ScAddr(11)
        search_mock.return_value = [MockScTemplateResult([ScAddr(0), arc1, self.el1])]
        sc_set = ScSet(ScAddr(4))
        await sc_set.remove(self.el1)
        search_mock.assert_awaited_once()
        erase_mock.assert_awaited_once_with(arc1)

    @patch("sc_async_kpm.sc_sets.sc_set.erase_elements", new_callable=AsyncMock)
    @patch("sc_async_kpm.sc_sets.sc_set.search_by_template", new_callable=AsyncMock)
    async def test_clear(
        self, search_mock: AsyncMock, erase_mock: AsyncMock, gen_node_mock: AsyncMock
    ):
        arc1, arc2 = ScAddr(11), ScAddr(12)
        search_mock.return_value = [
            MockScTemplateResult([ScAddr(0), arc1, self.el1]),
            MockScTemplateResult([ScAddr(0), arc2, self.el2]),
        ]
        sc_set = ScSet(ScAddr(4))
        await sc_set.clear()
        search_mock.assert_awaited_once()
        erase_mock.assert_awaited_once_with(arc1, arc2)
