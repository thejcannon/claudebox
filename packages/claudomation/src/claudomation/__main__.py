import json
from functools import partial

from cyclopts import App
from mcp import StdioServerParameters
from mmcp_client import MultiMCPClient

from claudomation.backends.api_loop import api_loop
from claudomation.frontends.tui.app import ClaudomationTUIApp

app = App(help="Claudomation")


@app.command
async def tui(*, prompt: str, mcp_server_configs_json: str | None = None):
    """Run the TUI"""
    mcp_server_configs = {
        key: StdioServerParameters(**value) for key, value in json.loads(mcp_server_configs_json or "{}").items()
    }
    # @TODO: Put some kind of spinner while MCP servers fire up?
    # NB: We start up here so that any errors on startup are visible
    #  (I think this is likely solvable inside of textual, in which case we might can move it down)
    async with await MultiMCPClient.start(mcp_server_configs) as mcp_client:
        await ClaudomationTUIApp(worker_run=partial(api_loop, prompt=prompt, mcp_client=mcp_client)).run_async()


def main():
    from dotenv import load_dotenv

    load_dotenv()
    app()


if __name__ == "__main__":
    main()
