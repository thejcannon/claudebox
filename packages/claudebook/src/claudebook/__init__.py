import json
import re
from pathlib import Path
from textwrap import dedent

import claudomation.__main__ as claudomation_main
import cyclopts
import yaml

DOC_SEP_RE = re.compile(r"\n---\n", re.DOTALL)

app = cyclopts.App("Claudebook")


@app.default()
async def run(runbook: Path, context: str = ""):
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))

    content = runbook.read_text()
    front_matter, prose = DOC_SEP_RE.split(content, 1)
    config = yaml.safe_load(front_matter)

    prompt = dedent(
        """\
        The following is a runbook that you should follow.

        When in doubt, a human can be prompted for more clarity/info.

        <additional context>
        {context}
        </additional context>

        <runbook>
        {prose}
        </runbook>
        """
    ).format(context=context, prose=prose)

    await claudomation_main.tui(prompt=prompt, mcp_server_configs_json=json.dumps(config["mcp"]))


if __name__ == "__main__":
    app()
