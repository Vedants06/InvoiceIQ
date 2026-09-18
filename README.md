# InvoiceIQ

**An invoice never lies on its own. Put it next to the contract and the timesheet, and the truth shows up.**

InvoiceIQ takes an invoice and cross-examines it against the contract that governs it and the timesheet that backs it up. Out comes a list of inconsistencies, billing anomalies, and financial risk indicators, each one backed by evidence, rolled up into a single explainable risk score for a human reviewer to act on.

> **Core principle:** AI understands documents. Backend code makes decisions based on verified data. AI explains those decisions. The LLM never independently determines whether an invoice is risky.

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

cp .env.example .env          # optional: add OPENAI_API_KEY for live extraction
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

## A 60-second demo (no AI key required)

1. Open **Upload & Analyze**.
2. Click **Demo scenarios -> Critical Invoice**.
3. On the analysis screen, walk through: the risk gauge (**90 CRITICAL**), the verification summary (rate / hours / amount / timesheet, each flagged pass or fail), the evidence-backed risk indicators (invoice vs. contract vs. timesheet, side by side), the document preview tab, the AI assessment, and the deterministic explanation underneath it.
4. Click **Reject Invoice**, add a reason, confirm. It moves to **Rejected**.
5. Check the **Review Queue**, **Invoices** list, and **Dashboard** (risk distribution chart).
6. Repeat with **Clean Invoice** (0, LOW, approved-looking) and **Timesheet Anomaly** (25, MEDIUM, the quiet issue that only a three-source reconciliation would ever catch).

Live uploads work as soon as `OPENAI_API_KEY` is set. Without it, the UI simply steers you toward Demo Mode instead of breaking.

---

## Environment variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | no | local SQLite | SQLAlchemy database URL |
| `OPENAI_API_KEY` | no | none | Enables live AI extraction/explanation |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | OpenAI model |
| `MAX_UPLOAD_MB` | no | `10` | Upload size limit |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Allowed frontend origins |

Secrets never touch the frontend. API keys live only in `backend/.env`.

---

## How it was built

Built incrementally against the PRD, one step at a time, each shipped as its own pull request.

- [x] **Step 1 -- Project setup:** FastAPI + React/Vite/Tailwind shells, database/session/config layer, health check, app layout, README.
- [x] **Step 2 -- Database models:** invoices, contracts, timesheets, documents, anomalies, reviews, with relationships and portable enums.
- [x] **Steps 3-4 -- Backend API & file upload:** `POST /api/invoices/upload` (extension validation, size limit, filename sanitization, disk storage), `GET /api/invoices` (filters), `GET /api/invoices/{id}`.
- [x] **Steps 5-7 -- Extraction & timesheet parsing:** OpenAI Structured Outputs client with Pydantic-validated invoice/contract schemas (PDF via PyMuPDF, image invoices via vision), a deterministic CSV/XLSX timesheet parser (no LLM involved), and `POST /api/invoices/{id}/analyze` with graceful 503/422 failure handling.
- [x] **Steps 8-12 -- Verification, reconciliation, anomalies, risk, explanation:** a deterministic 8-check verification engine (vendor, period, currency, rate, hours, amount, arithmetic), timesheet reconciliation, an anomaly engine with structured evidence, a deterministic risk score (LOW/MEDIUM/HIGH/CRITICAL), and an AI explanation layer that never fails the analysis. All three demo scenarios score exactly as specified.
- [x] **Steps 13-16 -- Analysis UI, review workflow, review queue, dashboard:** the full React app -- an Upload page with dropzones and a visible processing pipeline; the Invoice Analysis screen (risk score dial, invoice/contract/timesheet facts, verification summary, evidence-backed anomaly cards, AI assessment, approve/reject with a required rejection reason); a Review Queue for pending decisions; an Invoices list; a live Dashboard. Backend review and stats endpoints with guards (completed-only, reject requires a reason, one review per invoice).
- [x] **Step 17 -- Demo Mode:** three deterministic scenarios (Clean 0/LOW, Critical 90/CRITICAL, Timesheet Anomaly 25/MEDIUM), built through the exact same pipeline and response shape as a real analysis, with a deterministic explanation fallback so they work without any AI key. `POST /api/demo/{scenario}` plus one-click scenario cards on the Upload page; demo invoices support the full review workflow and show up in the list, queue, and dashboard like any other.
- [x] **Steps 18-19 -- Tests & polish:** 88 backend tests (upload, models, timesheet, extraction, verification, reconciliation, anomalies, risk, analyze, review, stats, demo, historical); error/empty/processing states across the UI.
- [x] **P1 -- Historical vendor analysis (UNUSUAL_AMOUNT):** compares an invoice against a vendor's prior completed same-currency invoices, and flags a total 50% or more above historical average as an evidence-backed anomaly (PRD §19), with a vendor-history card on the analysis screen.
- [x] **P1 -- Dashboard chart:** a Recharts risk-level distribution (LOW/MEDIUM/HIGH/CRITICAL) fed by a `risk_distribution` stats field.
- [x] **P1 -- Document preview (PRD §27):** a tabbed invoice/contract/timesheet preview beside the analysis. Real uploads embed the original file (PDF inline in an iframe, images rendered directly) via a path-traversal-safe `GET /api/documents/{id}/raw`; demo documents show a structured preview built from verified data instead.
- [x] **P1 -- Extraction coverage:** a deterministic field-presence measure (share of expected invoice/contract fields successfully extracted) shown on the analysis screen -- a backend metric, not an AI confidence score.
- [x] **P1 -- Better filtering:** a reusable filter bar on Invoices and Review Queue, with risk level, status, and vendor search, all filtered server-side.
- [x] **P2 -- CSV export:** `GET /api/invoices/{id}/export` downloads the full deterministic analysis (invoice/contract/timesheet facts, verification checks with status, anomalies with evidence) via an "Export CSV" button on the analysis screen. Deterministic data only, no AI text.
- [x] **Polish & hardening (§55):** an animated SVG risk gauge on the priority screen, an invoice line-items breakdown card, and full PRD §54 edge-case coverage (clean, critical, timesheet anomaly, missing timesheet, invalid document, currency mismatch, arithmetic mismatch including tax no-false-positive, AI extraction failure, AI explanation failure) -- 96 tests in total.
- [x] **UI redesign -- design system & rebuilt screens:** a warm, print-inspired interface on ink-on-paper stock -- Newsreader serif headings and figures over a system sans, hairline rules instead of shadows, an olive accent, and a warmed risk palette (sage / ochre / terracotta / brick). Shared tokens and primitives (`paper`, `accent`, `risk` scales; `.card` / `.panel` / `.btn` / `.chip` / `.input` / `.skeleton`) live in `tailwind.config.js`, `src/index.css`, and `src/components/ui`. A ruled app shell with a serif wordmark, active-underline nav, and mobile bottom navigation; a dashboard with ruled stat cards, a chart with legend, and a needs-attention list; segmented filters and an invoice table with vendor monograms and a timesheet marker; a two-column upload screen with dropzones, a progress pipeline, and demo cards; a 240-degree risk gauge with band legend and top risk contributors; utilisation bars in the facts panel; severity-tinted anomaly cards; a confirmation step on approve/reject; a tabbed document preview; and skeleton, empty, loading, and error states on every screen.
