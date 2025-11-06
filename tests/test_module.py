from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from sc_async_kpm.sc_agent import ScAgentAbstract
from sc_async_kpm.sc_module import ScModule


class ScModuleTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent1 = MagicMock(spec=ScAgentAbstract)
        self.agent1._register = AsyncMock()
        self.agent1._unregister = AsyncMock()
        self.agent2 = MagicMock(spec=ScAgentAbstract)
        self.agent2._register = AsyncMock()
        self.agent2._unregister = AsyncMock()

    async def test_add_agent(self):
        module = ScModule()
        await module.add_agent(self.agent1)
        self.assertIn(self.agent1, module._agents)
        self.agent1._register.assert_not_awaited()

    async def test_add_agent_registered(self):
        module = ScModule(self.agent2)
        await module._register()
        await module.add_agent(self.agent1)
        self.assertIn(self.agent1, module._agents)
        self.agent1._register.assert_awaited_once()

    async def test_remove_agent(self):
        module = ScModule(self.agent1)
        await module.remove_agent(self.agent1)
        self.assertNotIn(self.agent1, module._agents)
        self.agent1._unregister.assert_not_awaited()

    async def test_remove_agent_registered(self):
        module = ScModule(self.agent1, self.agent2)
        await module._register()
        await module.remove_agent(self.agent1)
        self.assertNotIn(self.agent1, module._agents)
        self.agent1._unregister.assert_awaited_once()
        self.agent2._register.assert_awaited_once()

    async def test_register(self):
        module = ScModule(self.agent1, self.agent2)
        await module._register()
        self.assertTrue(module._is_registered)
        self.agent1._register.assert_awaited_once()
        self.agent2._register.assert_awaited_once()
        # Test already registered
        await module._register()
        self.agent1._register.assert_awaited_once()
        self.agent2._register.assert_awaited_once()

    async def test_register_empty(self):
        module = ScModule()
        await module._register()
        self.assertTrue(module._is_registered)

    async def test_unregister(self):
        module = ScModule(self.agent1, self.agent2)
        await module._register()
        await module._unregister()
        self.assertFalse(module._is_registered)
        self.agent1._unregister.assert_awaited_once()
        self.agent2._unregister.assert_awaited_once()
