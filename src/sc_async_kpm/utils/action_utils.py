"""
This source file is part of an OSTIS project. For the latest info, see https://github.com/ostis-ai
Distributed under the MIT License
(See an accompanying file LICENSE or a copy at https://opensource.org/licenses/MIT)
"""

import asyncio
from typing import Dict, List, Tuple, Union, cast

from sc_async_client import client
from sc_async_client.client import (
    create_elementary_event_subscriptions,
    destroy_elementary_event_subscriptions,
)
from sc_async_client.constants import sc_type
from sc_async_client.constants.common import ScEventType
from sc_async_client.models import (
    ScAddr,
    ScConstruction,
    ScEventSubscriptionParams,
    ScTemplate,
)

from sc_async_kpm.identifiers import ActionStatus, CommonIdentifiers, ScAlias
from sc_async_kpm.sc_keynodes import Idtf, ScKeynodes
from sc_async_kpm.sc_result import ScResult
from sc_async_kpm.sc_sets.sc_structure import ScStructure
from sc_async_kpm.utils.common_utils import (
    check_connector,
    generate_connector,
    generate_node,
    generate_non_role_relation,
    generate_role_relation,
    search_element_by_role_relation,
)

COMMON_WAIT_TIME: float = 5


async def check_action_class(
    action_class: Union[ScAddr, Idtf], action_node: ScAddr
) -> bool:
    action_class = (
        await ScKeynodes.get_by_idtf(action_class)
        if isinstance(action_class, Idtf)
        else action_class
    )
    templ = ScTemplate()
    templ.triple(action_class, sc_type.VAR_PERM_POS_ARC, action_node)
    templ.triple(
        await ScKeynodes.get_by_idtf(CommonIdentifiers.ACTION),
        sc_type.VAR_PERM_POS_ARC,
        action_node,
    )
    search_results = await client.search_by_template(templ)
    return len(search_results) > 0


async def get_action_arguments(action_node: ScAddr, count: int) -> List[ScAddr]:
    arguments = []
    for index in range(1, count + 1):
        rrel_index = await ScKeynodes.rrel_index(index)
        argument = await search_element_by_role_relation(action_node, rrel_index)
        arguments.append(argument)
    return arguments


async def generate_action_result(action_node: ScAddr, *elements: ScAddr) -> None:
    struct = await ScStructure.create(*elements)
    result_struct_node = struct.set_node
    await generate_non_role_relation(
        action_node,
        result_struct_node,
        await ScKeynodes.get_by_idtf(CommonIdentifiers.NREL_RESULT),
    )


async def get_action_result(action_node: ScAddr) -> ScAddr:
    templ = ScTemplate()
    templ.quintuple(
        action_node,
        sc_type.VAR_COMMON_ARC >> ScAlias.RELATION_ARC,
        sc_type.VAR_NODE_STRUCTURE >> ScAlias.ELEMENT,
        sc_type.VAR_PERM_POS_ARC,
        await ScKeynodes.get_by_idtf(CommonIdentifiers.NREL_RESULT),
    )
    search_results = await client.search_by_template(templ)
    if search_results:
        return search_results[0].get(ScAlias.ELEMENT)
    return ScAddr(0)


IsDynamic = bool


async def execute_agent(
    arguments: Dict[ScAddr, IsDynamic],
    concepts: List[Idtf],
    initiation: Idtf = ActionStatus.ACTION_INITIATED,
    reaction: Idtf = ActionStatus.ACTION_FINISHED_SUCCESSFULLY,
    wait_time: float = COMMON_WAIT_TIME,
) -> Tuple[ScAddr, bool]:
    action = await call_agent(arguments, concepts, initiation)
    await wait_agent(wait_time, action)
    result = await check_connector(
        sc_type.VAR_PERM_POS_ARC, await ScKeynodes.get_by_idtf(reaction), action
    )
    return action, result


async def call_agent(
    arguments: Dict[ScAddr, IsDynamic],
    concepts: List[Idtf],
    initiation: Idtf = ActionStatus.ACTION_INITIATED,
) -> ScAddr:
    action = await generate_action(*concepts)
    await add_action_arguments(action, arguments)
    await call_action(action, initiation)
    return action


