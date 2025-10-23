# pyright: reportArgumentType = false

from sc_async_client.constants import sc_type
from sc_async_client.constants.exceptions import InvalidValueError
from sc_async_client.models import ScAddr

from sc_async_kpm import ScKeynodes

from unittest.mock import AsyncMock, patch
from unittest import IsolatedAsyncioTestCase


class KeynodesTests(IsolatedAsyncioTestCase):
    @patch("sc_async_client.client.resolve_keynodes", new_callable=AsyncMock)
    async def test_get_unknown_idtf(self, mock_resolve_keynodes):
        mock_resolve_keynodes.return_value = [ScAddr(0)]
        idtf = "idtf_unknown_idtf"
        with self.assertRaises(InvalidValueError):
            print(await ScKeynodes.get_by_idtf(idtf))
        mock_resolve_keynodes.assert_awaited_once()
        self.assertEqual(await ScKeynodes.get(idtf), ScAddr(0))

    @patch("sc_async_client.client.resolve_keynodes", new_callable=AsyncMock)
    async def test_resolve_keynode(self, mock_resolve_keynodes):
        mock_resolve_keynodes.return_value = [ScAddr(5)]
        idtf = "idtf_new_keynode"
        addr = await ScKeynodes.resolve(idtf, sc_type.CONST_NODE)
        addr_2 = await ScKeynodes.get_by_idtf(idtf)
        self.assertTrue(addr.is_valid())
        self.assertEqual(addr, ScAddr(5))
        self.assertEqual(addr, addr_2)
        mock_resolve_keynodes.assert_awaited_once()

    @patch("sc_async_client.client.resolve_keynodes", new_callable=AsyncMock)
    @patch("sc_async_kpm.sc_keynodes.erase_elements", new_callable=AsyncMock)
    async def test_erase_keynode(self, mock_erase_elements, mock_resolve_keynodes):
        mock_resolve_keynodes.return_value = [ScAddr(5)]
        mock_erase_elements.return_value = True
        idtf = "idtf_to_erase_keynode"
        await ScKeynodes.resolve(idtf, sc_type.CONST_NODE)
        self.assertTrue(await ScKeynodes.erase(idtf))
        mock_resolve_keynodes.return_value = [ScAddr(0)]
        self.assertFalse((await ScKeynodes.get(idtf)).is_valid())
        with self.assertRaises(InvalidValueError):
            await ScKeynodes.erase(idtf)

    async def test_keynodes_initialization(self):
        with self.assertRaises(TypeError):
            ScKeynodes()

    @patch("sc_async_client.client.resolve_keynodes", new_callable=AsyncMock)
    async def test_rrel(self, mock_resolve_keynodes):
        mock_resolve_keynodes.return_value = [ScAddr(5)]
        rrel_1 = await ScKeynodes.rrel_index(1)
        self.assertTrue(rrel_1.is_valid())
        mock_resolve_keynodes.assert_awaited_once()

    async def test_max_rrel(self):
        with self.assertRaises(KeyError):
            await ScKeynodes.rrel_index(ScKeynodes._max_rrel_index + 1)

    async def test_min_rrel(self):
        with self.assertRaises(KeyError):
            await ScKeynodes.rrel_index(ScKeynodes._min_rrel_index - 1)

    async def test_wrong_rrel(self):
        with self.assertRaises(TypeError):
            await ScKeynodes.rrel_index("str")
