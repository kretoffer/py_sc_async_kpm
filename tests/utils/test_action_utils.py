from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_client.constants import sc_type
from sc_async_client.models import ScAddr, ScTemplateResult

from sc_async_kpm.identifiers import ActionStatus
from sc_async_kpm.utils.action_utils import (
    add_action_arguments,
    call_action,
    check_action_class,
    finish_action,
    finish_action_with_status,
    generate_action,
    generate_action_result,
    get_action_arguments,
    get_action_result,
)


@patch(
    "sc_async_kpm.utils.action_utils.client.search_by_template", new_callable=AsyncMock
)
@patch("sc_async_kpm.utils.action_utils.ScKeynodes", new_callable=MagicMock)
class TestActionUtils(IsolatedAsyncioTestCase):
    async def test_check_action_class(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        keynodes_mock.get_by_idtf = AsyncMock(return_value=ScAddr(10))
        search_mock.return_value = [ScTemplateResult([], 0)]
        self.assertTrue(await check_action_class("action_class", ScAddr(2)))
        search_mock.return_value = []
        self.assertFalse(await check_action_class("action_class", ScAddr(2)))

    async def test_get_action_arguments(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        rrel_1, rrel_2 = ScAddr(101), ScAddr(102)
        arg1, arg2 = ScAddr(201), ScAddr(202)
        keynodes_mock.rrel_index = AsyncMock(side_effect=[rrel_1, rrel_2])
        with patch(
            "sc_async_kpm.utils.action_utils.search_element_by_role_relation",
            new_callable=AsyncMock,
        ) as search_elem_mock:
            search_elem_mock.side_effect = [arg1, arg2]
            args = await get_action_arguments(ScAddr(1), 2)
            self.assertEqual(args, [arg1, arg2])
            self.assertEqual(search_elem_mock.call_count, 2)

    async def test_generate_action_result(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        nrel_result = ScAddr(301)
        keynodes_mock.get_by_idtf = AsyncMock(return_value=nrel_result)
        with patch(
            "sc_async_kpm.utils.action_utils.ScStructure.create", new_callable=AsyncMock
        ) as create_struct_mock, patch(
            "sc_async_kpm.utils.action_utils.generate_non_role_relation",
            new_callable=AsyncMock,
        ) as gen_rel_mock:
            struct_mock = MagicMock()
            struct_node = ScAddr(401)
            struct_mock.set_node = struct_node
            create_struct_mock.return_value = struct_mock

            action_node = ScAddr(1)
            result_elements = [ScAddr(2), ScAddr(3)]
            await generate_action_result(action_node, *result_elements)

            create_struct_mock.assert_awaited_once_with(*result_elements)
            gen_rel_mock.assert_awaited_once_with(action_node, struct_node, nrel_result)

    async def test_get_action_result(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        result_node = ScAddr(401)
        keynodes_mock.get_by_idtf = AsyncMock()
        search_mock.return_value = [MagicMock(get=MagicMock(return_value=result_node))]
        self.assertEqual(await get_action_result(ScAddr(1)), result_node)
        search_mock.return_value = []
        self.assertEqual(await get_action_result(ScAddr(1)), ScAddr(0))

    async def test_generate_action(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        with patch(
            "sc_async_kpm.utils.action_utils.client.generate_elements",
            new_callable=AsyncMock,
        ) as gen_elements_mock:
            action_node = ScAddr(1)
            gen_elements_mock.return_value = [action_node]
            keynodes_mock.resolve = AsyncMock(return_value=ScAddr(10))

            result = await generate_action("concept1", "concept2")
            self.assertEqual(result, action_node)
            self.assertEqual(keynodes_mock.resolve.call_count, 2)
            gen_elements_mock.assert_awaited_once()

    async def test_add_action_arguments(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        rrel_dynamic = ScAddr(100)
        rrel_1, rrel_2 = ScAddr(101), ScAddr(102)
        keynodes_mock.get_by_idtf = AsyncMock(return_value=rrel_dynamic)
        keynodes_mock.rrel_index = AsyncMock(side_effect=[rrel_1, rrel_2])

        with patch(
            "sc_async_kpm.utils.action_utils.generate_node", new_callable=AsyncMock
        ) as gen_node_mock, patch(
            "sc_async_kpm.utils.action_utils.generate_role_relation",
            new_callable=AsyncMock,
        ) as gen_role_mock, patch(
            "sc_async_kpm.utils.action_utils.generate_connector", new_callable=AsyncMock
        ) as gen_conn_mock:
            dynamic_node = ScAddr(500)
            gen_node_mock.return_value = dynamic_node

            action_node = ScAddr(1)
            arg1, arg2 = ScAddr(201), ScAddr(202)
            arguments = {arg1: True, arg2: False}

            await add_action_arguments(action_node, arguments)

            gen_node_mock.assert_awaited_once_with(sc_type.CONST_NODE)
            self.assertEqual(gen_role_mock.call_count, 2)
            gen_conn_mock.assert_awaited_once_with(
                sc_type.CONST_TEMP_POS_ARC, dynamic_node, arg1
            )

    async def test_call_action(self, keynodes_mock: MagicMock, search_mock: AsyncMock):
        initiation_node = ScAddr(10)
        keynodes_mock.resolve = AsyncMock(return_value=initiation_node)
        with patch(
            "sc_async_kpm.utils.action_utils.generate_connector", new_callable=AsyncMock
        ) as gen_conn_mock:
            action_node = ScAddr(1)
            await call_action(action_node, ActionStatus.ACTION_INITIATED)
            keynodes_mock.resolve.assert_awaited_once_with(
                ActionStatus.ACTION_INITIATED, sc_type.CONST_NODE_CLASS
            )
            gen_conn_mock.assert_awaited_once_with(
                sc_type.CONST_PERM_POS_ARC, initiation_node, action_node
            )

    async def test_finish_action(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        status_node = ScAddr(10)
        keynodes_mock.get_by_idtf = AsyncMock(return_value=status_node)
        with patch(
            "sc_async_kpm.utils.action_utils.generate_connector", new_callable=AsyncMock
        ) as gen_conn_mock:
            arc = ScAddr(11)
            gen_conn_mock.return_value = arc
            action_node = ScAddr(1)
            result = await finish_action(action_node, ActionStatus.ACTION_FINISHED)
            self.assertEqual(result, arc)
            keynodes_mock.get_by_idtf.assert_awaited_once_with(
                ActionStatus.ACTION_FINISHED
            )
            gen_conn_mock.assert_awaited_once_with(
                sc_type.CONST_PERM_POS_ARC, status_node, action_node
            )

    async def test_finish_action_with_status(
        self, keynodes_mock: MagicMock, search_mock: AsyncMock
    ):
        with patch(
            "sc_async_kpm.utils.action_utils.finish_action", new_callable=AsyncMock
        ) as finish_action_mock:
            action_node = ScAddr(1)
            await finish_action_with_status(action_node, is_success=True)
            self.assertEqual(finish_action_mock.call_count, 2)
            finish_action_mock.assert_any_await(
                action_node, ActionStatus.ACTION_FINISHED_SUCCESSFULLY
            )
            finish_action_mock.assert_any_await(
                action_node, ActionStatus.ACTION_FINISHED
            )

            finish_action_mock.reset_mock()
            await finish_action_with_status(action_node, is_success=False)
            self.assertEqual(finish_action_mock.call_count, 2)
            finish_action_mock.assert_any_await(
                action_node, ActionStatus.ACTION_FINISHED_UNSUCCESSFULLY
            )
            finish_action_mock.assert_any_await(
                action_node, ActionStatus.ACTION_FINISHED
            )