async def generate_action(*concepts: Idtf) -> ScAddr:
    construction = ScConstruction()
    construction.generate_node(sc_type.CONST_NODE, ScAlias.ACTION_NODE)
    for concept in concepts:
        concept_addr = await ScKeynodes.resolve(concept, sc_type.CONST_NODE_CLASS)
        construction.generate_connector(
            sc_type.CONST_PERM_POS_ARC,
            concept_addr,
            ScAlias.ACTION_NODE,
        )
    generate_results = await client.generate_elements(construction)
    action_node = generate_results[0]
    return action_node


async def add_action_arguments(
    action_node: ScAddr, arguments: Dict[ScAddr, IsDynamic]
) -> None:
    rrel_dynamic_arg = await ScKeynodes.get_by_idtf(
        CommonIdentifiers.RREL_DYNAMIC_ARGUMENT
    )
    argument: ScAddr
    for index, (argument, is_dynamic) in enumerate(arguments.items(), 1):
        if argument.is_valid():
            rrel_i = await ScKeynodes.rrel_index(index)
            if is_dynamic:
                dynamic_node = await generate_node(sc_type.CONST_NODE)
                await generate_role_relation(
                    action_node, dynamic_node, rrel_dynamic_arg, rrel_i
                )
                await generate_connector(
                    sc_type.CONST_TEMP_POS_ARC, dynamic_node, argument
                )
            else:
                await generate_role_relation(action_node, argument, rrel_i)


async def execute_action(
    action_node: ScAddr,
    initiation: Idtf = ActionStatus.ACTION_INITIATED,
    reaction: Idtf = ActionStatus.ACTION_FINISHED_SUCCESSFULLY,
    wait_time: float = COMMON_WAIT_TIME,
) -> bool:
    await call_action(action_node, initiation)
    await wait_agent(wait_time, action_node)
    result = await check_connector(
        sc_type.VAR_PERM_POS_ARC, await ScKeynodes.get_by_idtf(reaction), action_node
    )
    return result


async def call_action(
    action_node: ScAddr, initiation: Idtf = ActionStatus.ACTION_INITIATED
) -> None:
    initiation_node = await ScKeynodes.resolve(initiation, sc_type.CONST_NODE_CLASS)
    await generate_connector(sc_type.CONST_PERM_POS_ARC, initiation_node, action_node)


async def wait_agent(
    seconds: float, action_node: ScAddr, reaction_node: ScAddr | None = None
) -> None:
    reaction_node = reaction_node or await ScKeynodes.get_by_idtf(
        ActionStatus.ACTION_FINISHED
    )
    finish_event = asyncio.Event()

    async def event_callback(_: ScAddr, __: ScAddr, trg: ScAddr) -> ScResult:
        if trg != reaction_node:
            return ScResult.SKIP
        finish_event.set()
        return ScResult.OK

    event_params = ScEventSubscriptionParams(
        action_node, ScEventType.AFTER_GENERATE_INCOMING_ARC, event_callback
    )
    sc_events = await create_elementary_event_subscriptions(event_params)
    sc_event = sc_events[0]

    if not await check_connector(
        sc_type.VAR_PERM_POS_ARC, cast(ScAddr, reaction_node), action_node
    ):
        try:
            await asyncio.wait_for(finish_event.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    await destroy_elementary_event_subscriptions(sc_event)


async def finish_action(
    action_node: ScAddr, status: Idtf = ActionStatus.ACTION_FINISHED
) -> ScAddr:
    return await generate_connector(
        sc_type.CONST_PERM_POS_ARC, await ScKeynodes.get_by_idtf(status), action_node
    )


async def finish_action_with_status(
    action_node: ScAddr, is_success: bool = True
) -> None:
    status = (
        ActionStatus.ACTION_FINISHED_SUCCESSFULLY
        if is_success
        else ActionStatus.ACTION_FINISHED_UNSUCCESSFULLY
    )
    await finish_action(action_node, status)
    await finish_action(action_node, ActionStatus.ACTION_FINISHED)
