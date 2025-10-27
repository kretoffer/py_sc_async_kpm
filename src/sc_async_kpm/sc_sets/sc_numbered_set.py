from typing import AsyncIterator, List

from sc_async_client.client import generate_by_template, search_by_template
from sc_async_client.constants import sc_type
from sc_async_client.models import ScAddr, ScTemplate

from sc_async_kpm.sc_keynodes import ScKeynodes
from sc_async_kpm.sc_sets.sc_set import ScSet


class ScNumberedSet(ScSet):
    """
    ScNumberedSet is a class for handling numbered set structure in kb.

    It has main set_node and arc elements:
    Arcs to each element marked with 'rrel_1', 'rrel_2', and so on nodes.
    """

    async def add(self, *elements: ScAddr) -> None:
        """Add elements to ScNumberedSet"""
        if elements:
            template = ScTemplate()
            elements_list = await self.get_elements_list()
            for index, element in enumerate(elements, len(elements_list) + 1):
                template.quintuple(
                    self._set_node,
                    sc_type.VAR_PERM_POS_ARC,
                    element,
                    sc_type.VAR_PERM_POS_ARC,
                    await ScKeynodes.rrel_index(index),
                )
            await generate_by_template(template)

    async def __aiter__(self) -> AsyncIterator[ScAddr]:
        elements = await self.get_elements_set()
        for el in elements:
            yield el

    async def get_elements_list(self) -> List[ScAddr]:
        """Iterate by ScNumberedSet elements"""
        templ = ScTemplate()
        templ.quintuple(
            self._set_node,
            sc_type.VAR_PERM_POS_ARC,
            sc_type.UNKNOWN,
            sc_type.VAR_PERM_POS_ARC,
            sc_type.VAR_NODE_ROLE,
        )
        results = await search_by_template(templ)
        sorted_results = sorted(
            (result for result in results), key=lambda res: res[4].value
        )
        # Sort rrel elements addrs
        return [result[2] for result in sorted_results]

    async def get_by_index(self, i: int) -> ScAddr:
        templ = ScTemplate()
        templ.quintuple(
            self._set_node,
            sc_type.VAR_PERM_POS_ARC,
            sc_type.UNKNOWN,
            sc_type.VAR_PERM_POS_ARC,
            await ScKeynodes.rrel_index(i + 1),
        )
        results = await search_by_template(templ)
        if not results:
            raise KeyError("No element by index")
        return results[0][2]

    async def remove(self, *elements: ScAddr) -> None:
        """Clear and add existing elements without given ones"""
        # TODO: optimize
        elements_new = [element async for element in self if element not in elements]
        await self.clear()
        await self.add(*elements_new)
