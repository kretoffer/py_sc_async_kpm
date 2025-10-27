from sc_async_client.client import get_elements_types
from sc_async_client.constants import ScType, sc_type
from sc_async_client.constants.exceptions import InvalidTypeError
from sc_async_client.models import ScAddr

from sc_async_kpm.sc_sets.sc_set import ScSet
from sc_async_kpm.utils.common_utils import generate_node


class ScStructure(ScSet):
    """
    ScStructure is a class for handling structure construction in kb.

    It has main set_node with type CONST_NODE_STRUCTURE and elements.
    """

    def __init__(self, set_node: ScAddr, set_node_type: ScType) -> None:
        """
        Initialize ScStructure.

        This constructor does not perform async operations directly.
        Use `ScStructure.create()` for async initialization.
        """
        super().__init__(set_node=set_node, set_node_type=set_node_type)

    @classmethod
    async def create(
        cls,
        *elements: ScAddr,
        set_node: ScAddr | None = None,
        set_node_type: ScType | None = None,
    ) -> "ScStructure":
        if set_node_type is None:
            set_node_type = sc_type.CONST_NODE_STRUCTURE

        if set_node is not None:
            types = await get_elements_types(set_node)
            set_node_type = types[0]
        else:
            set_node = await generate_node(set_node_type)

        if not set_node_type.is_structure():
            raise InvalidTypeError(f"Provided type {set_node_type} is not a structure")

        instance = cls(set_node=set_node, set_node_type=set_node_type)
        await instance.add(*elements)
        return instance
