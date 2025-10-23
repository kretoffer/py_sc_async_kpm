"""
This source file is part of an OSTIS project. For the latest info, see https://github.com/ostis-ai
Distributed under the MIT License
(See an accompanying file LICENSE or a copy at https://opensource.org/licenses/MIT)
"""

from logging import Logger, getLogger
from typing import Dict, Optional

from sc_async_client import client
from sc_async_client.client import erase_elements
from sc_async_client.constants.exceptions import InvalidValueError
from sc_async_client.constants.sc_type import CONST_NODE_ROLE, ScType
from sc_async_client.models import ScAddr, ScIdtfResolveParams

Idtf = str


class ScKeynodesMeta(type):
    """Metaclass to use ScKeynodes without creating an instance of a class"""

    def __init__(cls, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        cls._dict: Dict[Idtf, ScAddr] = {}
        cls._logger: Logger = getLogger(f"{__name__}.{cls.__name__}")
        cls._min_rrel_index: int = 1
        cls._max_rrel_index: int = 10

    def __call__(cls, *args, **kwargs) -> None:
        raise TypeError(f"Use {cls.__name__} without initialization")

    async def get_by_idtf(cls, identifier: Idtf) -> ScAddr:
        """Get keynode, cannot be invalid ScAddr(0)"""
        addr = await cls.get(identifier)
        if not addr.is_valid():
            cls._logger.error(
                "Failed to get ScAddr by %s keynode: ScAddr is invalid", identifier
            )
            raise InvalidValueError(f"ScAddr of {identifier} is invalid")
        return addr

    async def erase(cls, identifier: Idtf) -> bool:
        """Erase keynode from the kb and memory and return boolean status"""
        addr = await cls.get_by_idtf(identifier)
        del cls._dict[identifier]
        return await erase_elements(addr)

    async def get(cls, identifier: Idtf) -> ScAddr:
        """Get keynode, can be ScAddr(0)"""
        return await cls.resolve(identifier, None)

    async def resolve(cls, identifier: Idtf, sc_type: Optional[ScType]) -> ScAddr:
        """Get keynode. If sc_type is valid, an element will be created in the KB"""
        addr = cls._dict.get(identifier)
        if addr is None:
            params = ScIdtfResolveParams(idtf=identifier, type=sc_type)
            res = await client.resolve_keynodes(params)
            addr = res[0]
            if addr.is_valid():
                cls._dict[identifier] = addr
            cls._logger.debug(
                "Resolved %s identifier with type %s: %s",
                repr(identifier),
                repr(sc_type),
                repr(addr),
            )
        return addr

    async def rrel_index(cls, index: int) -> ScAddr:
        """Get rrel_i node. Max rrel index is 10. Min rrel is 1."""
        if not isinstance(index, int):
            raise TypeError("Index of rrel node must be int")
        if index > cls._max_rrel_index:
            raise KeyError(f"You cannot use rrel more than {cls._max_rrel_index}")
        if index < cls._min_rrel_index:
            raise KeyError(f"You cannot use rrel less than {cls._min_rrel_index}")
        return await cls.resolve(f"rrel_{index}", CONST_NODE_ROLE)


class ScKeynodes(metaclass=ScKeynodesMeta):
    """Class which provides the ability to cache the identifier and ScAddr of keynodes stored in the KB."""
