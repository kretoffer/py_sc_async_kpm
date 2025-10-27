"""
This source file is part of an OSTIS project. For the latest info, see https://github.com/ostis-ai
Distributed under the MIT License
(See an accompanying file LICENSE or a copy at https://opensource.org/licenses/MIT)
"""

from abc import ABC, abstractmethod
from logging import getLogger
from typing import Set

from sc_async_kpm.sc_agent import ScAgentAbstract


class ScModuleAbstract(ABC):
    """
    ScModule is a container for handling multiple ScAgent objects.
    You can add and remove agents while module is registered or unregistered.
    """

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    async def add_agent(self, agent: ScAgentAbstract) -> None:
        """Add agent to the module and register it if module is registered"""

    @abstractmethod
    async def remove_agent(self, agent: ScAgentAbstract) -> None:
        """Remove agent from the module and unregister it if module is registered"""

    @abstractmethod
    async def _register(self) -> None:
        """Register all agents in the module"""

    @abstractmethod
    async def _unregister(self) -> None:
        """Unregister all agents from the module"""


class ScModule(ScModuleAbstract):
    def __init__(self, *agents: ScAgentAbstract) -> None:
        self._agents: Set[ScAgentAbstract] = {*agents}
        self._is_registered: bool = False
        self.logger = getLogger(f"{self.__module__}.{self.__class__.__name__}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(map(repr, self._agents))})"

    async def add_agent(self, agent: ScAgentAbstract) -> None:
        if self._is_registered:
            await agent._register()
        self._agents.add(agent)

    async def remove_agent(self, agent: ScAgentAbstract) -> None:
        if self._is_registered:
            await agent._unregister()
        self._agents.remove(agent)

    async def _register(self) -> None:
        if self._is_registered:
            self.logger.warning("Already registered")
            return
        if not self._agents:
            self.logger.warning("No agents to register")
        for agent in self._agents:
            await agent._register()
        self._is_registered = True
        self.logger.info("Registered")

    async def _unregister(self) -> None:
        for agent in self._agents:
            await agent._unregister()
        self._is_registered = False
        self.logger.info("Unregistered")
