# Claudebook

Claudebook is a way to automate runbooks using MCP and Claude!

```md
#! /usr/bin/env uvx claudebook
mcp:
    github:
        name: github
        command: uv
        args: ["run", "mcp-servers/github.py"]
    buildkite:
        name: buildkite
        command: uv
        args: ["run", "mcp-servers/buildkite.py"]
    s3:
        name: s3
        command: uv
        args: ["run", "mcp-servers/s3.py"]
---

# Fix test failures

## Get the build

Use the GitHub API to find the build for the Pull request that failed.

## Find the failing jobs

Use the buildkite GraphQL API to query the build for jobs which failed.

## Get the logs

For those jobs, get the logs to see what went wrong.

## Fix the issue

Make a change to the PR branch to fix the issue.
```

then,

`./runbooks/fix-test-failure.md --context 'https://github.com/myorg/myrepo/pull/51463'
