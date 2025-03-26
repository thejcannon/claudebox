from pathlib import Path
from textwrap import dedent
from unittest.mock import AsyncMock, patch

import pytest
from claudebook import app


@pytest.fixture
def mock_tui():
    with patch("claudomation.__main__.tui", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def sample_runbook(tmp_path: Path) -> Path:
    content = dedent("""\
        mcp:
            foo: bar
        ---
        This is the prose section
        """)
    runbook = tmp_path / "test.runbook"
    runbook.write_text(content)
    return runbook


def test_parses_correctly(mock_tui, sample_runbook: Path):
    app([str(sample_runbook)])

    mock_tui.assert_called_once()
    call_args = mock_tui.call_args[1]
    assert "This is the prose section" in call_args["prompt"]
    assert call_args["mcp_server_configs_json"] == '{"foo": "bar"}'


def test_includes_context(mock_tui, sample_runbook: Path):
    context = "Some extra context"
    app([str(sample_runbook), f"--context={context}"])

    mock_tui.assert_called_once()
    assert context in mock_tui.call_args[1]["prompt"]
