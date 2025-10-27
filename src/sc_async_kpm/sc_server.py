"""
This source file is part of an OSTIS project. For the latest info, see https:#github.com/ostis-ai
Distributed under the MIT License
(See an accompanying file LICENSE or a copy at https:#opensource.org/licenses/MIT)
"""

from __future__ import annotations

import asyncio
import signal
from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import Callable, Awaitable

from sc_async_client import client

from sc_async_kpm.identifiers import _IdentifiersResolver
from sc_async_kpm.sc_module import ScModuleAbstract


class ScServerAbstract(ABC):
    """ScServer connects to server and stores"""

    @abstractmethod
    async def connect(self) -> _Finisher:
        """Connect to server"""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the server"""
        raise NotImplementedError

    @abstractmethod
    async def add_modules(self, *modules: ScModuleAbstract) -> None:
        """Add modules to the server and register them if server is registered"""
        raise NotImplementedError

    @abstractmethod
    async def remove_modules(self, *modules: ScModuleAbstract) -> None:
        """Remove modules from the server and unregister them if server is registered"""
        raise NotImplementedError

    @abstractmethod
    async def clear_modules(self) -> None:
        """Remove all modules from the server and unregister them if server is registered"""
        raise NotImplementedError

    @abstractmethod
    async def register_modules(self) -> _Finisher:
        """Register all modules in the server"""
        raise NotImplementedError

    @abstractmethod
    async def unregister_modules(self) -> None:
        """Unregister all modules from the server"""
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> _Finisher:
        """Connect and register modules"""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Disconnect and unregister modules"""
        raise NotImplementedError


class ScServer(ScServerAbstract):
    def __init__(self, sc_server_url: str) -> None:
        self._url: str = sc_server_url
        self._modules: set[ScModuleAbstract] = set()
        self.is_registered = False
        self.logger = getLogger(f"{self.__module__}.{self.__class__.__name__}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(map(repr, self._modules))})"

    async def connect(self) -> _Finisher:
        await client.connect(self._url)
        self.logger.info("Connected by url: %s", repr(self._url))
        await _IdentifiersResolver.resolve()
        return _Finisher(self.disconnect, self.logger)

    async def disconnect(self) -> None:
        await client.disconnect()
        self.logger.info("Disconnected from url: %s", repr(self._url))

    async def add_modules(self, *modules: ScModuleAbstract) -> None:
        if self.is_registered:
            await self._register(*modules)
        self._modules |= {*modules}
        self.logger.info("Added modules: %s", ", ".join(map(repr, modules)))

    async def remove_modules(self, *modules: ScModuleAbstract) -> None:
        if self.is_registered:
            await self._unregister(*modules)
        self._modules -= {*modules}
        self.logger.info("Removed modules: %s", ", ".join(map(repr, modules)))

    async def clear_modules(self) -> None:
        if self.is_registered:
            await self._unregister(*self._modules)
        self.logger.info("Removed all modules: %s", ", ".join(map(repr, self._modules)))
        self._modules.clear()

    async def register_modules(self) -> _Finisher:
        if self.is_registered:
            self.logger.warning("Modules are already registered")
        else:
            await self._register(*self._modules)
            self.is_registered = True
            self.logger.info("Registered modules successfully")
        return _Finisher(self.unregister_modules, self.logger)

    async def unregister_modules(self) -> None:
        if not self.is_registered:
            self.logger.warning("Modules are already unregistered")
            return
        await self._unregister(*self._modules)
        self.is_registered = False
        self.logger.info("Unregistered modules successfully")

    async def start(self) -> _Finisher:
        await self.connect()
        await self.register_modules()
        return _Finisher(self.stop, self.logger)

    async def stop(self) -> None:
        await self.unregister_modules()
        await self.disconnect()

    async def _register(self, *modules: ScModuleAbstract) -> None:
        if not client.is_connected():
            self.logger.error("Failed to register: connection lost")
            raise ConnectionError(f"Connection to url {repr(self._url)} lost")
        for module in modules:
            if not isinstance(module, ScModuleAbstract):
                self.logger.error(
                    "Failed to register: type of %s is not ScModule", repr(module)
                )
                raise TypeError(f"{repr(module)} is not ScModule")
            await module._register()  # pylint: disable=protected-access

    async def _unregister(self, *modules: ScModuleAbstract) -> None:
        if not client.is_connected():
            self.logger.error(
                "Failed to unregister: connection to %s lost", repr(self._url)
            )
            raise ConnectionError(f"Connection to {repr(self._url)} lost")
        for module in modules:
            await module._unregister()  # pylint: disable=protected-access

    async def serve(self) -> None:
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def handle_sigint():
            self.logger.info("^C SIGINT was interrupted")
            stop_event.set()

        loop.add_signal_handler(signal.SIGINT, handle_sigint)
        await stop_event.wait()


class _Finisher:
    """Class for calling finish method in with-statement"""

    def __init__(
        self, finish_method: Callable[[], Awaitable[None]], logger: Logger
    ) -> None:
        self._finish_method = finish_method
        self._logger = logger

    async def __aenter__(self) -> None:
        pass  # Interaction through the beginning method (with server.start_method(): ...)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None:
            self._logger.error("Raised error %s, finishing", repr(exc_val))
        await self._finish_method()
