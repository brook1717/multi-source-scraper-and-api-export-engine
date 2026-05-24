<div align="center">

# Multi-Source Data Scraper & API Export Engine

### Event-Driven, Serverless Extraction Engine

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900.svg?style=flat&logo=aws-lambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![AWS Fargate](https://img.shields.io/badge/AWS-Fargate-FF9900.svg?style=flat&logo=amazon-ecs&logoColor=white)](https://aws.amazon.com/fargate/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC.svg?style=flat&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**A production-grade, serverless data extraction platform that intelligently routes workloads between AWS Lambda and ECS Fargate, features AI-powered self-healing parsers, and delivers structured data via webhooks — all at near-zero idle cost.**

[Quick Start](#quick-start) · [Architecture](#architecture) · [How It Works](#how-it-works) · [Deployment](#deployment) · [API Reference](#api-reference)

</div>

---

## Why This Exists

Traditional scrapers break when websites change their layout. They require always-on servers that burn money while idle. They can't scale from 10 URLs to 10,000 without re-architecture.

This engine solves all three problems:

- **Self-healing** — AI detects broken selectors and extracts data anyway
- **Zero idle cost** — SQS + Lambda + Fargate = pay only when scraping
- **Infinite scale** — event-driven architecture scales horizontally with no code changes

---

## Features

| Layer | Capability | Tech |
|-------|-----------|------|
| **Ingestion** | REST API, stealth browser, proxy rotation | `requests`, `Playwright`, `playwright-stealth` |
| **Queue** | Zero-maintenance message broker, zero idle cost | AWS SQS (FIFO) |
| **Compute** | Smart routing — lightweight vs. heavy workloads | AWS Lambda + ECS Fargate |
| **Extraction** | Two-stage: DOM selectors → AI fallback | `BeautifulSoup`, Gemini 2.0 Flash |
| **Storage** | Idempotent upserts, no duplicates ever | PostgreSQL + `ON CONFLICT` |
| **Delivery** | Real-time push to client endpoints | Webhook with exponential backoff |
| **API** | RESTful job dispatch and result retrieval | FastAPI + Uvicorn |
| **Marketplace** | Plug-and-play cloud actor | Apify SDK |
| **Infrastructure** | One-command cloud deployment | Terraform + Docker |

---

## Architecture

```
                                ┌─────────────────────────────────────────────┐
                                │              CLIENT LAYER                    │
                                │   CLI  ·  FastAPI  ·  Apify Actor           │
                                └──────────────────┬──────────────────────────┘
                                                   │ POST /jobs
                                                   ▼
                              ┌──────────────────────────────────────────┐
                              │           AWS SQS (FIFO Queue)           │
                              │     Zero idle cost · Guaranteed order    │
                              └──────────────────┬──────────────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                    ┌───────────────────────┐   ┌───────────────────────────┐
                    │     AWS LAMBDA         │   │      ECS FARGATE           │
                    │  Standard HTTP fetch   │   │  Playwright stealth mode   │
                    │  ~$0.0000002/request   │   │  JS-rendered pages         │
                    │  DataFetcher           │   │  Anti-bot bypass           │
                    └───────────┬───────────┘   └─────────────┬─────────────┘
                                │                             │
                                └──────────────┬──────────────┘
                                               ▼
                              ┌──────────────────────────────────────────┐
                              │       COST-AWARE EXTRACTION ENGINE        │
                              │                                          │
                              │  Stage 1: BeautifulSoup DOM Selectors    │
                              │           (zero cost, ~5ms)              │
                              │                    │                      │
                              │         required fields = None?           │
                              │                    │                      │
                              │  Stage 2: Gemini 2.0 Flash + Pydantic   │
                              │           (HTML→Markdown→Structured)     │
                              │           (~$0.001/page, only if needed) │
                              └──────────────────┬──────────────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                    ┌───────────────────────┐   ┌───────────────────────────┐
                    │     POSTGRESQL         │   │    WEBHOOK DELIVERY        │
                    │  Idempotent upsert    │   │  Zapier · Make · Custom    │
                    │  SHA-256 dedup hash   │   │  Retry w/ backoff          │
                    └───────────────────────┘   └───────────────────────────┘
```

### Source Tree

```
├── src/
│   ├── main.py              # CLI orchestrator
│   ├── api.py               # FastAPI endpoints (POST /jobs, GET /jobs/{id})
│   ├── cli.py               # Argument parsing
│   ├── fetcher.py           # DataFetcher + BrowserFetcher (Playwright)
│   ├── processor.py         # Cost-aware two-stage extraction engine
│   ├── ai_parser.py         # Gemini LLM structured extraction
│   ├── queue_manager.py     # SQS message send/poll/delete
│   ├── lambda_handler.py    # AWS Lambda entry point
│   ├── delivery.py          # WebhookDeliverer with retry
│   ├── exporter.py          # CSV / JSON file export
│   ├── proxy_manager.py     # Round-robin proxy rotation
│   ├── worker.py            # Celery worker (legacy/local dev)
│   ├── tasks.py             # Celery task chains (legacy/local dev)
│   ├── logger.py            # Centralized logging
│   └── db/
│       ├── database.py      # Async SQLAlchemy engine
│       ├── models.py        # ScrapeJob + ScrapedRecord ORM
│       └── crud.py          # Idempotent upsert (ON CONFLICT)
├── terraform/               # AWS infrastructure as code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── tests/
│   └── test_processor.py    # Unit tests (pytest)
├── main_apify.py            # Apify Actor entry point
├── Dockerfile               # Multi-stage (api + worker targets)
├── docker-compose.yml       # Local dev orchestration
├── print_secrets_template.py # Generates .env.example
└── requirements.txt
```

---

## How It Works

### 1. Intelligent Workload Routing (Lambda ↔ Fargate)

When a URL enters the SQS queue, the Lambda handler inspects the message:

| Condition | Route | Cost |
|-----------|-------|------|
| Standard HTTP (no JS rendering needed) | **Lambda** executes `DataFetcher` directly | ~$0.0000002 |
| JavaScript-rendered page (`use_browser=true`) | Lambda triggers **ECS Fargate** task | ~$0.01/min |

This hybrid approach keeps costs near zero for API-heavy workloads while supporting full browser rendering only when necessary.

### 2. Idempotent Database Storage

Every record is stored with a **SHA-256 hash** derived from the source URL + payload content:

```python
# src/db/crud.py
stmt = pg_insert(ScrapedRecord).values(...)
stmt = stmt.on_conflict_do_update(
    index_elements=["source_url"],
    set_={"payload": stmt.excluded.payload, ...}
)
```

**Result:** You can re-scrape the same URL 1,000 times — only one row exists. If the data changed, it updates in place. Zero duplicates, ever.

### 3. Cost-Aware AI Self-Healing Parser

The extraction engine **never** calls the LLM unnecessarily:

```
Page HTML ──→ BeautifulSoup (free, ~5ms)
                    │
              All required fields present?
                    │
            ┌───────┴────────┐
            │ YES            │ NO (layout changed)
            ▼                ▼
      Return data     HTML → Markdown (80% token reduction)
                             │
                      Gemini 2.0 Flash + Pydantic
                             │
                      Return structured data
                      + LOG WARNING: "Update selectors"
```

**Key insight:** The system logs every AI fallback trigger, telling you exactly which site's selectors need updating — so you can fix them and stop paying for AI on that site.

### 4. Premium Webhook Delivery

After extraction, data is pushed directly to client systems in real-time:

- Zapier, Make.com, n8n, Pipedream, or any custom endpoint
- Automatic retry with exponential backoff (2s → 4s → 8s → 16s → 32s)
- Batch delivery (configurable chunk size) to avoid overwhelming endpoints
- 429/5xx retries, permanent failure on 4xx client errors

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/brook1717/multi-source-scraper-and-api-export-engine.git
cd multi-source-scraper-and-api-export-engine
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt
python setup_playwright.py  # Only for browser mode
```

### 2. Configure Environment

```bash
python print_secrets_template.py  # Generates .env.example
cp .env.example .env              # Fill in your secrets
```

### 3. Run Locally

```bash
# Simple API fetch
python -m src.main --source "https://api.example.com/data" --output results.csv

# Browser mode with proxy and webhook delivery
python -m src.main \
  --source "https://protected-site.com" \
  --output data.json --format json \
  --use-browser --proxies proxies.txt \
  --webhook "https://hooks.zapier.com/hooks/catch/123/abc/"

# Dispatch to SQS (serverless mode)
python -m src.main \
  --source "https://api.example.com/data" \
  --output results.csv --queue
```

### 4. Run via FastAPI

```bash
uvicorn src.api:app --reload

# Dispatch a batch job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/page1", "https://example.com/page2"], "use_browser": true}'

# Check results
curl http://localhost:8000/jobs/{job_id}
```

---

## Deployment

### Docker (Local / VPS)

```bash
docker-compose up --build
```

Spins up: **FastAPI** (port 8000) + **Worker** (×2 replicas) + **PostgreSQL** + **Redis**

### AWS (Terraform)

```bash
cd terraform
terraform init
terraform plan \
  -var="db_password=YOUR_SECURE_PASSWORD" \
  -var="api_image=YOUR_ECR_URI:latest" \
  -var="worker_image=YOUR_ECR_URI:latest" \
  -var="gemini_api_key=YOUR_KEY"
terraform apply
```

Provisions: **VPC** + **RDS** (db.t4g.micro) + **ElastiCache Redis** + **ECS Fargate** + **ALB** + **CloudWatch Logs**

---

## API Reference

### CLI Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--source` | string | Yes | URL or API endpoint to fetch |
| `--output` | string | Yes | Output filename (saved in `output/`) |
| `--search` | string | No | Search term passed as query parameter |
| `--format` | csv \| json | No | Export format (default: `csv`) |
| `--filter-key` | string | No | Column name to filter on |
| `--filter-value` | string | No | Value to match (case-insensitive) |
| `--use-browser` | flag | No | Use Playwright stealth browser |
| `--proxies` | string | No | Path to proxy list file |
| `--queue` | flag | No | Dispatch to AWS SQS instead of local execution |
| `--webhook` | string | No | Webhook URL for real-time data delivery |

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/jobs` | Submit URLs for scraping, returns `job_id` |
| `GET` | `/jobs/{job_id}` | Retrieve job status and extracted records |

---

## Cost Analysis

| Component | Idle Cost | Per-1000-URLs Cost |
|-----------|-----------|-------------------|
| SQS | $0.00 | $0.0004 |
| Lambda (standard fetch) | $0.00 | $0.20 |
| Fargate (browser fetch) | $0.00 | ~$2.00 |
| RDS (db.t4g.micro) | ~$12/mo | — |
| AI Fallback (Gemini Flash) | $0.00 | ~$0.05 (only when triggered) |
| **Total (API-heavy workload)** | **~$12/mo** | **~$0.25/1000 URLs** |

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| **Language** | Python 3.12+ |
| **HTTP Client** | Requests + Tenacity (retry) |
| **Browser** | Playwright + playwright-stealth |
| **Queue** | AWS SQS (FIFO) |
| **Compute** | AWS Lambda + ECS Fargate |
| **Database** | PostgreSQL 16 (RDS) + SQLAlchemy Async |
| **AI/ML** | Google Gemini 2.0 Flash + Instructor + Pydantic |
| **API** | FastAPI + Uvicorn |
| **Delivery** | Webhook (Zapier/Make/Custom) |
| **IaC** | Terraform + Docker |
| **Marketplace** | Apify SDK |
| **Testing** | Pytest |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## License

MIT

---

<p align="center">
  <strong>Built by <a href="https://birukkasahun.com">Biruk Kasahun</a></strong><br/>
  <sub>Enterprise-grade data infrastructure for the modern web.</sub>
</p>
