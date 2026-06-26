# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the official Python SDK for the Pangram Labs API, which provides AI-generated text detection and plagiarism checking services.

## Build and Development Commands

**Install dependencies:**
```bash
poetry install
```

**Run tests:**
```bash
poetry run python -m unittest tests/pangram_test.py
```
Most tests are mocked unit tests. Live plagiarism coverage is skipped unless `PANGRAM_API_KEY` is set.

**Run a single test:**
```bash
poetry run python -m unittest tests.pangram_test.TestPredict.test_predict
```

**Build documentation:**
```bash
poetry install --with docs
cd docs && make html
```

## Architecture

The SDK is minimal with two main files:

- `pangram/__init__.py` - Exports `Pangram` (alias for `PangramText`) as the main client class
- `pangram/text_classifier.py` - Contains the `PangramText` class with all API methods

### API Methods

- `predict(text)` - Main async inference endpoint for AI-assistance detection with segment-level analysis
- `check_plagiarism(text)` - Plagiarism detection against online content database

### API Configuration

API endpoints are defined as constants at the top of `text_classifier.py`. The SDK uses `requests` for HTTP calls and authenticates via `x-api-key` header. The main prediction call submits a task and polls until completion.

## Secrets, tokens, and API keys

This is a public SDK and users authenticate with a Pangram API key, so be especially careful never to commit or leak credentials.

- Treat all credentials (API keys, access tokens, OAuth secrets, passwords, private keys, connection strings) as sensitive — never let them enter the repo.
- Never hardcode secrets in source, config, tests, fixtures, comments, examples, or commit messages. Load them from environment variables (e.g. `PANGRAM_API_KEY`) or a secret manager at runtime.
- Never commit secret files. Real values go in gitignored `.env` / local config; commit only a `.env.example` with placeholders. Verify a file is gitignored before staging it.
- Never print or log secrets (stdout, logs, error messages, screenshots or recordings shared in chat). Redact them when reporting output.
- Use obvious placeholders in docs, sample code, and README snippets (e.g. `YOUR_PANGRAM_API_KEY`), never real values.
- **Scan every diff before pushing.** Before committing, and again before pushing, review the full diff (`git diff`, `git diff --cached`) and confirm no keys, tokens, or other sensitive data are present — including unintentionally staged files. A quick check:
  ```bash
  git diff --cached | grep -iE 'api[_-]?key|secret|token|password|BEGIN [A-Z ]*PRIVATE KEY|sk-[a-zA-Z0-9]'
  ```
  If anything matches, remove it and rotate the exposed credential before pushing.
- If a secret was already committed, treat it as compromised: rotate/revoke it immediately, remove it from the working tree, and remember that a follow-up commit does **not** purge git history. Flag it so the history can be scrubbed (e.g. `git filter-repo` or BFG) and the credential rotated.
