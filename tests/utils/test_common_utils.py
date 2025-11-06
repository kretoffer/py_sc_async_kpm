from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_client.constants import sc_type
from sc_async_client.models import ScAddr, ScLinkContent

from sc_async_kpm.utils.common_utils import (
    check_connector,
    erase_connectors,
    generate_binary_relation,
    generate_connector,
    generate_link,
    generate_node,
    generate_non_role_relation,
    generate_role_relation,
    get_element_system_identifier,
    get_link_content_data,
    search_connector,
    search_element_by_non_role_relation,
    search_element_by_role_relation,
)


@patch("sc_async_kpm.utils.common_utils.client", new_callable=MagicMock)
class TestCommonUtils(IsolatedAsyncioTestCase):
    async def test_generate_node(self, client_mock: MagicMock):
        client_mock.generate_elements = AsyncMock(return_value=[ScAddr(1)])
        addr = await generate_node(sc_type.CONST_NODE)
        self.assertTrue(addr.is_valid())
        client_mock.generate_elements.assert_awaited_once()

    async def test_generate_link(self, client_mock: MagicMock):
        client_mock.generate_elements = AsyncMock(return_value=[ScAddr(1)])
        addr = await generate_link("hello")
        self.assertTrue(addr.is_valid())
        client_mock.generate_elements.assert_awaited_once()

    async def test_generate_connector(self, client_mock: MagicMock):
        client_mock.generate_elements = AsyncMock(return_value=[ScAddr(3)])
        addr = await generate_connector(
            sc_type.CONST_PERM_POS_ARC, ScAddr(1), ScAddr(2)
        )
        self.assertTrue(addr.is_valid())
        client_mock.generate_elements.assert_awaited_once()

    async def test_generate_binary_relation(self, client_mock: MagicMock):
        client_mock.generate_elements = AsyncMock(return_value=[ScAddr(1)])
        addr = await generate_binary_relation(
            sc_type.CONST_PERM_POS_ARC, ScAddr(1), ScAddr(2), ScAddr(3)
        )
        self.assertTrue(addr.is_valid())
        client_mock.generate_elements.assert_awaited_once()

    async def test_generate_role_relation(self, client_mock: MagicMock):
        with patch(
            "sc_async_kpm.utils.common_utils.generate_binary_relation",
            new_callable=AsyncMock,
        ) as gen_bin_rel_mock:
            await generate_role_relation(ScAddr(1), ScAddr(2), ScAddr(3))
            gen_bin_rel_mock.assert_awaited_once_with(
                sc_type.CONST_PERM_POS_ARC, ScAddr(1), ScAddr(2), ScAddr(3)
            )

    async def test_generate_non_role_relation(self, client_mock: MagicMock):
        with patch(
            "sc_async_kpm.utils.common_utils.generate_binary_relation",
            new_callable=AsyncMock,
        ) as gen_bin_rel_mock:
            await generate_non_role_relation(ScAddr(1), ScAddr(2), ScAddr(3))
            gen_bin_rel_mock.assert_awaited_once_with(
                sc_type.CONST_COMMON_ARC, ScAddr(1), ScAddr(2), ScAddr(3)
            )

    async def test_check_connector(self, client_mock: MagicMock):
        res = MagicMock()
        res.__getitem__.return_value = ScAddr(3)
        client_mock.search_by_template = AsyncMock(return_value=[res])
        self.assertTrue(
            await check_connector(sc_type.VAR_PERM_POS_ARC, ScAddr(1), ScAddr(2))
        )
        client_mock.search_by_template.return_value = []
        self.assertFalse(
            await check_connector(sc_type.VAR_PERM_POS_ARC, ScAddr(1), ScAddr(2))
        )

    async def test_search_connector(self, client_mock: MagicMock):
        arc = ScAddr(3)
        res = MagicMock()
        res.__getitem__.return_value = arc
        client_mock.search_by_template = AsyncMock(return_value=[res])
        self.assertEqual(
            await search_connector(ScAddr(1), ScAddr(2), sc_type.VAR_PERM_POS_ARC), arc
        )
        res.__getitem__.assert_called_with(1)
        client_mock.search_by_template.return_value = []
        self.assertEqual(
            await search_connector(ScAddr(1), ScAddr(2), sc_type.VAR_PERM_POS_ARC),
            ScAddr(0),
        )

    @patch("sc_async_kpm.utils.common_utils.ScKeynodes", new_callable=MagicMock)
    async def test_get_element_system_identifier(
        self, keynodes_mock: MagicMock, client_mock: MagicMock
    ):
        nrel_sys_idtf = ScAddr(10)
        keynodes_mock.get_by_idtf = AsyncMock(return_value=nrel_sys_idtf)
        link_addr = ScAddr(20)
        idtf = "test_idtf"
        client_mock.search_by_template = AsyncMock(
            return_value=[MagicMock(get=MagicMock(return_value=link_addr))]
        )
        client_mock.get_link_content = AsyncMock(return_value=[ScLinkContent(idtf, 0)])

        result = await get_element_system_identifier(ScAddr(1))
        self.assertEqual(result, idtf)

        client_mock.search_by_template.return_value = []
        result = await get_element_system_identifier(ScAddr(1))
        self.assertEqual(result, "")

    async def test_get_link_content_data(self, client_mock: MagicMock):
        data = "test_content"
        client_mock.get_link_content = AsyncMock(return_value=[ScLinkContent(data, 0)])
        result = await get_link_content_data(ScAddr(1))
        self.assertEqual(result, data)

    async def test_erase_connectors(self, client_mock: MagicMock):
        arc1, arc2 = ScAddr(11), ScAddr(12)
        res1 = MagicMock()
        res1.__getitem__.return_value = arc1
        res2 = MagicMock()
        res2.__getitem__.return_value = arc2

        async def search_side_effect(*args, **kwargs):
            if args[0].triple_list[0].connector.value == sc_type.VAR_PERM_POS_ARC:
                return [res1]
            return [res2]

        client_mock.search_by_template = AsyncMock(side_effect=search_side_effect)
        client_mock.erase_elements = AsyncMock(return_value=True)

        result = await erase_connectors(
            ScAddr(1), ScAddr(2), sc_type.VAR_PERM_POS_ARC, sc_type.VAR_COMMON_ARC
        )
        self.assertTrue(result)
        client_mock.erase_elements.assert_awaited_once_with(arc1, arc2)

    async def test_search_element_by_role_relation(self, client_mock: MagicMock):
        with patch(
            "sc_async_kpm.utils.common_utils.search_role_relation_template",
            new_callable=AsyncMock,
        ) as search_templ_mock:
            element = ScAddr(10)
            search_templ_mock.return_value = MagicMock(
                get=MagicMock(return_value=element)
            )
            result = await search_element_by_role_relation(ScAddr(1), ScAddr(2))
            self.assertEqual(result, element)

            search_templ_mock.return_value = None
            result = await search_element_by_role_relation(ScAddr(1), ScAddr(2))
            self.assertEqual(result, ScAddr(0))

    async def test_search_element_by_non_role_relation(self, client_mock: MagicMock):
        with patch(
            "sc_async_kpm.utils.common_utils.search_non_role_relation_template",
            new_callable=AsyncMock,
        ) as search_templ_mock:
            element = ScAddr(10)
            search_templ_mock.return_value = MagicMock(
                get=MagicMock(return_value=element)
            )
            result = await search_element_by_non_role_relation(ScAddr(1), ScAddr(2))
            self.assertEqual(result, element)

            search_templ_mock.return_value = None
            result = await search_element_by_non_role_relation(ScAddr(1), ScAddr(2))
            self.assertEqual(result, ScAddr(0))
