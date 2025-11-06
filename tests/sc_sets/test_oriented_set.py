from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_client.models import ScAddr

from sc_async_kpm.sc_sets.sc_oriented_set import ScOrientedSet


@patch("sc_async_kpm.sc_sets.sc_set.generate_node", new_callable=AsyncMock)
class ScOrientedSetTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.el1, self.el2, self.el3 = ScAddr(1), ScAddr(2), ScAddr(3)
        self.set_node = ScAddr(4)

    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet.is_empty",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._generate_first_element_arc",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._generate_next_arc",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._mark_arc_with_rrel_last",
        new_callable=AsyncMock,
    )
    async def test_add_to_empty_set(
        self,
        mark_last_mock: AsyncMock,
        gen_next_mock: AsyncMock,
        gen_first_mock: AsyncMock,
        is_empty_mock: AsyncMock,
        _: AsyncMock,
    ):
        is_empty_mock.return_value = True
        first_arc = ScAddr(11)
        gen_first_mock.return_value = first_arc
        next_arc = ScAddr(12)
        gen_next_mock.return_value = next_arc

        sc_set = ScOrientedSet(self.set_node)
        await sc_set.add(self.el1, self.el2)

        is_empty_mock.assert_awaited_once()
        gen_first_mock.assert_awaited_once_with(self.el1)
        gen_next_mock.assert_awaited_once_with(first_arc, self.el2)
        mark_last_mock.assert_awaited_once_with(next_arc)

    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet.is_empty",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._get_last_arc_and_erase_rrel_last",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._generate_next_arc",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._mark_arc_with_rrel_last",
        new_callable=AsyncMock,
    )
    async def test_add_to_non_empty_set(
        self,
        mark_last_mock: AsyncMock,
        gen_next_mock: AsyncMock,
        get_last_mock: AsyncMock,
        is_empty_mock: AsyncMock,
        _: AsyncMock,
    ):
        is_empty_mock.return_value = False
        last_arc = ScAddr(11)
        get_last_mock.return_value = last_arc
        next_arc = ScAddr(12)
        gen_next_mock.return_value = next_arc

        sc_set = ScOrientedSet(self.set_node)
        await sc_set.add(self.el1)

        is_empty_mock.assert_awaited_once()
        get_last_mock.assert_awaited_once()
        gen_next_mock.assert_awaited_once_with(last_arc, self.el1)
        mark_last_mock.assert_awaited_once_with(next_arc)

    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.search_role_relation_template",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet._search_next_element_template",
        new_callable=AsyncMock,
    )
    @patch("sc_async_kpm.sc_sets.sc_oriented_set.ScKeynodes", new_callable=MagicMock)
    async def test_iteration(
        self,
        keynodes_mock: MagicMock,
        search_next_mock: AsyncMock,
        search_role_mock: AsyncMock,
        _: AsyncMock,
    ):
        keynodes_mock.get_by_idtf = AsyncMock(return_value=ScAddr(101))

        start_res = MagicMock()
        start_res.get.side_effect = [self.el1, ScAddr(11)]
        search_role_mock.return_value = start_res

        next_res1 = MagicMock()
        next_res1.get.side_effect = [self.el2, ScAddr(12)]
        next_res2 = MagicMock()
        next_res2.get.side_effect = [self.el3, ScAddr(13)]
        search_next_mock.side_effect = [next_res1, next_res2, None]

        sc_set = ScOrientedSet(self.set_node)
        elements = [el async for el in sc_set]

        self.assertEqual(elements, [self.el1, self.el2, self.el3])

    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet.clear",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet.add", new_callable=AsyncMock
    )
    @patch("sc_async_kpm.sc_sets.sc_oriented_set.ScOrientedSet.__aiter__")
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

        sc_set = ScOrientedSet(self.set_node)
        await sc_set.remove(self.el2)

        clear_mock.assert_awaited_once()
        add_mock.assert_awaited_once_with(self.el1, self.el3)
