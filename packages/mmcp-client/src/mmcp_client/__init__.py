import asyncio
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager, AsyncExitStack
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


@dataclass(frozen=True)
class MultiMCPClient(AbstractAsyncContextManager):
    _exit_stack: AsyncExitStack
    _sessions_by_name: dict[str, ClientSession]

    @classmethod
    async def start(cls, servers_params_by_name: Mapping[str, StdioServerParameters]) -> "MultiMCPClient":
        async def get_session(exit_stack: AsyncExitStack, server_params: StdioServerParameters) -> ClientSession:
            read, write = await exit_stack.enter_async_context(stdio_client(server_params))
            session = await exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            return session

        async with AsyncExitStack() as exit_stack:
            sessions = await asyncio.gather(
                *(get_session(exit_stack, server_params) for server_params in servers_params_by_name.values()),
            )
            return cls(
                exit_stack.pop_all(),
                dict(zip(servers_params_by_name.keys(), sessions, strict=True)),
            )

        raise AssertionError("Unreachable")  # noqa: EM101

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.aclose()

    async def list_tools(self) -> types.ListToolsResult:
        """Send a tools/list request."""
        results = await asyncio.gather(*[session.list_tools() for session in self._sessions_by_name.values()])
        for server_name, result in zip(self._sessions_by_name.keys(), results, strict=True):
            for tool in result.tools:
                tool.name = f"{server_name}-{tool.name}"

        return types.ListToolsResult(tools=[tool for result in results for tool in result.tools])

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> types.CallToolResult:
        """Send a tools/call request."""
        server_name, tool_name = name.split("-", 1)
        session = self._sessions_by_name[server_name]
        return await session.call_tool(tool_name, arguments)

    # @TODO: Add other primitives like resources/prompts
