from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from sc_async_client.constants import sc_type
from sc_async_client.constants.exceptions import InvalidTypeError
from sc_async_client.models import ScAddr

from sc_async_kpm.sc_sets.sc_structure import ScStructure


class ScStructureTest(IsolatedAsyncioTestCase):
    @patch("sc_async_kpm.sc_sets.sc_set.generate_elements", new_callable=AsyncMock)
    @patch("sc_async_kpm.sc_sets.sc_structure.generate_node", new_callable=AsyncMock)
    async def test_create_sc_structure(
        self, gen_node_mock: AsyncMock, gen_elements_mock: AsyncMock
    ):
        set_node = ScAddr(4)
        gen_node_mock.return_value = set_node
        sc_struct = await ScStructure.create(ScAddr(1), ScAddr(2))
        gen_node_mock.assert_awaited_once_with(sc_type.CONST_NODE_STRUCTURE)
        gen_elements_mock.assert_awaited_once()
        self.assertEqual(sc_struct.set_node, set_node)
        self.assertEqual(sc_struct._set_node_type, sc_type.CONST_NODE_STRUCTURE)

    @patch(
        "sc_async_kpm.sc_sets.sc_structure.get_elements_types", new_callable=AsyncMock
    )
    async def test_create_with_existing_node(self, get_types_mock: AsyncMock):
        set_node = ScAddr(5)
        get_types_mock.return_value = [sc_type.CONST_NODE_STRUCTURE]
        sc_struct = await ScStructure.create(set_node=set_node)
        self.assertEqual(sc_struct.set_node, set_node)
        get_types_mock.assert_awaited_once_with(set_node)

    @patch(
        "sc_async_kpm.sc_sets.sc_structure.get_elements_types", new_callable=AsyncMock
    )
    async def test_create_with_invalid_type(self, get_types_mock: AsyncMock):
        set_node = ScAddr(5)
        get_types_mock.return_value = [sc_type.CONST_NODE]
        with self.assertRaises(InvalidTypeError):
            await ScStructure.create(set_node=set_node)

    @patch("sc_async_kpm.sc_sets.sc_structure.generate_node", new_callable=AsyncMock)
    async def test_create_with_invalid_type_generated(self, gen_node_mock: AsyncMock):
        with self.assertRaises(InvalidTypeError):
            await ScStructure.create(set_node_type=sc_type.CONST_NODE)
