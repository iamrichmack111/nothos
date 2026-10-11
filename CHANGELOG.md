# Changelog

All notable changes to NOTHOS are documented here.

This changelog reflects verified repository history and the v6 release.
Earlier development milestones are not assigned invented dates.

## [6.0.0] — Medusa Edition

Release commit: `145594a`

### Added

- Unified `nothos` command-line interface.
- LSJ and mythology research dispatch.
- FastAPI REST server.
- `/health` endpoint.
- `/api/v1/search` endpoint.
- `/api/v1/research` endpoint.
- JSON, Markdown, HTML, and text exporters.
- Medusa terminal banner integration.
- Installation diagnostics.
- macOS/Linux installer.
- Windows PowerShell installer.
- Python project packaging metadata.
- Expanded README.
- Five automated CLI/API tests.

### Verified

- CLI installation and help.
- Five passing automated tests.
- API health check: HTTP 200.
- Greek LSJ semantic search: HTTP 200.
- Semantic results returned as structured JSON.

### Changed

- Expanded Python dependencies to support FastAPI and Uvicorn.
- Added Git ignore rules for generated packaging files and local databases.
- Removed a tracked SQLite journal from version control.

### Known limitations

- Semantic ranking does not guarantee exact-lemma priority.
- AI research API requires further end-to-end verification.
- Windows and Linux installers require platform testing.
- Source-checkout installation is currently the primary supported workflow.
- API authentication is not implemented; bind to localhost.
- Research databases are not bundled.

## Earlier development

Earlier NOTHOS development includes the existing LSJ research engines,
mythology research tools, embedding databases, and Medusa terminal theme.

Consult the repository's original Git history for the actual sequence
and dates of those changes.

## Planned — 6.1

- Exact Greek lemma prioritization.
- Ollama API integration tests.
- Distributable wheel packaging.
- Windows and Linux installation validation.
- GitHub Actions CI.
- API security improvements.
- Structured AI evidence responses.
- Greek lexical regression tests.

## Planned — 7.0

- Greek primary-source corpus integration.
- Interactive browser-based research workbench.
