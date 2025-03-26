import asyncio
import json
from pathlib import Path
from typing import cast

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, ToolParam, ToolResultBlockParam, ToolUseBlock
from mcp.types import TextContent
from mmcp_client import MultiMCPClient
from pydantic_core import to_jsonable_python
from textual.containers import VerticalScroll
from textual.widgets import Static

from claudomation.frontends.tui.widgets.claude_message_box import ClaudeMessageBox
from claudomation.frontends.tui.widgets.tool_use_box import ToolUseBox
from claudomation.frontends.tui.widgets.user_message_box import UserMessageBox

USER_DENIED_CONTENT_TEXT = "((Tool use denied by user, see user text))"
SUMMARY_PROPNAME = "__summary__"


async def _get_tools(mcp_client: MultiMCPClient) -> list[ToolParam]:
    tools = []
    for tool in (await mcp_client.list_tools()).tools:
        properties = tool.inputSchema.setdefault("properties", {})
        properties[SUMMARY_PROPNAME] = {
            "type": "string",
            "description": "(A brief summary of what the tool use will do. Will be displayed to the user in the UI).",
        }

        tools.append(
            ToolParam(
                input_schema=tool.inputSchema,
                name=tool.name,
                description=tool.description or "",
            )
        )

    return tools


async def api_loop(
    # @TODO: Not the chat log, but the "context"
    chat_log: VerticalScroll,
    prompt: str,
    mcp_client: MultiMCPClient,
) -> None:
    messages = [MessageParam(role="user", content=prompt)]
    # NB: Right now we cache tools list
    #   (But in the future we could ask in each loop turn)
    tools = await _get_tools(mcp_client)
    tools.append(
        ToolParam(
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
            },
            name="__prompt_human__",
            description="Provides a brief prompt to the human for input. (Since you are being controlled fully agentically, this is the only way to solicit input from the human)",
        )
    )

    tools_by_name = {tool["name"]: tool for tool in tools}

    async def maybe_call_tool(
        tool_use_block: ToolUseBlock, tool_use_box: ToolUseBox
    ) -> tuple[bool, ToolResultBlockParam]:
        is_approved = await tool_use_box.decision
        if not is_approved:
            return True, ToolResultBlockParam(
                type="tool_result",
                tool_use_id=tool_use_block.id,
                content=USER_DENIED_CONTENT_TEXT,
                is_error=True,
            )

        assert isinstance(tool_use_block.input, dict)
        tool_input = tool_use_block.input.copy()
        tool_input.pop(SUMMARY_PROPNAME, None)
        tool_call_result = await mcp_client.call_tool(tool_use_block.name, tool_input)
        # @TODO: Handle errors
        # @TODO: <venv>/mcp/server/fastmcp/server.py:528
        #   - None -> (empty list)
        #   - str -> itself
        #   - list result -> (recursive)
        #   - otherwise this'll be JSON
        assert isinstance(tool_call_result.content[0], TextContent)
        await tool_use_box.set_tool_result(tool_call_result.content[0].text)
        if tool_call_result.isError:
            tool_use_box.add_class("error")
        else:
            tool_use_box.add_class("success")

        return False, ToolResultBlockParam(
            type="tool_result",
            tool_use_id=tool_use_block.id,
            content=tool_call_result.content[0].text,
            is_error=tool_call_result.isError,
        )

    async def prompt_human(
        tool_use_block: ToolUseBlock, user_message_box: UserMessageBox
    ) -> tuple[bool, ToolResultBlockParam]:
        result = await user_message_box.submission
        return False, ToolResultBlockParam(
            type="tool_result",
            tool_use_id=tool_use_block.id,
            content=result,
            is_error=False,
        )

    # @TODO: use helper class
    logfile = Path("logs.jsonl.tmp").open("w")  # noqa: SIM115, ASYNC230
    # @TODO: Log the MCP server configs?

    anthropic_client = AsyncAnthropic()

    logfile.write(json.dumps(messages[0]) + "\n")
    while True:
        claude_message_box = ClaudeMessageBox()
        chat_log.mount(claude_message_box)
        tool_use_futures = []
        async with anthropic_client.messages.stream(
            # @TODO: Take these in as params? (Maybe just the entire client object?)
            max_tokens=2048,
            model="claude-3-7-sonnet-latest",
            # @TODO: Use the `token-efficient-tools-2025-02-19`
            messages=messages,
            tools=tools,
        ) as stream:
            async for event in stream:
                if event.type == "message_start":
                    claude_message_box.border_subtitle = event.message.id
                elif event.type == "text":
                    if not claude_message_box.children:
                        claude_message_box.mount(Static("", markup=False))
                    cast(Static, claude_message_box.children[0]).update(event.snapshot)
                elif event.type == "content_block_stop":
                    content = event.content_block
                    if content.type == "tool_use":
                        assert isinstance(content.input, dict)
                        if content.name == "__prompt_human__":
                            user_message_box = UserMessageBox(reason=content.input["prompt"])
                            chat_log.mount(user_message_box)
                            tool_use_futures.append(prompt_human(content, user_message_box))
                        else:
                            summary = content.input.pop("summary", None)
                            tool_use_box = ToolUseBox(
                                content,
                                summary=summary,
                                requires_approval=not tools_by_name[content.name]["input_schema"].get(
                                    "readOnly", False
                                ),
                            )
                            tool_use_futures.append(maybe_call_tool(content, tool_use_box))
                            chat_log.mount(tool_use_box)
                elif event.type == "message_stop":
                    await claude_message_box.stop_spinning()

            final = await stream.get_final_message()

        messages.append(MessageParam(role="assistant", content=final.content))
        logfile.write(json.dumps(to_jsonable_python(messages[-1])) + "\n")
        if not tool_use_futures:
            break

        tool_result_pairs = await asyncio.gather(*tool_use_futures)
        user_message = MessageParam(role="user", content=[pair[1] for pair in tool_result_pairs])
        if any(pair[0] for pair in tool_result_pairs):
            user_message_box = UserMessageBox()
            chat_log.mount(user_message_box)
            result = await user_message_box.submission
            assert isinstance(user_message["content"], list)
            user_message["content"].append({"type": "text", "text": result})

        messages.append(user_message)
        logfile.write(json.dumps(to_jsonable_python(messages[-1])) + "\n")
