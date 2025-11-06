from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_kpm.sc_module import ScModuleAbstract
from sc_async_kpm.sc_server import ScServer


@patch("sc_async_kpm.sc_server._IdentifiersResolver.resolve", new_callable=AsyncMock)
@patch("sc_async_kpm.sc_server.client", new_callable=MagicMock)
class ScServerTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.server_url = "ws://localhost:8090"
        self.server = ScServer(self.server_url)
        self.module1 = MagicMock(spec=ScModuleAbstract)
        self.module1._register = AsyncMock()
        self.module1._unregister = AsyncMock()
        self.module2 = MagicMock(spec=ScModuleAbstract)
        self.module2._register = AsyncMock()
        self.module2._unregister = AsyncMock()

    async def test_connect_disconnect(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.connect = AsyncMock()
        client_mock.disconnect = AsyncMock()
        async with await self.server.connect():
            client_mock.connect.assert_awaited_once_with(self.server_url)
            id_resolver_mock.assert_awaited_once()
        client_mock.disconnect.assert_awaited_once()

    async def test_add_modules(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        await self.server.add_modules(self.module1, self.module2)
        self.assertEqual(self.server._modules, {self.module1, self.module2})

    async def test_add_modules_registered(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        self.server.is_registered = True
        await self.server.add_modules(self.module1)
        self.module1._register.assert_awaited_once()

    async def test_remove_modules(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        await self.server.add_modules(self.module1, self.module2)
        await self.server.remove_modules(self.module1)
        self.assertEqual(self.server._modules, {self.module2})

    async def test_remove_modules_registered(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        await self.server.add_modules(self.module1)
        self.server.is_registered = True
        await self.server.remove_modules(self.module1)
        self.module1._unregister.assert_awaited_once()

    async def test_clear_modules(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        await self.server.add_modules(self.module1, self.module2)
        await self.server.clear_modules()
        self.assertEqual(self.server._modules, set())

    async def test_register_unregister_modules(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        await self.server.add_modules(self.module1, self.module2)
        async with await self.server.register_modules():
            self.assertTrue(self.server.is_registered)
            self.module1._register.assert_awaited_once()
            self.module2._register.assert_awaited_once()
        self.assertFalse(self.server.is_registered)
        self.module1._unregister.assert_awaited_once()
        self.module2._unregister.assert_awaited_once()

    async def test_register_already_registered(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        await self.server.add_modules(self.module1)
        await self.server.register_modules()
        self.module1._register.assert_awaited_once()
        await self.server.register_modules()
        self.module1._register.assert_awaited_once()  # Still once
        await self.server.unregister_modules()

    async def test_unregister_already_unregistered(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        await self.server.unregister_modules()  # No error
        client_mock.is_connected.return_value = True
        await self.server.add_modules(self.module1)
        await self.server.register_modules()
        await self.server.unregister_modules()
        self.module1._unregister.assert_awaited_once()
        await self.server.unregister_modules()
        self.module1._unregister.assert_awaited_once()  # Still once

    async def test_start_stop(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        client_mock.connect = AsyncMock()
        client_mock.disconnect = AsyncMock()
        await self.server.add_modules(self.module1)
        async with await self.server.start():
            client_mock.connect.assert_awaited_once_with(self.server_url)
            id_resolver_mock.assert_awaited_once()
            self.module1._register.assert_awaited_once()
        self.module1._unregister.assert_awaited_once()
        client_mock.disconnect.assert_awaited_once()

    async def test_register_connection_error(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = False
        await self.server.add_modules(self.module1)
        with self.assertRaises(ConnectionError):
            await self.server.register_modules()

    async def test_unregister_connection_error(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        await self.server.add_modules(self.module1)
        await self.server.register_modules()
        client_mock.is_connected.return_value = False
        with self.assertRaises(ConnectionError):
            await self.server.unregister_modules()

    async def test_register_type_error(
        self, client_mock: MagicMock, id_resolver_mock: AsyncMock
    ):
        client_mock.is_connected.return_value = True
        self.server._modules.add("not a module")
        with self.assertRaises(TypeError):
            await self.server.register_modules()
