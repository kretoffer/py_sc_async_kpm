from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_client.constants import sc_type
from sc_async_client.constants.common import ScEventType
from sc_async_client.constants.exceptions import InvalidValueError
from sc_async_client.models import ScAddr, ScEventSubscription

from sc_async_kpm.sc_agent import ScAgent, ScAgentClassic
from sc_async_kpm.sc_result import ScResult


# Concrete agent for testing, underscore to avoid pytest collection
class _TestAgent(ScAgent):
    async def on_event(self, *args, **kwargs) -> ScResult:
        return ScResult.OK


class _TestAgentClassic(ScAgentClassic):
    async def on_event(self, *args, **kwargs) -> ScResult:
        return ScResult.OK


class ScAgentTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.agent_event_element = ScAddr(1)
        self.agent_event_type = ScEventType.AFTER_GENERATE_OUTGOING_ARC

    async def test_sc_agent_create_with_sc_addr(self):
        agent = await _TestAgent.create(self.agent_event_element, self.agent_event_type)
        self.assertEqual(agent._event_element, self.agent_event_element)
        self.assertEqual(agent._event_type, self.agent_event_type)

    @patch("sc_async_kpm.sc_agent.ScKeynodes", new_callable=MagicMock)
    async def test_sc_agent_create_with_idtf(self, sc_keynodes_mock: MagicMock):
        sc_keynodes_mock.resolve = AsyncMock(return_value=self.agent_event_element)
        idtf = "test_idtf"
        agent = await _TestAgent.create(idtf, self.agent_event_type)
        sc_keynodes_mock.resolve.assert_awaited_once_with(
            idtf, sc_type.CONST_NODE_CLASS
        )
        self.assertEqual(agent._event_element, self.agent_event_element)

    @patch("sc_async_kpm.sc_agent.ScKeynodes", new_callable=MagicMock)
    async def test_sc_agent_create_invalid(self, sc_keynodes_mock: MagicMock):
        sc_keynodes_mock.resolve = AsyncMock(return_value=ScAddr(0))
        with self.assertRaises(InvalidValueError):
            await _TestAgent.create("invalid_idtf", self.agent_event_type)

    @patch(
        "sc_async_kpm.sc_agent.client.create_elementary_event_subscriptions",
        new_callable=AsyncMock,
    )
    async def test_register(self, create_event_mock: AsyncMock):
        event = ScEventSubscription(
            ScAddr(123), ScEventType.AFTER_GENERATE_OUTGOING_ARC, 1
        )
        create_event_mock.return_value = [event]
        agent = await _TestAgent.create(self.agent_event_element, self.agent_event_type)
        await agent._register()
        self.assertIsNotNone(agent._event)
        self.assertEqual(agent._event, event)
        create_event_mock.assert_awaited_once()
        # Test almost registered
        await agent._register()
        create_event_mock.assert_awaited_once()

    @patch(
        "sc_async_kpm.sc_agent.client.destroy_elementary_event_subscriptions",
        new_callable=AsyncMock,
    )
    @patch(
        "sc_async_kpm.sc_agent.client.create_elementary_event_subscriptions",
        new_callable=AsyncMock,
    )
    async def test_unregister(
        self, create_event_mock: AsyncMock, destroy_event_mock: AsyncMock
    ):
        event = ScEventSubscription(
            ScAddr(123), ScEventType.AFTER_GENERATE_OUTGOING_ARC, 1
        )
        create_event_mock.return_value = [event]
        agent = await _TestAgent.create(self.agent_event_element, self.agent_event_type)
        # Test unregister without register
        await agent._unregister()
        destroy_event_mock.assert_not_awaited()
        # Test unregister
        await agent._register()
        await agent._unregister()
        self.assertIsNone(agent._event)
        destroy_event_mock.assert_awaited_once_with(event)

    async def test_callback(self):
        agent = await _TestAgent.create(self.agent_event_element, self.agent_event_type)
        result = await agent._callback(ScAddr(1), ScAddr(2), ScAddr(3))
        self.assertEqual(result, ScResult.OK)


class ScAgentClassicTest(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.action_class_name = "test_action_class"
        self.action_class_addr = ScAddr(1)
        self.event_element_addr = ScAddr(2)

    @patch("sc_async_kpm.sc_agent.ScKeynodes", new_callable=MagicMock)
    async def test_create(self, sc_keynodes_mock: MagicMock):
        sc_keynodes_mock.resolve = AsyncMock(
            side_effect=[self.action_class_addr, self.event_element_addr]
        )
        agent = await _TestAgentClassic.create(self.action_class_name)
        self.assertEqual(agent._action_class, self.action_class_addr)
        self.assertEqual(agent._event_element, self.event_element_addr)

    @patch("sc_async_kpm.sc_agent.ScKeynodes", new_callable=MagicMock)
    async def test_create_invalid_event_element(self, sc_keynodes_mock: MagicMock):
        sc_keynodes_mock.resolve = AsyncMock(
            side_effect=[self.action_class_addr, ScAddr(0)]
        )
        with self.assertRaises(InvalidValueError):
            await _TestAgentClassic.create(self.action_class_name)

    @patch("sc_async_kpm.sc_agent.check_action_class", new_callable=AsyncMock)
    @patch("sc_async_kpm.sc_agent.ScKeynodes", new_callable=MagicMock)
    async def test_callback(
        self, sc_keynodes_mock: MagicMock, check_action_class_mock: AsyncMock
    ):
        sc_keynodes_mock.resolve = AsyncMock(return_value=self.action_class_addr)
        agent = await _TestAgentClassic.create(self.action_class_name)

        check_action_class_mock.return_value = True
        result = await agent._callback(ScAddr(1), ScAddr(2), ScAddr(3))
        self.assertEqual(result, ScResult.OK)
        check_action_class_mock.assert_awaited_once_with(agent._action_class, ScAddr(3))

        check_action_class_mock.reset_mock()
        check_action_class_mock.return_value = False
        result = await agent._callback(ScAddr(1), ScAddr(2), ScAddr(3))
        self.assertEqual(result, ScResult.SKIP)
        check_action_class_mock.assert_awaited_once_with(agent._action_class, ScAddr(3))
