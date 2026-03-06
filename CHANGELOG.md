# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- version list -->

## v0.6.1 (2026-03-06)

### Bug Fixes

- Add shellcheck shell directive to .envrc
  ([`3619eea`](https://github.com/detailobsessed/spm-search-mcp/commit/3619eeacbcc87a8a86ffd5e3510e8ed7f6bd9876))

- Broaden exception handling from ConnectError to NetworkError
  ([`f545f9c`](https://github.com/detailobsessed/spm-search-mcp/commit/f545f9cbcd0ad06a97dbba8a9b5844fd0ea76c49))

- Broaden exception handling from NetworkError to TransportError
  ([`523a394`](https://github.com/detailobsessed/spm-search-mcp/commit/523a394576eeb4c8ddff0267104de263b0405033))

- Patch scraper.httpx in test_server.py (consistent with test_error_handling.py)
  ([`8b16e37`](https://github.com/detailobsessed/spm-search-mcp/commit/8b16e373ebfcfb9551efd0fac9cab08534bfa42a))

- Remove curl_cffi, swap to httpx, put project on hold
  ([`9a1bbbb`](https://github.com/detailobsessed/spm-search-mcp/commit/9a1bbbb0c41a832a9ea665bac25e83688268611a))

- Split SC2155 export in .envrc
  ([`64cfea6`](https://github.com/detailobsessed/spm-search-mcp/commit/64cfea6d97f93c23038d639eb69d4ae861d3180c))

### Chores

- Bump all dependencies (uv sync --upgrade)
  ([`4553742`](https://github.com/detailobsessed/spm-search-mcp/commit/4553742b0b03ce9a1095e51fadf59640a90a2677))

- Rename repo to spm-search-mcp, add badges, fix install instructions
  ([#16](https://github.com/detailobsessed/spm-search-mcp/pull/16),
  [`4c1fde9`](https://github.com/detailobsessed/spm-search-mcp/commit/4c1fde9a43e0311a96c8077953dd6c4ef28480d8))


## v0.6.0 (2026-02-27)

### Chores

- Update template to v0.31.3 ([#14](https://github.com/detailobsessed/spm-search-mcp/pull/14),
  [`27c7dd1`](https://github.com/detailobsessed/spm-search-mcp/commit/27c7dd1a94fafcfa058c977fca90e9168fffba15))

### Features

- Add list_search_filters discovery tool
  ([#15](https://github.com/detailobsessed/spm-search-mcp/pull/15),
  [`6194804`](https://github.com/detailobsessed/spm-search-mcp/commit/61948045dc880750c91d40d8a7c7028535bdca2b))


## v0.5.0 (2026-02-27)

### Features

- Add exclusion filter support for platforms and product_type
  ([#13](https://github.com/detailobsessed/spm-search/pull/13),
  [`ff7ac54`](https://github.com/detailobsessed/spm-search/commit/ff7ac54362f1ed57d4d5855195ef41259eb46496))


## v0.4.0 (2026-02-27)

### Chores

- Add __main__.py for python -m spm_search_mcp
  ([#4](https://github.com/detailobsessed/spm-search/pull/4),
  [`5100d44`](https://github.com/detailobsessed/spm-search/commit/5100d443b87b00634734a836d8a6956d00b83ea8))

- Update template, dependencies, and hook versions
  ([#8](https://github.com/detailobsessed/spm-search/pull/8),
  [`970a2e9`](https://github.com/detailobsessed/spm-search/commit/970a2e93f99871162461d9914edef37a5b145bf6))

### Documentation

- Rewrite README with fastmcp install, full tool docs, error handling, and design patterns
  ([#6](https://github.com/detailobsessed/spm-search/pull/6),
  [`d4398ef`](https://github.com/detailobsessed/spm-search/commit/d4398efc7f89634a9448ff2d7022d4151756da7a))

### Features

- Add last_activity_before and last_commit_before date filter params
  ([#12](https://github.com/detailobsessed/spm-search/pull/12),
  [`1d32587`](https://github.com/detailobsessed/spm-search/commit/1d325876c16309668593722cd0bc3cc9e8a3a6d3))

### Testing

- Get coverage above 90% fail-under gate (91.99%)
  ([#5](https://github.com/detailobsessed/spm-search/pull/5),
  [`ad7f4b6`](https://github.com/detailobsessed/spm-search/commit/ad7f4b601dd95ebc9dcbba32c14bdcf4887f3088))


## v0.3.0 (2026-02-26)

### Features

- Add error resilience with ERROR_CLASSIFICATION and RECOVERY_GUIDE patterns
  ([#3](https://github.com/detailobsessed/spm-search/pull/3),
  [`e603455`](https://github.com/detailobsessed/spm-search/commit/e603455776ab414cbfb0881199560247ce719d24))


## v0.2.0 (2026-02-26)

### Features

- Implement SPI search MCP server with scraper, models, and tests
  ([#2](https://github.com/detailobsessed/spm-search/pull/2),
  [`10bafdf`](https://github.com/detailobsessed/spm-search/commit/10bafdfef428a5efd27e2e1a841d0263de329f3a))


## v0.1.0 (2026-02-25)

- Initial Release
