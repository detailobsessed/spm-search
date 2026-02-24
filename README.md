# spm-search-mcp

[![ci](https://github.com/detailobsessed/spm-search-mcp/workflows/ci/badge.svg)](https://github.com/detailobsessed/spm-search-mcp/actions?query=workflow%3Aci)
[![release](https://github.com/detailobsessed/spm-search-mcp/workflows/release/badge.svg)](https://github.com/detailobsessed/spm-search-mcp/actions?query=workflow%3Arelease)
[![documentation](https://img.shields.io/badge/docs-mkdocs-708FCC.svg?style=flat)](https://detailobsessed.github.io/spm-search-mcp/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/detailobsessed/spm-search-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/detailobsessed/spm-search-mcp)

MCP server to help your coding agent search the Swift package index

## Branch protection

The CI workflow includes a `ci-pass` gate job that aggregates the status of all CI jobs.
Add a [branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-a-branch-protection-rule/managing-a-branch-protection-rule) for `main` requiring the **`ci-pass`** status check to pass before merging.

