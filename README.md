# InvoiceIQ

**An invoice never lies on its own. Put it next to the contract and the timesheet, and the truth shows up.**

InvoiceIQ takes an invoice and cross-examines it against the contract that governs it and the timesheet that backs it up. Out comes a list of inconsistencies, billing anomalies, and financial risk indicators, each one backed by evidence, rolled up into a single explainable risk score for a human reviewer to act on.

---

## How the pieces fit together

```
frontend/   React + TypeScript + Vite + Tailwind CSS
backend/    Python + FastAPI + SQLAlchemy + Pydantic
database    SQLite by default (zero setup) -- PostgreSQL via DATABASE_URL
AI          OpenAI structured outputs (extraction + explanation only)
```

Verification, anomaly detection, and risk scoring are all deterministic and all live in the backend. The frontend renders results; it never calculates a risk score itself.

### Who does what

| AI handles | AI never touches |
| --- | --- |
| Document understanding & extraction | Arithmetic |
| Contract field interpretation | Risk scoring |
| Explanation generation (from verified facts) | Business-rule / contract comparisons |
| | Evidence generation |
| | Approval decisions |

If the AI API is unreachable, extraction can fall back to Demo Mode and the deterministic pipeline keeps running regardless. A failed AI explanation never fails an analysis, it's the one place the system is allowed to shrug.

---

## Getting it running locally

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

SQLite is the default (`backend/invoiceiq.db`, created automatically on first run). To point at PostgreSQL instead, set in `.env`:

```
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/invoiceiq
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

The Vite dev server proxies `/api/*` to `http://localhost:8000`, so there's nothing extra to configure.

### 3. Tests

```bash
cd backend
pytest
```

---

## Features

- **Three-way verification** -- an 8-check deterministic engine cross-references invoice, contract, and timesheet on vendor, period, currency, rate, hours, amount, and arithmetic.
- **Timesheet reconciliation** -- catches billed hours that don't match logged hours, even when every other field looks clean.
- **Evidence-backed anomaly detection** -- every flagged issue ships with the actual invoice/contract/timesheet values side by side, not just a label.
- **Explainable risk scoring** -- a deterministic LOW/MEDIUM/HIGH/CRITICAL score with an AI-written explanation layered on top of verified facts, never the other way around.
- **Historical vendor analysis** -- flags a total 50%+ above a vendor's historical average against their prior completed same-currency invoices.
- **Review workflow** -- approve or reject with a required rejection reason, backed by guards (completed-only, one review per invoice).
- **Document preview** -- tabbed invoice/contract/timesheet preview, with real files embedded inline via a path-traversal-safe raw document endpoint.
- **Live dashboard** -- risk distribution chart, review queue, and a filterable invoice list (risk level, status, vendor search).
- **CSV export** -- downloads the full deterministic analysis (facts, verification checks, anomalies with evidence) per invoice.
- **Demo Mode** -- three deterministic scenarios (Clean, Critical, Timesheet Anomaly) that run through the exact same pipeline as a real analysis, so the app works end to end with no AI key at all.

---

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | SQLite by default, PostgreSQL via `DATABASE_URL` |
| Document extraction | PyMuPDF (PDF text), OpenAI vision (image invoices) |
| Timesheet parsing | Deterministic CSV/XLSX parser, no LLM involved |
| AI | OpenAI Structured Outputs, used only for extraction and explanation |
| Charts | Recharts |
| Testing | pytest (96 backend tests) |

---

## License

MIT.

---

*InvoiceIQ doesn't guess whether an invoice is risky. It checks.*