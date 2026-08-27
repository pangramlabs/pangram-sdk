# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the official Python SDK for the Pangram Labs API, which provides
model-selectable AI-generated text detection, bulk and file analysis, and
plagiarism checking services.

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

The SDK is intentionally small:

- `pangram/__init__.py` - Exports `Pangram` (alias for `PangramText`) and public response schemas
- `pangram/text_classifier.py` - Contains the `PangramText` class with all API methods
- `pangram/schemas.py` - Defines the public typed dictionary response contracts

### API Methods

- `list_models()` - Returns the detection models available to the API key
- `predict(text, ..., *, model=None)` - Main async inference endpoint for AI-assistance detection with segment-level analysis
- `submit_bulk(text=None, items=None, *, model=None, idempotency_key=None)` - Submits model-selectable asynchronous bulk work; always sends an `Idempotency-Key` header (auto-generated per call unless supplied) so exact retries with the same key replay instead of double-billing
- `predict_file()` / `predict_files()` - Uploads documents using the file service's current default model
- `check_plagiarism(text)` - Plagiarism detection against online content database

### API Configuration

API endpoints are defined as constants at the top of `text_classifier.py`. The
SDK uses `requests` for HTTP calls and authenticates via the `x-api-key` header.
Text and bulk submissions accept a keyword-only `model`; callers should pass
`model="default"` explicitly or discover available selectors with
`list_models()`. Omitting `model` temporarily preserves the server-default
behavior and emits a deprecation warning; explicit selection becomes required
after September 30, 2026. The main prediction call submits a task and polls
until completion.
