from __future__ import annotations

from typing import AsyncIterator

from sc_async_client.client import erase_elements, generate_elements, search_by_template
from sc_async_client.constants import ScType, sc_type
from sc_async_client.models import ScAddr, ScConstruction, ScTemplate, ScTemplateResult

from sc_async_kpm.utils.common_utils import generate_node


class ScSet:
    """
    ScSet is a class for handling set construction in kb.

    It has main set_node and elements.
    """

    def __init__(
        self, set_node: ScAddr | None = None, set_node_type: ScType | None = None
    ) -> None:
        """
        Initialize ScSet.

        This constructor does not perform async operations directly.
        Use `ScSet.create()` for async initialization.
        """
        if not set_node:
            raise Exception("Set node must be valid")
        self._set_node = set_node
        self._set_node_type = set_node_type or sc_type.CONST_NODE

    @classmethod
    async def create(
        cls,
        *elements: ScAddr,
        set_node: ScAddr | None = None,
        set_node_type: ScType | None = None,
    ) -> "ScSet":
        """
        Asynchronous factory method to create an ScSet instance.

        :param elements: Elements of a set to initialize it.
        :param set_node: Optional existing set node.
        :param set_node_type: Type for generated set node if not provided.
        :return: Initialized ScSet instance.
        """
        if set_node is None:
            if set_node_type is None:
                set_node_type = sc_type.CONST_NODE
            set_node = await generate_node(set_node_type)

        instance = cls(set_node=set_node, set_node_type=set_node_type)
        await instance.add(*elements)
        return instance

    async def add(self, *elements: ScAddr) -> None:
        """Add elements to ScSet"""
        if elements:
            construction = ScConstruction()
            for element in elements:
                construction.generate_connector(
                    sc_type.CONST_PERM_POS_ARC, self._set_node, element
                )
            await generate_elements(construction)

    @property
    def set_node(self) -> ScAddr:
        """Get the main element of ScSet"""
        return self._set_node

    def __eq__(self, other) -> bool:
        if not isinstance(other, ScSet):
            raise TypeError("ScSet can be compare only with ScSets")
        return self._set_node == other._set_node

    async def get_elements_set(self) -> set[ScAddr]:
        """Set of elements without order and duplicates"""
        search_results = await self._elements_search_results()
        elements = {result[2] for result in search_results}
        return elements

    async def size(self) -> int:
        """Get ScSet power"""
        elements = await self.get_elements_set()
        return len(elements)

    async def is_nonempty(self) -> bool:
        """Check ScSet is not empty"""
        search_results = await self._elements_search_results()
        return bool(search_results)

    async def is_empty(self) -> bool:
        """Check if ScSet doesn't contain any element"""
        return not await self.is_nonempty()

    async def __iter__(self) -> AsyncIterator[ScAddr]:
        """Iterate by ScSet elements"""
        elements = await self.get_elements_set()
        for el in elements:
            yield el

    async def contains(self, element: ScAddr) -> bool:
        """Check if ScSet contains element"""
        elements = await self.get_elements_set()
        return element in elements

    async def remove(self, *elements: ScAddr) -> None:
        """Erase the connections between set_node and elements"""
        templ = ScTemplate()
        for element in elements:
            templ.triple(self._set_node, sc_type.VAR_PERM_POS_ARC, element)
        template_results = await search_by_template(templ)
        await erase_elements(*(res[1] for res in template_results))

    async def clear(self) -> None:
        """Erase the arcs between set_node and all elements"""
        template_results = await self._elements_search_results()
        await erase_elements(*(res[1] for res in template_results))

    async def _elements_search_results(self) -> list[ScTemplateResult]:
        """Template search of all elements"""
        templ = ScTemplate()
        templ.triple(self._set_node, sc_type.VAR_PERM_POS_ARC, sc_type.UNKNOWN)
        return await search_by_template(templ)
