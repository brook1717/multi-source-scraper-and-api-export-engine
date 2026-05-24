# Multi-Source Data Scraper & API Export Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-grade, modular Python CLI tool for scraping, fetching, processing, and exporting data from multiple sources — including REST APIs, web pages, and JavaScript-rendered sites protected by Cloudflare.


---

## Features

| Category | Capability |
|----------|-----------|
| **Data Fetching** | REST API client with automatic pagination and retry logic |
| **Anti-Bot Bypass** | Playwright-based stealth browser with fingerprint evasion |
| **Proxy Rotation** | Round-robin proxy manager loaded from a file |
| **Data Processing** | Pandas-powered cleaning, deduplication, and filtering |
| **Export Formats** | CSV and JSON output with clean, index-free formatting |
| **Retry & Resilience** | Exponential backoff (tenacity) for 429 / 5xx errors |
| **Logging** | Dual-output logging (console + file) with configurable levels |
| **CLI Interface** | Fully parameterized via argparse with sensible defaults |

---

## Architecture

```
src/
├── main.py            # Orchestrator — wires the full pipeline
├── cli.py             # Argument parsing (argparse)
├── fetcher.py         # DataFetcher (requests) + BrowserFetcher (Playwright)
├── processor.py       # DataProcessor — clean, deduplicate, filter
├── exporter.py        # DataExporter — CSV / JSON export
├── proxy_manager.py   # ProxyManager — round-robin proxy rotation
└── logger.py          # Centralized logging setup
tests/
└── test_processor.py  # Unit tests (pytest)
output/                # Generated export files
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/brook1717/multi-source-scraper-and-api-export-engine.git
cd multi-source-scraper-and-api-export-engine
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers (only if using `--use-browser`)

```bash
python setup_playwright.py
```

---

## Usage

### Basic API Fetch → CSV

```bash
python -m src.main \
  --source "https://jsonplaceholder.typicode.com/posts" \
  --output posts.csv
```

### API Fetch with Search & JSON Export

```bash
python -m src.main \
  --source "https://api.example.com/products" \
  --search "laptop" \
  --format json \
  --output laptops.json
```

### Apply Column Filter

```bash
python -m src.main \
  --source "https://api.example.com/users" \
  --output active_users.csv \
  --filter-key status \
  --filter-value "active"
```

### Stealth Browser Mode (Cloudflare-protected sites)

```bash
python -m src.main \
  --source "https://protected-site.com/data" \
  --output scraped.csv \
  --use-browser
```

### Full Pipeline with Proxy Rotation

```bash
python -m src.main \
  --source "https://protected-site.com/data" \
  --output results.json \
  --format json \
  --use-browser \
  --proxies proxies.txt \
  --filter-key category \
  --filter-value "electronics"
```

---

## Proxy File Format

Create a `proxies.txt` file with one proxy per line:

```
http://user:pass@192.168.1.1:8080
http://user:pass@192.168.1.2:8080
socks5://user:pass@10.0.0.1:1080
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## CLI Reference

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--source` | string | Yes | URL or API endpoint to fetch |
| `--output` | string | Yes | Output filename (saved in `output/`) |
| `--search` | string | No | Search term passed as query parameter |
| `--format` | csv \| json | No | Export format (default: `csv`) |
| `--filter-key` | string | No | Column name to filter on |
| `--filter-value` | string | No | Value to match (case-insensitive for strings) |
| `--use-browser` | flag | No | Use Playwright stealth browser |
| `--proxies` | string | No | Path to proxy list file |

---

## Tech Stack

- **Python 3.10+**
- **Requests** — HTTP client
- **Pandas** — Data manipulation & export
- **Tenacity** — Retry with exponential backoff
- **Playwright** — Headless browser automation
- **playwright-stealth** — Anti-detection patches
- **fake-useragent** — Realistic User-Agent generation
- **Pytest** — Unit testing framework

---

## Engineering Notes

- The `DataFetcher` automatically paginates APIs using `?page=N` and stops when empty results are returned.
- The `BrowserFetcher` applies stealth patches to evade basic bot detection (navigator.webdriver, etc.).
- If Cloudflare Turnstile or advanced CAPTCHAs still block requests, consider routing through a proxy API service (ScrapingBee, ScraperAPI, BrightData Web Unlocker).
- All pipeline steps are decoupled — swap any fetcher, processor, or exporter without touching the rest.

---


---

<p align="center">
  Built by <a href="https://birukkasahun.com">Biruk Kasahun</a>
</p>
