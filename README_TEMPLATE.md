# spm-search-mcp — Template Documentation

This file is managed by [copier-uv-bleeding](https://github.com/detailobsessed/copier-uv-bleeding)
and kept up to date on every `copier update`. Your project README lives in `README.md`.

## Badges

Copy these into your `README.md` to show project status:

```markdown
[![ci](https://github.com/detailobsessed/spm-search-mcp/workflows/ci/badge.svg)](https://github.com/detailobsessed/spm-search-mcp/actions?query=workflow%3Aci)
[![release](https://github.com/detailobsessed/spm-search-mcp/workflows/release/badge.svg)](https://github.com/detailobsessed/spm-search-mcp/actions?query=workflow%3Arelease)
[![documentation](https://img.shields.io/badge/docs-zensical-708FCC.svg?style=flat)](https://detailobsessed.github.io/spm-search-mcp/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/detailobsessed/spm-search-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/detailobsessed/spm-search-mcp)
```

## Installation

```bash
pip install spm-search-mcp
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install spm-search-mcp
```

## Template Updates

This project was generated with [copier-uv-bleeding](https://github.com/detailobsessed/copier-uv-bleeding).

To pull the latest template changes (smart 3-way merge that respects your project changes):

```bash
poe update-template
```

This runs `copier update --trust . --skip-answered --defaults` followed by `uv sync --upgrade` and `prek autoupdate` to keep dependencies and hooks current.

To re-apply the template from scratch (ignores your project diff):

```bash
copier recopy --trust --overwrite .
```
