# ClaudeBox

ClaudeBox contains tools/utilities for interacting with Claude.

## Claudomation

Claudomation is the CLI backbone of the toolbox.
It is meant to support several "modes" of interacting with Claude.

Currently it supports:

- A TUI mode
- (that's it!)

Eventually, the plan is to support:

- Several TUI modes
- A "just plain CLI" mode

Notable features:

- Supports mutliple (stdio) MCP servers
- Supports `readOnly` MCP tools

## Claudebook

Claudebook is a way to automate runbooks using MCP and Claude!

## MMCP-client

MMCP-client is a Python library for interacting with mutlipleMCP servers.

(Ideally, this is just lift-and-shifted into the Python SDK)
